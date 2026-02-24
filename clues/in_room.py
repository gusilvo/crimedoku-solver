from __future__ import annotations
from clues.base import Clue
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.state import GameState


def in_room(person: str, room_id: str, invert: bool) -> Clue:
    """Person must be located in *room_id*."""
    def clue(state: "GameState") -> bool:
        result = state.room_of(person) == room_id
        return not result if invert else result
    tag = "not_in_room" if invert else "in_room"
    clue.__name__ = f"{tag}({person!r}, {room_id!r})"
    return clue
