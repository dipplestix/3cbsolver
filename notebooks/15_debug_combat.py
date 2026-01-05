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
        # 15: Debug - Combat Resolution

        Deep dive into combat damage resolution with step-by-step tracing.

        ## Scenarios Covered
        1. First strike vs vanilla
        2. Double strike damage
        3. Deathtouch interactions
        4. Multiple blockers
        5. Unblocked creatures
        """
    )
    return


@app.cell
def _():
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
    from simulator.helpers import (
        get_creature_power, get_creature_toughness,
        has_first_strike, has_double_strike, has_deathtouch,
        is_lethal_damage
    )
    return (
        Creature,
        GameState,
        get_creature_power,
        get_creature_toughness,
        has_deathtouch,
        has_double_strike,
        has_first_strike,
        is_lethal_damage,
        resolve_combat_damage,
    )


@app.cell
def _(mo):
    mo.md("---\n## Scenario 1: First Strike Advantage")
    return


@app.cell
def _(Creature, GameState, has_first_strike, resolve_combat_damage):
    # 3/2 first strike vs 4/4 vanilla
    fs_attacker = Creature("First Striker", 0, 3, 2, {'W': 1}, keywords=['first_strike'])
    fs_attacker.attacking = True

    big_blocker = Creature("Big Blocker", 1, 4, 4, {'G': 1})

    fs_state = GameState(
        life=[20, 20],
        battlefield=[[fs_attacker], [big_blocker]],
        blocking_assignments={0: 0},
        phase="combat_damage",
        active_player=0
    )

    print("SCENARIO: 3/2 First Strike vs 4/4 Vanilla")
    print(f"  Attacker has first strike: {has_first_strike(fs_attacker)}")
    print("\nStep 1: First strike damage")
    print("  3/2 deals 3 to 4/4 → 4/4 takes 3 damage (survives)")
    print("\nStep 2: Regular damage")
    print("  4/4 deals 4 to 3/2 → 3/2 takes 4 damage (dies, 4 >= 2)")
    print("  3/2 already dealt damage, doesn't deal again")

    result = resolve_combat_damage(fs_state)
    print(f"\nResult:")
    print(f"  Attackers remaining: {len(result.battlefield[0])}")
    print(f"  Blockers remaining: {len(result.battlefield[1])}")
    print(f"  Blocker damage: {result.battlefield[1][0].damage if result.battlefield[1] else 'N/A'}")
    return big_blocker, fs_attacker, fs_state, result


@app.cell
def _(mo):
    mo.md("---\n## Scenario 2: Double Strike")
    return


@app.cell
def _(Creature, GameState, resolve_combat_damage):
    # 2/2 double strike vs 3/3 vanilla
    ds_attacker = Creature("Double Striker", 0, 2, 2, {'R': 1})
    ds_attacker.attacking = True
    ds_attacker.has_double_strike = True

    vanilla_blocker = Creature("Vanilla", 1, 3, 3, {'G': 1})

    ds_state = GameState(
        life=[20, 20],
        battlefield=[[ds_attacker], [vanilla_blocker]],
        blocking_assignments={0: 0},
        phase="combat_damage",
        active_player=0
    )

    print("SCENARIO: 2/2 Double Strike vs 3/3 Vanilla")
    print("\nStep 1: First strike damage")
    print("  2/2 DS deals 2 → 3/3 takes 2 damage")
    print("\nStep 2: Regular damage")
    print("  2/2 DS deals 2 MORE → 3/3 takes 4 total (dies)")
    print("  3/3 deals 3 → 2/2 takes 3 (dies)")

    ds_result = resolve_combat_damage(ds_state)
    print(f"\nResult: BOTH DIE")
    print(f"  Attackers: {len(ds_result.battlefield[0])}")
    print(f"  Blockers: {len(ds_result.battlefield[1])}")
    return ds_attacker, ds_result, ds_state, vanilla_blocker


@app.cell
def _(mo):
    mo.md("---\n## Scenario 3: Deathtouch")
    return


@app.cell
def _(Creature, GameState, is_lethal_damage, resolve_combat_damage):
    # 1/1 deathtouch vs 10/10
    dt_attacker = Creature("Deathtouch", 0, 1, 1, {'B': 1})
    dt_attacker.attacking = True
    dt_attacker.has_deathtouch = True

    giant = Creature("Giant", 1, 10, 10, {'G': 3})

    dt_state = GameState(
        life=[20, 20],
        battlefield=[[dt_attacker], [giant]],
        blocking_assignments={0: 0},
        phase="combat_damage",
        active_player=0
    )

    print("SCENARIO: 1/1 Deathtouch vs 10/10")
    print(f"\nDeathtouch lethality check:")
    print(f"  1 damage to 10 toughness (no DT): {is_lethal_damage(1, 10, False)}")
    print(f"  1 damage to 10 toughness (WITH DT): {is_lethal_damage(1, 10, True)}")

    dt_result = resolve_combat_damage(dt_state)
    print(f"\nResult: BOTH DIE (deathtouch kills giant)")
    print(f"  Attackers: {len(dt_result.battlefield[0])}")
    print(f"  Blockers: {len(dt_result.battlefield[1])}")
    return dt_attacker, dt_result, dt_state, giant


@app.cell
def _(mo):
    mo.md("---\n## Scenario 4: First Strike + Deathtouch")
    return


@app.cell
def _(Creature, GameState, resolve_combat_damage):
    # 1/1 first strike deathtouch vs 5/5
    fsdt = Creature("FS+DT", 0, 1, 1, {'B': 1}, keywords=['first_strike'])
    fsdt.attacking = True
    fsdt.has_deathtouch = True

    big_guy = Creature("Big Guy", 1, 5, 5, {'G': 2})

    fsdt_state = GameState(
        life=[20, 20],
        battlefield=[[fsdt], [big_guy]],
        blocking_assignments={0: 0},
        phase="combat_damage",
        active_player=0
    )

    print("SCENARIO: 1/1 First Strike Deathtouch vs 5/5")
    print("\nStep 1: First strike damage")
    print("  1/1 FS+DT deals 1 deathtouch → 5/5 DIES")
    print("  5/5 is dead, doesn't deal damage back")
    print("\nStep 2: Regular damage")
    print("  1/1 already dealt (no double strike)")
    print("  5/5 is dead, removed")

    fsdt_result = resolve_combat_damage(fsdt_state)
    print(f"\nResult: Only 5/5 dies!")
    print(f"  Attackers: {len(fsdt_result.battlefield[0])}")
    print(f"  Blockers: {len(fsdt_result.battlefield[1])}")
    return big_guy, fsdt, fsdt_result, fsdt_state


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Key Takeaways

        1. **First strike** deals damage first, can kill before getting hit
        2. **Double strike** hits twice (FS step + regular step)
        3. **Deathtouch** makes any damage lethal (damage > 0)
        4. **FS + DT** is powerful - kills before counterattack

        Combat resolution order matters significantly for game outcomes.
        """
    )
    return


if __name__ == "__main__":
    app.run()
