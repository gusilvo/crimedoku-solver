import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from cell import Cell, ObjectType
from grid import Grid
from state import GameState
from clues import (
    in_room, on_object, only_on_object, next_to_object, alone_with_murderer,
    in_corner, not_next_to_wall, below_person, above_person, at_column,
)


def make_state():
    """
    2x2 grid, two rooms.
    Alice (row 0) at col 0 → (0,0) room=top  has WINDOW.
    Bob   (row 1) at col 1 → (1,1) room=bot  has BED.
    """
    grid = Grid([
        [Cell(0, 0, "top", frozenset({ObjectType.WINDOW})),
         Cell(0, 1, "top", frozenset())],
        [Cell(1, 0, "bot", frozenset()),
         Cell(1, 1, "bot", frozenset({ObjectType.BED}))],
    ])
    return GameState(["Alice", "Bob"], [0, 1], grid)


def test_in_room_true():
    assert in_room("Alice", "top")(make_state()) is True


def test_in_room_false():
    assert in_room("Alice", "bot")(make_state()) is False


def test_on_object_true():
    assert on_object("Alice", ObjectType.WINDOW)(make_state()) is True


def test_on_object_false():
    assert on_object("Alice", ObjectType.BED)(make_state()) is False


def test_only_on_object_true():
    assert only_on_object("Bob", ObjectType.BED)(make_state()) is True


def test_only_on_object_false_wrong_person():
    assert only_on_object("Alice", ObjectType.BED)(make_state()) is False


def test_next_to_object_false():
    # Alice at (0,0); BED is at (1,1) — diagonal only, not an orthogonal neighbor
    assert next_to_object("Alice", ObjectType.BED)(make_state()) is False


def test_next_to_object_true():
    # Alice at (0,0) is orthogonally adjacent to (0,1) which has BED
    grid = Grid([
        [Cell(0, 0, "r", frozenset()),
         Cell(0, 1, "r", frozenset({ObjectType.BED}))],
        [Cell(1, 0, "r", frozenset()),
         Cell(1, 1, "r", frozenset())],
    ])
    state = GameState(["Alice", "Bob"], [0, 1], grid)  # Alice(0,0), Bob(1,1)
    assert next_to_object("Alice", ObjectType.BED)(state) is True


def test_alone_with_murderer_true():
    # Alice(0,0)=same, Bob(1,1)=same → both in room "same" → exactly 2 people
    grid = Grid([
        [Cell(0, 0, "same",  frozenset()), Cell(0, 1, "same", frozenset())],
        [Cell(1, 0, "other", frozenset()), Cell(1, 1, "same", frozenset())],
    ])
    state = GameState(["Alice", "Bob"], [0, 1], grid)
    assert alone_with_murderer("Alice")(state) is True


def test_alone_with_murderer_false_alone():
    # Alice alone in roomA
    grid = Grid([
        [Cell(0, 0, "roomA", frozenset()), Cell(0, 1, "roomB", frozenset())],
        [Cell(1, 0, "roomB", frozenset()), Cell(1, 1, "roomB", frozenset())],
    ])
    state = GameState(["Alice", "Bob"], [0, 1], grid)
    assert alone_with_murderer("Alice")(state) is False


def test_alone_with_murderer_false_three_in_room():
    # Three people all in room "r" → victim not alone with just one other
    grid = Grid([
        [Cell(r, c, "r", frozenset()) for c in range(3)]
        for r in range(3)
    ])
    state = GameState(["Alice", "Bob", "Carol"], [0, 1, 2], grid)
    assert alone_with_murderer("Alice")(state) is False


# ── invert param ──────────────────────────────────────────────────────────────

def test_on_object_invert_true():
    # Alice is on WINDOW; invert=True → clue should be False
    assert on_object("Alice", ObjectType.WINDOW, invert=True)(make_state()) is False


def test_on_object_invert_false_when_not_on():
    # Alice is on WINDOW; invert=True on BED → should be True (she's NOT on bed)
    assert on_object("Alice", ObjectType.BED, invert=True)(make_state()) is True


def test_next_to_object_invert():
    # Alice at (0,0); BED is at (1,1) — not a neighbor; invert=True → True
    assert next_to_object("Alice", ObjectType.BED, invert=True)(make_state()) is True


# ── in_corner ─────────────────────────────────────────────────────────────────

def _make_corner_state():
    """
    3x3 single-room grid. Alice at (0,0), Bob at (1,1), Carol at (2,2).
    """
    grid = Grid([[Cell(r, c, "r", frozenset()) for c in range(3)] for r in range(3)])
    return GameState(["Alice", "Bob", "Carol"], [0, 1, 2], grid)


def test_in_corner_at_grid_corner():
    # Alice at (0,0): up and left are out-of-bounds → sequential pair → corner
    assert in_corner("Alice")(_make_corner_state()) is True


def test_in_corner_at_center():
    # Bob at (1,1): all 4 neighbors exist and are same room → not a corner
    assert in_corner("Bob")(_make_corner_state()) is False


def test_in_corner_at_opposite_walls():
    """
    Person at (0,2) in a single-room 3x3: up is OOB, right is OOB.
    up+right are sequential → corner.
    """
    grid = Grid([[Cell(r, c, "r", frozenset()) for c in range(3)] for r in range(3)])
    state = GameState(["Alice", "Bob", "Carol"], [2, 0, 1], grid)  # Alice at (0,2)
    assert in_corner("Alice")(state) is True


def test_in_corner_room_boundary():
    """
    Person at (1,0): left is OOB, up neighbor is different room.
    left+up are sequential → corner.
    """
    grid = Grid([
        [Cell(0, 0, "other", frozenset()), Cell(0, 1, "other", frozenset()), Cell(0, 2, "other", frozenset())],
        [Cell(1, 0, "r",     frozenset()), Cell(1, 1, "r",     frozenset()), Cell(1, 2, "r",     frozenset())],
        [Cell(2, 0, "r",     frozenset()), Cell(2, 1, "r",     frozenset()), Cell(2, 2, "r",     frozenset())],
    ])
    state = GameState(["Alice", "Bob", "Carol"], [0, 1, 2], grid)  # Alice at (1,0)
    assert in_corner("Alice")(state) is True


# ── not_next_to_wall ──────────────────────────────────────────────────────────

def test_not_next_to_wall_center():
    # Bob at (1,1) in 3x3 → interior → True
    assert not_next_to_wall("Bob")(_make_corner_state()) is True


def test_not_next_to_wall_edge():
    # Alice at (0,0) in 3x3 → on edge → False
    assert not_next_to_wall("Alice")(_make_corner_state()) is False


# ── below_person / above_person ───────────────────────────────────────────────

def test_below_person_true():
    # Carol at row 2, Alice at row 0 → Carol is below Alice
    assert below_person("Carol", "Alice")(_make_corner_state()) is True


def test_below_person_false():
    assert below_person("Alice", "Carol")(_make_corner_state()) is False


def test_above_person_true():
    assert above_person("Alice", "Carol")(_make_corner_state()) is True


def test_above_person_false():
    assert above_person("Carol", "Alice")(_make_corner_state()) is False


# ── at_column ─────────────────────────────────────────────────────────────────

def test_at_column_true():
    # Alice at (0,0) → col 0
    assert at_column("Alice", 0)(_make_corner_state()) is True


def test_at_column_false():
    assert at_column("Alice", 2)(_make_corner_state()) is False

