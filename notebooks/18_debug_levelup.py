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
        # 18: Debug - Level-Up Mechanics

        Deep dive into Student of Warfare auto-leveling.

        ## Key Questions
        1. When does auto-level happen?
        2. What triggers level-up?
        3. How does level affect stats?
        4. Why doesn't level-up cause branching?
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
    from simulator.cards.student_of_warfare import StudentOfWarfare
    from simulator.cards.land import create_plains
    from simulator.game_state import GameState
    return GameState, StudentOfWarfare, create_plains


@app.cell
def _(mo):
    mo.md("---\n## Student of Warfare Stats by Level")
    return


@app.cell
def _(StudentOfWarfare):
    student = StudentOfWarfare(owner=0)

    print("Student of Warfare level progression:")
    print(f"  Level 0: {student.current_power}/{student.current_toughness}")

    student.level = 1
    print(f"  Level 1: {student.current_power}/{student.current_toughness}")

    student.level = 2
    print(f"  Level 2: {student.current_power}/{student.current_toughness}, first strike: {student.has_first_strike}")

    student.level = 6
    print(f"  Level 6: {student.current_power}/{student.current_toughness}, first strike: {student.has_first_strike}")

    student.level = 7
    print(f"  Level 7: {student.current_power}/{student.current_toughness}, double strike: {student.has_double_strike}")
    return (student,)


@app.cell
def _(mo):
    mo.md("---\n## Auto-Level Mechanics")
    return


@app.cell
def _(GameState, StudentOfWarfare, create_plains):
    # Create state with student and mana
    test_student = StudentOfWarfare(owner=0)
    test_student.level = 0

    plains1 = create_plains(0)
    plains2 = create_plains(0)

    state = GameState(
        battlefield=[[plains1, plains2, test_student], []],
        active_player=0
    )

    print("Auto-level scenario:")
    print(f"  Available mana: {state.get_available_mana_by_color(0)}")
    print(f"  Student level before: {test_student.level}")

    # Call auto-level
    new_state = test_student.do_auto_level(state)

    # Find student in new state
    for card in new_state.battlefield[0]:
        if card.name == "Student of Warfare":
            print(f"  Student level after: {card.level}")
            print(f"  (Leveled up using all available W mana)")
            break
    return new_state, plains1, plains2, state, test_student


@app.cell
def _(mo):
    mo.md("---\n## When Auto-Level Triggers")
    return


@app.cell
def _(mo):
    mo.md(
        """
        Auto-level happens in **two places**:

        ### 1. Upkeep Phase
        ```python
        # In phases/upkeep.py:
        for card in ns.battlefield[ns.active_player]:
            if hasattr(card, 'auto_level') and card.auto_level:
                ns = card.do_auto_level(ns)
        ```

        Uses mana from untapped lands (from previous turns).

        ### 2. Pass to Combat
        ```python
        # In actions.py pass_to_combat:
        for card in ns.battlefield[player]:
            if hasattr(card, 'auto_level') and card.auto_level:
                ns = card.do_auto_level(ns)
        ```

        Uses mana from lands played this turn.
        """
    )
    return


@app.cell
def _(mo):
    mo.md("---\n## Why No Branching?")
    return


@app.cell
def _(mo):
    mo.md(
        """
        Level-up doesn't cause action branching because:

        1. **No manual level-up actions**
           ```python
           def get_battlefield_actions(self, state):
               # Level up is automatic, no manual actions
               return []
           ```

        2. **Auto-level uses all available mana**
           - No choice about how much to level
           - Always levels as much as possible

        3. **Deterministic timing**
           - Upkeep: Level with existing mana
           - Pass to combat: Level with new mana

        This reduces Student vs Student from exponential to linear!
        """
    )
    return


@app.cell
def _(mo):
    mo.md("---\n## Level 7 Cap and Heuristics")
    return


@app.cell
def _(mo):
    mo.md(
        """
        ### The Level 7 Problem

        Student maxes out at level 7 (4/4 double strike).
        After level 7:
        - `_can_grow()` returns False
        - Heuristic detects symmetric creatures
        - Game declared Draw

        ```python
        def _can_grow(creatures):
            for c in creatures:
                if hasattr(c, 'level'):
                    if c.level < 7:
                        return True  # Can still grow
                    # At max level, can't grow
            return False
        ```

        This is why Student vs Student terminates!
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Summary

        | Aspect | Implementation |
        |--------|---------------|
        | Level cost | 1W per level |
        | Auto-level timing | Upkeep + Pass to combat |
        | Manual actions | None (auto_level=True) |
        | Max level | 7 (4/4 double strike) |
        | Growth detection | level < 7 → can grow |

        The auto-level system makes Student tractable by eliminating
        branching from level-up decisions while still allowing the
        creature to grow optimally.
        """
    )
    return


if __name__ == "__main__":
    app.run()
