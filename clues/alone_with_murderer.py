from __future__ import annotations
from clues.base import Clue
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.state import GameState


def alone_with_murderer(victim: str) -> Clue:
    """Victim's room contains exactly 2 people (victim + murderer)."""
    def clue(state: "GameState") -> bool:
        room = state.room_of(victim)
        return len(state.people_in_room(room)) == 2
    clue.__name__ = f"alone_with_murderer({victim!r})"
    return clue
