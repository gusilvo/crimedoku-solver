from __future__ import annotations
from clues.base import Clue
from models.cell import ObjectType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.state import GameState


def only_on_object(person: str, obj: ObjectType) -> Clue:
    """Person is the *only* one standing on any cell that has *obj*."""
    def clue(state: "GameState") -> bool:
        return state.people_on_object(obj) == [person]
    clue.__name__ = f"only_on_object({person!r}, {obj.name})"
    return clue
