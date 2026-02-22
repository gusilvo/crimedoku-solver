from __future__ import annotations
from dataclasses import dataclass
from itertools import permutations
from typing import Any, Dict, List
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
    while keeping rows and columns unique.  For N=6 this is 518 400 candidates,
    all visited in well under a second.
    """

    def __init__(self, puzzle: Puzzle):
        self.puzzle = puzzle

    def solve(self) -> Solution:
        """Return the unique Solution, or raise NoSolutionError / MultipleSolutionsError."""
        puzzle = self.puzzle
        people = puzzle.people
        n = len(people)
        found: List[Solution] = []

        for row_order in permutations(people):
            for col_perm in permutations(range(n)):
                # Fast-reject: any person placed on a blocked cell?
                if any(
                    puzzle.grid.get_cell(row, col).is_blocked
                    for row, col in enumerate(col_perm)
                ):
                    continue

                state = GameState(list(row_order), list(col_perm), puzzle.grid)

                # Validate all clues
                if not all(clue(state) for clue in puzzle.clues):
                    continue

                # Murder rule: victim's room must hold exactly 2 people
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
