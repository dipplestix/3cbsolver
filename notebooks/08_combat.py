import marimo

__generated_with = "0.10.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _(mo):
    mo.md(
        """
        # 08: Combat Damage Resolution

        **File:** `simulator/combat.py`

        Handles the combat_damage phase with full MTG combat rules:
        - First strike / double strike ordering
        - Deathtouch lethality
        - Player damage for unblocked creatures
        - Death triggers and graveyard movement

        ## Combat Flow
        ```
        combat_attack → combat_block → combat_damage → end_turn
                                            ↑
                                       (this module)
        ```
        """
    )
    return


@app.cell
def _():
    # Setup: Add parent directory to path for imports
    import sys
    from pathlib import Path

    project_root = Path(__file__).parent.parent if "__file__" in dir() else Path.cwd().parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    return Path, project_root, sys


@app.cell
def _():
    from simulator.combat import resolve_combat_damage
    from simulator.game_state import GameState
    from simulator.cards.creature import Creature
    return Creature, GameState, resolve_combat_damage


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## First Strike / Double Strike

        Combat damage happens in two steps:

        ### Step 1: First Strike Damage
        Only creatures with first strike OR double strike deal damage.
        Deaths are checked immediately.

        ### Step 2: Regular Damage
        - Creatures WITHOUT first strike deal damage
        - Creatures WITH double strike deal damage AGAIN
        - Deaths are checked

        ### Key Insight
        First strike advantage: Kill before being hit back.
        """
    )
    return


@app.cell
def _(Creature, GameState, resolve_combat_damage):
    # First strike example: 2/2 first strike vs 3/3 vanilla

    first_striker = Creature("First Striker", 0, 2, 2, {'W': 1}, keywords=['first_strike'])
    first_striker.attacking = True

    vanilla = Creature("Vanilla", 1, 3, 3, {'G': 1})

    fs_state = GameState(
        battlefield=[[first_striker], [vanilla]],
        blocking_assignments={0: 0},  # Vanilla blocks First Striker
        phase="combat_damage",
        active_player=0
    )

    print("First Strike Example:")
    print(f"  Attacker: 2/2 first strike")
    print(f"  Blocker: 3/3 vanilla")
    print(f"\nStep 1: First strike deals 2 damage to 3/3")
    print(f"  3/3 takes 2 damage (survives)")
    print(f"Step 2: 3/3 deals 3 damage to 2/2")
    print(f"  2/2 takes 3 damage (dies)")

    after_fs = resolve_combat_damage(fs_state)
    print(f"\nResult:")
    print(f"  Attackers left: {len(after_fs.battlefield[0])}")
    print(f"  Blockers left: {len(after_fs.battlefield[1])}")
    print(f"  Blocker damage: {after_fs.battlefield[1][0].damage if after_fs.battlefield[1] else 'N/A'}")
    return after_fs, first_striker, fs_state, vanilla


@app.cell
def _(Creature, GameState, resolve_combat_damage):
    # Double strike: hits twice!
    double_striker = Creature("Double Striker", 0, 2, 2, {'R': 1})
    double_striker.attacking = True
    double_striker.has_double_strike = True  # 2 + 2 = 4 damage

    blocker_3_4 = Creature("Big Blocker", 1, 3, 4, {'G': 1})

    ds_state = GameState(
        battlefield=[[double_striker], [blocker_3_4]],
        blocking_assignments={0: 0},
        phase="combat_damage",
        active_player=0
    )

    print("Double Strike Example:")
    print(f"  Attacker: 2/2 double strike")
    print(f"  Blocker: 3/4 vanilla")
    print(f"\nStep 1: 2/2 deals 2 first strike damage")
    print(f"Step 2: 2/2 deals 2 more + 3/4 deals 3")
    print(f"  Blocker takes 4 total, dies (4 >= 4 toughness)")
    print(f"  Attacker takes 3, dies (3 >= 2 toughness)")

    after_ds = resolve_combat_damage(ds_state)
    print(f"\nResult:")
    print(f"  Attackers left: {len(after_ds.battlefield[0])}")
    print(f"  Blockers left: {len(after_ds.battlefield[1])}")
    return after_ds, blocker_3_4, double_striker, ds_state


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Deathtouch

        Deathtouch makes ANY damage lethal (damage > 0).

        ```python
        def is_lethal_damage(damage, toughness, has_deathtouch):
            if has_deathtouch and damage > 0:
                return True
            return damage >= toughness
        ```

        1/1 deathtouch kills any creature it hits!
        """
    )
    return


