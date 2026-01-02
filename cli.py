#!/usr/bin/env python3
"""3CB Simulator CLI - Unified interface for running simulations."""
import argparse
import signal
from simulator import (
    solve, GameState, get_available_actions, minimax,
    resolve_combat_damage, end_turn, untap, upkeep,
    create_island, create_forest, create_plains, create_mountain,
    create_hammerheim,
    create_mox_jet, create_mutavault,
    create_sleep_cursed_faerie, create_scythe_tiger,
    create_undiscovered_paradise, create_sazhs_chocobo,
    create_student_of_warfare, create_old_growth_dryads,
    create_dryad_arbor, create_dragon_sniper,
    create_stromkirk_noble, create_heartfire_hero,
    create_bottomless_vault, create_tomb_of_urami,
    create_remote_farm, create_luminarch_aspirant,
    create_thallid, create_pendelhaven,
)

# Deck definitions - only enabled decks for now
DECKS = {
    "student": ("Plains + Student of Warfare", lambda p: [create_plains(p), create_student_of_warfare(p)]),
    "scf": ("Island + Sleep-Cursed Faerie", lambda p: [create_island(p), create_sleep_cursed_faerie(p)]),
    "tiger": ("Forest + Scythe Tiger", lambda p: [create_forest(p), create_scythe_tiger(p)]),
    # Temporarily disabled for refactoring:
    # "mutavault": ("Mox Jet + Mutavault", lambda p: [create_mox_jet(p), create_mutavault(p)]),
    # "sniper": ("Dryad Arbor + Dragon Sniper", lambda p: [create_dryad_arbor(p), create_dragon_sniper(p)]),
    # "noble": ("Mountain + Stromkirk Noble", lambda p: [create_mountain(p), create_stromkirk_noble(p)]),
    # "hero": ("Hammerheim + Heartfire Hero", lambda p: [create_hammerheim(p), create_heartfire_hero(p)]),
    # "urami": ("Bottomless Vault + Tomb of Urami", lambda p: [create_bottomless_vault(p), create_tomb_of_urami(p)]),
    # "aspirant": ("Remote Farm + Luminarch Aspirant", lambda p: [create_remote_farm(p), create_luminarch_aspirant(p)]),
    # "thallid": ("Pendelhaven + Thallid", lambda p: [create_pendelhaven(p), create_thallid(p)]),
    # "dryads": ("Forest + Old-Growth Dryads", lambda p: [create_forest(p), create_old_growth_dryads(p)]),
    # "chocobo": ("Undiscovered Paradise + Sazh's Chocobo", lambda p: [create_undiscovered_paradise(p), create_sazhs_chocobo(p)]),
}

# Load cached results
import json
from pathlib import Path
CACHE_FILE = Path(__file__).parent / "matchup_results.json"

def load_cache():
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text())
    return {}

def save_cache(cache):
    CACHE_FILE.write_text(json.dumps(cache, indent=2))

MATCHUP_CACHE = load_cache()


class TimeoutError(Exception):
    pass


def timeout_handler(signum, frame):
    raise TimeoutError()


def solve_with_timeout(deck1, deck2, first_player, timeout_sec=30):
    """Run solver with timeout."""
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_sec)
    try:
        result, desc = solve(deck1, deck2, first_player=first_player)
        signal.alarm(0)
        return result, desc
    except TimeoutError:
        signal.alarm(0)
        return None, None


def cmd_solve(args):
    """Solve a single matchup."""
    d1_name, d1_factory = DECKS[args.deck1][0], DECKS[args.deck1][1]
    d2_name, d2_factory = DECKS[args.deck2][0], DECKS[args.deck2][1]

    print(f"\n{d1_name} vs {d2_name}")
    print(f"First player: {'P1' if args.first == 0 else 'P2'}")
    print("-" * 40)

    p1_hand = d1_factory(0)
    p2_hand = d2_factory(1)

    result, desc = solve_with_timeout(
        [c.copy() for c in p1_hand],
        [c.copy() for c in p2_hand],
        first_player=args.first,
        timeout_sec=args.timeout
    )

    if desc is None:
        print("TIMEOUT - solver took too long")
        # Check cache
        cache_key = f"{args.deck1}_vs_{args.deck2}_p{args.first}"
        if cache_key in MATCHUP_CACHE:
            known = MATCHUP_CACHE[cache_key]
            print(f"Cached result: {known}")
    else:
        print(f"Result: {desc}")
        # Cache the result
        cache_key = f"{args.deck1}_vs_{args.deck2}_p{args.first}"
        result_str = "P1" if desc == "P1 Wins" else ("P2" if desc == "P2 Wins" else "Tie")
        if cache_key not in MATCHUP_CACHE:
            MATCHUP_CACHE[cache_key] = result_str
            save_cache(MATCHUP_CACHE)


