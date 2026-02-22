"""
Loads a Murdoku puzzle from a JSON file and returns a Puzzle object.

JSON format:
{
  "grid": {
    "rows": 6,
    "cols": 6,
    "cells": [
      {"row": 0, "col": 0, "room": "living_room"},
      {"row": 0, "col": 1, "room": "living_room", "objects": ["window"]},
      ...
    ]
  },
  "people": ["Axel", "Bella", "Cora", "Douglas", "Ella", "Vincent"],
  "victim": "Vincent",
  "clues": [
    {"type": "on_object",           "person": "Axel",    "object": "window"},
    {"type": "on_object",           "person": "Axel",    "object": "window", "invert": true},
    {"type": "in_room",             "person": "Bella",   "room":   "hall"},
    {"type": "next_to_object",      "person": "Ella",    "object": "plant"},
    {"type": "only_on_object",      "person": "Cora",    "object": "carpet"},
    {"type": "in_corner",           "person": "Antonio"},
    {"type": "not_next_to_wall",    "person": "Dahlia"},
    {"type": "below_person",        "person": "Don",     "target": "Aria"},
    {"type": "above_person",        "person": "Dwayne",  "target": "Chloe"},
    {"type": "at_column",           "person": "Chloe",   "column": 1},
    {"type": "alone_with_murderer", "person": "Vincent"}
  ]
}

Notes:
- Every cell in the grid must be listed explicitly (row + col + room).
- "objects" is optional; omit it or leave it empty for empty cells.
- Object names must match ObjectType enum values (case-insensitive):
    window, bed, carpet, plant, table, chair, tv, bookshelf, cash_register
- Blocked objects (plant, table, tv, bookshelf) prevent a person from standing on that cell.
- "invert": true on on_object / next_to_object negates the constraint.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from cell import Cell, ObjectType
from grid import Grid
from clues import (
    in_room, on_object, only_on_object, next_to_object, alone_with_murderer,
    in_corner, not_next_to_wall, below_person, above_person, at_column,
)
from puzzle import Puzzle

# Map lowercase object name → ObjectType
_OBJECT_MAP: Dict[str, ObjectType] = {o.value: o for o in ObjectType}


def _parse_objects(names: List[str]) -> frozenset:
    result = set()
    for name in names:
        key = name.lower()
        if key not in _OBJECT_MAP:
            raise ValueError(f"Unknown object type: {name!r}. Valid: {list(_OBJECT_MAP)}")
        result.add(_OBJECT_MAP[key])
    return frozenset(result)


def _parse_clue(spec: Dict[str, Any]):
    clue_type = spec.get("type")
    person = spec["person"]
    invert = spec.get("invert", False)

    if clue_type == "in_room":
        return in_room(person, spec["room"])
    elif clue_type in ("on_object", "only_on_object", "next_to_object"):
        obj = _OBJECT_MAP[spec["object"].lower()]
        if clue_type == "on_object":
            return on_object(person, obj, invert=invert)
        elif clue_type == "only_on_object":
            return only_on_object(person, obj)
        else:
            return next_to_object(person, obj, invert=invert)
    elif clue_type == "alone_with_murderer":
        return alone_with_murderer(person)
    elif clue_type == "in_corner":
        return in_corner(person)
    elif clue_type == "not_next_to_wall":
        return not_next_to_wall(person)
    elif clue_type == "below_person":
        return below_person(person, spec["target"])
    elif clue_type == "above_person":
        return above_person(person, spec["target"])
    elif clue_type == "at_column":
        return at_column(person, spec["column"])
    else:
        valid = [
            "in_room", "on_object", "only_on_object", "next_to_object",
            "alone_with_murderer", "in_corner", "not_next_to_wall",
            "below_person", "above_person", "at_column",
        ]
        raise ValueError(f"Unknown clue type: {clue_type!r}. Valid: {valid}")


def load_puzzle(path: str | Path) -> Puzzle:
    """Read a JSON puzzle file and return a ready-to-solve Puzzle."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))

    grid_spec = data["grid"]
    n_rows: int = grid_spec["rows"]
    n_cols: int = grid_spec["cols"]

    # Build an empty cell matrix first, then fill from JSON
    cell_matrix: List[List[Cell | None]] = [[None] * n_cols for _ in range(n_rows)]

    for cell_spec in grid_spec["cells"]:
        r = cell_spec["row"]
        c = cell_spec["col"]
        room = cell_spec["room"]
        objects = _parse_objects(cell_spec.get("objects", []))
        cell_matrix[r][c] = Cell(row=r, col=c, room_id=room, objects=objects)

    # Verify every cell was defined
    for r in range(n_rows):
        for c in range(n_cols):
            if cell_matrix[r][c] is None:
                raise ValueError(f"Cell ({r}, {c}) is missing from the puzzle JSON.")

    grid = Grid(cell_matrix)
    people: List[str] = data["people"]
    victim: str = data["victim"]
    clues = [_parse_clue(spec) for spec in data["clues"]]

    return Puzzle(grid=grid, people=people, victim=victim, clues=clues)
