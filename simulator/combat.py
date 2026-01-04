"""Combat damage resolution for the 3CB simulator."""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .game_state import GameState

from .helpers import (
    get_creature_power,
    get_creature_toughness,
    has_first_strike,
    has_double_strike,
    has_deathtouch,
    is_lethal_damage,
)


def resolve_combat_damage(state: 'GameState') -> 'GameState':
    """Resolve combat damage with first strike and double strike support."""
    ns = state.copy()
    defender = 1 - ns.active_player

    # Build attacker list with indices for blocking lookup
    attackers_with_idx = []
    for i, card in enumerate(ns.battlefield[ns.active_player]):
        if hasattr(card, 'attacking') and card.attacking:
            attackers_with_idx.append((i, card))

    # Check if any creature has first strike or double strike
    any_first_strike = False
    for att_idx, attacker in attackers_with_idx:
        if has_first_strike(attacker) or has_double_strike(attacker):
            any_first_strike = True
            break
        blocker_idx = ns.blocking_assignments.get(att_idx)
        if blocker_idx is not None and blocker_idx < len(ns.battlefield[defender]):
            blocker = ns.battlefield[defender][blocker_idx]
            if has_first_strike(blocker) or has_double_strike(blocker):
                any_first_strike = True
                break

    # Track which creatures die (by battlefield index) to remove them later
    dead_attackers = set()  # indices in active_player's battlefield
    dead_blockers = set()   # indices in defender's battlefield

    # First strike damage step (if applicable)
    if any_first_strike:
        for att_idx, attacker in attackers_with_idx:
            if att_idx in dead_attackers:
                continue
            attacker_has_fs = has_first_strike(attacker) or has_double_strike(attacker)
            blocker_idx = ns.blocking_assignments.get(att_idx)

            if blocker_idx is not None and blocker_idx < len(ns.battlefield[defender]) and blocker_idx not in dead_blockers:
                blocker = ns.battlefield[defender][blocker_idx]
                blocker_has_fs = has_first_strike(blocker) or has_double_strike(blocker)
                attacker_has_dt = has_deathtouch(attacker)
                blocker_has_dt = has_deathtouch(blocker)

                # First strikers deal damage first
                if attacker_has_fs:
                    blocker.damage += get_creature_power(attacker)
                if blocker_has_fs:
                    attacker.damage += get_creature_power(blocker)

                # Check for deaths after first strike (considering deathtouch)
                attacker_toughness = get_creature_toughness(attacker)
                blocker_toughness = get_creature_toughness(blocker)

                if is_lethal_damage(blocker.damage, blocker_toughness, attacker_has_dt):
                    dead_blockers.add(blocker_idx)
                if is_lethal_damage(attacker.damage, attacker_toughness, blocker_has_dt):
                    dead_attackers.add(att_idx)
            else:
                # Unblocked with first strike - deal damage to player
                if attacker_has_fs:
                    damage = get_creature_power(attacker)
                    ns.life[defender] -= damage
                    if hasattr(attacker, 'on_deal_combat_damage_to_player'):
                        ns = attacker.on_deal_combat_damage_to_player(ns)

        # Check for game over after first strike damage to players
        if ns.life[0] <= 0:
            ns.game_over = True
            ns.winner = 1
            ns.phase = "end_turn"
            return ns
        if ns.life[1] <= 0:
            ns.game_over = True
            ns.winner = 0
            ns.phase = "end_turn"
            return ns

    # Regular damage step
    for att_idx, attacker in attackers_with_idx:
        if att_idx in dead_attackers:
            continue
        attacker_has_fs = has_first_strike(attacker)
        attacker_has_ds = has_double_strike(attacker)
        blocker_idx = ns.blocking_assignments.get(att_idx)

        if blocker_idx is not None and blocker_idx < len(ns.battlefield[defender]) and blocker_idx not in dead_blockers:
            blocker = ns.battlefield[defender][blocker_idx]
            blocker_has_fs = has_first_strike(blocker)
            blocker_has_ds = has_double_strike(blocker)
            attacker_has_dt = has_deathtouch(attacker)
            blocker_has_dt = has_deathtouch(blocker)

            # Non-first-strikers and double-strikers deal damage now
            if not attacker_has_fs or attacker_has_ds:
                blocker.damage += get_creature_power(attacker)
            if not blocker_has_fs or blocker_has_ds:
                attacker.damage += get_creature_power(blocker)

            # Check for deaths (considering deathtouch)
            attacker_toughness = get_creature_toughness(attacker)
            blocker_toughness = get_creature_toughness(blocker)

            if is_lethal_damage(attacker.damage, attacker_toughness, blocker_has_dt):
                dead_attackers.add(att_idx)
            if is_lethal_damage(blocker.damage, blocker_toughness, attacker_has_dt):
                dead_blockers.add(blocker_idx)
        else:
            # Unblocked - deal damage (double strikers deal again, non-FS deal now)
            if not attacker_has_fs or attacker_has_ds:
                damage = get_creature_power(attacker)
                ns.life[defender] -= damage
                if hasattr(attacker, 'on_deal_combat_damage_to_player'):
                    ns = attacker.on_deal_combat_damage_to_player(ns)

    # Check for game over from combat damage to players BEFORE death triggers
    # If a player is at 0 or less life from combat damage, they lose immediately
    if ns.life[0] <= 0:
        ns.game_over = True
        ns.winner = 1
        ns.phase = "end_turn"
        return ns
    elif ns.life[1] <= 0:
        ns.game_over = True
        ns.winner = 0
        ns.phase = "end_turn"
        return ns

    # Remove dead creatures and trigger death abilities
    # Process in reverse index order to avoid index shifting issues
    for blocker_idx in sorted(dead_blockers, reverse=True):
        blocker = ns.battlefield[defender][blocker_idx]
        ns.graveyard[defender].append(blocker)
        if hasattr(blocker, 'on_death'):
            ns = blocker.on_death(ns)
        ns.battlefield[defender].pop(blocker_idx)

    for att_idx in sorted(dead_attackers, reverse=True):
        attacker = ns.battlefield[ns.active_player][att_idx]
        ns.graveyard[ns.active_player].append(attacker)
        if hasattr(attacker, 'on_death'):
            ns = attacker.on_death(ns)
        ns.battlefield[ns.active_player].pop(att_idx)

    # Check for game over
    if ns.life[0] <= 0:
        ns.game_over = True
        ns.winner = 1
    elif ns.life[1] <= 0:
        ns.game_over = True
        ns.winner = 0

    ns.phase = "end_turn"
    return ns