def colorize_result(play, draw):
    """Colorize a result cell based on play/draw outcome."""
    # ANSI color codes
    BLUE = '\033[94m'       # WW - bright blue
    RED = '\033[91m'        # LL - bright red
    YELLOW = '\033[93m'     # TT, WL, LW - yellow
    LIGHT_BLUE = '\033[96m' # WT, TW - cyan (light blue)
    LIGHT_RED = '\033[95m'  # LT, TL - magenta (light red)
    RESET = '\033[0m'

    cell = f"{play}{draw}"

    if cell == 'WW':
        return f"{BLUE}{cell}{RESET}"
    elif cell == 'LL':
        return f"{RED}{cell}{RESET}"
    elif cell in ('TT', 'WL', 'LW'):
        return f"{YELLOW}{cell}{RESET}"
    elif cell in ('WT', 'TW'):
        return f"{LIGHT_BLUE}{cell}{RESET}"
    elif cell in ('LT', 'TL'):
        return f"{LIGHT_RED}{cell}{RESET}"
    else:
        return cell


def cmd_metagame(args):
    """Run full metagame table."""
    import time
    start_time = time.time()

    deck_names = list(DECKS.keys())
    n = len(deck_names)
    points = [[0] * n for _ in range(n)]
    # results[i][j] = (play_result, draw_result) for row i vs col j
    # where result is 'W', 'L', or 'T' from row's perspective
    results = [[None] * n for _ in range(n)]

    print("=" * 60)
    print("METAGAME TABLE")
    print("Win=2, Tie=1, Loss=0 | Each matchup played twice")
    print("=" * 60)
    print()

    for i, d1 in enumerate(deck_names):
        for j, d2 in enumerate(deck_names):
            if j < i:
                continue

            # Check cache first
            cache_key1 = f"{d1}_vs_{d2}_p0"
            cache_key2 = f"{d1}_vs_{d2}_p1"

            g1_res = MATCHUP_CACHE.get(cache_key1)
            g2_res = MATCHUP_CACHE.get(cache_key2)

            # If not in cache, try to compute
            if g1_res is None or g2_res is None:
                p1_hand = DECKS[d1][1](0)
                p2_hand = DECKS[d2][1](1)

                if g1_res is None:
                    _, desc1 = solve_with_timeout(
                        [c.copy() for c in p1_hand],
                        [c.copy() for c in p2_hand],
                        first_player=0,
                        timeout_sec=args.timeout
                    )
                    if desc1 is not None:
                        g1_res = "P1" if desc1 == "P1 Wins" else ("P2" if desc1 == "P2 Wins" else "Tie")
                        MATCHUP_CACHE[cache_key1] = g1_res

                if g2_res is None:
                    _, desc2 = solve_with_timeout(
                        [c.copy() for c in p1_hand],
                        [c.copy() for c in p2_hand],
                        first_player=1,
                        timeout_sec=args.timeout
                    )
                    if desc2 is not None:
                        g2_res = "P1" if desc2 == "P1 Wins" else ("P2" if desc2 == "P2 Wins" else "Tie")
                        MATCHUP_CACHE[cache_key2] = g2_res

                # Save cache after new results
                if g1_res is not None or g2_res is not None:
                    save_cache(MATCHUP_CACHE)

            if g1_res is None or g2_res is None:
                print(f"  {d1} vs {d2}: TIMEOUT")
                points[i][j] = 2
                points[j][i] = 2
                results[i][j] = ('?', '?')
                results[j][i] = ('?', '?')
                continue

            # Convert to W/L/T from d1's perspective
            # g1_res is when d1 is on the play (P1 goes first)
            # g2_res is when d1 is on the draw (P2 goes first)
            def to_wlt(res):
                if res == "P1":
                    return 'W'
                elif res == "P2":
                    return 'L'
                else:
                    return 'T'

            d1_play = to_wlt(g1_res)  # d1 on play
            d1_draw = to_wlt(g2_res)  # d1 on draw

            # Flip for d2's perspective
            flip = {'W': 'L', 'L': 'W', 'T': 'T'}
            d2_play = flip[d1_draw]  # d2 on play = d1 on draw, flipped
            d2_draw = flip[d1_play]  # d2 on draw = d1 on play, flipped

            results[i][j] = (d1_play, d1_draw)
            results[j][i] = (d2_play, d2_draw)

            # Calculate points
            d1_pts, d2_pts = 0, 0
            if g1_res == "P1":
                d1_pts += 2
            elif g1_res == "P2":
                d2_pts += 2
            else:
                d1_pts += 1
                d2_pts += 1

            if g2_res == "P1":
                d1_pts += 2
            elif g2_res == "P2":
                d2_pts += 2
            else:
                d1_pts += 1
                d2_pts += 1

            points[i][j] = d1_pts
            points[j][i] = d2_pts
            print(f"  {d1} vs {d2}: {d1}:{d1_pts}, {d2}:{d2_pts}")

    elapsed = time.time() - start_time

    print()
    print("=" * 60)
    print("RESULTS TABLE (Play/Draw from row's perspective)")
    print("W=Win, L=Loss, T=Tie | First letter=on play, Second=on draw")
    print("=" * 60)
    print()

    header = f"{'Deck':<12}" + "".join(f"{name:<10}" for name in deck_names)
    print(header)
    print("-" * len(header))

    for i, name in enumerate(deck_names):
        row = f"{name:<12}"
        for j in range(n):
            if results[i][j]:
                play, draw = results[i][j]
                colored = colorize_result(play, draw)
                # Pad to 10 chars (accounting for ANSI codes not taking visual space)
                row += colored + " " * 8
            else:
                row += f"{'--':<10}"
        print(row)

    print()
    print("=" * 60)
    print("ZERO-SUM PAYOFF MATRIX")
    print("(Points - 2 to make zero-sum)")
    print("=" * 60)
    print()

    # Convert to zero-sum matrix (subtract 2 from all entries)
    import numpy as np
    payoff_matrix = np.array([[points[i][j] - 2 for j in range(n)] for i in range(n)])

    header = f"{'Deck':<12}" + "".join(f"{name:<10}" for name in deck_names)
    print(header)
    print("-" * len(header))

    for i, name in enumerate(deck_names):
        row = f"{name:<12}"
        for j in range(n):
            val = payoff_matrix[i][j]
            row += f"{val:+.0f}".ljust(10)
        print(row)

    # Calculate Nash equilibrium
    print()
    print("=" * 60)
    print("NASH EQUILIBRIUM")
    print("=" * 60)
    print()

    from simulator.nash import compute_nash_equilibrium, format_nash_strategy
    row_strat, col_strat, game_value = compute_nash_equilibrium(payoff_matrix)

    print("Optimal mixed strategy:")
    for i, prob in enumerate(row_strat):
        if prob >= 0.01:  # Only show if >= 1%
            print(f"  {deck_names[i]:<12}: {prob*100:5.1f}%")

    print()
    print(f"Game value: {game_value:+.4f}")
    print()
    print(f"Total time: {elapsed:.2f} seconds")


