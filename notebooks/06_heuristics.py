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
        # 06: Heuristics Module

        **File:** `simulator/heuristics.py`

        Early termination heuristics that detect mathematically determined outcomes
        without full tree search.

        ## Why Heuristics?
        Some game states have determined outcomes:
        - **Symmetric creatures** → Draw (neither can attack profitably)
        - **Token generator vs static** → Token generator wins
        - **Growing creature vs tokens** → Growing creature wins

        ## Activation Conditions
        - `evaluate_early_grinding()`: Depth > 15, hands empty
        - `evaluate_max_depth()`: Depth > 500 (fallback)
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
    from simulator.heuristics import (
        _has_token_generator,
        _can_grow,
        _has_creature_land,
        _has_deathtouch,
        _get_creatures,
        _creatures_are_symmetric,
        _is_combat_stalemate,
        evaluate_early_grinding,
        evaluate_max_depth,
        evaluate_position
    )
    return (
        _can_grow,
        _creatures_are_symmetric,
        _get_creatures,
        _has_creature_land,
        _has_deathtouch,
        _has_token_generator,
        _is_combat_stalemate,
        evaluate_early_grinding,
        evaluate_max_depth,
        evaluate_position,
    )


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Helper Functions

        ### Detection Functions
        | Function | Detects |
        |----------|---------|
        | `_has_token_generator` | Thallid (infinite tokens) |
        | `_can_grow` | Counters, levels < 7, Stromkirk |
        | `_has_creature_land` | Mutavault, etc. |
        | `_has_deathtouch` | Deathtouch keyword |
        | `_get_creatures` | All creatures with power > 0 |
        """
    )
    return


@app.cell
def _(_can_grow):
    # Test _can_grow with different creature types

    class StudentLevel3:
        """Student at level 3 (can still grow)."""
        level = 3

    class StudentLevel7:
        """Student at level 7+ (maxed out)."""
        level = 7

    class CounterCreature:
        """Creature with +1/+1 counters potential."""
        plus_counters = 0

    class StromkirkNoble:
        """Grows on combat damage."""
        name = "Stromkirk Noble"

    class StaticCreature:
        """Cannot grow."""
        power = 2
        toughness = 2

    print("_can_grow tests:")
    print(f"  Student level 3: {_can_grow([StudentLevel3()])}")
    print(f"  Student level 7: {_can_grow([StudentLevel7()])}")
    print(f"  Counter creature: {_can_grow([CounterCreature()])}")
    print(f"  Stromkirk Noble: {_can_grow([StromkirkNoble()])}")
    print(f"  Static creature: {_can_grow([StaticCreature()])}")
    return (
        CounterCreature,
        StaticCreature,
        StromkirkNoble,
        StudentLevel3,
        StudentLevel7,
    )


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Symmetric Creature Detection

        `_creatures_are_symmetric()` compares creature signatures:
        - Power, toughness
        - Deathtouch, first strike, double strike

        If both sides have equivalent creatures, neither can attack profitably.
        """
    )
    return


@app.cell
def _(_creatures_are_symmetric):
    # Test symmetric creature detection

    class Creature2_2:
        power = 2
        toughness = 2
        has_deathtouch = False
        has_first_strike = False
        has_double_strike = False

    class Creature3_3:
        power = 3
        toughness = 3
        has_deathtouch = False
        has_first_strike = False
        has_double_strike = False

    class Creature2_2_DT:
        power = 2
        toughness = 2
        has_deathtouch = True
        has_first_strike = False
        has_double_strike = False

    p1_same = [Creature2_2()]
    p2_same = [Creature2_2()]
    p1_diff = [Creature2_2()]
    p2_diff = [Creature3_3()]
    p1_dt = [Creature2_2_DT()]
    p2_dt = [Creature2_2_DT()]

    print("Symmetric creature tests:")
    print(f"  2/2 vs 2/2: {_creatures_are_symmetric(p1_same, p2_same)}")
    print(f"  2/2 vs 3/3: {_creatures_are_symmetric(p1_diff, p2_diff)}")
    print(f"  2/2 DT vs 2/2 DT: {_creatures_are_symmetric(p1_dt, p2_dt)}")
    return (
        Creature2_2,
        Creature2_2_DT,
        Creature3_3,
        p1_diff,
        p1_dt,
        p1_same,
        p2_diff,
        p2_dt,
        p2_same,
    )


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Combat Stalemate Detection

        `_is_combat_stalemate()` detects when combat leads nowhere:
        1. **Both have deathtouch** - Attacking = mutual destruction
        2. **Symmetric creatures** - Trading = no progress
        """
    )
    return


@app.cell
def _(_is_combat_stalemate):
    # Test combat stalemate detection

    class DeathtouchCreature:
        power = 1
        toughness = 1
        has_deathtouch = True

    class NormalCreature:
        power = 2
        toughness = 2
        has_deathtouch = False

    dt_vs_dt = [DeathtouchCreature()], [DeathtouchCreature()]
    dt_vs_normal = [DeathtouchCreature()], [NormalCreature()]
    normal_vs_normal = [NormalCreature()], [NormalCreature()]

    print("Combat stalemate tests:")
    print(f"  Deathtouch vs Deathtouch: {_is_combat_stalemate(*dt_vs_dt)}")
    print(f"  Deathtouch vs Normal: {_is_combat_stalemate(*dt_vs_normal)}")
    print(f"  Normal vs Normal (symmetric): {_is_combat_stalemate(*normal_vs_normal)}")
    return (
        DeathtouchCreature,
        NormalCreature,
        dt_vs_dt,
        dt_vs_normal,
        normal_vs_normal,
    )


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Early Grinding Heuristic

        `evaluate_early_grinding()` activates when:
        - Depth > 15
        - Both hands are empty (no more cards to play)

        ### Rules
        | Condition | Result |
        |-----------|--------|
        | Symmetric, no growth | Draw |
        | Token gen vs static | Token gen wins |
        """
    )
    return