@app.cell
def _(Creature, GameState, resolve_combat_damage):
    # Deathtouch example
    deathtouch = Creature("Deathtouch", 0, 1, 1, {'B': 1})
    deathtouch.attacking = True
    deathtouch.has_deathtouch = True

    big_creature = Creature("Big Guy", 1, 5, 5, {'G': 2})

    dt_state = GameState(
        battlefield=[[deathtouch], [big_creature]],
        blocking_assignments={0: 0},
        phase="combat_damage",
        active_player=0
    )

    print("Deathtouch Example:")
    print(f"  Attacker: 1/1 deathtouch")
    print(f"  Blocker: 5/5 vanilla")
    print(f"\nBoth deal damage simultaneously:")
    print(f"  1 deathtouch damage to 5/5 → LETHAL")
    print(f"  5 damage to 1/1 → lethal")

    after_dt = resolve_combat_damage(dt_state)
    print(f"\nResult (mutual destruction):")
    print(f"  Attackers left: {len(after_dt.battlefield[0])}")
    print(f"  Blockers left: {len(after_dt.battlefield[1])}")
    return after_dt, big_creature, deathtouch, dt_state


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Unblocked Creatures

        Unblocked attackers deal damage to the defending player:

        ```python
        if not blocked:
            ns.life[defender] -= get_creature_power(attacker)
            if hasattr(attacker, 'on_deal_combat_damage_to_player'):
                ns = attacker.on_deal_combat_damage_to_player(ns)
        ```

        The `on_deal_combat_damage_to_player` hook is for creatures like Stromkirk Noble.
        """
    )
    return


@app.cell
def _(Creature, GameState, resolve_combat_damage):
    # Unblocked damage
    attacker = Creature("Attacker", 0, 3, 3, {'R': 1})
    attacker.attacking = True

    unblocked_state = GameState(
        life=[20, 20],
        battlefield=[[attacker], []],  # No blockers
        blocking_assignments={},  # Not blocked
        phase="combat_damage",
        active_player=0
    )

    print("Unblocked Creature:")
    print(f"  3/3 attacks, no blockers")
    print(f"  Defender life before: {unblocked_state.life[1]}")

    after_unblocked = resolve_combat_damage(unblocked_state)
    print(f"  Defender life after: {after_unblocked.life[1]}")
    print(f"  Damage dealt: {unblocked_state.life[1] - after_unblocked.life[1]}")
    return after_unblocked, attacker, unblocked_state


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Death Handling

        When creatures die:
        1. Added to graveyard
        2. `on_death()` trigger called (if exists)
        3. Removed from battlefield

        Removal happens in reverse index order to avoid index shifting bugs.

        ```python
        for blocker_idx in sorted(dead_blockers, reverse=True):
            blocker = ns.battlefield[defender][blocker_idx]
            ns.graveyard[defender].append(blocker)
            if hasattr(blocker, 'on_death'):
                ns = blocker.on_death(ns)
            ns.battlefield[defender].pop(blocker_idx)
        ```
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Game Over Check

        After combat, check for lethal damage:

        ```python
        if ns.life[0] <= 0:
            ns.game_over = True
            ns.winner = 1
        elif ns.life[1] <= 0:
            ns.game_over = True
            ns.winner = 0
        ```

        Then transition to `end_turn` phase.
        """
    )
    return


@app.cell
def _(Creature, GameState, resolve_combat_damage):
    # Lethal damage to player
    big_attacker = Creature("Big Attacker", 0, 10, 10, {'R': 2})
    big_attacker.attacking = True

    lethal_state = GameState(
        life=[20, 5],  # Defender at 5 life
        battlefield=[[big_attacker], []],
        blocking_assignments={},
        phase="combat_damage",
        active_player=0
    )

    print("Lethal Damage Example:")
    print(f"  Attacker: 10/10")
    print(f"  Defender life: {lethal_state.life[1]}")

    after_lethal = resolve_combat_damage(lethal_state)
    print(f"\nAfter combat:")
    print(f"  Defender life: {after_lethal.life[1]}")
    print(f"  Game over: {after_lethal.game_over}")
    print(f"  Winner: {after_lethal.winner} (Player {after_lethal.winner})")
    return after_lethal, big_attacker, lethal_state


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Combat Damage Algorithm

        ```
        1. Build attacker list with indices
        2. Check if any creature has first strike
        3. IF any_first_strike:
           a. First strike damage step
           b. Check deaths, mark dead creatures
        4. Regular damage step (skip dead, double-strikers hit again)
        5. Check deaths
        6. Remove dead creatures (graveyard, triggers)
        7. Check game over
        8. Transition to end_turn
        ```
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Summary

        | Feature | Implementation |
        |---------|---------------|
        | First strike | Separate damage step |
        | Double strike | Hits in both steps |
        | Deathtouch | Any damage is lethal |
        | Unblocked | Damage to player |
        | Deaths | Graveyard + triggers |
        | Game over | Life <= 0 check |

        The combat system correctly handles complex scenarios like:
        - Double strike + deathtouch (kills in first step)
        - First strike vs vanilla (first striker survives)
        - Mutual deathtouch (both die)
        """
    )
    return


if __name__ == "__main__":
    app.run()
