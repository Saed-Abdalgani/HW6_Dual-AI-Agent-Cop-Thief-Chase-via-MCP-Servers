"""Board state for a single sub-game of Cop–Thief.

Holds the grid dimensions, agent positions, and barrier cells.
Delegates pure helper logic to :mod:`._board_helpers`.

Traces: FR-B1, FR-B2, FR-B3, FR-B4, FR-BR3, FR-M3, NFR-11,
        T-P1-02, T-P1-03, T-P1-04, T-P1-05.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from cop_thief.constants import Agent, StartMode
from cop_thief.services.engine._board_helpers import (
    all_free_cells,
    choose_start_positions,
    in_bounds,
)


@dataclass
class Board:
    """Grid, positions, and barrier state for one sub-game.

    Args:
        rows: Number of rows (from ``config.grid_size[0]``).
        cols: Number of columns (from ``config.grid_size[1]``).

    """

    rows: int
    cols: int

    cop_pos: tuple[int, int] = field(default=(0, 0), init=False)
    thief_pos: tuple[int, int] = field(default=(0, 0), init=False)
    barriers: frozenset[tuple[int, int]] = field(default_factory=frozenset, init=False)
    barriers_used: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        """Validate grid dimensions."""
        if self.rows < 2 or self.cols < 2:  # noqa: PLR2004
            msg = f"Grid dimensions must be >= 2×2; got {self.rows}×{self.cols}."
            raise ValueError(msg)

    # ------------------------------------------------------------------
    # In-bounds / barrier helpers (T-P1-03, T-P1-04)
    # ------------------------------------------------------------------

    def in_bounds(self, pos: tuple[int, int]) -> bool:
        """Return True iff *pos* is within the grid.

        Args:
            pos: ``(row, col)`` to test.

        Returns:
            ``True`` when the cell is inside the grid boundaries.

        """
        return in_bounds(self.rows, self.cols, pos)

    def is_blocked(self, pos: tuple[int, int]) -> bool:
        """Return True iff *pos* is a barrier cell.

        Args:
            pos: ``(row, col)`` to test.

        Returns:
            ``True`` when *pos* is in the barrier set.

        """
        return pos in self.barriers

    def is_legal_cell(self, pos: tuple[int, int]) -> bool:
        """Return True iff *pos* is in-bounds and not blocked.

        Args:
            pos: ``(row, col)`` to test.

        Returns:
            ``True`` when the cell is both in-bounds and free.

        """
        return self.in_bounds(pos) and not self.is_blocked(pos)

    def all_free_cells(self) -> list[tuple[int, int]]:
        """Return all in-bounds, non-barrier cells.

        Returns:
            Sorted list of ``(row, col)`` tuples.

        """
        return all_free_cells(self.rows, self.cols, self.barriers)

    # ------------------------------------------------------------------
    # Barrier placement (T-P1-04)
    # ------------------------------------------------------------------

    def place_barrier(self, pos: tuple[int, int]) -> None:
        """Add *pos* to the barrier set and increment the counter.

        Args:
            pos: ``(row, col)`` of the cell to block.

        """
        self.barriers = self.barriers | frozenset([pos])
        self.barriers_used += 1

    # ------------------------------------------------------------------
    # Agent-position helpers
    # ------------------------------------------------------------------

    def get_pos(self, agent: Agent) -> tuple[int, int]:
        """Return the current position of *agent*.

        Args:
            agent: The agent whose position to retrieve.

        Returns:
            ``(row, col)`` of the agent.

        """
        return self.cop_pos if agent is Agent.COP else self.thief_pos

    def set_pos(self, agent: Agent, pos: tuple[int, int]) -> None:
        """Update the position of *agent* to *pos*.

        Args:
            agent: The agent to move.
            pos: New ``(row, col)`` position.

        """
        if agent is Agent.COP:
            self.cop_pos = pos
        else:
            self.thief_pos = pos

    # ------------------------------------------------------------------
    # Start-position generation (T-P1-05)
    # ------------------------------------------------------------------

    def reset(self, start_mode: StartMode, rng: random.Random, max_barriers: int) -> None:  # noqa: ARG002
        """Reset barriers and place agents for a new sub-game.

        Args:
            start_mode: ``RANDOM`` or ``STRATEGY`` placement.
            rng: Seeded :class:`random.Random` for determinism.
            max_barriers: Unused here; kept for caller API consistency.

        """
        self.barriers = frozenset()
        self.barriers_used = 0
        self.cop_pos, self.thief_pos = choose_start_positions(
            self.rows, self.cols, self.barriers, start_mode, rng
        )