def get_creature_powers(state):
    """Get a dict of creature name -> current power for all creatures on battlefield."""
    powers = {}
    for player in [0, 1]:
        for card in state.battlefield[player]:
            if hasattr(card, 'power'):
                if hasattr(card, 'current_power'):
                    powers[card.name] = card.current_power
                else:
                    powers[card.name] = card.power
    return powers


def format_power_changes(before, after):
    """Format power changes as (Name: X→Y, ...)."""
    changes = []
    for name in after:
        if name in before and before[name] != after[name]:
            changes.append(f"{name}: {before[name]}→{after[name]}")
        elif name not in before:
            # New creature entered
            pass
    if changes:
        return f"({', '.join(changes)})"
    return ""


def get_card_states(state):
    """Get relevant state info for all cards (tapped status, counters, etc)."""
    cards = {}
    for player in [0, 1]:
        for i, card in enumerate(state.battlefield[player]):
            info = {'tapped': card.tapped}
            # Track various counter types
            if hasattr(card, 'storage_counters'):
                info['storage'] = card.storage_counters
            if hasattr(card, 'depletion_counters'):
                info['depletion'] = card.depletion_counters
            if hasattr(card, 'stun_counters'):
                info['stun'] = card.stun_counters
            if hasattr(card, 'plus_counters'):
                info['plus'] = card.plus_counters
            if hasattr(card, 'level'):
                info['level'] = card.level
            if hasattr(card, 'mana_produced'):
                info['mana'] = card.mana_produced
            if hasattr(card, 'spore_counters'):
                info['spore'] = card.spore_counters
            cards[(player, card.name, i)] = info
        # Track token counts for notes
        saproling_count = sum(1 for c in state.battlefield[player] if c.name == "Saproling")
        if saproling_count > 0:
            cards[(player, "_saproling_count", 0)] = {'count': saproling_count}
        for i, card in enumerate(state.artifacts[player]):
            info = {'tapped': card.tapped}
            if hasattr(card, 'mana_produced'):
                info['mana'] = card.mana_produced
            cards[(player, card.name, i)] = info
    return cards


