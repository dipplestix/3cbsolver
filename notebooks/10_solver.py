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
        # 10: Solver (Minimax with Alpha-Beta)

        **File:** `simulator/solver.py`

        The heart of the system: finds optimal play for both players using
        minimax search with alpha-beta pruning, transposition tables, and
        dominance pruning.

        ## Result Values
        - `1` = Player wins
        - `-1` = Player loses
        - `0` = Draw

        ## Key Functions
        - `solve(p1_hand, p2_hand, ...)` - Main entry point
        - `minimax(state, player, ...)` - Recursive search
        - `find_optimal_line(state, player, ...)` - Show optimal play
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
    from simulator.solver import solve, minimax, find_optimal_line
    from simulator.game_state import GameState
    from simulator.cards.land import create_plains
    from simulator.cards.creature import Creature
    return (
        Creature,
        GameState,
        create_plains,
        find_optimal_line,
        minimax,
        solve,
    )


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Minimax Algorithm

        ```
        minimax(state, player):
            if terminal:
                return win/loss/draw

            if heuristic applies:
                return heuristic result

            if in transposition table:
                return cached value

            if dominated by known result:
                return dominated value

            # Handle automatic phases
            if automatic phase:
                return minimax(next_state)

            # Generate and evaluate actions
            for each action:
                score = minimax(action.execute(state))
                if maximizing (my turn):
                    best = max(best, score)
                else (opponent's turn):
                    best = min(best, score)

            store in tables
            return best
        ```
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Alpha-Beta Pruning

        Prunes branches that can't affect the final result:

        - **Alpha**: Best score the maximizing player can guarantee
        - **Beta**: Best score the minimizing player can guarantee

        If `alpha >= beta`, we can prune (cutoff).

        ```python
        if decision_maker == player:  # Maximizing
            best_score = -2
            for action in actions:
                score = minimax(new_state, player, memo, depth+1, alpha, beta)
                best_score = max(best_score, score)
                alpha = max(alpha, score)
                if alpha >= beta:
                    break  # Beta cutoff
        else:  # Minimizing
            best_score = 2
            for action in actions:
                score = minimax(new_state, player, memo, depth+1, alpha, beta)
                best_score = min(best_score, score)
                beta = min(beta, score)
                if alpha >= beta:
                    break  # Alpha cutoff
        ```
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Simple Example: Tiger vs Nothing

        Let's trace through a simple solve:
        """
    )
    return


@app.cell
def _(Creature, create_plains, solve):
    # Simple matchup: creature + land vs nothing
    class ScytheTiger(Creature):
        def __init__(self, owner):
            super().__init__("Scythe Tiger", owner, 3, 2, {'G': 1}, keywords=['shroud'])

    plains = create_plains(0)
    tiger = ScytheTiger(0)

    print("Solving: Plains + Tiger vs Nothing")
    result, desc = solve([plains, tiger], [], first_player=0)
    print(f"Result: {desc} (value: {result})")
    return ScytheTiger, desc, plains, result, tiger


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Automatic Phase Handling

        Some phases have no choices - just state transitions:

        ```python
        if state.phase == "combat_damage":
            new_state = resolve_combat_damage(state)
            result = minimax(new_state, player, ...)
            return result

        if state.phase == "untap":
            new_state = untap(state)
            result = minimax(new_state, player, ...)
            return result
        ```

        These phases don't branch - they just apply deterministic rules.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Decision Maker

        Who makes the choice depends on the phase:

        | Phase | Decision Maker |
        |-------|----------------|
        | main1 | Active player |
        | combat_attack | Active player |
        | combat_block | **Defender** (1 - active_player) |
        | response | **Opponent of top spell's owner** |

        ```python
        if state.phase == "combat_block":
            decision_maker = 1 - state.active_player
        elif state.phase == "response" and state.stack:
            # Responder is opponent of whoever owns the top spell
            decision_maker = 1 - state.stack[-1].owner
        else:
            decision_maker = state.active_player
        ```

        The response phase logic enables **counter-wars**: when Player A casts a
        spell and Player B counters it, Player A can counter the counter!
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Optimization Stack

        The solver uses multiple optimization techniques:

        1. **Alpha-Beta Pruning** - Skip branches that can't matter
        2. **Transposition Table** - Cache positions (same state via different paths)
        3. **Dominance Pruning** - Life-relative comparisons
        4. **Heuristics** - Early termination for determined outcomes
        5. **Attack Deduplication** - Reduce 2^n to 2^unique_types

        Without these, Student vs Student would never complete.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## find_optimal_line()

        Shows the actual moves both players would make:

        ```python
        def find_optimal_line(state, player, memo, depth):
            path = []
            while not game_over and depth < 100:
                # Handle automatic phases
                # Get actions
                # Find best action for decision maker
                # Execute and record
                path.append((action.description, state))
            return path
        ```

        This is used by the `show` command in the CLI.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Memoization Keys

        The transposition table uses:
        ```python
        key = (state.signature(), state.phase, player)
        ```

        The dominance table uses:
        ```python
        board_key = (state.board_signature(), state.phase, player)
        ```

        Note: Turn number is NOT in the key - only position matters.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Summary

        The solver implements a complete game tree search:

        | Component | Purpose |
        |-----------|---------|
        | minimax | Recursive search |
        | alpha-beta | Branch pruning |
        | transposition | Position caching |
        | dominance | Life-relative pruning |
        | heuristics | Early termination |

        ### Complexity
        - Without optimization: O(b^d) where b=branching, d=depth
        - With optimization: Much smaller in practice
        - Student vs Student: Terminates via stalemate/heuristics

        The solver guarantees **perfect play** - both players make
        optimal decisions at every turn.
        """
    )
    return


if __name__ == "__main__":
    app.run()
