from __future__ import annotations
from clues.base import Clue
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.state import GameState


def alone_in_room(person: str, room: str) -> Clue:
    """Person is the only one in *room*."""
    def clue(state: "GameState") -> bool:
        if state.room_of(person) != room:
            return False
        return state.people_in_room(room) == [person]
    clue.__name__ = f"alone_in_room({person!r}, {room!r})"
    return clue
