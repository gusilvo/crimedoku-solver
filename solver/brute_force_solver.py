from __future__ import annotations
import re
from dataclasses import dataclass
from itertools import permutations
from math import factorial
from typing import Any, Dict, List, Optional, Tuple
from state import GameState
from puzzle import Puzzle


class NoSolutionError(Exception):
    """Raised when no valid configuration satisfies all clues."""


class MultipleSolutionsError(Exception):
    """Raised when more than one valid configuration is found.

    All discovered solutions are stored in ``self.solutions`` so the puzzle
    designer can inspect which clues are ambiguous.
    """

    def __init__(self, solutions: List[Dict[str, Any]]):
        self.solutions = solutions
        lines = [
            f"\n  Solution {i + 1}: murderer={s['murderer']}, positions={s['positions']}"
            for i, s in enumerate(solutions)
        ]
        super().__init__(
            f"Puzzle has {len(solutions)} solutions (expected exactly 1):{''.join(lines)}"
        )


@dataclass
class Solution:
    positions: Dict[str, tuple]   # person -> (row, col)
    murderer: str


class Solver:
    """
    Brute-force permutation solver for Murdoku puzzles.

    Search space: (N!)^2 — all ways to assign N people to N rows *and* N columns
    while keeping rows and columns unique.

    Optimizations applied:
    - Row-level pre-pruning: above_person / below_person constraints are checked
      before the inner col_perm loop, eliminating N! inner iterations early.
    - Column prefilter: at_column constraints reduce the inner loop from N! to
      (N-k)! by fixing known columns and only permuting the rest.
    """

    def __init__(self, puzzle: Puzzle, verbose: bool = False):
        self.puzzle = puzzle
        self.verbose = verbose
        # Pre-parse clue names to extract row-order and column constraints.
        self._above: List[Tuple[str, str]] = []   # (person, must_be_above)
        self._below: List[Tuple[str, str]] = []   # (person, must_be_below)
        self._col_fixed: Dict[str, int] = {}       # person -> required column

        for clue in puzzle.clues:
            name = getattr(clue, "__name__", "")
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
                self._col_fixed[m.group(1)] = int(m.group(2))

    def _col_perms(self, row_order: Tuple[str, ...]):
        """Yield col permutations that satisfy at_column constraints."""
        n = len(row_order)
        if not self._col_fixed:
            yield from permutations(range(n))
            return

        fixed: Dict[int, int] = {}  # row_idx -> col
        for row_idx, person in enumerate(row_order):
            if person in self._col_fixed:
                col = self._col_fixed[person]
                if col in fixed.values():
                    return  # Two people need the same column — impossible
                fixed[row_idx] = col

        fixed_cols = set(fixed.values())
        free_rows = [r for r in range(n) if r not in fixed]
        free_cols = [c for c in range(n) if c not in fixed_cols]

        for perm in permutations(free_cols):
            col_p = [0] * n
            for r, c in fixed.items():
                col_p[r] = c
            for i, r in enumerate(free_rows):
                col_p[r] = perm[i]
            yield col_p

    def solve(self) -> Solution:
        """Return the unique Solution, or raise NoSolutionError / MultipleSolutionsError."""
        puzzle = self.puzzle
        people = puzzle.people
        found: List[Solution] = []

        row_iter = permutations(people)
        if self.verbose:
            from tqdm import tqdm
            row_iter = tqdm(row_iter, total=factorial(len(people)),
                            desc="Brute-force", unit="row-perm")

        for row_order in row_iter:
            ro_idx = {p: i for i, p in enumerate(row_order)}

            # Row-level pre-pruning (no col_perm loop needed for invalid row orders)
            if any(ro_idx[p] >= ro_idx[t] for p, t in self._above):
                continue
            if any(ro_idx[p] <= ro_idx[t] for p, t in self._below):
                continue

            for col_perm in self._col_perms(row_order):
                # Fast-reject: any person placed on a blocked cell?
                if any(
                    puzzle.grid.get_cell(row, col).is_blocked
                    for row, col in enumerate(col_perm)
                ):
                    continue

                state = GameState(list(row_order), list(col_perm), puzzle.grid)

                if not all(clue(state) for clue in puzzle.clues):
                    continue

                victim_room = state.room_of(puzzle.victim)
                room_members = state.people_in_room(victim_room)
                if len(room_members) != 2:
                    continue

                murderer = next(p for p in room_members if p != puzzle.victim)
                positions = {p: state.position(p) for p in people}
                found.append(Solution(positions=positions, murderer=murderer))

        if not found:
            raise NoSolutionError("No valid configuration satisfies all clues.")
        if len(found) > 1:
            raise MultipleSolutionsError([
                {"murderer": s.murderer, "positions": s.positions}
                for s in found
            ])
        return found[0]
