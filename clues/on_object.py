from __future__ import annotations
from clues.base import Clue
from models.cell import ObjectType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.state import GameState


def on_object(person: str, obj: ObjectType, invert: bool = False) -> Clue:
    """Person's cell must contain (or not contain if invert=True) *obj*."""
    def clue(state: "GameState") -> bool:
        result = state.cell_of(person).has_object(obj)
        return (not result) if invert else result
    tag = "not_on_object" if invert else "on_object"
    clue.__name__ = f"{tag}({person!r}, {obj.name})"
    return clue
