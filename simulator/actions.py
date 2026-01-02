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
        ns.phase = "combat_attack"
        return ns
    actions.append(Action("Pass to Combat", pass_to_combat))

    return actions


def _get_attack_actions(state: 'GameState', player: int) -> List[Action]:
    """Get actions available during combat attack phase."""
    actions = []

    # Collect battlefield actions for active player (e.g., Luminarch Aspirant trigger)
    # These are treated as mandatory - if any exist, ONLY offer them (not attack actions)
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

        # Create a signature for this creature type (include eot boosts for pumped creatures)
        creature_sig = (card.name, getattr(card, 'power', 0), getattr(card, 'toughness', 0),
                        getattr(card, 'plus_counters', 0), getattr(card, 'level', 0),
                        getattr(card, 'eot_power_boost', 0), getattr(card, 'eot_toughness_boost', 0))
        if creature_sig in seen_attackers:
            continue  # Skip duplicate creature types
        seen_attackers.add(creature_sig)

        # Generate attack action that picks this specific creature
        def make_attack(card_idx):
            def attack(s: 'GameState') -> 'GameState':
                ns = s.copy()
                attacker = ns.battlefield[player][card_idx]
                attacker.attacking = True
                attacker.tapped = True
                return ns
            return attack
        actions.append(Action(f"Attack with {card.name}", make_attack(i)))

    # Always can choose not to attack
    def no_attack(s: 'GameState') -> 'GameState':
        ns = s.copy()
        # Check if any attackers
        if ns.get_attackers():
            ns.phase = "combat_block"
        else:
            ns.phase = "end_turn"
        return ns
    actions.append(Action("No Attack", no_attack))

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
