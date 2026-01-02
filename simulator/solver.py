"""
Solver for the 3CB simulator.
Takes any two hands and finds optimal play using minimax.
"""
from typing import List, Dict, Optional, Tuple

from .game_state import GameState
from .cards import Card, Creature, Land, CreatureLand, Artifact, Action
from .phases import untap, upkeep, end_turn
from .combat import resolve_combat_damage
from .heuristics import evaluate_position


# -----------------------------------------------------------------------------
# Transposition Table Functions
# -----------------------------------------------------------------------------

def lookup_transposition(memo: Dict, key: tuple, alpha: int, beta: int) -> Optional[int]:
    """Check transposition table for a usable cached value.

    Args:
        memo: The transposition table
        key: (signature, phase, player) tuple
        alpha: Current alpha bound
        beta: Current beta bound

    Returns:
        Cached value if usable, None otherwise
    """
    if key not in memo:
        return None

    cached_value, flag = memo[key]

    if flag == 'exact':
        return cached_value
    elif flag == 'lower' and cached_value >= beta:
        return cached_value  # Fail high
    elif flag == 'upper' and cached_value <= alpha:
        return cached_value  # Fail low

    return None


def store_transposition(memo: Dict, key: tuple, value: int, original_alpha: int, beta: int) -> str:
    """Store result in transposition table with appropriate bound flag.

    Args:
        memo: The transposition table
        key: (signature, phase, player) tuple
        value: The computed value
        original_alpha: Alpha value at start of search
        beta: Beta bound

    Returns:
        The flag used ('exact', 'lower', or 'upper')
    """
    if value <= original_alpha:
        flag = 'upper'  # Failed low, this is an upper bound
    elif value >= beta:
        flag = 'lower'  # Failed high, this is a lower bound
    else:
        flag = 'exact'

    memo[key] = (value, flag)
    return flag


# -----------------------------------------------------------------------------
# Dominance Table Functions
# -----------------------------------------------------------------------------

def check_dominance(dominance: Dict, board_key: tuple, life: List[int], player: int) -> Optional[int]:
    """Check if position is dominated by a known result.

    If a better state was a loss, this state is also a loss.
    If a worse state was a win, this state is also a win.

    Args:
        dominance: The dominance table
        board_key: (board_signature, phase, player) tuple
        life: [player_life, opponent_life]
        player: The player we're evaluating for

    Returns:
        1 if dominated by win, -1 if dominated by loss, None otherwise
    """
    if board_key not in dominance:
        return None

    my_life = life[player]
    opp_life = life[1 - player]

    for (cached_my_life, cached_opp_life, cached_result) in dominance[board_key]:
        # If cached state had better/equal life for player and worse/equal for opponent
        # and resulted in a loss, then this state is also a loss
        if cached_my_life >= my_life and cached_opp_life <= opp_life:
            if cached_result == -1:
                return -1  # Dominated by a losing state

        # If cached state had worse/equal life for player and better/equal for opponent
        # and resulted in a win, then this state is also a win
        if cached_my_life <= my_life and cached_opp_life >= opp_life:
            if cached_result == 1:
                return 1  # Dominates a winning state

    return None


def store_dominance(dominance: Dict, board_key: tuple, life: List[int], player: int, result: int):
    """Store result in dominance table.

    Only stores exact values (not alpha-beta bounds).

    Args:
        dominance: The dominance table
        board_key: (board_signature, phase, player) tuple
        life: [player_life, opponent_life]
        player: The player we're evaluating for
        result: The computed result (1, -1, or 0)
    """
    if board_key not in dominance:
        dominance[board_key] = []
    dominance[board_key].append((life[player], life[1 - player], result))


# -----------------------------------------------------------------------------
# Action Generation
# -----------------------------------------------------------------------------

