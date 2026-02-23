"""
Backtracking solver for Murdoku puzzles.

Improves on the brute-force approach by:
1. Domain reduction — pre-computing per-person candidate cells from
   single-person clues (parsed from clue.__name__).
2. Backtracking column search — columns are assigned recursively using
   only each person's filtered candidates, pruning empty branches early.

Relational clues (involving multiple people) are evaluated on the full
GameState at the leaf, keeping clue evaluation logic unchanged.
"""
from __future__ import annotations

import re
from itertools import permutations
from math import factorial
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

from models.cell import Cell, ObjectType
from models.grid import Grid
from models.puzzle import Puzzle
from models.state import GameState
from clues.base import is_wall, _SEQUENTIAL_DIR_PAIRS
from solver.base import Solution, NoSolutionError, MultipleSolutionsError

# Maps ObjectType string value → ObjectType member
_OBJ_MAP: Dict[str, ObjectType] = {o.value: o for o in ObjectType}


# ------------------------------------------------------------------
# Cell geometry helpers
# ------------------------------------------------------------------

def _is_corner(cell: Cell, grid: Grid) -> bool:
    """True if the cell sits at a room corner (2 sequential wall-neighbors)."""
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
    return any(
        n.room_id == cell.room_id and n.has_object(obj)
        for n in grid.neighbors(cell.row, cell.col)
    )


# ------------------------------------------------------------------
# Solver
# ------------------------------------------------------------------