def format_notes(before, after, active_player):
    """Format notes about state changes (mana tapped, counters changed, etc)."""
    notes = []

    # Check for changes in existing cards
    for key in before:
        player, name, idx = key
        if key not in after:
            # Card was removed (sacrificed)
            if before[key].get('mana') and not before[key]['tapped']:
                notes.append(f"{name} (sac)")
            continue

        old = before[key]
        new = after[key]

        # Mana tapped (only for active player)
        if player == active_player and old.get('mana'):
            if not old['tapped'] and new['tapped']:
                if 'storage' in old and 'storage' in new and old['storage'] != new['storage']:
                    notes.append(f"{name} {old['storage']}→{new['storage']} counters")
                elif 'depletion' in old and 'depletion' in new and old['depletion'] != new['depletion']:
                    notes.append(f"{name} {old['depletion']}→{new['depletion']} counters")
                else:
                    notes.append(f"tap {name}")

        # Storage counter changes (even when not tapping - e.g., upkeep)
        if 'storage' in old and 'storage' in new and old['storage'] != new['storage']:
            if old['tapped'] == new['tapped']:  # Counter changed without tap state change
                notes.append(f"{name} {old['storage']}→{new['storage']} counters")

        # Level changes (Student of Warfare)
        if 'level' in old and 'level' in new and old['level'] != new['level']:
            notes.append(f"{name} lvl {old['level']}→{new['level']}")

    if notes:
        return "[" + ", ".join(notes) + "]"
    return ""


def format_upkeep_notes(before, after, active_player):
    """Format notes about counter changes during upkeep."""
    notes = []

    # Check for counter changes in the active player's permanents
    for key in after:
        player, name, idx = key
        if player != active_player:
            continue

        # Find matching card in before state (might have different index due to switching players)
        old_key = None
        for bkey in before:
            if bkey[0] == player and bkey[1] == name:
                old_key = bkey
                break

        if old_key is None:
            continue

        old = before[old_key]
        new = after[key]

        # Storage counter changes (upkeep trigger for Bottomless Vault)
        if 'storage' in old and 'storage' in new and old['storage'] != new['storage']:
            notes.append(f"{name} {old['storage']}→{new['storage']} counters")

        # Stun counter removal during untap
        if 'stun' in old and 'stun' in new and old['stun'] != new['stun']:
            notes.append(f"{name} stun {old['stun']}→{new['stun']}")

        # Spore counter changes (Thallid upkeep)
        if 'spore' in old and 'spore' in new and old['spore'] != new['spore']:
            notes.append(f"{name} spores {old['spore']}→{new['spore']}")

        # Level changes (Student of Warfare auto-level)
        if 'level' in old and 'level' in new and old['level'] != new['level']:
            notes.append(f"{name} lvl {old['level']}→{new['level']}")

    # Check for Saproling token creation
    old_sap_key = (active_player, "_saproling_count", 0)
    new_sap_key = (active_player, "_saproling_count", 0)
    old_count = before.get(old_sap_key, {}).get('count', 0)
    new_count = after.get(new_sap_key, {}).get('count', 0)
    if new_count > old_count:
        created = new_count - old_count
        if created == 1:
            notes.append("Created Saproling token")
        else:
            notes.append(f"Created {created} Saproling tokens")

    if notes:
        return "[" + ", ".join(notes) + "]"
    return ""


