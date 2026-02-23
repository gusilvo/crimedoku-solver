from __future__ import annotations
from typing import Dict, List, Tuple
from models.cell import Cell, ObjectType
from models.grid import Grid


class GameState:
    """
    A candidate placement of all people on the grid.

    ``row_order[i]`` is the name of the person assigned to row *i*.
    ``col_perm[i]``  is the column assigned to row *i*.

    Therefore person ``row_order[i]`` is placed at ``(row=i, col=col_perm[i])``.
    """

    def __init__(self, row_order: List[str], col_perm: List[int], grid: Grid):
        self.row_order = list(row_order)
        self.col_perm = list(col_perm)
        self.grid = grid
        self._pos: Dict[str, Tuple[int, int]] = {
            row_order[i]: (i, col_perm[i]) for i in range(len(row_order))
        }

    def position(self, person: str) -> Tuple[int, int]:
        return self._pos[person]

    def cell_of(self, person: str) -> Cell:
        r, c = self._pos[person]
        return self.grid.get_cell(r, c)

    def room_of(self, person: str) -> str:
        return self.cell_of(person).room_id

    def people_in_room(self, room_id: str) -> List[str]:
        return [p for p in self.row_order if self.room_of(p) == room_id]

    def people_on_object(self, obj: ObjectType) -> List[str]:
        return [p for p in self.row_order if self.cell_of(p).has_object(obj)]
