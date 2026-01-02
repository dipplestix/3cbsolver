"""End turn phase handler."""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..game_state import GameState

from ..cards import CreatureLand


def end_turn(state: 'GameState') -> 'GameState':
    """Handle end of turn cleanup, then switch to next player's untap."""
    ns = state.copy()

    # Reset combat state for active player
    for card in ns.battlefield[ns.active_player]:
        if hasattr(card, 'attacking'):
            card.attacking = False

    # Clear damage on ALL creatures (happens at end of each turn)
    for player in [0, 1]:
        for card in ns.battlefield[player]:
            if hasattr(card, 'damage'):
                card.damage = 0

    # Clear "until end of turn" effects
    for player in [0, 1]:
        for card in ns.battlefield[player]:
            if hasattr(card, 'eot_power_boost'):
                card.eot_power_boost = 0
            if hasattr(card, 'eot_toughness_boost'):
                card.eot_toughness_boost = 0

    # Call on_end_turn for creature lands (reset creature status)
    for card in ns.battlefield[ns.active_player]:
        if isinstance(card, CreatureLand):
            card._is_creature = False
            card.damage = 0
            card.attacking = False

    ns.blocking_assignments = {}

    # Switch to next player
    ns.active_player = 1 - ns.active_player
    ns.land_played_this_turn = False

    # Each player's turn increments the turn counter
    ns.turn += 1

    # Go to untap phase
    ns.phase = "untap"

    return ns
