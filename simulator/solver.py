"""
Solver for the 3CB simulator.
Takes any two hands and finds optimal play using minimax.
"""
from typing import List, Dict, Optional, Tuple

from .game_state import GameState
from .cards import Card
from .actions import get_available_actions
from .phases import untap, upkeep, end_turn
from .combat import resolve_combat_damage
from .heuristics import evaluate_position
from .tables import lookup_transposition, store_transposition, check_dominance, store_dominance


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
    original_beta = beta

    # Handle automatic phases - use wide bounds to get exact values for caching
    if state.phase == "combat_damage":
        new_state = resolve_combat_damage(state)
        result = minimax(new_state, player, memo, depth + 1, -2, 2, dominance)
        memo[key] = (result, 'exact')
        return result

    if state.phase == "end_turn":
        new_state = end_turn(state)
        result = minimax(new_state, player, memo, depth + 1, -2, 2, dominance)
        memo[key] = (result, 'exact')
        return result

    if state.phase == "untap":
        new_state = untap(state)
        result = minimax(new_state, player, memo, depth + 1, -2, 2, dominance)
        memo[key] = (result, 'exact')
        return result

    if state.phase == "upkeep":
        new_state = upkeep(state)
        result = minimax(new_state, player, memo, depth + 1, -2, 2, dominance)
        memo[key] = (result, 'exact')
        return result

    # Get available actions
    actions = get_available_actions(state)

    if not actions:
        # No actions available, pass to next phase - use wide bounds for exact values
        if state.phase == "main1":
            new_state = state.copy()
            new_state.phase = "combat_attack"
            result = minimax(new_state, player, memo, depth + 1, -2, 2, dominance)
        elif state.phase == "combat_attack":
            new_state = state.copy()
            new_state.phase = "end_turn"
            result = minimax(new_state, player, memo, depth + 1, -2, 2, dominance)
        elif state.phase == "combat_block":
            new_state = state.copy()
            new_state.phase = "combat_damage"
            result = minimax(new_state, player, memo, depth + 1, -2, 2, dominance)
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

    # Store results - only store exact values to avoid bound-related bugs
    if best_score > original_alpha and best_score < original_beta:
        memo[key] = (best_score, 'exact')
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
