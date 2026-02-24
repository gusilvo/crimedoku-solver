from __future__ import annotations
from clues.base import Clue
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.state import GameState


def only_with_person(person: str, target: str) -> Clue:
    """Person is in the same room as *target* (or not, if invert=True)."""
    def clue(state: "GameState") -> bool:
        return set(state.people_in_room(state.room_of(person))) == {person, target}
    clue.__name__ = f"with_person({person!r}, {target!r})"
    return clue
