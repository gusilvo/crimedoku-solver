"""
Clue registry: maps clue type strings (from JSON) to builder callables.

Each builder receives the raw spec dict and returns a Clue (callable).
Adding a new clue type requires only:
  1. A new file in clues/ with the factory function.
  2. A new entry in CLUE_REGISTRY below.
"""
from __future__ import annotations
from typing import Callable, Dict
from models.cell import ObjectType
from clues.base import Clue
from clues.in_room import in_room
from clues.on_object import on_object
from clues.only_on_object import only_on_object
from clues.only_one_person_on import only_one_person_on
from clues.next_to_object import next_to_object
from clues.alone_with_murderer import alone_with_murderer
from clues.with_person import with_person
from clues.alone_in_room import alone_in_room
from clues.in_corner import in_corner
from clues.not_next_to_wall import not_next_to_wall
from clues.below_person import below_person
from clues.above_person import above_person
from clues.at_column import at_column
from clues.same_column_as_object import same_column_as_object
from clues.left_of import left_of

# Maps lowercase object name string → ObjectType member
_OBJ: Dict[str, ObjectType] = {o.value: o for o in ObjectType}


def _obj(spec: dict) -> ObjectType:
    name = spec["object"].lower()
    if name not in _OBJ:
        raise ValueError(f"Unknown object: {name!r}. Valid: {list(_OBJ)}")
    return _OBJ[name]


def _obj_target(spec: dict) -> ObjectType:
    """For clues that use 'target' as the object field (e.g. left_of)."""
    name = spec["target"].lower()
    if name not in _OBJ:
        raise ValueError(f"Unknown object: {name!r}. Valid: {list(_OBJ)}")
    return _OBJ[name]


CLUE_REGISTRY: Dict[str, Callable[[dict], Clue]] = {
    "in_room":
        lambda s: in_room(s["person"], s["room"]),

    "on_object":
        lambda s: on_object(s["person"], _obj(s), s.get("invert", False)),

    "only_on_object":
        lambda s: only_on_object(s["person"], _obj(s)),

    "only_one_person_on":
        lambda s: only_one_person_on(_obj(s)),

    "next_to_object":
        lambda s: next_to_object(s["person"], _obj(s), s.get("invert", False)),

    "alone_with_murderer":
        lambda s: alone_with_murderer(s["person"]),

    "with_person":
        lambda s: with_person(s["person"], s["target"], s.get("invert", False)),

    # Alias used in some puzzles
    "in_same_room_as_person":
        lambda s: with_person(s["person"], s["target"], s.get("invert", False)),

    "alone_in_room":
        lambda s: alone_in_room(s["person"], s["room"]),

    "in_corner":
        lambda s: in_corner(s["person"]),

    # Alias
    "at_corner":
        lambda s: in_corner(s["person"]),

    "not_next_to_wall":
        lambda s: not_next_to_wall(s["person"]),

    "below_person":
        lambda s: below_person(s["person"], s["target"]),

    "above_person":
        lambda s: above_person(s["person"], s["target"]),

    "at_column":
        lambda s: at_column(s["person"], s["column"]),

    "same_column_as_object":
        lambda s: same_column_as_object(s["person"], _obj(s), s.get("different_room", False)),

    "left_of":
        lambda s: left_of(s["person"], _obj_target(s), s.get("different_room", False)),
}
