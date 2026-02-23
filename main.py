"""Entry point: interactively choose a solver and puzzle, then solve."""
import sys
import time
from pathlib import Path
import questionary
from loading import load_puzzle
from solver.brute_force import Solver
from solver.backtracking import BacktrackingSolver
from solver.base import NoSolutionError, MultipleSolutionsError

COLUMNS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
PUZZLES_DIR = Path(__file__).parent / "puzzles"

SOLVERS = {
    "Backtracking Solver": BacktrackingSolver,
    "Brute Force Solver": Solver,
}


def choose_solver():
    name = questionary.select(
        "Which solver do you want to use?",
        choices=list(SOLVERS),
    ).ask()
    if name is None:
        sys.exit(0)
    return SOLVERS[name]


def choose_puzzle() -> Path:
    puzzle_files = sorted(PUZZLES_DIR.glob("*.json"))
    if not puzzle_files:
        print("No puzzle files found in", PUZZLES_DIR)
        sys.exit(1)
    choice = questionary.select(
        "Which puzzle do you want to solve?",
        choices=[p.stem for p in puzzle_files],
    ).ask()
    if choice is None:
        sys.exit(0)
    return PUZZLES_DIR / f"{choice}.json"


def print_solution(solution, puzzle) -> None:
    print("\n=== Murdoku Solved ===\n")
    for person, (row, col) in sorted(solution.positions.items()):
        col_letter = COLUMNS[col]
        cell = puzzle.grid.get_cell(row, col)
        objs = ", ".join(o.value for o in cell.objects) or "empty"
        print(f"  {person:<10} {col_letter}{row}  room={cell.room_id}  ({objs})")
    print(f"\n  Murderer: {solution.murderer}")


def main() -> None:
    solver_cls = choose_solver()
    puzzle_path = choose_puzzle()

    puzzle = load_puzzle(puzzle_path)
    solver = solver_cls(puzzle, verbose=True)

    t0 = time.perf_counter()
    try:
        solution = solver.solve()
        elapsed = time.perf_counter() - t0
        print_solution(solution, puzzle)
        print(f"\n  Solved in {elapsed:.3f}s")
    except NoSolutionError as e:
        elapsed = time.perf_counter() - t0
        print(f"\n[NO SOLUTION] {e}  ({elapsed:.3f}s)")
    except MultipleSolutionsError as e:
        elapsed = time.perf_counter() - t0
        print(f"\n[MULTIPLE SOLUTIONS] {e}  ({elapsed:.3f}s)")


if __name__ == "__main__":
    main()
