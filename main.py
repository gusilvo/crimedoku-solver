"""Entry point: solve a Murdoku puzzle and print the result."""
import time
from pathlib import Path
from puzzle_loader import load_puzzle
from solver.backtracking_solver import BacktrackingSolver, NoSolutionError, MultipleSolutionsError

COLUMNS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
PUZZLES_DIR = Path(__file__).parent / "puzzles"


def main() -> None:
    puzzle = load_puzzle(PUZZLES_DIR / "puzzle_12.json")
    solver = BacktrackingSolver(puzzle, verbose=True)
    t0 = time.perf_counter()
    try:
        solution = solver.solve()
        elapsed = time.perf_counter() - t0
        print("=== Murdoku Solved ===\n")
        for person, (row, col) in sorted(solution.positions.items()):
            col_letter = COLUMNS[col]
            cell = puzzle.grid.get_cell(row, col)
            objs = ", ".join(o.value for o in cell.objects) or "empty"
            print(f"  {person:<10} {col_letter}{row}  room={cell.room_id}  ({objs})")
        print(f"\n  Murderer: {solution.murderer}")
        print(f"\n  Solved in {elapsed:.3f}s")
    except NoSolutionError as e:
        elapsed = time.perf_counter() - t0
        print(f"[NO SOLUTION] {e}  ({elapsed:.3f}s)")
    except MultipleSolutionsError as e:
        elapsed = time.perf_counter() - t0
        print(f"[MULTIPLE SOLUTIONS] {e}  ({elapsed:.3f}s)")


if __name__ == "__main__":
    main()

