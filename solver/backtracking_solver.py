"""
Backtracking solver for Murdoku puzzles.

Improves on the brute-force approach by:
1. Domain reduction — pre-computing which cells each person may occupy
   based on single-person clues (parsed from clue.__name__).
2. Backtracking column search — for each row-order permutation, columns
   are assigned recursively using only each person's pre-filtered candidates,
   skipping entire sub-trees when the candidate set is empty.

Relational clues (involving multiple people) are still evaluated on the
full GameState at the leaf, keeping clue evaluation logic unchanged.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from itertools import permutations
from math import factorial
from typing import Dict, List, Optional, Set, Tuple

from cell import Cell, ObjectType
from grid import Grid
from puzzle import Puzzle
from state import GameState

# Re-use the same Solution / error types so callers can use either solver
# interchangeably.
from solver.brute_force_solver import Solution, NoSolutionError, MultipleSolutionsError

# Reuse is_wall helper from clues.py
from clues import is_wall, _SEQUENTIAL_DIR_PAIRS


def _is_corner(cell: Cell, grid: Grid) -> bool:
    """True if (cell.row, cell.col) is a room corner."""
    r, c, room = cell.row, cell.col, cell.room_id
    for (dr1, dc1), (dr2, dc2) in _SEQUENTIAL_DIR_PAIRS:
        if is_wall(r + dr1, c + dc1, grid, room) and is_wall(r + dr2, c + dc2, grid, room):
            return True
    return False


def _is_interior(cell: Cell, grid: Grid) -> bool:
    """True if none of the 4 orthogonal neighbors is a wall/room-boundary."""
    r, c, room = cell.row, cell.col, cell.room_id
    return not any(
        is_wall(r + dr, c + dc, grid, room)
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]
    )


def _has_neighbor_with_object(cell: Cell, obj: ObjectType, grid: Grid) -> bool:
    """True if any same-room orthogonal neighbor of *cell* contains *obj*."""
    for n in grid.neighbors(cell.row, cell.col):
        if n.room_id == cell.room_id and n.has_object(obj):
            return True
    return False


# Maps ObjectType string value → ObjectType member
_OBJ_MAP: Dict[str, ObjectType] = {o.value: o for o in ObjectType}


class BacktrackingSolver:
    """
    Constraint-propagating backtracking solver.

    Parameters
    ----------
    puzzle : Puzzle
    verbose : bool
        When True, displays a tqdm progress bar over row-order permutations.
    """

    def __init__(self, puzzle: Puzzle, verbose: bool = False) -> None:
        self.puzzle = puzzle
        self.verbose = verbose

        # --- Row / column ordering constraints (same as brute-force) --------
        self._above: List[Tuple[str, str]] = []
        self._below: List[Tuple[str, str]] = []
        self._col_fixed: Dict[str, int] = {}

        # --- Domain reduction ------------------------------------------------
        # Start every person with all non-blocked cells, then narrow down.
        all_valid: List[Cell] = puzzle.grid.valid_cells()
        candidates: Dict[str, List[Cell]] = {p: list(all_valid) for p in puzzle.people}

        for clue in puzzle.clues:
            name = getattr(clue, "__name__", "")

            # above / below / at_column (row-ordering; handled separately)
            m = re.match(r"above_person\('(.+?)', '(.+?)'\)", name)
            if m:
                self._above.append((m.group(1), m.group(2)))
                continue
            m = re.match(r"below_person\('(.+?)', '(.+?)'\)", name)
            if m:
                self._below.append((m.group(1), m.group(2)))
                continue
            m = re.match(r"at_column\('(.+?)', (\d+)\)", name)
            if m:
                person, col = m.group(1), int(m.group(2))
                self._col_fixed[person] = col
                candidates[person] = [c for c in candidates[person] if c.col == col]
                continue

            # in_room
            m = re.match(r"in_room\('(.+?)', '(.+?)'\)", name)
            if m:
                person, room = m.group(1), m.group(2)
                candidates[person] = [c for c in candidates[person] if c.room_id == room]
                continue

            # on_object / not_on_object
            m = re.match(r"(not_on_object|on_object)\('(.+?)', (\w+)\)", name)
            if m:
                tag, person, obj_name = m.group(1), m.group(2), m.group(3).lower()
                obj = _OBJ_MAP.get(obj_name)
                if obj is not None:
                    if tag == "on_object":
                        candidates[person] = [c for c in candidates[person] if c.has_object(obj)]
                    else:
                        candidates[person] = [c for c in candidates[person] if not c.has_object(obj)]
                continue

            # only_on_object  →  person must be on a cell that has the object
            m = re.match(r"only_on_object\('(.+?)', (\w+)\)", name)
            if m:
                person, obj_name = m.group(1), m.group(2).lower()
                obj = _OBJ_MAP.get(obj_name)
                if obj is not None:
                    candidates[person] = [c for c in candidates[person] if c.has_object(obj)]
                continue

            # next_to_object / not_next_to_object
            m = re.match(r"(not_next_to_object|next_to_object)\('(.+?)', (\w+)\)", name)
            if m:
                tag, person, obj_name = m.group(1), m.group(2), m.group(3).lower()
                obj = _OBJ_MAP.get(obj_name)
                if obj is not None:
                    if tag == "next_to_object":
                        candidates[person] = [
                            c for c in candidates[person]
                            if _has_neighbor_with_object(c, obj, puzzle.grid)
                        ]
                    else:
                        candidates[person] = [
                            c for c in candidates[person]
                            if not _has_neighbor_with_object(c, obj, puzzle.grid)
                        ]
                continue

            # in_corner
            m = re.match(r"in_corner\('(.+?)'\)", name)
            if m:
                person = m.group(1)
                candidates[person] = [
                    c for c in candidates[person]
                    if _is_corner(c, puzzle.grid)
                ]
                continue

            # not_next_to_wall
            m = re.match(r"not_next_to_wall\('(.+?)'\)", name)
            if m:
                person = m.group(1)
                candidates[person] = [
                    c for c in candidates[person]
                    if _is_interior(c, puzzle.grid)
                ]
                continue

            # alone_in_room  →  person must be in that room (partial filter)
            m = re.match(r"alone_in_room\('(.+?)', '(.+?)'\)", name)
            if m:
                person, room = m.group(1), m.group(2)
                candidates[person] = [c for c in candidates[person] if c.room_id == room]
                continue

        # Build: _candidate_cols[person][row] = frozenset of valid columns
        n_rows = puzzle.grid.n_rows
        self._candidate_cols: Dict[str, Dict[int, frozenset]] = {}
        for person, cells in candidates.items():
            by_row: Dict[int, set] = {r: set() for r in range(n_rows)}
            for cell in cells:
                by_row[cell.row].add(cell.col)
            self._candidate_cols[person] = {r: frozenset(cols) for r, cols in by_row.items()}

    # ------------------------------------------------------------------
    def solve(self) -> Solution:
        """Return the unique Solution, or raise NoSolutionError / MultipleSolutionsError."""
        puzzle = self.puzzle
        people = puzzle.people
        n = len(people)
        found: List[Solution] = []

        row_iter = permutations(people)
        if self.verbose:
            from tqdm import tqdm
            row_iter = tqdm(row_iter, total=factorial(n),
                            desc="Backtracking", unit="row-perm")

        col_perm = [0] * n

        def backtrack(row_idx: int, used_cols: frozenset) -> None:
            if row_idx == n:
                state = GameState(list(row_order), list(col_perm), puzzle.grid)
                if not all(clue(state) for clue in puzzle.clues):
                    return
                victim_room = state.room_of(puzzle.victim)
                room_members = state.people_in_room(victim_room)
                if len(room_members) != 2:
                    return
                murderer = next(p for p in room_members if p != puzzle.victim)
                positions = {p: state.position(p) for p in people}
                found.append(Solution(positions=positions, murderer=murderer))
                return

            person = row_order[row_idx]
            allowed = self._candidate_cols[person].get(row_idx, frozenset()) - used_cols
            for col in allowed:
                col_perm[row_idx] = col
                backtrack(row_idx + 1, used_cols | {col})

        for row_order in row_iter:
            ro_idx = {p: i for i, p in enumerate(row_order)}

            if any(ro_idx[p] >= ro_idx[t] for p, t in self._above):
                continue
            if any(ro_idx[p] <= ro_idx[t] for p, t in self._below):
                continue

            backtrack(0, frozenset())

        if not found:
            raise NoSolutionError("No valid configuration satisfies all clues.")
        if len(found) > 1:
            raise MultipleSolutionsError([
                {"murderer": s.murderer, "positions": s.positions}
                for s in found
            ])
        return found[0]
