from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, List, TYPE_CHECKING
from grid import Grid

if TYPE_CHECKING:
    from state import GameState

Clue = Callable[["GameState"], bool]


@dataclass
class Puzzle:
    grid: Grid
    people: List[str]   # all people, including the victim
    victim: str         # name of the victim
    clues: List[Clue]   # all clues that must be satisfied simultaneously
