# CrimeDoku Solver

A logic puzzle game engine where players solve murder mysteries on a grid.  
Each puzzle places suspects on a grid of rooms and uses clues to deduce the murderer.

## Project Structure

```
crimedoku-solver/
├── main.py               # Entry point — load and solve a puzzle
├── puzzle.py             # Puzzle dataclass
├── puzzle_loader.py      # JSON → Puzzle parser
├── cell.py               # Cell and ObjectType definitions
├── grid.py               # Grid class
├── state.py              # GameState (candidate placement)
├── clues.py              # All clue factory functions
├── puzzles/              # JSON puzzle files (puzzle_1.json … puzzle_8.json)
├── solver/
│   └── brute_force_solver.py  # Brute-force permutation solver
└── tests/                # pytest test suite
```

## How to Run

```bash
# Solve a puzzle (edit main.py to choose which puzzle)
python main.py

# Run tests
python -m pytest tests/ -v
```

## Puzzle Format

Puzzles are defined in JSON. Every cell is listed explicitly with its room — no hidden logic functions.

```json
{
  "grid": {
    "rows": 6,
    "cols": 6,
    "cells": [
      {"row": 0, "col": 0, "room": "living_room"},
      {"row": 0, "col": 1, "room": "living_room", "objects": ["window"]},
      ...
    ]
  },
  "people": ["Axel", "Bella", "Cora", "Douglas", "Ella", "Vincent"],
  "victim": "Vincent",
  "clues": [
    {"type": "on_object",      "person": "Axel",  "object": "window"},
    {"type": "in_room",        "person": "Bella", "room":   "hall"},
    {"type": "next_to_object", "person": "Ella",  "object": "plant", "invert": true},
    {"type": "alone_with_murderer", "person": "Vincent"}
  ]
}
```

### Available Objects

| Object         | Blocks movement |
|----------------|-----------------|
| `window`       | No              |
| `bed`          | No              |
| `carpet`       | No              |
| `chair`        | No              |
| `cash_register`| No              |
| `plant`        | Yes             |
| `table`        | Yes             |
| `tv`           | Yes             |
| `bookshelf`    | Yes             |

### Available Clue Types

| Type                  | Parameters                     | Description |
|-----------------------|--------------------------------|-------------|
| `on_object`           | person, object, [invert]       | Person is (or isn't) on a cell with the object |
| `next_to_object`      | person, object, [invert]       | Person is (or isn't) orthogonally adjacent to the object |
| `only_on_object`      | person, object                 | Person is the only one on any cell with this object |
| `in_room`             | person, room                   | Person must be in the given room |
| `in_corner`           | person                         | Person is at a room corner (2 sequential walls/doorways) |
| `not_next_to_wall`    | person                         | Person is not on any grid edge |
| `below_person`        | person, target                 | Person's row > target's row |
| `above_person`        | person, target                 | Person's row < target's row |
| `at_column`           | person, column                 | Person must be in the given column index |
| `alone_with_murderer` | person (victim)                | Victim's room contains exactly 2 people |

> Add `"invert": true` to `on_object` or `next_to_object` to negate the constraint.