class BacktrackingSolver:
    def __init__(self, puzzle: Puzzle, verbose: bool = False) -> None:
        self.puzzle = puzzle
        self.verbose = verbose
        self._above, self._below, self._col_fixed = self._parse_constraints(puzzle.clues)
        candidates = self._build_candidate_cells(puzzle.clues, puzzle.grid.valid_cells())
        self._candidate_cols = self._build_candidate_cols(candidates, puzzle.grid.n_rows)

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_constraints(clues) -> Tuple[List, List, Dict]:
        """Extract row-order and column constraints from clue __name__ strings."""
        above, below, col_fixed = [], [], {}
        for clue in clues:
            name = getattr(clue, "__name__", "")
            m = re.match(r"above_person\('(.+?)', '(.+?)'\)", name)
            if m:
                above.append((m.group(1), m.group(2)))
                continue
            m = re.match(r"below_person\('(.+?)', '(.+?)'\)", name)
            if m:
                below.append((m.group(1), m.group(2)))
                continue
            m = re.match(r"at_column\('(.+?)', (\d+)\)", name)
            if m:
                col_fixed[m.group(1)] = int(m.group(2))
        return above, below, col_fixed

    def _build_candidate_cells(
        self, clues, valid_cells: List[Cell]
    ) -> Dict[str, List[Cell]]:
        """Apply single-person clue filters to produce per-person candidate cell sets."""
        candidates: Dict[str, List[Cell]] = {
            p: list(valid_cells) for p in self.puzzle.people
        }
        grid = self.puzzle.grid

        for clue in clues:
            name = getattr(clue, "__name__", "")
            self._apply_domain_filter(name, candidates, grid)

        return candidates

    def _apply_domain_filter(
        self,
        name: str,
        candidates: Dict[str, List[Cell]],
        grid: Grid,
    ) -> None:
        """Narrow candidates[person] based on a single parseable clue name."""
        patterns = [
            (r"at_column\('(.+?)', (\d+)\)",
             lambda p, m, c: [cell for cell in c if cell.col == int(m.group(2))]),

            (r"in_room\('(.+?)', '(.+?)'\)",
             lambda p, m, c: [cell for cell in c if cell.room_id == m.group(2)]),

            (r"on_object\('(.+?)', (\w+)\)",
             lambda p, m, c: [cell for cell in c
                              if cell.has_object(_OBJ_MAP.get(m.group(2).lower()))]),

            (r"not_on_object\('(.+?)', (\w+)\)",
             lambda p, m, c: [cell for cell in c
                              if not cell.has_object(_OBJ_MAP.get(m.group(2).lower()))]),

            (r"only_on_object\('(.+?)', (\w+)\)",
             lambda p, m, c: [cell for cell in c
                              if cell.has_object(_OBJ_MAP.get(m.group(2).lower()))]),

            (r"next_to_object\('(.+?)', (\w+)\)",
             lambda p, m, c: [cell for cell in c
                              if _has_neighbor_with_object(
                                  cell, _OBJ_MAP.get(m.group(2).lower()), grid)]),

            (r"not_next_to_object\('(.+?)', (\w+)\)",
             lambda p, m, c: [cell for cell in c
                              if not _has_neighbor_with_object(
                                  cell, _OBJ_MAP.get(m.group(2).lower()), grid)]),

            (r"in_corner\('(.+?)'\)",
             lambda p, m, c: [cell for cell in c if _is_corner(cell, grid)]),

            (r"not_next_to_wall\('(.+?)'\)",
             lambda p, m, c: [cell for cell in c if _is_interior(cell, grid)]),

            (r"alone_in_room\('(.+?)', '(.+?)'\)",
             lambda p, m, c: [cell for cell in c if cell.room_id == m.group(2)]),
        ]

        for pattern, filter_fn in patterns:
            m = re.match(pattern, name)
            if m:
                person = m.group(1)
                if person in candidates:
                    candidates[person] = filter_fn(person, m, candidates[person])
                return

    @staticmethod
    def _build_candidate_cols(
        candidates: Dict[str, List[Cell]], n_rows: int
    ) -> Dict[str, Dict[int, FrozenSet[int]]]:
        """Build candidates[person][row] → frozenset of valid columns."""
        result: Dict[str, Dict[int, FrozenSet[int]]] = {}
        for person, cells in candidates.items():
            by_row: Dict[int, Set[int]] = {r: set() for r in range(n_rows)}
            for cell in cells:
                by_row[cell.row].add(cell.col)
            result[person] = {r: frozenset(cols) for r, cols in by_row.items()}
        return result

    # ------------------------------------------------------------------
    # Row-order pruning
    # ------------------------------------------------------------------

    def _row_order_valid(self, ro_idx: Dict[str, int]) -> bool:
        """Return False if this row assignment violates above/below constraints."""
        if any(ro_idx[p] >= ro_idx[t] for p, t in self._above):
            return False
        if any(ro_idx[p] <= ro_idx[t] for p, t in self._below):
            return False
        return True

    # ------------------------------------------------------------------
    # Solution evaluation
    # ------------------------------------------------------------------

    def _try_solution(
        self,
        row_order: Tuple[str, ...],
        col_perm: List[int],
        found: List[Solution],
    ) -> None:
        """Evaluate a full placement; append to found if valid."""
        state = GameState(list(row_order), list(col_perm), self.puzzle.grid)
        if not all(clue(state) for clue in self.puzzle.clues):
            return
        victim_room = state.room_of(self.puzzle.victim)
        room_members = state.people_in_room(victim_room)
        if len(room_members) != 2:
            return
        murderer = next(p for p in room_members if p != self.puzzle.victim)
        positions = {p: state.position(p) for p in self.puzzle.people}
        found.append(Solution(positions=positions, murderer=murderer))

    # ------------------------------------------------------------------
    # Result finalisation
    # ------------------------------------------------------------------

    @staticmethod
    def _finalize(found: List[Solution]) -> Solution:
        if not found:
            raise NoSolutionError("No valid configuration satisfies all clues.")
        if len(found) > 1:
            raise MultipleSolutionsError([
                {"murderer": s.murderer, "positions": s.positions}
                for s in found
            ])
        return found[0]

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def solve(self) -> Solution:
        """Return the unique Solution, or raise NoSolutionError / MultipleSolutionsError."""
        puzzle = self.puzzle
        people = puzzle.people
        n = len(people)
        found: List[Solution] = []
        col_perm = [0] * n

        row_iter = permutations(people)
        if self.verbose:
            from tqdm import tqdm
            row_iter = tqdm(row_iter, total=factorial(n),
                            desc="Backtracking", unit="row-perm")

        def backtrack(row_idx: int, used_cols: FrozenSet[int]) -> None:
            if row_idx == n:
                self._try_solution(row_order, col_perm, found)
                return
            person = row_order[row_idx]
            allowed = self._candidate_cols[person].get(row_idx, frozenset()) - used_cols
            for col in allowed:
                col_perm[row_idx] = col
                backtrack(row_idx + 1, used_cols | {col})

        for row_order in row_iter:
            ro_idx = {p: i for i, p in enumerate(row_order)}
            if not self._row_order_valid(ro_idx):
                continue
            backtrack(0, frozenset())

        return self._finalize(found)