def cmd_show(args):
    """Show optimal play line."""
    d1_name, d1_factory = DECKS[args.deck1][0], DECKS[args.deck1][1]
    d2_name, d2_factory = DECKS[args.deck2][0], DECKS[args.deck2][1]

    print("=" * 85)
    print(f"{d1_name} vs {d2_name}")
    print(f"First player: {'P1' if args.first == 0 else 'P2'}")
    print("=" * 85)

    p1_hand = d1_factory(0)
    p2_hand = d2_factory(1)

    state = GameState(
        life=[20, 20],
        hands=[[c.copy() for c in p1_hand], [c.copy() for c in p2_hand]],
        battlefield=[[], []],
        artifacts=[[], []],
        graveyard=[[], []],
        active_player=args.first,
        phase="main1",
        turn=1
    )

    result, desc = solve(
        [c.copy() for c in p1_hand],
        [c.copy() for c in p2_hand],
        first_player=args.first
    )
    print(f"Result: {desc}")
    print()

    print(f"{'Turn':<6} {'Player':<6} {'Action':<35} {'P1 Life':<8} {'P2 Life':<8} {'Notes'}")
    print("-" * 100)

    last_turn_end_state = None
    stalemate_count = 0
    depth = 0
    memo = {}

    while not state.game_over and depth < args.max_depth:
        if state.phase == "combat_damage":
            state = resolve_combat_damage(state)
            continue
        if state.phase == "end_turn":
            # Include level, spore_counters, and other changing state in signature
            def card_sig(c):
                return (c.name, getattr(c, 'stun_counters', 0), getattr(c, 'level', 0),
                        getattr(c, 'spore_counters', 0), getattr(c, 'storage_counters', 0))
            bf0_sig = tuple(card_sig(c) for c in state.battlefield[0])
            bf1_sig = tuple(card_sig(c) for c in state.battlefield[1])
            current_state_sig = (
                tuple(state.life),
                bf0_sig, bf1_sig,
                tuple(c.name for c in state.hands[0]),
                tuple(c.name for c in state.hands[1]),
            )
            if current_state_sig == last_turn_end_state:
                stalemate_count += 1
                if stalemate_count >= 3:
                    print("... (stalemate) ...")
                    break
            else:
                stalemate_count = 0
            last_turn_end_state = current_state_sig
            state = end_turn(state)
            continue
        if state.phase == "untap":
            state = untap(state)
            continue
        if state.phase == "upkeep":
            # Track state changes during upkeep (triggers, auto-level)
            cards_before = get_card_states(state)
            active = state.active_player  # Save before upkeep modifies state
            state = upkeep(state)
            cards_after = get_card_states(state)
            upkeep_notes = format_upkeep_notes(cards_before, cards_after, active)
            if upkeep_notes:
                player = "P1" if active == 0 else "P2"
                print(f"{state.turn:<6} {player:<6} {'(upkeep)':<35} {state.life[0]:<8} {state.life[1]:<8} {upkeep_notes}")
            continue

        actions = get_available_actions(state)
        if not actions:
            break

        if state.phase == "combat_block":
            decision_maker = 1 - state.active_player
        else:
            decision_maker = state.active_player

        best_action = None
        best_score = None
        for action in actions:
            new_state = action.execute(state)
            score = minimax(new_state, decision_maker, memo, 0)
            if best_score is None or score > best_score:
                best_score = score
                best_action = action

        if best_action:
            player = "P1" if state.active_player == 0 else "P2"
            action_player = state.active_player
            if state.phase == "combat_block":
                player = "P1" if (1 - state.active_player) == 0 else "P2"
                action_player = 1 - state.active_player
            powers_before = get_creature_powers(state)
            cards_before = get_card_states(state)
            state = best_action.execute(state)
            powers_after = get_creature_powers(state)
            cards_after = get_card_states(state)
            power_str = format_power_changes(powers_before, powers_after)
            notes_str = format_notes(cards_before, cards_after, action_player)
            extra = " ".join(filter(None, [notes_str, power_str]))
            print(f"{state.turn:<6} {player:<6} {best_action.description:<35} {state.life[0]:<8} {state.life[1]:<8} {extra}")

        depth += 1

    if state.game_over:
        if state.winner == 0:
            print(f"\n>>> P1 WINS")
        elif state.winner == 1:
            print(f"\n>>> P2 WINS")
        else:
            print(f"\n>>> DRAW")
    elif desc == "Draw/Tie":
        print(f"\n>>> DRAW (stalemate)")


def cmd_list(args):
    """List available decks."""
    print("Available decks:")
    for key, (name, _) in DECKS.items():
        print(f"  {key:<12} {name}")


