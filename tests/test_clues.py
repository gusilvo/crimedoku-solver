import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from cell import Cell, ObjectType
from grid import Grid
from state import GameState
from clues import (
    in_room, on_object, only_on_object, next_to_object, alone_with_murderer,
    in_corner, not_next_to_wall, below_person, above_person, at_column,
    with_person, alone_in_room, only_one_person_on, same_column_as_object, left_of,
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


# ── with_person ───────────────────────────────────────────────────────────────

def _make_room_state():
    """
    3x3 grid: Alice(0,0) and Bob(1,0) in roomA; Carol(2,2) in roomB.
    """
    grid = Grid([
        [Cell(0, 0, "roomA", frozenset()), Cell(0, 1, "roomA", frozenset()), Cell(0, 2, "roomA", frozenset())],
        [Cell(1, 0, "roomA", frozenset()), Cell(1, 1, "roomB", frozenset()), Cell(1, 2, "roomB", frozenset())],
        [Cell(2, 0, "roomB", frozenset()), Cell(2, 1, "roomB", frozenset()), Cell(2, 2, "roomB", frozenset())],
    ])
    return GameState(["Alice", "Bob", "Carol"], [0, 0, 2], grid)


def test_with_person_same_room():
    # Alice(0,0) and Bob(1,0) both in roomA → True
    assert with_person("Alice", "Bob")(_make_room_state()) is True


def test_with_person_different_room():
    # Alice(0,0) roomA, Carol(2,2) roomB → False
    assert with_person("Alice", "Carol")(_make_room_state()) is False


def test_with_person_invert_true():
    # Alice and Carol in different rooms; invert=True → True
    assert with_person("Alice", "Carol", invert=True)(_make_room_state()) is True


def test_with_person_invert_false():
    # Alice and Bob in same room; invert=True → False
    assert with_person("Alice", "Bob", invert=True)(_make_room_state()) is False


# ── alone_in_room ─────────────────────────────────────────────────────────────

def test_alone_in_room_true():
    # Carol is the only one in roomB → True
    assert alone_in_room("Carol", "roomB")(_make_room_state()) is True


def test_alone_in_room_false_not_alone():
    # Both Alice and Bob are in roomA → neither is alone
    assert alone_in_room("Alice", "roomA")(_make_room_state()) is False


def test_alone_in_room_false_wrong_room():
    # Carol is in roomB; checking roomA → False
    assert alone_in_room("Carol", "roomA")(_make_room_state()) is False


# ── only_one_person_on ────────────────────────────────────────────────────────

def test_only_one_person_on_true():
    # Alice on WINDOW, no one else on WINDOW
    assert only_one_person_on(ObjectType.WINDOW)(make_state()) is True


def test_only_one_person_on_false_two_people():
    # Both Alice and Bob on BED
    grid = Grid([
        [Cell(0, 0, "r", frozenset({ObjectType.BED})), Cell(0, 1, "r", frozenset())],
        [Cell(1, 0, "r", frozenset()), Cell(1, 1, "r", frozenset({ObjectType.BED}))],
    ])
    state = GameState(["Alice", "Bob"], [0, 1], grid)
    assert only_one_person_on(ObjectType.BED)(state) is False


def test_only_one_person_on_zero_is_ok():
    # No one on PLANT → 0 <= 1 → True
    assert only_one_person_on(ObjectType.PLANT)(make_state()) is True


# ── same_column_as_object ─────────────────────────────────────────────────────

def _make_col_state():
    """
    2x3 grid: Alice(0,0), Bob(1,2).
    Col0: room=A, Col1: room=A, Col2: room=B.
    WINDOW at (0,2), BED at (1,0).
    """
    grid = Grid([
        [Cell(0, 0, "A", frozenset({ObjectType.BED})),
         Cell(0, 1, "A", frozenset()),
         Cell(0, 2, "B", frozenset({ObjectType.WINDOW}))],
        [Cell(1, 0, "A", frozenset()),
         Cell(1, 1, "A", frozenset()),
         Cell(1, 2, "B", frozenset())],
    ])
    # Alice at (0,0) roomA, Bob at (1,2) roomB
    return GameState(["Alice", "Bob"], [0, 2], grid)


def test_same_column_as_object_same_room():
    # Alice at col 0, BED at (0,0) col 0 roomA, Alice in roomA → same_room=True
    assert same_column_as_object("Alice", ObjectType.BED, different_room=False)(_make_col_state()) is True


def test_same_column_as_object_diff_room():
    # Alice at col 0, WINDOW at (0,2) col 2 roomB, Alice in roomA → diff_room
    # Col doesn't match → False
    assert same_column_as_object("Alice", ObjectType.WINDOW, different_room=True)(_make_col_state()) is False


def test_same_column_as_object_diff_room_match():
    # Bob at col 2, BED at (0,0) col 0 roomA, Bob in roomB → col doesn't match → False
    # WINDOW at (0,2) col 2 roomB, Bob in roomB → same room → diff_room=True → False
    assert same_column_as_object("Bob", ObjectType.WINDOW, different_room=True)(_make_col_state()) is False


def test_same_column_as_object_same_room_match():
    # Bob at col 2, WINDOW at (0,2) col 2 roomB, Bob in roomB → same room → True
    assert same_column_as_object("Bob", ObjectType.WINDOW, different_room=False)(_make_col_state()) is True


# ── left_of ───────────────────────────────────────────────────────────────────

def test_left_of_same_room_true():
    # Alice at col 0, WINDOW at (0,2) col 2 roomB — Alice in roomA not roomB
    # different_room=False (same room) → Alice roomA, WINDOW roomB → no match → False
    assert left_of("Alice", ObjectType.WINDOW, different_room=False)(_make_col_state()) is False


def test_left_of_diff_room_true():
    # Alice at col 0, WINDOW at (0,2) col 2 roomB, Alice in roomA → different rooms and col 0 < col 2 → True
    assert left_of("Alice", ObjectType.WINDOW, different_room=True)(_make_col_state()) is True


def test_left_of_not_left():
    # Bob at col 2, BED at (0,0) col 0, col 2 < col 0 is False → False
    assert left_of("Bob", ObjectType.BED, different_room=True)(_make_col_state()) is False

