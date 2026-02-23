from __future__ import annotations
from clues.base import Clue
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.state import GameState


def above_person(person: str, target: str) -> Clue:
    """Person's row is strictly less than target's row (person is above)."""
    def clue(state: "GameState") -> bool:
        return state.position(person)[0] < state.position(target)[0]
    clue.__name__ = f"above_person({person!r}, {target!r})"
    return clue
