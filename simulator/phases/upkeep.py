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

    # Handle upkeep triggers for active player's cards
    for card in ns.battlefield[ns.active_player]:
        if hasattr(card, 'on_upkeep'):
            ns = card.on_upkeep(ns)

    # Handle opponent's enchantments that trigger on active player's upkeep
    # (e.g., Shrieking Affliction)
    opponent = 1 - ns.active_player
    for card in ns.enchantments[opponent]:
        if hasattr(card, 'on_opponent_upkeep'):
            ns = card.on_opponent_upkeep(ns)

    # Check for game over after triggers (e.g., life loss from Shrieking Affliction)
    if ns.life[ns.active_player] <= 0:
        ns.game_over = True
        ns.winner = opponent

    # Auto-level creatures that should always level up (e.g., Student of Warfare)
    # This reduces branching by making level-up automatic when mana is available
    for card in ns.battlefield[ns.active_player]:
        if hasattr(card, 'auto_level') and card.auto_level:
            ns = card.do_auto_level(ns)

    # Stalemate detection: check if board state is unchanged from last main phase
    # Create a signature of just the board position (excluding active_player, life, etc.)
    p1_bf = tuple(sorted(c.get_signature_state() for c in ns.battlefield[0]))
    p2_bf = tuple(sorted(c.get_signature_state() for c in ns.battlefield[1]))
    p1_hand = tuple(sorted(c.name for c in ns.hands[0]))
    p2_hand = tuple(sorted(c.name for c in ns.hands[1]))
    p1_art = tuple(sorted(c.get_signature_state() for c in ns.artifacts[0]))
    p2_art = tuple(sorted(c.get_signature_state() for c in ns.artifacts[1]))
    p1_ench = tuple(sorted(c.get_signature_state() for c in ns.enchantments[0]))
    p2_ench = tuple(sorted(c.get_signature_state() for c in ns.enchantments[1]))
    current_sig = (p1_bf, p2_bf, p1_hand, p2_hand, p1_art, p2_art, p1_ench, p2_ench)

    if ns.prev_main_sig is not None and current_sig == ns.prev_main_sig:
        ns.stale_turns += 1
    else:
        ns.stale_turns = 0
    ns.prev_main_sig = current_sig

    # If stalemate persists for 10 main phases (5 full rounds), declare draw
    if ns.stale_turns >= 10:
        ns.game_over = True
        ns.winner = None  # Draw

    # Only transition to draw phase if there are cards to draw
    if ns.library[ns.active_player]:
        ns.phase = "draw"
    else:
        ns.phase = "main1"

    return ns
