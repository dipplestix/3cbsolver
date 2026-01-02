"""Transposition and dominance tables for search optimization.

The transposition table memoizes game states to avoid recomputing positions.
The dominance table prunes positions dominated by known results.
"""
from typing import Dict, List, Optional


# -----------------------------------------------------------------------------
# Transposition Table
# -----------------------------------------------------------------------------

def lookup_transposition(memo: Dict, key: tuple, alpha: int, beta: int) -> Optional[int]:
    """Check transposition table for a usable cached value.

    Args:
        memo: The transposition table
        key: (signature, phase, player) tuple
        alpha: Current alpha bound
        beta: Current beta bound

    Returns:
        Cached value if usable, None otherwise
    """
    if key not in memo:
        return None

    cached_value, flag = memo[key]

    if flag == 'exact':
        return cached_value
    elif flag == 'lower' and cached_value >= beta:
        return cached_value  # Fail high
    elif flag == 'upper' and cached_value <= alpha:
        return cached_value  # Fail low

    return None


def store_transposition(memo: Dict, key: tuple, value: int, original_alpha: int, beta: int) -> str:
    """Store result in transposition table with appropriate bound flag.

    Args:
        memo: The transposition table
        key: (signature, phase, player) tuple
        value: The computed value
        original_alpha: Alpha value at start of search
        beta: Beta bound

    Returns:
        The flag used ('exact', 'lower', or 'upper')
    """
    if value <= original_alpha:
        flag = 'upper'  # Failed low, this is an upper bound
    elif value >= beta:
        flag = 'lower'  # Failed high, this is a lower bound
    else:
        flag = 'exact'

    memo[key] = (value, flag)
    return flag


# -----------------------------------------------------------------------------
# Dominance Table
# -----------------------------------------------------------------------------

def check_dominance(dominance: Dict, board_key: tuple, life: List[int], player: int) -> Optional[int]:
    """Check if position is dominated by a known result.

    If a better state was a loss, this state is also a loss.
    If a worse state was a win, this state is also a win.

    Args:
        dominance: The dominance table
        board_key: (board_signature, phase, player) tuple
        life: [player0_life, player1_life]
        player: The player we're evaluating for

    Returns:
        1 if dominated by win, -1 if dominated by loss, None otherwise
    """
    if board_key not in dominance:
        return None

    my_life = life[player]
    opp_life = life[1 - player]

    for (cached_my_life, cached_opp_life, cached_result) in dominance[board_key]:
        # If cached state had better/equal life for player and worse/equal for opponent
        # and resulted in a loss, then this state is also a loss
        if cached_my_life >= my_life and cached_opp_life <= opp_life:
            if cached_result == -1:
                return -1  # Dominated by a losing state

        # If cached state had worse/equal life for player and better/equal for opponent
        # and resulted in a win, then this state is also a win
        if cached_my_life <= my_life and cached_opp_life >= opp_life:
            if cached_result == 1:
                return 1  # Dominates a winning state

    return None


def store_dominance(dominance: Dict, board_key: tuple, life: List[int], player: int, result: int):
    """Store result in dominance table.

    Only stores exact values (not alpha-beta bounds).

    Args:
        dominance: The dominance table
        board_key: (board_signature, phase, player) tuple
        life: [player0_life, player1_life]
        player: The player we're evaluating for
        result: The computed result (1, -1, or 0)
    """
    if board_key not in dominance:
        dominance[board_key] = []
    dominance[board_key].append((life[player], life[1 - player], result))
