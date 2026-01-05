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
        # 05: Tables Module (Transposition & Dominance)

        **File:** `simulator/tables.py`

        Two optimization techniques that dramatically improve solver performance:

        ## 1. Transposition Table
        Memoizes game states to avoid recomputing positions already seen.
        Key insight: Same position can be reached through different move orders.

        ## 2. Dominance Table
        Prunes positions dominated by known results.
        Key insight: If a "better" position lost, "worse" positions also lose.

        Both use the signature system from GameState.
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
    from simulator.tables import (
        lookup_transposition,
        store_transposition,
        check_dominance,
        store_dominance
    )
    return (
        check_dominance,
        lookup_transposition,
        store_dominance,
        store_transposition,
    )


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Transposition Table

        Caches game positions with three bound types:

        | Flag | Meaning | When Used |
        |------|---------|-----------|
        | `exact` | True value | Search completed normally |
        | `lower` | Value >= actual | Alpha cutoff (failed high) |
        | `upper` | Value <= actual | Beta cutoff (failed low) |

        ### Lookup Rules
        - `exact`: Always usable
        - `lower`: Usable if `value >= beta` (proves cutoff)
        - `upper`: Usable if `value <= alpha` (proves cutoff)
        """
    )
    return


@app.cell
def _(lookup_transposition, store_transposition):
    # Simulate transposition table usage
    memo = {}

    # Store an exact result
    key1 = ("sig1", "main1", 0)
    store_transposition(memo, key1, value=1, original_alpha=-2, beta=2)

    print("Transposition table after storing exact result:")
    print(f"  {key1}: {memo[key1]}")
    return key1, memo


@app.cell
def _(key1, lookup_transposition, memo):
    # Lookup the stored value
    result = lookup_transposition(memo, key1, alpha=-2, beta=2)
    print(f"Lookup result (exact): {result}")

    # Lookup a non-existent key
    missing = lookup_transposition(memo, ("missing", "main1", 0), alpha=-2, beta=2)
    print(f"Lookup non-existent: {missing}")
    return missing, result


@app.cell
def _(lookup_transposition, store_transposition):
    # Demonstrate bound flags
    memo2 = {}

    # Store a lower bound (failed high, value >= beta)
    key_lower = ("sig_lower", "main1", 0)
    store_transposition(memo2, key_lower, value=1, original_alpha=-2, beta=0)
    print(f"Lower bound stored: {memo2[key_lower]}")

    # Can use if current beta <= cached value
    result_lower = lookup_transposition(memo2, key_lower, alpha=-2, beta=0)
    print(f"Lookup with beta=0: {result_lower}")

    # Cannot use if beta > cached value
    result_lower2 = lookup_transposition(memo2, key_lower, alpha=-2, beta=2)
    print(f"Lookup with beta=2: {result_lower2}")
    return key_lower, memo2, result_lower, result_lower2


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Dominance Table

        Exploits life total relationships. For a given board position:
        - If state A (better life) was a **loss**, state B (worse life) is also a loss
        - If state A (worse life) was a **win**, state B (better life) is also a win

        ### Key Concepts
        - **Better for player**: Higher own life, lower opponent life
        - **Worse for player**: Lower own life, higher opponent life
        - Uses `board_signature()` (excludes life totals)
        """
    )
    return


@app.cell
def _(check_dominance, store_dominance):
    # Simulate dominance table usage
    dominance = {}

    # Store a result: player 0 with 15 life, opponent with 18 life, lost
    board_key = ("board_sig", "main1", 0)
    store_dominance(dominance, board_key, life=[15, 18], player=0, result=-1)

    print("Dominance table after storing loss:")
    print(f"  {board_key}: {dominance[board_key]}")
    return board_key, dominance


@app.cell
def _(board_key, check_dominance, dominance):
    # Check dominance: same board, but WORSE life for player 0
    # If better life lost, worse life also loses
    worse_result = check_dominance(dominance, board_key, life=[10, 20], player=0)
    print(f"Worse life (10 vs 15, opp 20 vs 18): {worse_result}")
    print("  (Dominated by loss - player has less life, opponent has more)")

    # Check with BETTER life for player 0
    better_result = check_dominance(dominance, board_key, life=[20, 10], player=0)
    print(f"\nBetter life (20 vs 15, opp 10 vs 18): {better_result}")
    print("  (Not dominated - need to search)")
    return better_result, worse_result


@app.cell
def _(check_dominance, store_dominance):
    # Store a win and check dominance
    dom2 = {}
    board_key2 = ("board_sig2", "main1", 0)

    # Player 0 with 5 life, opponent with 15 life, WON
    store_dominance(dom2, board_key2, life=[5, 15], player=0, result=1)
    print("Stored: Player with 5 life, opponent 15 life = WIN")

    # Better life should also win
    better_check = check_dominance(dom2, board_key2, life=[10, 10], player=0)
    print(f"\nBetter life (10 vs 5, opp 10 vs 15): {better_check}")
    print("  (Dominates winning state - if worse life won, better life wins)")
    return better_check, board_key2, dom2


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Integration with Solver

        The solver uses both tables in the minimax function:

        ```python
        def minimax(state, player, memo, depth, alpha, beta, dominance):
            # 1. Check transposition table
            key = (state.signature(), state.phase, player)
            cached = lookup_transposition(memo, key, alpha, beta)
            if cached is not None:
                return cached

            # 2. Check dominance
            board_key = (state.board_signature(), state.phase, player)
            dominated = check_dominance(dominance, board_key, state.life, player)
            if dominated is not None:
                return dominated

            # 3. Do actual search...
            result = ...

            # 4. Store results
            store_transposition(memo, key, result, original_alpha, beta)
            store_dominance(dominance, board_key, state.life, player, result)

            return result
        ```
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Why Two Tables?

        ### Transposition Table
        - **Key**: Full signature (includes life)
        - **Purpose**: Exact position lookup
        - **Pruning**: Same position → same result

        ### Dominance Table
        - **Key**: Board signature (excludes life)
        - **Purpose**: Life-relative comparisons
        - **Pruning**: Better/worse life → implied result

        They complement each other:
        - Transposition handles identical positions
        - Dominance handles positions that differ only in life
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Summary

        | Table | Key | Stores | Prunes When |
        |-------|-----|--------|-------------|
        | Transposition | Full signature | (value, flag) | Exact match + bounds |
        | Dominance | Board only | (my_life, opp_life, result) | Life dominance |

        Together these tables can reduce search space by orders of magnitude,
        especially in games with many transpositions (same board, different paths)
        and life-symmetric positions.
        """
    )
    return


if __name__ == "__main__":
    app.run()
