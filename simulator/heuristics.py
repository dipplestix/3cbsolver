"""Heuristics for early termination in grinding games.

These heuristics detect game states where the outcome is mathematically
determined, allowing the solver to terminate early without full search.
"""
from __future__ import annotations
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .game_state import GameState


def _has_token_generator(battlefield: list) -> bool:
    """Check if battlefield has a token generator (e.g., Thallid)."""
    return any(c.name == 'Thallid' for c in battlefield)


def _can_grow(creatures: list) -> bool:
    """Check if any creature can grow (counters, levels, combat triggers)."""
    for c in creatures:
        if hasattr(c, 'plus_counters'):  # Aspirant, landfall creatures
            return True
        if hasattr(c, 'level'):  # Student of Warfare
            return True
        if c.name == 'Stromkirk Noble':  # Grows on combat damage
            return True
    return False


def _get_creatures(battlefield: list) -> list:
    """Get all creatures with positive power from a battlefield."""
    return [c for c in battlefield if hasattr(c, 'power') and c.power > 0]


def evaluate_early_grinding(state: 'GameState', player: int, depth: int) -> Optional[int]:
    """Early heuristic for grinding games (depth > 30).

    Detects token generator vs static creature matchups where the outcome
    is mathematically determined.

    Returns:
        1 if player wins, -1 if player loses, None if no determination
    """
    if depth <= 30:
        return None

    # Only apply when hands are empty (grinding phase)
    if state.hands[0] or state.hands[1]:
        return None

    p1_creatures = _get_creatures(state.battlefield[0])
    p2_creatures = _get_creatures(state.battlefield[1])
    p1_token_gen = _has_token_generator(state.battlefield[0])
    p2_token_gen = _has_token_generator(state.battlefield[1])
    p1_grows = _can_grow(p1_creatures)
    p2_grows = _can_grow(p2_creatures)

    # Token generator beats static creature (infinite tokens overwhelm)
    if p2_token_gen and not p1_token_gen and not p1_grows and p1_creatures:
        return 1 if player == 1 else -1
    if p1_token_gen and not p2_token_gen and not p2_grows and p2_creatures:
        return 1 if player == 0 else -1

    return None


def evaluate_max_depth(state: 'GameState', player: int, depth: int, max_depth: int = 500) -> Optional[int]:
    """Heuristics applied at maximum search depth.

    When search reaches max depth without resolution, apply heuristics
    to determine likely winner.

    Returns:
        1 if player wins, -1 if player loses, 0 for draw, None if no determination
    """
    if depth <= max_depth:
        return None

    # Only apply when hands are empty (grinding phase)
    if state.hands[0] or state.hands[1]:
        return 0  # Draw by excessive depth with cards in hand

    p1_creatures = _get_creatures(state.battlefield[0])
    p2_creatures = _get_creatures(state.battlefield[1])

    # One side has creatures, other has nothing
    if p1_creatures and not p2_creatures:
        return 1 if player == 0 else -1
    if p2_creatures and not p1_creatures:
        return 1 if player == 1 else -1

    p1_token_gen = _has_token_generator(state.battlefield[0])
    p2_token_gen = _has_token_generator(state.battlefield[1])
    p1_grows = _can_grow(p1_creatures)
    p2_grows = _can_grow(p2_creatures)

    # Token generator beats static creature
    if p2_token_gen and not p1_token_gen and not p1_grows:
        return 1 if player == 1 else -1
    if p1_token_gen and not p2_token_gen and not p2_grows:
        return 1 if player == 0 else -1

    # Growing creature beats token generator (quadratic damage vs linear blockers)
    if p1_grows and not p1_token_gen and p2_token_gen and not p2_grows:
        return 1 if player == 0 else -1
    if p2_grows and not p2_token_gen and p1_token_gen and not p1_grows:
        return 1 if player == 1 else -1

    return 0  # Draw by excessive depth (stalemate)


def evaluate_position(state: 'GameState', player: int, depth: int) -> Optional[int]:
    """Main entry point for heuristic evaluation.

    Tries early grinding heuristics first, then max depth heuristics.

    Returns:
        1 if player wins, -1 if player loses, 0 for draw, None to continue search
    """
    # Try early grinding heuristics
    result = evaluate_early_grinding(state, player, depth)
    if result is not None:
        return result

    # Try max depth heuristics
    result = evaluate_max_depth(state, player, depth)
    if result is not None:
        return result

    return None
