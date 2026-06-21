"""Board helpers: in-bounds checks, barrier queries, and free-cell listing.

Contains the pure helper methods factored out of :class:`~board.Board` to
keep each module under ~150 LOC.

Traces: FR-B1, FR-B2, FR-BR3, FR-M3, T-P1-03, T-P1-04.
"""

from __future__ import annotations

from cop_thief.constants import StartMode


def in_bounds(rows: int, cols: int, pos: tuple[int, int]) -> bool:
    """Return True iff *pos* is within the ``rows × cols`` grid.

    Args:
        rows: Grid row count.
        cols: Grid column count.
        pos: ``(row, col)`` to test.

    Returns:
        ``True`` when ``0 <= row < rows`` and ``0 <= col < cols``.

    """
    r, c = pos
    return 0 <= r < rows and 0 <= c < cols


def all_free_cells(
    rows: int,
    cols: int,
    barriers: frozenset[tuple[int, int]],
) -> list[tuple[int, int]]:
    """Return all in-bounds, non-barrier cells as a sorted list.

    Args:
        rows: Grid row count.
        cols: Grid column count.
        barriers: Set of blocked cells.

    Returns:
        Sorted list of ``(row, col)`` tuples that are in-bounds and free.

    """
    return [
        (r, c)
        for r in range(rows)
        for c in range(cols)
        if (r, c) not in barriers
    ]


def choose_start_positions(
    rows: int,
    cols: int,
    barriers: frozenset[tuple[int, int]],
    start_mode: StartMode,
    rng: object,  # random.Random
) -> tuple[tuple[int, int], tuple[int, int]]:
    """Return ``(cop_pos, thief_pos)`` for the start of a sub-game.

    Args:
        rows: Grid row count.
        cols: Grid column count.
        barriers: Current barrier set (should be empty at sub-game start).
        start_mode: ``RANDOM`` for random placement; ``STRATEGY`` for corners.
        rng: Seeded :class:`random.Random` instance.

    Returns:
        A pair ``(cop_pos, thief_pos)`` of distinct, free, in-bounds cells.

    Raises:
        RuntimeError: If there are fewer than 2 free cells available.

    """
    free = all_free_cells(rows, cols, barriers)
    if len(free) < 2:  # noqa: PLR2004
        msg = "Board has fewer than 2 free cells; cannot place agents."
        raise RuntimeError(msg)

    if start_mode is StartMode.RANDOM:
        chosen = rng.sample(free, 2)
        return chosen[0], chosen[1]

    # STRATEGY: cop at top-left, thief at bottom-right
    cop = (0, 0)
    thief = (rows - 1, cols - 1)
    if cop in free and thief in free and cop != thief:
        return cop, thief
    # Fallback: random
    chosen = rng.sample(free, 2)
    return chosen[0], chosen[1]
