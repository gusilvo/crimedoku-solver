"""
Brute-force permutation solver for Murdoku puzzles.

Explores all (N!)^2 placements with two optimisations:
- Row-level pruning:  above_person / below_person constraints skip invalid row orders.
- Column prefilter:   at_column constraints reduce the inner permutation space.
"""
from __future__ import annotations

import re
from itertools import permutations
from math import factorial
from typing import Dict, List, Optional, Tuple

from models.puzzle import Puzzle
from models.state import GameState
from solver.base import Solution, NoSolutionError, MultipleSolutionsError


class Solver:
    def __init__(self, puzzle: Puzzle, verbose: bool = False) -> None:
        self.puzzle = puzzle
        self.verbose = verbose
        self._above, self._below, self._col_fixed = self._parse_constraints(puzzle.clues)

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
    # Column permutation generation
    # ------------------------------------------------------------------

    def _col_perms(self, row_order: Tuple[str, ...]):
        """Yield col permutations that satisfy at_column constraints."""
        n = len(row_order)
        if not self._col_fixed:
            yield from permutations(range(n))
            return

        fixed: Dict[int, int] = {}
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

    # ------------------------------------------------------------------
    # Placement evaluation
    # ------------------------------------------------------------------

    def _blocked_placement(self, col_perm: List[int]) -> bool:
        """Return True if any person is placed on a blocked cell."""
        return any(
            self.puzzle.grid.get_cell(row, col).is_blocked
            for row, col in enumerate(col_perm)
        )

    def _extract_solution(self, state: GameState) -> Optional[Solution]:
        """Return a Solution if the state satisfies all clues and the victim
        is alone with exactly one other person; otherwise return None."""
        if not all(clue(state) for clue in self.puzzle.clues):
            return None
        victim_room = state.room_of(self.puzzle.victim)
        room_members = state.people_in_room(victim_room)
        if len(room_members) != 2:
            return None
        murderer = next(p for p in room_members if p != self.puzzle.victim)
        positions = {p: state.position(p) for p in self.puzzle.people}
        return Solution(positions=positions, murderer=murderer)

    # ------------------------------------------------------------------
    # Result finalisation
    # ------------------------------------------------------------------

    @staticmethod
    def _finalize(found: List[Solution]) -> Solution:
        """Return the unique solution or raise the appropriate error."""
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
        found: List[Solution] = []

        row_iter = permutations(people)
        if self.verbose:
            from tqdm import tqdm
            row_iter = tqdm(row_iter, total=factorial(len(people)),
                            desc="Brute-force", unit="row-perm")

        for row_order in row_iter:
            ro_idx = {p: i for i, p in enumerate(row_order)}
            if not self._row_order_valid(ro_idx):
                continue

            for col_perm in self._col_perms(row_order):
                if self._blocked_placement(col_perm):
                    continue
                state = GameState(list(row_order), list(col_perm), puzzle.grid)
                solution = self._extract_solution(state)
                if solution:
                    found.append(solution)

        return self._finalize(found)
