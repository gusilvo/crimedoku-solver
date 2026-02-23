"""Public API for loading puzzles from JSON files."""
from pathlib import Path
from loading.loader import load_json
from loading.parser import parse_puzzle
from models.puzzle import Puzzle


def load_puzzle(path: str | Path) -> Puzzle:
    """Read a JSON puzzle file and return a ready-to-solve Puzzle."""
    return parse_puzzle(load_json(path))


__all__ = ["load_puzzle", "load_json", "parse_puzzle"]
