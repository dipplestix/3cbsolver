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
        # 11: Nash Equilibrium Calculation

        **File:** `simulator/nash.py`

        Computes Nash equilibrium for the metagame using R-NAD
        (Replicator Neural Annealing Dynamics).

        ## What is Nash Equilibrium?
        The optimal mixed strategy where neither player can improve
        by changing their deck choice, assuming optimal play.

        ## Zero-Sum Game
        In MTG matchups, one player's win is another's loss.
        The payoff matrix M has: M[i,j] = result of deck i vs deck j
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

    import numpy as np
    return Path, np, project_root, sys


@app.cell
def _():
    from simulator.nash import (
        compute_nash_equilibrium,
        rnad_replicator_step,
        format_nash_strategy
    )
    return compute_nash_equilibrium, format_nash_strategy, rnad_replicator_step


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## R-NAD Algorithm

        Replicator dynamics with entropy regularization:

        1. Start with uniform distribution over decks
        2. Iteratively adjust probabilities based on payoffs
        3. Entropy regularization prevents collapse to pure strategies
        4. Converges to Nash equilibrium

        ```python
        # Payoffs
        q_row = M @ y  # Expected payoff for each row strategy
        q_col = -M.T @ x  # Expected payoff for each col strategy

        # Regularized fitness
        f_row = q_row - eta * (log(x) - log(pi_ref))

        # Replicator update
        x = x * exp(dt * (f_row - x @ f_row))
        ```
        """
    )
    return


@app.cell
def _(compute_nash_equilibrium, np):
    # Example: Rock-Paper-Scissors payoff matrix
    # Rows = player 1 choice, Cols = player 2 choice
    # 1 = win, 0 = draw, -1 = loss
    rps_matrix = np.array([
        [0, -1, 1],   # Rock: ties rock, loses to paper, beats scissors
        [1, 0, -1],   # Paper: beats rock, ties paper, loses to scissors
        [-1, 1, 0]    # Scissors: loses to rock, beats paper, ties scissors
    ])

    x, y, value = compute_nash_equilibrium(rps_matrix)

    print("Rock-Paper-Scissors Nash Equilibrium:")
    print(f"  Player 1 strategy: Rock={x[0]:.3f}, Paper={x[1]:.3f}, Scissors={x[2]:.3f}")
    print(f"  Player 2 strategy: Rock={y[0]:.3f}, Paper={y[1]:.3f}, Scissors={y[2]:.3f}")
    print(f"  Game value: {value:.6f}")
    print(f"\n  (Expected: uniform 1/3 each, value 0)")
    return rps_matrix, value, x, y


@app.cell
def _(compute_nash_equilibrium, np):
    # Example: Asymmetric game
    # Deck A beats B, B beats C, C beats A
    asymmetric = np.array([
        [0, 1, -1],   # A: draws A, beats B, loses to C
        [-1, 0, 1],   # B: loses to A, draws B, beats C
        [1, -1, 0]    # C: beats A, loses to B, draws C
    ])

    x2, y2, v2 = compute_nash_equilibrium(asymmetric)

    print("Asymmetric Triangle Nash:")
    print(f"  Strategy: A={x2[0]:.3f}, B={x2[1]:.3f}, C={x2[2]:.3f}")
    print(f"  Game value: {v2:.6f}")
    return asymmetric, v2, x2, y2


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Usage in Metagame

        The CLI's `metagame` command:
        1. Solves all deck pairs to build payoff matrix
        2. Computes Nash equilibrium
        3. Shows optimal mixed strategy

        ```python
        payoff = build_payoff_matrix(deck_names, results)
        x, y, value = compute_nash_equilibrium(payoff)
        print(format_nash_strategy(x, deck_names))
        ```
        """
    )
    return


@app.cell
def _(format_nash_strategy, np):
    # Format strategy for display
    strategy = np.array([0.3, 0.5, 0.15, 0.05])
    deck_names = ["Tiger", "Student", "Sniper", "Thallid"]

    formatted = format_nash_strategy(strategy, deck_names, threshold=0.01)
    print(f"Nash Strategy: {formatted}")
    return deck_names, formatted, strategy


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Summary

        | Function | Purpose |
        |----------|---------|
        | `compute_nash_equilibrium` | Main solver |
        | `rnad_replicator_step` | Single iteration |
        | `format_nash_strategy` | Pretty printing |

        The Nash equilibrium tells you the optimal deck distribution
        for a tournament - any deviation can be exploited by opponents.
        """
    )
    return


if __name__ == "__main__":
    app.run()