def cmd_goldfish(args):
    """Test a deck against goldfish (no opponent cards)."""
    d1_name, d1_factory = DECKS[args.deck][0], DECKS[args.deck][1]

    print(f"\n{d1_name} vs Goldfish")
    print("-" * 40)

    p1_hand = d1_factory(0)

    if args.show:
        # Show detailed optimal line (reuse cmd_show logic)
        state = GameState(
            life=[20, 20],
            hands=[[c.copy() for c in p1_hand], []],
            battlefield=[[], []],
            artifacts=[[], []],
            graveyard=[[], []],
            active_player=0,
            phase="main1",
            turn=1
        )

        result, desc = solve([c.copy() for c in p1_hand], [], first_player=0)
        print(f"Result: {desc}")
        print()

        print(f"{'Turn':<6} {'Player':<6} {'Action':<35} {'P1 Life':<8} {'P2 Life':<8} {'Notes'}")
        print("-" * 100)

        memo = {}
        depth = 0

        while not state.game_over and depth < args.max_depth:
            if state.phase == "combat_damage":
                state = resolve_combat_damage(state)
                continue
            if state.phase == "end_turn":
                state = end_turn(state)
                continue
            if state.phase == "untap":
                state = untap(state)
                continue
            if state.phase == "upkeep":
                cards_before = get_card_states(state)
                active = state.active_player
                state = upkeep(state)
                cards_after = get_card_states(state)
                upkeep_notes = format_upkeep_notes(cards_before, cards_after, active)
                if upkeep_notes:
                    player = "P1" if active == 0 else "P2"
                    print(f"{state.turn:<6} {player:<6} {'(upkeep)':<35} {state.life[0]:<8} {state.life[1]:<8} {upkeep_notes}")
                continue

            actions = get_available_actions(state)
            if not actions:
                break

            if state.phase == "combat_block":
                decision_maker = 1 - state.active_player
            else:
                decision_maker = state.active_player

            best_action = None
            best_score = None
            for action in actions:
                new_state = action.execute(state)
                score = minimax(new_state, decision_maker, memo, 0)
                if best_score is None or score > best_score:
                    best_score = score
                    best_action = action

            if best_action:
                player = "P1" if state.active_player == 0 else "P2"
                action_player = state.active_player
                if state.phase == "combat_block":
                    player = "P1" if (1 - state.active_player) == 0 else "P2"
                    action_player = 1 - state.active_player
                cards_before = get_card_states(state)
                powers_before = get_creature_powers(state)
                state = best_action.execute(state)
                cards_after = get_card_states(state)
                powers_after = get_creature_powers(state)
                notes = format_notes(cards_before, cards_after, action_player)
                power_changes = format_power_changes(powers_before, powers_after)
                all_notes = " ".join(filter(None, [notes, power_changes]))
                print(f"{state.turn:<6} {player:<6} {best_action.description:<35} {state.life[0]:<8} {state.life[1]:<8} {all_notes}")

            depth += 1

        if state.game_over:
            if state.winner == 0:
                print(f"\n>>> P1 WINS on turn {state.turn}")
            elif state.winner == 1:
                print(f"\n>>> P2 WINS")
    else:
        # Compact output: actions, notes, and win turn
        state = GameState(
            life=[20, 20],
            hands=[[c.copy() for c in p1_hand], []],
            battlefield=[[], []],
            artifacts=[[], []],
            graveyard=[[], []],
            active_player=0,
            phase="main1",
            turn=1
        )

        print(f"{'Turn':<6} {'Action':<40} {'Life':<6} {'Notes'}")
        print("-" * 80)

        memo = {}
        depth = 0
        p1_turn = 1  # Track P1's turn count separately
        last_p1_turn_printed = 0

        while not state.game_over and depth < args.max_depth:
            if state.phase == "combat_damage":
                state = resolve_combat_damage(state)
                continue
            if state.phase == "end_turn":
                # Track when P1's turn ends to increment counter
                if state.active_player == 0:
                    p1_turn += 1
                state = end_turn(state)
                continue
            if state.phase == "untap":
                state = untap(state)
                continue
            if state.phase == "upkeep":
                cards_before = get_card_states(state)
                active = state.active_player
                state = upkeep(state)
                cards_after = get_card_states(state)
                upkeep_notes = format_upkeep_notes(cards_before, cards_after, active)
                if upkeep_notes and active == 0:
                    print(f"{p1_turn:<6} {'(upkeep)':<40} {state.life[1]:<6} {upkeep_notes}")
                    last_p1_turn_printed = p1_turn
                continue

            actions = get_available_actions(state)
            if not actions:
                break

            # Only care about P1's actions (goldfish just passes)
            if state.active_player == 1:
                for action in actions:
                    if "Pass" in action.description or "No" in action.description:
                        state = action.execute(state)
                        break
                depth += 1
                continue

            if state.phase == "combat_block":
                decision_maker = 1 - state.active_player
            else:
                decision_maker = state.active_player

            best_action = None
            best_score = None
            for action in actions:
                new_state = action.execute(state)
                score = minimax(new_state, decision_maker, memo, 0)
                if best_score is None or score > best_score:
                    best_score = score
                    best_action = action

            if best_action:
                # Skip Pass/No Attack/No Block for cleaner output
                if "Pass" not in best_action.description and "No " not in best_action.description:
                    cards_before = get_card_states(state)
                    powers_before = get_creature_powers(state)
                    state = best_action.execute(state)
                    cards_after = get_card_states(state)
                    powers_after = get_creature_powers(state)
                    notes = format_notes(cards_before, cards_after, 0)
                    power_changes = format_power_changes(powers_before, powers_after)
                    all_notes = " ".join(filter(None, [notes, power_changes]))
                    print(f"{p1_turn:<6} {best_action.description:<40} {state.life[1]:<6} {all_notes}")
                    last_p1_turn_printed = p1_turn
                else:
                    state = best_action.execute(state)

            depth += 1

        print("-" * 80)
        if state.game_over and state.winner == 0:
            # Use last printed turn or current p1_turn
            win_turn = last_p1_turn_printed if last_p1_turn_printed > 0 else p1_turn
            print(f"Goldfish defeated on turn {win_turn}")
        elif state.game_over and state.winner == 1:
            print(f"P1 LOSES (somehow?)")
        else:
            print(f"Draw/Timeout")


