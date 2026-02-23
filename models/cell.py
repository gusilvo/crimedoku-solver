from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import FrozenSet


class ObjectType(Enum):
    """Furniture/feature that can appear in a cell.

    Each member carries a ``blocks`` flag: if True, no person may stand on
    a cell that contains this object.
    """

    WINDOW = ("window", False)
    BED    = ("bed",    False)
    CARPET = ("carpet", False)
    PLANT  = ("plant",  True)
    TABLE  = ("table",  True)
    CHAIR         = ("chair",         False)
    TV            = ("tv",            True)
    BOOKSHELF     = ("bookshelf",     True)
    CASH_REGISTER = ("cash_register", False)
    RUBBISH       = ("rubbish",       True)
    ROCK          = ("rock",          True)
    COMPUTER      = ("computer",      True)
    GIFT          = ("gift",          False)
    BOX           = ("box",           True)
    VOID          = ("__void__",      True)

    def __new__(cls, value: str, blocks: bool):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.blocks = blocks
        return obj

    def __repr__(self) -> str:
        return f"ObjectType.{self.name}"


@dataclass(frozen=True)
class Cell:
    row: int
    col: int
    room_id: str
    objects: FrozenSet[ObjectType] = field(default_factory=frozenset)

    @property
    def is_blocked(self) -> bool:
        """True if any object in this cell prevents occupancy."""
        return any(o.blocks for o in self.objects)

    def has_object(self, obj: ObjectType) -> bool:
        return obj in self.objects

    def __repr__(self) -> str:
        return f"Cell(row={self.row}, col={self.col}, room={self.room_id!r})"
