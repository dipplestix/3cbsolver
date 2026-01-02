"""Nash equilibrium calculation using R-NAD (Replicator Neural Annealing Dynamics)."""
import numpy as np
from typing import Tuple, List


def rnad_replicator_step(x: np.ndarray, y: np.ndarray, M: np.ndarray,
                         pi_reg_row: np.ndarray, pi_reg_col: np.ndarray,
                         eta: float = 0.2, dt: float = 0.02, eps: float = 1e-12
                         ) -> Tuple[np.ndarray, np.ndarray]:
    """
    Single step of R-NAD replicator dynamics with entropy regularization.

    Args:
        x: Row player strategy (probability distribution)
        y: Column player strategy (probability distribution)
        M: Payoff matrix (row player maximizes, column player minimizes)
        pi_reg_row: Reference distribution for row player regularization
        pi_reg_col: Reference distribution for column player regularization
        eta: Entropy regularization strength
        dt: Time step for integration
        eps: Small constant for numerical stability

    Returns:
        Updated (x, y) strategy pair
    """
    # Normalize inputs
    x = np.clip(x, eps, None)
    x = x / x.sum()
    y = np.clip(y, eps, None)
    y = y / y.sum()
    pi_reg_row = np.clip(pi_reg_row, eps, None)
    pi_reg_row = pi_reg_row / pi_reg_row.sum()
    pi_reg_col = np.clip(pi_reg_col, eps, None)
    pi_reg_col = pi_reg_col / pi_reg_col.sum()

    # Payoffs (row maximizes, column minimizes)
    q_row = M @ y
    q_col = -M.T @ x

    # Regularized fitness with entropy regularization
    f_row = q_row - eta * (np.log(x + eps) - np.log(pi_reg_row + eps))
    f_col = q_col - eta * (np.log(y + eps) - np.log(pi_reg_col + eps))

    # Replicator dynamics equation
    u_row = f_row - x @ f_row
    u_col = f_col - y @ f_col

    # Multiplicative Euler integration step
    x = x * np.exp(dt * u_row)
    x = x / x.sum()
    y = y * np.exp(dt * u_col)
    y = y / y.sum()

    return x, y


def compute_nash_equilibrium(payoff_matrix: np.ndarray,
                             max_iters: int = 10000,
                             eta: float = 0.2,
                             dt: float = 0.1,
                             tol: float = 1e-8
                             ) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    Compute Nash equilibrium of a zero-sum game using R-NAD.

    Args:
        payoff_matrix: Zero-sum payoff matrix (row player's payoffs)
        max_iters: Maximum number of iterations
        eta: Entropy regularization parameter
        dt: Time step size
        tol: Convergence tolerance

    Returns:
        (row_strategy, col_strategy, game_value)
    """
    n = payoff_matrix.shape[0]
    m = payoff_matrix.shape[1]

    # Initialize uniform distributions
    x = np.ones(n) / n
    y = np.ones(m) / m

    # Reference distributions (uniform)
    pi_reg_row = np.ones(n) / n
    pi_reg_col = np.ones(m) / m

    # R-NAD iteration
    for i in range(max_iters):
        x_old, y_old = x.copy(), y.copy()
        x, y = rnad_replicator_step(x, y, payoff_matrix, pi_reg_row, pi_reg_col,
                                     eta=eta, dt=dt)

        # Check convergence
        if np.max(np.abs(x - x_old)) < tol and np.max(np.abs(y - y_old)) < tol:
            break

    # Calculate game value
    game_value = x @ payoff_matrix @ y

    return x, y, game_value


def format_nash_strategy(strategy: np.ndarray, deck_names: List[str],
                         threshold: float = 0.01) -> str:
    """Format Nash strategy as human-readable string."""
    parts = []
    for i, prob in enumerate(strategy):
        if prob >= threshold:
            parts.append(f"{deck_names[i]}: {prob*100:.1f}%")
    return ", ".join(parts)
