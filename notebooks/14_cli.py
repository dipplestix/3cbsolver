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
        # 14: CLI and Deck Registry

        **File:** `cli.py`

        ## Commands

        | Command | Purpose |
        |---------|---------|
        | `solve` | Solve single matchup |
        | `show` | Show optimal play line |
        | `metagame` | Full round-robin + Nash |
        | `goldfish` | Deck vs empty hand |
        | `list` | Available decks |

        ## Usage Examples
        ```bash
        python cli.py solve tiger student
        python cli.py show tiger student --first 0
        python cli.py metagame --timeout 30
        python cli.py goldfish student --show
        python cli.py list
        ```
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Deck Registry

        Decks are defined as functions returning [Card, Card]:

        ```python
        def student_deck(owner: int):
            return [create_plains(owner), StudentOfWarfare(owner)]

        def tiger_deck(owner: int):
            return [create_forest(owner), ScytheTiger(owner)]

        DECKS = {
            'student': student_deck,
            'tiger': tiger_deck,
            'scf': scf_deck,
            'noble': noble_deck,
            'hero': hero_deck,
            'sniper': sniper_deck,
            'mutavault': mutavault_deck,
            'urami': urami_deck,
            'aspirant': aspirant_deck,
        }
        ```

        Also available as Streamlit web GUI: `streamlit run app.py`
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Solve Command

        ```python
        @app.command()
        def solve(deck1, deck2, first, timeout, p1_life, p2_life):
            p1_hand = DECKS[deck1](0)
            p2_hand = DECKS[deck2](1)
            result, desc = solver.solve(p1_hand, p2_hand, first, p1_life, p2_life)
            print(desc)
        ```

        Returns: "P1 Wins", "P2 Wins", or "Draw/Tie"
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Show Command

        Traces optimal play for both players:

        ```
        Turn 1 (P1):
          Play Plains
          Cast Student of Warfare
        Turn 2 (P2):
          Play Plains
          Cast Student of Warfare
        ...
        ```

        Uses `find_optimal_line()` from solver.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Metagame Command

        1. Solve all deck pairs (n² matchups)
        2. Build payoff matrix
        3. Compute Nash equilibrium
        4. Display results table

        ```
             tiger student sniper
        tiger    D      L      W
        student  W      D      W
        sniper   L      L      D

        Nash: student 60%, tiger 40%
        Game value: 0.2 (P1 advantage)
        ```
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Goldfish Command

        Tests how fast a deck can win with no opponent:

        ```bash
        python cli.py goldfish student --show
        # Output: Wins on turn 6
        ```

        Useful for comparing clock speeds.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Timeout Handling

        Uses `multiprocessing` to enforce timeouts:

        ```python
        def solve_with_timeout(deck1, deck2, timeout):
            with Pool(1) as pool:
                result = pool.apply_async(solve, args)
                try:
                    return result.get(timeout=timeout)
                except TimeoutError:
                    return None, "Timeout"
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

        The CLI provides user-friendly access to the solver:

        | Feature | Implementation |
        |---------|---------------|
        | Deck loading | Factory functions in DECKS dict |
        | Solving | `simulator.solve()` |
        | Optimal play | `find_optimal_line()` |
        | Metagame | Round-robin + Nash equilibrium |
        | Timeout | Multiprocessing with timeout |
        """
    )
    return


if __name__ == "__main__":
    app.run()