def get_available_actions(state: GameState) -> List[Action]:
    """Get all available actions for the current player and phase."""
    actions = []
    player = state.active_player

    if state.phase == "main1":
        # Collect play actions from hand
        for card in state.hands[player]:
            actions.extend(card.get_play_actions(state))

        # Collect battlefield actions (activated abilities)
        for card in state.battlefield[player]:
            actions.extend(card.get_battlefield_actions(state))

        # Always can pass to combat
        def pass_to_combat(s: GameState) -> GameState:
            ns = s.copy()
            ns.phase = "combat_attack"
            return ns
        actions.append(Action("Pass to Combat", pass_to_combat))

    elif state.phase == "combat_attack":
        # Collect battlefield actions for active player (e.g., Luminarch Aspirant trigger)
        # These are treated as mandatory - if any exist, ONLY offer them (not attack actions)
        # Attack actions will be offered after triggers resolve
        for card in state.battlefield[player]:
            actions.extend(card.get_battlefield_actions(state))

        # If there are trigger actions, only offer those (triggers are mandatory)
        if actions:
            return actions

        # Collect attack actions, deduplicating identical creatures
        # Only generate one "Attack with X" action per creature type to avoid
        # exploring equivalent permutations (e.g., "Sap1 attacks then Sap2" vs "Sap2 then Sap1")
        seen_attackers = set()
        for i, card in enumerate(state.battlefield[player]):
            if isinstance(card, Creature) or isinstance(card, CreatureLand):
                # Check if this creature can attack
                if hasattr(card, 'can_attack') and not card.can_attack():
                    continue
                if card.tapped:
                    continue
                if getattr(card, 'attacking', False):
                    continue
                if getattr(card, 'entered_this_turn', False):
                    continue

                # Create a signature for this creature type (include eot boosts for pumped creatures)
                creature_sig = (card.name, getattr(card, 'power', 0), getattr(card, 'toughness', 0),
                                getattr(card, 'plus_counters', 0), getattr(card, 'level', 0),
                                getattr(card, 'eot_power_boost', 0), getattr(card, 'eot_toughness_boost', 0))
                if creature_sig in seen_attackers:
                    continue  # Skip duplicate creature types
                seen_attackers.add(creature_sig)

                # Generate attack action that picks this specific creature
                def make_attack(card_idx):
                    def attack(s: GameState) -> GameState:
                        ns = s.copy()
                        attacker = ns.battlefield[player][card_idx]
                        attacker.attacking = True
                        attacker.tapped = True
                        return ns
                    return attack
                actions.append(Action(f"Attack with {card.name}", make_attack(i)))

        # Always can choose not to attack
        def no_attack(s: GameState) -> GameState:
            ns = s.copy()
            # Check if any attackers
            if ns.get_attackers():
                ns.phase = "combat_block"
            else:
                ns.phase = "end_turn"
            return ns
        actions.append(Action("No Attack", no_attack))

    elif state.phase == "combat_block":
        # Defending player chooses blocks
        defender = 1 - player

        # Build attackers list with battlefield indices
        attackers_with_idx = []
        for i, card in enumerate(state.battlefield[state.active_player]):
            if hasattr(card, 'attacking') and card.attacking:
                attackers_with_idx.append((i, card))

        # Collect battlefield actions for defender (e.g., activate Mutavault to block)
        for card in state.battlefield[defender]:
            actions.extend(card.get_battlefield_actions(state))

        # Collect block actions, deduplicating identical blocker/attacker combinations
        # This avoids exploring equivalent permutations
        seen_blocks = set()  # (blocker_sig, attacker_sig)
        blocked_attackers = set(state.blocking_assignments.keys())
        assigned_blockers = set(state.blocking_assignments.values())

        for blocker_idx, blocker in enumerate(state.battlefield[defender]):
            if not (isinstance(blocker, Creature) or isinstance(blocker, CreatureLand)):
                continue
            if blocker.tapped:
                continue
            if blocker_idx in assigned_blockers:
                continue  # Already blocking

            # Check if creature (CreatureLand needs is_creature check)
            if isinstance(blocker, CreatureLand) and not blocker.is_creature:
                continue

            blocker_sig = (blocker.name, getattr(blocker, 'power', 0), getattr(blocker, 'toughness', 0),
                           getattr(blocker, 'plus_counters', 0), getattr(blocker, 'level', 0),
                           getattr(blocker, 'eot_power_boost', 0), getattr(blocker, 'eot_toughness_boost', 0))

            for att_idx, attacker in attackers_with_idx:
                if att_idx in blocked_attackers:
                    continue  # Already blocked

                # Check if can block
                if hasattr(blocker, 'can_block') and not blocker.can_block(attacker):
                    continue

                attacker_sig = (attacker.name, getattr(attacker, 'power', 0), getattr(attacker, 'toughness', 0),
                                getattr(attacker, 'plus_counters', 0), getattr(attacker, 'level', 0),
                                getattr(attacker, 'eot_power_boost', 0), getattr(attacker, 'eot_toughness_boost', 0))
                block_sig = (blocker_sig, attacker_sig)

                if block_sig in seen_blocks:
                    continue  # Skip duplicate blocker/attacker combination
                seen_blocks.add(block_sig)

                # Generate block action
                def make_block(b_idx, a_idx):
                    def block(s: GameState) -> GameState:
                        ns = s.copy()
                        ns.blocking_assignments[a_idx] = b_idx
                        return ns
                    return block
                actions.append(Action(f"Block {attacker.name} with {blocker.name}",
                                      make_block(blocker_idx, att_idx)))

        # Always can choose not to block (proceeds to combat damage)
        def no_block(s: GameState) -> GameState:
            ns = s.copy()
            ns.phase = "combat_damage"
            return ns
        actions.append(Action("No Block", no_block))

    return actions


