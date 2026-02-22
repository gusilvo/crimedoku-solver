import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from cell import Cell, ObjectType
from grid import Grid


def make_2x2_grid():
    """2x2 grid: (0,0) empty/r1, (0,1) WINDOW/r1, (1,0) TABLE/r2, (1,1) empty/r2."""
    return Grid([
        [Cell(0, 0, "r1", frozenset()),
         Cell(0, 1, "r1", frozenset({ObjectType.WINDOW}))],
        [Cell(1, 0, "r2", frozenset({ObjectType.TABLE})),
         Cell(1, 1, "r2", frozenset())],
    ])


def test_get_cell():
    g = make_2x2_grid()
    c = g.get_cell(0, 1)
    assert c.row == 0 and c.col == 1
    assert ObjectType.WINDOW in c.objects


def test_valid_cells_excludes_table():
    g = make_2x2_grid()
    valid = {(c.row, c.col) for c in g.valid_cells()}
    assert (1, 0) not in valid   # TABLE blocks
    assert (0, 0) in valid
    assert (0, 1) in valid
    assert (1, 1) in valid


def test_cells_with_object():
    g = make_2x2_grid()
    assert len(g.cells_with_object(ObjectType.WINDOW)) == 1
    assert g.cells_with_object(ObjectType.WINDOW)[0].col == 1


def test_cells_in_room():
    g = make_2x2_grid()
    r1 = g.cells_in_room("r1")
    assert len(r1) == 2
    assert all(c.room_id == "r1" for c in r1)


def test_neighbors_corner():
    g = make_2x2_grid()
    nbrs = {(n.row, n.col) for n in g.neighbors(0, 0)}
    assert nbrs == {(0, 1), (1, 0)}


def test_neighbors_inner():
    g = make_2x2_grid()
    nbrs = {(n.row, n.col) for n in g.neighbors(0, 1)}
    assert nbrs == {(0, 0), (1, 1)}


def test_object_type_blocks():
    assert ObjectType.TABLE.blocks is True
    assert ObjectType.WINDOW.blocks is False
    assert ObjectType.BED.blocks is False
    assert ObjectType.PLANT.blocks is False
    assert ObjectType.CARPET.blocks is False


def test_cell_is_blocked():
    assert Cell(0, 0, "r", frozenset({ObjectType.TABLE})).is_blocked is True
    assert Cell(0, 0, "r", frozenset({ObjectType.WINDOW})).is_blocked is False
    assert Cell(0, 0, "r", frozenset()).is_blocked is False
