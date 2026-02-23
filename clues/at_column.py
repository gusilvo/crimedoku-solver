from __future__ import annotations
from clues.base import Clue
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.state import GameState


def at_column(person: str, col: int) -> Clue:
    """Person must be placed in column *col*."""
    def clue(state: "GameState") -> bool:
        return state.position(person)[1] == col
    clue.__name__ = f"at_column({person!r}, {col})"
    return clue
