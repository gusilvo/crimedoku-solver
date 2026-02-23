from __future__ import annotations
from clues.base import Clue
from models.cell import ObjectType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.state import GameState


def left_of(person: str, obj: ObjectType, different_room: bool) -> Clue:
    """Person's column is strictly less than an *obj* cell's column;
    different_room controls room membership."""
    def clue(state: "GameState") -> bool:
        p_col = state.position(person)[1]
        p_room = state.room_of(person)
        for cell in state.grid.cells_with_object(obj):
            if p_col < cell.col:
                in_same = cell.room_id == p_room
                if different_room and not in_same:
                    return True
                if not different_room and in_same:
                    return True
        return False
    tag = "diff_room" if different_room else "same_room"
    clue.__name__ = f"left_of({person!r}, {obj.name}, {tag})"
    return clue