def minimax(state: GameState, player: int, memo: Dict = None, depth: int = 0,
            alpha: int = -2, beta: int = 2, dominance: Dict = None) -> int:
    """
    Minimax search with alpha-beta pruning and transposition table.
    Returns: 1 = player wins, -1 = player loses, 0 = draw
    """
    if memo is None:
        memo = {}
    if dominance is None:
        dominance = {}

    # Terminal conditions
    if state.game_over:
        if state.winner == player:
            return 1
        elif state.winner == 1 - player:
            return -1
        return 0

    # Apply heuristics for early termination
    heuristic_result = evaluate_position(state, player, depth)
    if heuristic_result is not None:
        return heuristic_result

    # Transposition table lookup
    key = (state.signature(), state.phase, player)
    cached = lookup_transposition(memo, key, alpha, beta)
    if cached is not None:
        return cached

    # Dominance check
    board_key = (state.board_signature(), state.phase, player)
    dominated = check_dominance(dominance, board_key, state.life, player)
    if dominated is not None:
        return dominated

    original_alpha = alpha

    # Handle automatic phases
    if state.phase == "combat_damage":
        new_state = resolve_combat_damage(state)
        result = minimax(new_state, player, memo, depth + 1, alpha, beta, dominance)
        memo[key] = (result, 'exact')
        return result

    if state.phase == "end_turn":
        new_state = end_turn(state)
        result = minimax(new_state, player, memo, depth + 1, alpha, beta, dominance)
        memo[key] = (result, 'exact')
        return result

    if state.phase == "untap":
        new_state = untap(state)
        result = minimax(new_state, player, memo, depth + 1, alpha, beta, dominance)
        memo[key] = (result, 'exact')
        return result

    if state.phase == "upkeep":
        new_state = upkeep(state)
        result = minimax(new_state, player, memo, depth + 1, alpha, beta, dominance)
        memo[key] = (result, 'exact')
        return result

    # Get available actions
    actions = get_available_actions(state)

    if not actions:
        # No actions available, pass to next phase
        if state.phase == "main1":
            new_state = state.copy()
            new_state.phase = "combat_attack"
            result = minimax(new_state, player, memo, depth + 1, alpha, beta, dominance)
        elif state.phase == "combat_attack":
            new_state = state.copy()
            new_state.phase = "end_turn"
            result = minimax(new_state, player, memo, depth + 1, alpha, beta, dominance)
        elif state.phase == "combat_block":
            new_state = state.copy()
            new_state.phase = "combat_damage"
            result = minimax(new_state, player, memo, depth + 1, alpha, beta, dominance)
        else:
            result = 0
        memo[key] = (result, 'exact')
        return result

    # Determine who is making the decision
    if state.phase == "combat_block":
        decision_maker = 1 - state.active_player
    else:
        decision_maker = state.active_player

    # Search with alpha-beta pruning
    if decision_maker == player:
        best_score = -2
        for action in actions:
            new_state = action.execute(state)
            score = minimax(new_state, player, memo, depth + 1, alpha, beta, dominance)
            best_score = max(best_score, score)
            alpha = max(alpha, score)
            if alpha >= beta:
                break
    else:
        best_score = 2
        for action in actions:
            new_state = action.execute(state)
            score = minimax(new_state, player, memo, depth + 1, alpha, beta, dominance)
            best_score = min(best_score, score)
            beta = min(beta, score)
            if alpha >= beta:
                break

    # Store results
    flag = store_transposition(memo, key, best_score, original_alpha, beta)
    if flag == 'exact':
        store_dominance(dominance, board_key, state.life, player, best_score)

    return best_score


