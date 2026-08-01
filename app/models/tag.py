import sqlite3
from dataclasses import dataclass
from typing import Optional


@dataclass
class Tag:
    id: Optional[int]
    name: str
    color: Optional[str]

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Tag":
        return cls(id=row["id"], name=row["name"], color=row["color"])