def main():
    parser = argparse.ArgumentParser(
        description="3CB Combat Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py solve tiger scf           Solve Tiger vs SCF matchup
  python cli.py solve student scf --first 1   Student vs SCF, P2 first
  python cli.py goldfish student          Test Student vs Goldfish
  python cli.py goldfish student --show   Show optimal line vs Goldfish
  python cli.py metagame                  Run full metagame table
  python cli.py show tiger scf            Show optimal play line
  python cli.py list                      List available decks
        """
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # solve command
    p = subparsers.add_parser("solve", help="Solve a matchup")
    p.add_argument("deck1", choices=DECKS.keys(), help="First deck")
    p.add_argument("deck2", choices=DECKS.keys(), help="Second deck")
    p.add_argument("--first", type=int, default=0, choices=[0, 1],
                   help="Who goes first (0=P1, 1=P2)")
    p.add_argument("--timeout", type=int, default=30, help="Solver timeout in seconds")

    # metagame command
    p = subparsers.add_parser("metagame", help="Run metagame table")
    p.add_argument("--timeout", type=int, default=30, help="Solver timeout per game")

    # show command
    p = subparsers.add_parser("show", help="Show optimal play line")
    p.add_argument("deck1", choices=DECKS.keys(), help="First deck")
    p.add_argument("deck2", choices=DECKS.keys(), help="Second deck")
    p.add_argument("--first", type=int, default=0, choices=[0, 1],
                   help="Who goes first (0=P1, 1=P2)")
    p.add_argument("--max-depth", type=int, default=200, help="Max turns to show")

    # list command
    subparsers.add_parser("list", help="List available decks")

    # goldfish command
    non_goldfish_decks = [k for k in DECKS.keys() if k != "goldfish"]
    p = subparsers.add_parser("goldfish", help="Test a deck against goldfish (no opponent)")
    p.add_argument("deck", choices=non_goldfish_decks, help="Deck to test")
    p.add_argument("--show", "-s", action="store_true", help="Show optimal play line")
    p.add_argument("--timeout", type=int, default=30, help="Solver timeout in seconds")
    p.add_argument("--max-depth", type=int, default=100, help="Max turns to show")

    args = parser.parse_args()
    {
        "solve": cmd_solve,
        "metagame": cmd_metagame,
        "show": cmd_show,
        "list": cmd_list,
        "goldfish": cmd_goldfish,
    }[args.command](args)


if __name__ == "__main__":
    main()
