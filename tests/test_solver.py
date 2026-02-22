import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from pathlib import Path
from puzzle_loader import load_puzzle
from solver.brute_force_solver import Solver, NoSolutionError, MultipleSolutionsError
from cell import Cell, ObjectType
from grid import Grid
from puzzle import Puzzle
from clues import in_room

PUZZLES_DIR = Path(__file__).parent.parent / "puzzles"
PUZZLE_1 = load_puzzle(PUZZLES_DIR / "puzzle_1.json")


def test_puzzle1_unique_solution():
    solution = Solver(PUZZLE_1).solve()
    assert solution.murderer == "Ella"


def test_puzzle1_axel_on_window():
    solution = Solver(PUZZLE_1).solve()
    cell = PUZZLE_1.grid.get_cell(*solution.positions["Axel"])
    assert cell.has_object(ObjectType.WINDOW)


def test_puzzle1_douglas_on_bed():
    solution = Solver(PUZZLE_1).solve()
    cell = PUZZLE_1.grid.get_cell(*solution.positions["Douglas"])
    assert cell.has_object(ObjectType.BED)


def test_puzzle1_vincent_and_ella_same_room():
    solution = Solver(PUZZLE_1).solve()
    grid = PUZZLE_1.grid
    vincent_room = grid.get_cell(*solution.positions["Vincent"]).room_id
    ella_room    = grid.get_cell(*solution.positions["Ella"]).room_id
    assert vincent_room == ella_room == "dinner_room"


def test_no_solution_raises():
    puzzle = load_puzzle(PUZZLES_DIR / "puzzle_1.json")
    # Axel on a window (living/main room) AND in hall → impossible
    puzzle.clues.append(in_room("Axel", "hall"))
    with pytest.raises(NoSolutionError):
        Solver(puzzle).solve()


def test_multiple_solutions_raises_and_shows_all():
    # No clues on a 2x2 all-same-room grid → multiple solutions
    cells = [
        [Cell(r, c, "room", frozenset()) for c in range(2)]
        for r in range(2)
    ]
    grid = Grid(cells)
    puzzle = Puzzle(grid=grid, people=["Alice", "Bob"], victim="Alice", clues=[])
    with pytest.raises(MultipleSolutionsError) as exc_info:
        Solver(puzzle).solve()
    assert len(exc_info.value.solutions) > 1
