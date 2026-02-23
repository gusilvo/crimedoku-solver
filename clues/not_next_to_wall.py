from __future__ import annotations
from clues.base import Clue, is_wall
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.state import GameState


def not_next_to_wall(person: str) -> Clue:
    """Person must NOT be adjacent to any wall or room boundary."""
    def clue(state: "GameState") -> bool:
        r, c = state.position(person)
        grid = state.grid
        room = state.room_of(person)
        return not any(
            is_wall(r + dr, c + dc, grid, room)
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]
        )
    clue.__name__ = f"not_next_to_wall({person!r})"
    return clue
