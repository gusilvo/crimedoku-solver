"""Shared base types and helpers for the clues package."""
from __future__ import annotations
from typing import Callable, TYPE_CHECKING
from models.grid import Grid

if TYPE_CHECKING:
    from models.state import GameState

# A Clue is a predicate evaluated against a candidate placement.
Clue = Callable[["GameState"], bool]

# Sequential (adjacent, 90°) direction pairs used by in_corner
_SEQUENTIAL_DIR_PAIRS = [
    ((-1, 0), (0, 1)),   # up + right
    ((0, 1),  (1, 0)),   # right + down
    ((1, 0),  (0, -1)),  # down + left
    ((0, -1), (-1, 0)),  # left + up
]


def is_wall(r: int, c: int, grid: Grid, room: str) -> bool:
    """True if (r, c) is out-of-bounds or belongs to a different room."""
    if r < 0 or r >= grid.n_rows or c < 0 or c >= grid.n_cols:
        return True
    return grid.get_cell(r, c).room_id != room
