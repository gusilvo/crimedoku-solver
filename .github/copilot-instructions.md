# Copilot Instructions

## Commands

```bash
# Run all tests
python -m pytest tests/ -v

# Run a single test file
python -m pytest tests/test_clues.py -v

# Run a single test by name
python -m pytest tests/test_clues.py::test_in_room_true -v

# Solve a puzzle (edit PUZZLES_DIR path in main.py to switch puzzles)
python main.py
```

## Architecture

The engine solves a logic puzzle: N people are placed on an NxN grid (one per row, one per column — like Sudoku), and clues constrain which placements are valid. The murderer is the non-victim person who shares a room with the victim.

**Data flow:**
```
puzzles/puzzle_N.json → puzzle_loader.load_puzzle() → Puzzle
                                                           ↓
                                               solver/brute_force_solver.Solver
                                                           ↓
                                                        Solution
```

**Core model:**
- `Cell` — immutable dataclass with `(row, col, room_id, objects: FrozenSet[ObjectType])`
- `Grid` — 2D list of Cells; exposes `valid_cells()`, `neighbors()`, `cells_with_object()`, `cells_in_room()`
- `GameState` — encodes a candidate placement as `row_order[i]` (person at row i) + `col_perm[i]` (column for row i). Person `row_order[i]` sits at `(row=i, col=col_perm[i])`.
- `Puzzle` — dataclass holding `grid`, `people`, `victim`, and `clues` (list of callables)
- `Solver` — iterates all `(N!)²` permutations of row_order × col_perm, with early pruning for `above_person`/`below_person` (row-level) and `at_column` (reduces col permutations)

**Clue system:**
Each clue is a factory function in `clues.py` that returns a `Clue = Callable[[GameState], bool]`. All clues are evaluated against a `GameState`; the solver accepts only states where every clue returns `True`. Clue `__name__` is set deliberately — the solver parses it with regex to extract pruning hints (see `Solver.__init__`).

**Blocked cells:** `ObjectType` carries a `blocks: bool` flag. Cells containing blocking objects (e.g. `PLANT`, `TABLE`) are excluded from valid placements. Undefined grid positions are auto-filled as `__void__` (always blocked).

## Key Conventions

- **No external dependencies** — pure stdlib + pytest. No `requirements.txt`.
- **Modules run from repo root** — all imports are flat (`from cell import ...`, `from grid import ...`). Test files manually prepend the parent dir to `sys.path`.
- **ObjectType enum values** — each member stores `(string_value, blocks_bool)` via a custom `__new__`. Access the string with `.value` and the flag with `.blocks`.
- **Adding a new clue type:** (1) add a factory function in `clues.py`, (2) add a `elif clue_type == ...` branch in `puzzle_loader._parse_clue`, (3) import it in `puzzle_loader.py`. If the clue encodes a row-order or column constraint that can enable early pruning, also add parsing logic to `Solver.__init__` and `_col_perms`.
- **`next_to_object` is room-scoped** — only orthogonal neighbors in the same room count.
- **`in_corner`** checks for two *sequential* (90°-adjacent) walls/room-boundaries, not just any two walls.
- **Puzzle JSON** must list every cell explicitly; missing positions become void. The `"invert": true` field on `on_object`, `next_to_object`, and `with_person` negates the constraint.
