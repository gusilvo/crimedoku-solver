"""
Clue factories for Murdoku puzzles.

Each factory returns a *Clue* — a callable ``(GameState) -> bool`` that
returns True when the constraint is satisfied.
"""
from __future__ import annotations
from typing import Callable, TYPE_CHECKING
from cell import ObjectType
from state import Grid

if TYPE_CHECKING:
    from state import GameState

# Type alias
Clue = Callable[["GameState"], bool]

# Sequential (adjacent, 90°) direction pairs used by in_corner
_SEQUENTIAL_DIR_PAIRS = [
    ((-1, 0), (0, 1)),   # up + right
    ((0, 1),  (1, 0)),   # right + down
    ((1, 0),  (0, -1)),  # down + left
    ((0, -1), (-1, 0)),  # left + up
]


def is_wall(r: int, c: int, grid: Grid, room: str) -> bool:
    if r < 0 or r >= grid.n_rows or c < 0 or c >= grid.n_cols:
        return True
    return grid.get_cell(r, c).room_id != room

def in_room(person: str, room_id: str) -> Clue:
    """Person must be located in *room_id*."""
    def clue(state: "GameState") -> bool:
        return state.room_of(person) == room_id
    clue.__name__ = f"in_room({person!r}, {room_id!r})"
    return clue


def on_object(person: str, obj: ObjectType, invert: bool = False) -> Clue:
    """Person's cell must contain (or not contain if invert=True) *obj*."""
    def clue(state: "GameState") -> bool:
        result = state.cell_of(person).has_object(obj)
        return (not result) if invert else result
    tag = "not_on_object" if invert else "on_object"
    clue.__name__ = f"{tag}({person!r}, {obj.name})"
    return clue


def only_on_object(person: str, obj: ObjectType) -> Clue:
    """Person is the *only* one standing on any cell that has *obj*."""
    def clue(state: "GameState") -> bool:
        return state.people_on_object(obj) == [person]
    clue.__name__ = f"only_on_object({person!r}, {obj.name})"
    return clue


def next_to_object(person: str, obj: ObjectType, invert: bool = False) -> Clue:
    """At least one orthogonal neighbor of person's cell contains (or none if invert=True) *obj*."""
    def clue(state: "GameState") -> bool:
        r, c = state.position(person)
        result = any(n.has_object(obj) and n.room_id == state.room_of(person) for n in state.grid.neighbors(r, c))
        return (not result) if invert else result
    tag = "not_next_to_object" if invert else "next_to_object"
    clue.__name__ = f"{tag}({person!r}, {obj.name})"
    return clue


def in_corner(person: str) -> Clue:
    """Person is at a room corner: 2 sequential (90°-adjacent) orthogonal
    neighbors are out-of-bounds or belong to a different room."""
    def clue(state: "GameState") -> bool:
        r, c = state.position(person)
        room = state.room_of(person)
        grid = state.grid
        for (dr1, dc1), (dr2, dc2) in _SEQUENTIAL_DIR_PAIRS:
            if is_wall(dr1+r, dc1+c, grid, room) and is_wall(dr2+r, dc2+c, grid, room):
                return True
        return False
    clue.__name__ = f"in_corner({person!r})"
    return clue


def not_next_to_wall(person: str) -> Clue:
    """Person must NOT be on any edge row or column of the grid."""
    def clue(state: "GameState") -> bool:
        r, c = state.position(person)
        grid = state.grid
        room = state.room_of(person)
        neighbors_cal = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for neighbor_cal in neighbors_cal:
            if (is_wall(r+neighbor_cal[0], c+neighbor_cal[1], grid, room)):
                return False
        return True
    clue.__name__ = f"not_next_to_wall({person!r})"
    return clue


def below_person(person: str, target: str) -> Clue:
    """Person's row is strictly greater than target's row (person is below)."""
    def clue(state: "GameState") -> bool:
        return state.position(person)[0] > state.position(target)[0]
    clue.__name__ = f"below_person({person!r}, {target!r})"
    return clue


def above_person(person: str, target: str) -> Clue:
    """Person's row is strictly less than target's row (person is above)."""
    def clue(state: "GameState") -> bool:
        return state.position(person)[0] < state.position(target)[0]
    clue.__name__ = f"above_person({person!r}, {target!r})"
    return clue


def at_column(person: str, col: int) -> Clue:
    """Person must be placed in column *col*."""
    def clue(state: "GameState") -> bool:
        return state.position(person)[1] == col
    clue.__name__ = f"at_column({person!r}, {col})"
    return clue


def alone_with_murderer(victim: str) -> Clue:
    """Victim's room contains exactly 2 people (victim + murderer)."""
    def clue(state: "GameState") -> bool:
        room = state.room_of(victim)
        return len(state.people_in_room(room)) == 2
    clue.__name__ = f"alone_with_murderer({victim!r})"
    return clue
