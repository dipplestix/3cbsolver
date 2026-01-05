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
        # 16: Debug - Solver Internals

        Explore minimax search, alpha-beta pruning, and memoization.

        ## Topics
        1. Transposition table hits
        2. Alpha-beta cutoffs
        3. Dominance pruning
        4. Heuristic applications
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
    from simulator.solver import minimax, solve
    from simulator.game_state import GameState
    from simulator.cards.land import create_plains
    from simulator.cards.creature import Creature
    from simulator.tables import lookup_transposition, store_transposition
    return (
        Creature,
        GameState,
        create_plains,
        lookup_transposition,
        minimax,
        solve,
        store_transposition,
    )


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Transposition Table Demo

        Same position via different paths → same result.
        """
    )
    return


@app.cell
def _(lookup_transposition, store_transposition):
    # Simulate transposition table
    memo = {}

    # Store a result for a position
    key = (("sig1",), "main1", 0)
    store_transposition(memo, key, value=1, original_alpha=-2, beta=2)

    print("Transposition table:")
    print(f"  Stored: {key} → {memo[key]}")

    # Lookup
    result = lookup_transposition(memo, key, alpha=-2, beta=2)
    print(f"  Lookup: {result}")

    # Different key - cache miss
    other_key = (("sig2",), "main1", 0)
    miss = lookup_transposition(memo, other_key, alpha=-2, beta=2)
    print(f"  Different key: {miss}")
    return key, memo, miss, other_key, result


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Alpha-Beta Pruning

        Prunes branches that can't affect the result:

        ```
        Maximizing player:
          best = -inf
          for action:
            score = minimax(child)
            best = max(best, score)
            alpha = max(alpha, score)
            if alpha >= beta:
              break  # Opponent won't let us reach here
        ```
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Dominance Example

        If state A (better life) was a loss, state B (worse life) is also a loss.

        ```
        State A: Player 15 life, Opponent 18 life → LOSS
        State B: Player 10 life, Opponent 20 life → LOSS (dominated)
        ```

        We skip evaluating state B because A already lost with better life.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Heuristic Shortcuts

        Heuristics detect determined outcomes early:

        | Condition | Result | Depth |
        |-----------|--------|-------|
        | Symmetric creatures, no growth | Draw | > 15 |
        | Token gen vs static | Token gen wins | > 15 |
        | Stalemate 10 turns | Draw | Any |

        Without heuristics, Student vs Student would search forever.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Debugging Tips

        1. **Check memo hits**: Print when transposition table returns cached value
        2. **Track depth**: Add depth to debug output to see search depth
        3. **Action ordering**: Print which action is being evaluated
        4. **Heuristic triggers**: Log when heuristics fire

        ```python
        # Add to minimax for debugging:
        if cached is not None:
            print(f"Transposition hit at depth {depth}")
            return cached
        ```
        """
    )
    return


if __name__ == "__main__":
    app.run()
