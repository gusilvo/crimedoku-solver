from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List


class NoSolutionError(Exception):
    """Raised when no valid configuration satisfies all clues."""


class MultipleSolutionsError(Exception):
    """Raised when more than one valid configuration is found."""

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
