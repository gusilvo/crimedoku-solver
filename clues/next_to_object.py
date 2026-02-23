from __future__ import annotations
from clues.base import Clue
from models.cell import ObjectType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.state import GameState


def next_to_object(person: str, obj: ObjectType, invert: bool = False) -> Clue:
    """At least one same-room orthogonal neighbor of person's cell
    contains (or none if invert=True) *obj*."""
    def clue(state: "GameState") -> bool:
        r, c = state.position(person)
        result = any(
            n.has_object(obj) and n.room_id == state.room_of(person)
            for n in state.grid.neighbors(r, c)
        )
        return (not result) if invert else result
    tag = "not_next_to_object" if invert else "next_to_object"
    clue.__name__ = f"{tag}({person!r}, {obj.name})"
    return clue