@app.cell
def _(evaluate_early_grinding):
    # Create a mock game state for testing
    class MockState:
        def __init__(self, hands, battlefield):
            self.hands = hands
            self.battlefield = battlefield

    class MockThallid:
        name = "Thallid"
        power = 1
        toughness = 1

    class MockStatic:
        name = "Bear"
        power = 2
        toughness = 2
        has_deathtouch = False
        has_first_strike = False
        has_double_strike = False

    # Thallid vs static creature
    thallid_state = MockState(
        hands=[[], []],  # Hands empty
        battlefield=[[MockThallid()], [MockStatic()]]
    )

    # Test at different depths
    print("Thallid (token gen) vs Static creature:")
    print(f"  Depth 10: {evaluate_early_grinding(thallid_state, player=0, depth=10)}")
    print(f"  Depth 20: {evaluate_early_grinding(thallid_state, player=0, depth=20)}")
    print(f"  (Player 0 has Thallid, should win)")

    # Flip perspective
    print(f"\n  Player 1 perspective: {evaluate_early_grinding(thallid_state, player=1, depth=20)}")
    return MockState, MockStatic, MockThallid, thallid_state


@app.cell
def _(MockState, MockStatic, evaluate_early_grinding):
    # Test symmetric static creatures
    class MockSymmetric:
        name = "Soldier"
        power = 2
        toughness = 2
        has_deathtouch = False
        has_first_strike = False
        has_double_strike = False

    symmetric_state = MockState(
        hands=[[], []],
        battlefield=[[MockSymmetric()], [MockSymmetric()]]
    )

    print("Symmetric 2/2 vs 2/2 (no growth):")
    print(f"  Depth 20: {evaluate_early_grinding(symmetric_state, player=0, depth=20)}")
    print("  (Should be 0 = draw)")
    return MockSymmetric, symmetric_state


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Max Depth Heuristic

        `evaluate_max_depth()` is the fallback when depth > 500.

        ### Rules (in order)
        1. Cards in hand → Draw (can't resolve)
        2. One side has creatures, other has nothing → Creatures win
        3. Deathtouch + extra creature beats creature land
        4. Token gen beats static
        5. Growing creature beats token gen
        6. Default: Draw
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Main Entry Point

        `evaluate_position()` chains the heuristics:

        ```python
        def evaluate_position(state, player, depth):
            # Try early grinding (depth > 15)
            result = evaluate_early_grinding(state, player, depth)
            if result is not None:
                return result

            # Try max depth (depth > 500)
            result = evaluate_max_depth(state, player, depth)
            if result is not None:
                return result

            return None  # Continue searching
        ```
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Key Heuristic Insights

        ### Student of Warfare Mirror
        - At level 7+: `_can_grow()` returns False
        - Both 4/4 double strike → `_creatures_are_symmetric()` = True
        - Result: Draw at depth > 15

        ### Dragon Sniper Mirror
        - Both 1/1 deathtouch → `_is_combat_stalemate()` = True
        - Result: Draw at depth > 15

        ### Thallid vs Student
        - Student can grow → `_can_grow()` = True
        - Growing beats tokens
        - Result: Student wins

        ### Thallid vs Static
        - Static can't grow
        - Token gen overwhelms
        - Result: Thallid wins
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Summary

        | Heuristic | Activation | Purpose |
        |-----------|------------|---------|
        | Early grinding | depth > 15, empty hands | Detect obvious outcomes |
        | Max depth | depth > 500 | Fallback termination |

        ### Detection Functions
        - `_can_grow()`: Level < 7, counters, Stromkirk
        - `_is_combat_stalemate()`: Symmetric or mutual deathtouch
        - `_has_token_generator()`: Thallid detection

        Without these heuristics, Student vs Student would search forever.
        With them, it terminates as Draw once both reach level 7.
        """
    )
    return


if __name__ == "__main__":
    app.run()
