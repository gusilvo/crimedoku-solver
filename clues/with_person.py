from __future__ import annotations
from clues.base import Clue
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.state import GameState


def with_person(person: str, target: str, invert: bool = False) -> Clue:
    """Person is in the same room as *target* (or not, if invert=True)."""
    def clue(state: "GameState") -> bool:
        result = state.room_of(person) == state.room_of(target)
        return (not result) if invert else result
    tag = "not_with_person" if invert else "with_person"
    clue.__name__ = f"{tag}({person!r}, {target!r})"
    return clue
