from __future__ import annotations
from typing import List
from cell import Cell, ObjectType


class Grid:
    """NxN grid of Cell objects."""

    def __init__(self, cells: List[List[Cell]]):
        """``cells[row][col]``."""
        self._cells = cells
        self.n_rows = len(cells)
        self.n_cols = len(cells[0]) if cells else 0

    def get_cell(self, row: int, col: int) -> Cell:
        return self._cells[row][col]

    def all_cells(self) -> List[Cell]:
        return [self._cells[r][c]
                for r in range(self.n_rows)
                for c in range(self.n_cols)]

    def valid_cells(self) -> List[Cell]:
        """Cells where a person may stand (not blocked)."""
        return [c for c in self.all_cells() if not c.is_blocked]

    def cells_with_object(self, obj: ObjectType) -> List[Cell]:
        return [c for c in self.all_cells() if c.has_object(obj)]

    def cells_in_room(self, room_id: str) -> List[Cell]:
        return [c for c in self.all_cells() if c.room_id == room_id]

    def neighbors(self, row: int, col: int) -> List[Cell]:
        """Orthogonal (4-directional) neighbors."""
        result = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = row + dr, col + dc
            if 0 <= nr < self.n_rows and 0 <= nc < self.n_cols:
                result.append(self._cells[nr][nc])
        return result
