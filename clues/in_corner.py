from __future__ import annotations
from clues.base import Clue, is_wall, _SEQUENTIAL_DIR_PAIRS
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.state import GameState


def in_corner(person: str) -> Clue:
    """Person is at a room corner: 2 sequential (90°-adjacent) orthogonal
    neighbors are out-of-bounds or belong to a different room."""
    def clue(state: "GameState") -> bool:
        r, c = state.position(person)
        room = state.room_of(person)
        grid = state.grid
        for (dr1, dc1), (dr2, dc2) in _SEQUENTIAL_DIR_PAIRS:
            if is_wall(dr1 + r, dc1 + c, grid, room) and is_wall(dr2 + r, dc2 + c, grid, room):
                return True
        return False
    clue.__name__ = f"in_corner({person!r})"
    return clue
