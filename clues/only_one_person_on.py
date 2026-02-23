from __future__ import annotations
from clues.base import Clue
from models.cell import ObjectType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.state import GameState


def only_one_person_on(obj: ObjectType) -> Clue:
    """At most one person total is standing on any cell that has *obj*."""
    def clue(state: "GameState") -> bool:
        return len(state.people_on_object(obj)) <= 1
    clue.__name__ = f"only_one_person_on({obj.name})"
    return clue