def solve(p1_hand: List[Card], p2_hand: List[Card], first_player: int = 0) -> Tuple[int, str]:
    """
    Solve a matchup given the starting hands.

    Args:
        p1_hand: Player 1's starting hand (list of Card objects)
        p2_hand: Player 2's starting hand (list of Card objects)
        first_player: Who goes first (0 = P1, 1 = P2)

    Returns:
        Tuple of (result, description)
        result: 1 = P1 wins, -1 = P1 loses, 0 = draw
        description: Human readable result
    """
    initial_state = GameState(
        life=[20, 20],
        hands=[[c.copy() for c in p1_hand], [c.copy() for c in p2_hand]],
        battlefield=[[], []],
        artifacts=[[], []],
        graveyard=[[], []],
        active_player=first_player,
        phase="main1",
        turn=1
    )

    result = minimax(initial_state, 0, {}, 0)

    if result == 1:
        return (1, "P1 Wins")
    elif result == -1:
        return (result, "P2 Wins")
    else:
        return (0, "Draw/Tie")


def find_optimal_line(state: GameState, player: int, memo: Dict = None, depth: int = 0) -> List[Tuple[str, GameState]]:
    """
    Find the optimal game line where both players play perfectly.
    Returns list of (action_description, resulting_state) tuples.
    """
    if memo is None:
        memo = {}

    path = []

    while not state.game_over and depth < 100:
        # Handle automatic phases
        if state.phase == "combat_damage":
            state = resolve_combat_damage(state)
            path.append(("Combat Damage", state.copy()))
            continue

        if state.phase == "end_turn":
            state = end_turn(state)
            path.append(("End Turn", state.copy()))
            continue

        if state.phase == "untap":
            state = untap(state)
            path.append(("Untap", state.copy()))
            continue

        if state.phase == "upkeep":
            state = upkeep(state)
            path.append(("Upkeep", state.copy()))
            continue

        # Get available actions
        actions = get_available_actions(state)

        if not actions:
            break

        # Determine decision maker
        if state.phase == "combat_block":
            decision_maker = 1 - state.active_player
        else:
            decision_maker = state.active_player

        # Find best action
        best_action = None
        best_score = None

        for action in actions:
            new_state = action.execute(state)
            score = minimax(new_state, decision_maker, memo, depth)

            if best_score is None or score > best_score:
                best_score = score
                best_action = action

        if best_action:
            state = best_action.execute(state)
            path.append((best_action.description, state.copy()))
        else:
            break

        depth += 1

    return path
