"""Entry point: solve a Murdoku puzzle and print the result."""
from pathlib import Path
from puzzle_loader import load_puzzle
from solver.brute_force_solver import Solver, NoSolutionError, MultipleSolutionsError

COLUMNS = "ABCDEF"
PUZZLES_DIR = Path(__file__).parent / "puzzles"


def main() -> None:
    puzzle = load_puzzle(PUZZLES_DIR / "puzzle_3.json")
    solver = Solver(puzzle)
    try:
        solution = solver.solve()
        print("=== Murdoku Solved ===\n")
        for person, (row, col) in sorted(solution.positions.items()):
            col_letter = COLUMNS[col]
            cell = puzzle.grid.get_cell(row, col)
            objs = ", ".join(o.value for o in cell.objects) or "empty"
            print(f"  {person:<10} {col_letter}{row}  room={cell.room_id}  ({objs})")
        print(f"\n  Murderer: {solution.murderer}")
    except NoSolutionError as e:
        print(f"[NO SOLUTION] {e}")
    except MultipleSolutionsError as e:
        print(f"[MULTIPLE SOLUTIONS] {e}")


if __name__ == "__main__":
    main()
