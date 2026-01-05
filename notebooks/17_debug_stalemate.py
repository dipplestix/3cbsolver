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
        # 17: Debug - Stalemate Detection

        Understanding how the solver detects and handles stalemates.

        ## Stalemate Types
        1. **Symmetric creatures** - Neither can attack profitably
        2. **Mutual deathtouch** - Attacking means mutual destruction
        3. **Board unchanged** - 10 turns with no progress
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
    from simulator.heuristics import (
        _creatures_are_symmetric,
        _is_combat_stalemate,
        _can_grow,
        evaluate_early_grinding
    )
    from simulator.game_state import GameState
    return (
        GameState,
        _can_grow,
        _creatures_are_symmetric,
        _is_combat_stalemate,
        evaluate_early_grinding,
    )


@app.cell
def _(mo):
    mo.md("---\n## Symmetric Creature Detection")
    return


@app.cell
def _(_creatures_are_symmetric):
    # Test symmetric detection
    class MaxStudent:
        """Student at level 7+"""
        power = 4
        toughness = 4
        has_first_strike = False
        has_double_strike = True
        has_deathtouch = False

        @property
        def current_power(self):
            return 4

        @property
        def current_toughness(self):
            return 4

    p1 = [MaxStudent()]
    p2 = [MaxStudent()]

    result = _creatures_are_symmetric(p1, p2)
    print("Student vs Student (both level 7):")
    print(f"  P1: 4/4 double strike")
    print(f"  P2: 4/4 double strike")
    print(f"  Symmetric: {result}")
    return MaxStudent, p1, p2, result


@app.cell
def _(mo):
    mo.md("---\n## Deathtouch Stalemate")
    return


@app.cell
def _(_is_combat_stalemate):
    class Sniper:
        """Dragon Sniper"""
        power = 1
        toughness = 1
        has_deathtouch = True
        has_first_strike = False
        has_double_strike = False

    snipers_p1 = [Sniper()]
    snipers_p2 = [Sniper()]

    stalemate = _is_combat_stalemate(snipers_p1, snipers_p2)
    print("Dragon Sniper vs Dragon Sniper:")
    print(f"  Both: 1/1 deathtouch")
    print(f"  Combat stalemate: {stalemate}")
    print("  (Attacking = mutual destruction, neither benefits)")
    return Sniper, snipers_p1, snipers_p2, stalemate


@app.cell
def _(mo):
    mo.md("---\n## Growth Detection")
    return


@app.cell
def _(_can_grow):
    class StudentLevel3:
        level = 3  # Can still grow

    class StudentLevel7:
        level = 7  # Maxed out

    class StaticCreature:
        power = 2

    print("_can_grow() tests:")
    print(f"  Student level 3: {_can_grow([StudentLevel3()])}")
    print(f"  Student level 7: {_can_grow([StudentLevel7()])}")
    print(f"  Static creature: {_can_grow([StaticCreature()])}")
    return StaticCreature, StudentLevel3, StudentLevel7


@app.cell
def _(mo):
    mo.md("---\n## Board Stalemate Counter")
    return


@app.cell
def _(GameState):
    # Simulate stalemate counting
    state = GameState(
        stale_turns=0,
        prev_main_sig=None
    )

    print("Stalemate detection in upkeep:")
    print(f"  Initial stale_turns: {state.stale_turns}")
    print(f"  Threshold for draw: 10 (5 full rounds)")
    print("\n  Each upkeep:")
    print("  - Compute board signature")
    print("  - If same as prev_main_sig: stale_turns++")
    print("  - If different: stale_turns = 0")
    print("  - If stale_turns >= 10: game_over = True, winner = None")
    return (state,)


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Why Stalemate Detection Matters

        Without it, symmetric matchups loop forever:

        | Matchup | Issue | Solution |
        |---------|-------|----------|
        | Student vs Student | Both reach 4/4 DS, can't attack | Symmetric heuristic |
        | Sniper vs Sniper | Both 1/1 DT, attacking = trade | Deathtouch stalemate |
        | Static vs Static | Neither can win | Board unchanged counter |

        The stalemate system makes these matchups terminate as draws.
        """
    )
    return


if __name__ == "__main__":
    app.run()
