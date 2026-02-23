"""
Converts a raw puzzle dict (from JSON) into a Puzzle domain object.

Clue parsing is fully driven by CLUE_REGISTRY — no if/elif chain.
"""
from __future__ import annotations
from typing import Any, Dict, List
from models.cell import Cell, ObjectType
from models.grid import Grid
from models.puzzle import Puzzle
from clues.registry import CLUE_REGISTRY

# Maps lowercase object name → ObjectType member
_OBJECT_MAP: Dict[str, ObjectType] = {o.value: o for o in ObjectType}

# Void objects used to fill undefined grid positions
_VOID_OBJECTS = frozenset({ObjectType.VOID})


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
    builder = CLUE_REGISTRY.get(clue_type)
    if builder is None:
        raise ValueError(
            f"Unknown clue type: {clue_type!r}. Valid: {sorted(CLUE_REGISTRY)}"
        )
    return builder(spec)


def _build_grid(grid_spec: Dict[str, Any]) -> Grid:
    n_rows: int = grid_spec["rows"]
    n_cols: int = grid_spec["cols"]

    cell_matrix: List[List[Cell | None]] = [[None] * n_cols for _ in range(n_rows)]

    for cell_spec in grid_spec["cells"]:
        r = cell_spec["row"]
        c = cell_spec["col"]
        room = cell_spec["room"]
        objects = _parse_objects(cell_spec.get("objects", []))
        cell_matrix[r][c] = Cell(row=r, col=c, room_id=room, objects=objects)

    # Fill undefined positions with void cells
    for r in range(n_rows):
        for c in range(n_cols):
            if cell_matrix[r][c] is None:
                cell_matrix[r][c] = Cell(row=r, col=c, room_id="__void__", objects=_VOID_OBJECTS)

    return Grid(cell_matrix)


def parse_puzzle(data: Dict[str, Any]) -> Puzzle:
    """Convert a raw JSON dict into a ready-to-solve Puzzle."""
    grid = _build_grid(data["grid"])
    people: List[str] = data["people"]
    victim: str = data["victim"]
    clues = [_parse_clue(spec) for spec in data["clues"]]
    return Puzzle(grid=grid, people=people, victim=victim, clues=clues)
