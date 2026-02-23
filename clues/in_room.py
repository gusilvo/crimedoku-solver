from __future__ import annotations
from clues.base import Clue
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.state import GameState


def in_room(person: str, room_id: str) -> Clue:
    """Person must be located in *room_id*."""
    def clue(state: "GameState") -> bool:
        return state.room_of(person) == room_id
    clue.__name__ = f"in_room({person!r}, {room_id!r})"
    return clue
