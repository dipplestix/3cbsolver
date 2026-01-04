"""Draw phase handler."""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..game_state import GameState


def draw(state: 'GameState') -> 'GameState':
    """Handle draw step for the active player.

    Note: This is only called when library has cards (checked in upkeep).
    """
    ns = state.copy()
    player = ns.active_player

    # Player going first skips their first draw (turn 1, player 0)
    if ns.turn == 1 and player == 0:
        ns.phase = "main1"
        return ns

    # Draw top card (upkeep already verified library is non-empty)
    card = ns.library[player].pop(0)
    ns.hands[player].append(card)

    ns.phase = "main1"
    return ns
