"""Heuristics for early termination in grinding games.

These heuristics detect game states where the outcome is mathematically
determined, allowing the solver to terminate early without full search.
"""
from __future__ import annotations
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .game_state import GameState

from .cards import CreatureLand


def _has_token_generator(battlefield: list) -> bool:
    """Check if battlefield has a token generator (e.g., Thallid)."""
    return any(c.name == 'Thallid' for c in battlefield)


def _can_grow(creatures: list) -> bool:
    """Check if any creature can still grow (counters, levels, combat triggers)."""
    for c in creatures:
        if hasattr(c, 'plus_counters'):  # Aspirant, landfall creatures
            return True
        if hasattr(c, 'level'):  # Student of Warfare - check if not at max level
            # Student of Warfare maxes out at level 7 (4/4 double strike)
            if c.level < 7:
                return True
            # At max level, can't grow further
        elif c.name == 'Stromkirk Noble':  # Grows on combat damage
            return True
    return False


def _has_creature_land(battlefield: list) -> bool:
    """Check if battlefield has a creature land (e.g., Mutavault)."""
    return any(isinstance(c, CreatureLand) for c in battlefield)


def _has_deathtouch(creatures: list) -> bool:
    """Check if any creature has deathtouch."""
    for c in creatures:
        if hasattr(c, 'keywords') and 'deathtouch' in c.keywords:
            return True
    return False


def _has_permanent_creature(battlefield: list) -> bool:
    """Check if battlefield has a permanent creature (always a creature, like Dryad Arbor).

    Unlike creature lands (Mutavault) that only become creatures when activated,
    permanent creatures like Dryad Arbor are always creatures.
    """
    for c in battlefield:
        # Check if it's a creature (has power > 0) that's also a land
        # but NOT a CreatureLand (which only becomes a creature when activated)
        if hasattr(c, 'power') and c.power > 0:
            if getattr(c, 'is_land', False) and not isinstance(c, CreatureLand):
                return True
    return False


def _get_creatures(battlefield: list) -> list:
    """Get all creatures with positive power from a battlefield."""
    return [c for c in battlefield if hasattr(c, 'power') and c.power > 0]


def _creatures_are_symmetric(p1_creatures: list, p2_creatures: list) -> bool:
    """Check if both sides have equivalent creatures (stalemate likely)."""
    if len(p1_creatures) != len(p2_creatures):
        return False
    if not p1_creatures:
        return False

    # Get creature signatures (name, power, toughness, key abilities)
    def creature_sig(c):
        power = getattr(c, 'current_power', None) or getattr(c, 'power', 0)
        toughness = getattr(c, 'current_toughness', None) or getattr(c, 'toughness', 0)
        deathtouch = hasattr(c, 'has_deathtouch') and c.has_deathtouch
        first_strike = hasattr(c, 'has_first_strike') and c.has_first_strike
        double_strike = hasattr(c, 'has_double_strike') and c.has_double_strike
        return (power, toughness, deathtouch, first_strike, double_strike)

    p1_sigs = sorted(creature_sig(c) for c in p1_creatures)
    p2_sigs = sorted(creature_sig(c) for c in p2_creatures)
    return p1_sigs == p2_sigs


def _is_combat_stalemate(p1_creatures: list, p2_creatures: list) -> bool:
    """Check if combat would result in mutual destruction or no progress."""
    if not p1_creatures or not p2_creatures:
        return False

    # If both sides have deathtouch creatures of equal count, it's a stalemate
    # (attacking means mutual destruction, neither benefits)
    p1_deathtouch = [c for c in p1_creatures if hasattr(c, 'has_deathtouch') and c.has_deathtouch]
    p2_deathtouch = [c for c in p2_creatures if hasattr(c, 'has_deathtouch') and c.has_deathtouch]
    if p1_deathtouch and p2_deathtouch and len(p1_deathtouch) == len(p2_deathtouch):
        return True

    # Symmetric creatures = stalemate
    if _creatures_are_symmetric(p1_creatures, p2_creatures):
        return True

    return False


def evaluate_early_grinding(state: 'GameState', player: int, depth: int) -> Optional[int]:
    """Early heuristic for grinding games (depth > 15).

    Detects token generator vs static creature matchups where the outcome
    is mathematically determined.

    Returns:
        1 if player wins, -1 if player loses, None if no determination
    """
    if depth <= 15:
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

    # Symmetric creatures with no growth potential = stalemate draw
    if not p1_grows and not p2_grows and _is_combat_stalemate(p1_creatures, p2_creatures):
        return 0

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
    p1_creature_land = _has_creature_land(state.battlefield[0])
    p2_creature_land = _has_creature_land(state.battlefield[1])

    # One side has creatures, other has nothing (not even creature lands)
    if p1_creatures and not p2_creatures and not p2_creature_land:
        return 1 if player == 0 else -1
    if p2_creatures and not p1_creatures and not p1_creature_land:
        return 1 if player == 1 else -1

    # Check for deathtouch and multiple creatures
    p1_deathtouch = _has_deathtouch(p1_creatures)
    p2_deathtouch = _has_deathtouch(p2_creatures)
    p1_permanent_creature = _has_permanent_creature(state.battlefield[0])
    p2_permanent_creature = _has_permanent_creature(state.battlefield[1])

    # Creatures with deathtouch + another creature beat creature lands
    # (deathtouch trades with creature land, other creature remains to win)
    if p1_creatures and not p2_creatures and p2_creature_land:
        if p1_deathtouch and len(p1_creatures) > 1:
            return 1 if player == 0 else -1  # Deathtouch trades, other creature wins
        if p1_permanent_creature and p1_deathtouch:
            # Dryad Arbor + deathtouch creature: deathtouch trades, Arbor wins
            return 1 if player == 0 else -1
        return 0  # Draw - single creature vs creature land can trade to stalemate
    if p2_creatures and not p1_creatures and p1_creature_land:
        if p2_deathtouch and len(p2_creatures) > 1:
            return 1 if player == 1 else -1  # Deathtouch trades, other creature wins
        if p2_permanent_creature and p2_deathtouch:
            return 1 if player == 1 else -1
        return 0  # Draw - single creature vs creature land can trade to stalemate

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
