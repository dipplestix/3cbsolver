"""Untap phase handler."""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..game_state import GameState


def untap(state: 'GameState') -> 'GameState':
    """Handle untap step for the active player."""
    ns = state.copy()

    # Untap all permanents for the active player
    # But stun counters replace untapping!
    # Also handle Undiscovered Paradise returning to hand
    cards_to_return = []
    for card in ns.battlefield[ns.active_player]:
        # Check for Undiscovered Paradise bounce
        if hasattr(card, 'return_to_hand') and card.return_to_hand:
            cards_to_return.append(card)
            continue
        if hasattr(card, 'stun_counters') and card.stun_counters > 0:
            # Stun counter replaces untap - remove counter, stay tapped
            card.stun_counters -= 1
        elif hasattr(card, 'stay_tapped') and card.stay_tapped:
            # Storage lands can choose to stay tapped
            pass
        else:
            card.tapped = False
        # Clear summoning sickness - permanents that were here at start of turn can attack
        if hasattr(card, 'entered_this_turn'):
            card.entered_this_turn = False
        # Reset Valiant trigger tracking
        if hasattr(card, 'targeted_this_turn'):
            card.targeted_this_turn = False
        # Reset Luminarch Aspirant combat trigger
        if hasattr(card, 'combat_trigger_used'):
            card.combat_trigger_used = False

    # Return bouncing lands to hand
    for card in cards_to_return:
        ns.battlefield[ns.active_player].remove(card)
        card.tapped = False
        card.return_to_hand = False
        ns.hands[ns.active_player].append(card)

    # Untap artifacts
    for card in ns.artifacts[ns.active_player]:
        card.tapped = False

    # Move to upkeep phase
    ns.phase = "upkeep"

    return ns
