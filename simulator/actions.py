"""Action generation for the 3CB simulator.

Generates available actions based on game state and current phase.
"""
from __future__ import annotations
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .game_state import GameState

from .cards import Creature, CreatureLand, Action


def get_available_actions(state: 'GameState') -> List[Action]:
    """Get all available actions for the current player and phase."""
    actions = []
    player = state.active_player

    if state.phase == "main1":
        actions = _get_main_phase_actions(state, player)

    elif state.phase == "combat_attack":
        actions = _get_attack_actions(state, player)

    elif state.phase == "combat_block":
        actions = _get_block_actions(state, player)

    elif state.phase == "response":
        actions = _get_response_actions(state)

    return actions


def _get_main_phase_actions(state: 'GameState', player: int) -> List[Action]:
    """Get actions available during main phase."""
    actions = []

    # Collect play actions from hand
    for card in state.hands[player]:
        actions.extend(card.get_play_actions(state))

    # Collect battlefield actions (activated abilities)
    for card in state.battlefield[player]:
        actions.extend(card.get_battlefield_actions(state))

    # Always can pass to combat
    def pass_to_combat(s: 'GameState') -> 'GameState':
        ns = s.copy()
        # Auto-level creatures before combat (uses any mana gained from land drops this turn)
        for card in ns.battlefield[player]:
            if hasattr(card, 'auto_level') and card.auto_level:
                ns = card.do_auto_level(ns)
        ns.phase = "combat_attack"
        return ns
    actions.append(Action("Pass to Combat", pass_to_combat))

    return actions


def _get_attack_actions(state: 'GameState', player: int) -> List[Action]:
    """Get actions available during combat attack phase.

    Generates all combinations of attackers as single actions (2^n for n unique creatures).
    Each action immediately transitions to the next phase.
    """
    from itertools import combinations as itertools_combinations
    actions = []

    # Collect battlefield actions for active player (e.g., Luminarch Aspirant trigger)
    # These are treated as mandatory - if any exist, ONLY offer them (not attack actions)
    for card in state.battlefield[player]:
        actions.extend(card.get_battlefield_actions(state))

    # If there are trigger actions, only offer those (triggers are mandatory)
    if actions:
        return actions

    # Collect eligible attackers, deduplicating identical creatures
    eligible_attackers = []  # List of (index, card, signature)
    seen_sigs = set()

    for i, card in enumerate(state.battlefield[player]):
        # Use is_creature() method for unified creature check
        if not card.is_creature():
            continue
        # Check if this creature can attack
        if hasattr(card, 'can_attack') and not card.can_attack():
            continue
        if card.tapped:
            continue
        if getattr(card, 'attacking', False):
            continue
        if getattr(card, 'entered_this_turn', False):
            continue

        # Create a signature for this creature type
        sig = (card.name, getattr(card, 'power', 0), getattr(card, 'toughness', 0),
               getattr(card, 'plus_counters', 0), getattr(card, 'level', 0),
               getattr(card, 'eot_power_boost', 0), getattr(card, 'eot_toughness_boost', 0))
        if sig in seen_sigs:
            continue  # Skip duplicate creature types
        seen_sigs.add(sig)
        eligible_attackers.append((i, card, sig))

    # Generate attack combo action factory
    def make_attack_combo(attacker_indices: list):
        def attack(s: 'GameState') -> 'GameState':
            ns = s.copy()
            for idx in attacker_indices:
                attacker = ns.battlefield[player][idx]
                attacker.attacking = True
                # Vigilance: creature doesn't tap when attacking
                if not (hasattr(attacker, 'keywords') and 'vigilance' in attacker.keywords):
                    attacker.tapped = True
            # Immediately transition to next phase
            if attacker_indices:
                ns.phase = "combat_block"
            else:
                ns.phase = "end_turn"
            return ns
        return attack

    # Generate actions for all subsets - larger sets first for better alpha-beta pruning
    for r in range(len(eligible_attackers), -1, -1):
        for combo in itertools_combinations(eligible_attackers, r):
            indices = [idx for idx, card, sig in combo]
            names = [card.name for idx, card, sig in combo]

            if names:
                description = "Attack with " + ", ".join(names)
            else:
                description = "No Attack"

            actions.append(Action(description, make_attack_combo(indices)))

    return actions


def _get_block_actions(state: 'GameState', player: int) -> List[Action]:
    """Get actions available during combat block phase."""
    actions = []
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
    seen_blocks = set()  # (blocker_sig, attacker_sig)
    blocked_attackers = set(state.blocking_assignments.keys())
    assigned_blockers = set(state.blocking_assignments.values())

    for blocker_idx, blocker in enumerate(state.battlefield[defender]):
        # Use is_creature() method for unified creature check
        if not blocker.is_creature():
            continue
        if blocker.tapped:
            continue
        if blocker_idx in assigned_blockers:
            continue  # Already blocking

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
                def block(s: 'GameState') -> 'GameState':
                    ns = s.copy()
                    ns.blocking_assignments[a_idx] = b_idx
                    return ns
                return block
            actions.append(Action(f"Block {attacker.name} with {blocker.name}",
                                  make_block(blocker_idx, att_idx)))

    # Always can choose not to block (proceeds to combat damage)
    def no_block(s: 'GameState') -> 'GameState':
        ns = s.copy()
        ns.phase = "combat_damage"
        return ns
    actions.append(Action("No Block", no_block))

    return actions


def _get_response_actions(state: 'GameState') -> List[Action]:
    """Get actions available during response phase.

    The non-active player can respond to spells on the stack with instants,
    or pass to let the stack resolve.
    """
    actions = []
    # The responding player is the opponent of the spell caster (active player)
    responder = 1 - state.active_player

    # Collect instant response actions from responder's hand
    for card in state.hands[responder]:
        actions.extend(card.get_response_actions(state))

    # Always can pass (resolves the stack)
    def pass_priority(s: 'GameState') -> 'GameState':
        ns = s.copy()

        # Resolve top spell on stack
        if ns.stack:
            spell = ns.stack.pop()
            # Call the spell's resolve method
            ns = spell.resolve(ns)
            # Move spell to graveyard (if not already there)
            if spell not in ns.graveyard[spell.owner]:
                ns.graveyard[spell.owner].append(spell)

        # If stack is empty, return to main phase
        if not ns.stack:
            ns.phase = "main1"
        # Otherwise stay in response phase for next spell

        return ns

    actions.append(Action("Pass (resolve spell)", pass_priority))

    return actions
