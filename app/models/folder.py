import sqlite3
from dataclasses import dataclass
from typing import Optional


@dataclass
class Folder:
    id: Optional[int]
    name: str
    parent_id: Optional[int]
    sort_order: int
    created_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Folder":
        return cls(
            id=row["id"],
            name=row["name"],
            parent_id=row["parent_id"],
            sort_order=row["sort_order"],
            created_at=row["created_at"],
        )
