"""Upkeep phase handler."""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..game_state import GameState


def upkeep(state: 'GameState') -> 'GameState':
    """Handle upkeep step for the active player.

    This phase handles:
    - Upkeep triggers (e.g., Sleep-Cursed Faerie's ward payment)
    - Auto-leveling creatures (e.g., Student of Warfare)
    """
    ns = state.copy()

    # Handle upkeep triggers (for cards that have them)
    for card in ns.battlefield[ns.active_player]:
        if hasattr(card, 'on_upkeep'):
            ns = card.on_upkeep(ns)

    # Auto-level creatures that should always level up (e.g., Student of Warfare)
    # This reduces branching by making level-up automatic when mana is available
    for card in ns.battlefield[ns.active_player]:
        if hasattr(card, 'auto_level') and card.auto_level:
            ns = card.do_auto_level(ns)

    # Move to main phase
    ns.phase = "main1"

    return ns
