# Copilot Instructions

## Commands

```bash
# Run all tests
python -m pytest tests/ -v

# Run a single test file
python -m pytest tests/test_clues.py -v

# Run a single test by name
python -m pytest tests/test_clues.py::test_in_room_true -v

# Run the interactive solver (arrow-key menus for solver + puzzle)
python main.py
```

## Architecture

The engine solves a logic puzzle: N people are placed on an NxN grid (one per row, one per column — like Sudoku), and clues constrain which placements are valid. The murderer is the non-victim person who shares a room with the victim.

**Data flow:**
```
puzzles/puzzle_N.json
  → loading/loader.py   (load_json → raw dict)
  → loading/parser.py   (parse_puzzle → Puzzle, uses CLUE_REGISTRY)
  → solver/brute_force.py  OR  solver/backtracking.py
  → Solution
```

**Package layout:**
```
models/      Cell, ObjectType, Grid, GameState, Puzzle — core domain types
clues/       One file per clue factory + base.py + registry.py + __init__.py
loading/     loader.py (JSON→dict), parser.py (dict→Puzzle), __init__.py
solver/      base.py (Solution + errors), brute_force.py, backtracking.py
puzzles/     JSON puzzle files (puzzle_1.json … puzzle_15.json)
tests/       pytest test suite
main.py      questionary-based interactive entry point
```

**Core model:**
- `Cell` — immutable dataclass: `(row, col, room_id, objects: FrozenSet[ObjectType])`
- `Grid` — 2D list of Cells; exposes `valid_cells()`, `neighbors()`, `cells_with_object()`, `cells_in_room()`
- `GameState` — encodes a candidate placement as `row_order[i]` (person at row i) + `col_perm[i]` (column for row i). Person `row_order[i]` sits at `(row=i, col=col_perm[i])`.
- `Puzzle` — dataclass holding `grid`, `people`, `victim`, and `clues` (list of callables)

**Clue system:**
Each clue is a factory function in its own file under `clues/`. Every factory returns a `Clue = Callable[[GameState], bool]`. Clue `__name__` is set deliberately — both solvers parse it with regex to extract pruning hints.

`clues/registry.py` holds `CLUE_REGISTRY: Dict[str, Callable[[dict], Clue]]` — a plain dict that maps each JSON type string to a lambda builder. `loading/parser.py` does a single registry lookup instead of an if/elif chain. To add a new clue: create `clues/my_clue.py`, add an entry to `CLUE_REGISTRY`.

**Solvers:**
Both solvers share the same method structure: `_parse_constraints`, `_row_order_valid`, `_finalize`. The backtracking solver additionally has `_build_candidate_cells` and `_build_candidate_cols` for domain reduction, and `_try_solution` at the leaf. Both support `verbose=True` for a tqdm progress bar.

## Key Conventions

- **No external dependencies** beyond `tqdm` and `questionary`. No `requirements.txt`.
- **Flat module imports** — all packages are imported from the repo root (e.g., `from models import Cell`). Test files manually prepend the parent dir to `sys.path`.
- **ObjectType enum values** — each member stores `(string_value, blocks_bool)` via a custom `__new__`. Access the string with `.value` and the flag with `.blocks`.
- **Adding a new clue type:** (1) add `clues/my_clue.py` with the factory function, (2) import it in `clues/registry.py` and add a `"my_clue": lambda s: ...` entry to `CLUE_REGISTRY`, (3) re-export from `clues/__init__.py`. If the clue enables early pruning (row-order or column constraints), also add regex parsing in both solver `_parse_constraints` / `_apply_domain_filter`.
- **`next_to_object` is room-scoped** — only orthogonal neighbors in the same room count.
- **`in_corner`** checks for two *sequential* (90°-adjacent) walls/room-boundaries, not just any two walls.
- **Puzzle JSON** must list every cell explicitly; missing positions become void. The `"invert": true` field on `on_object`, `next_to_object`, and `with_person` negates the constraint.

