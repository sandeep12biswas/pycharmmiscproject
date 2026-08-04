import sqlite3
from dataclasses import dataclass


@dataclass
class Tile:
    id: int
    note_id: int
    x: float
    y: float
    width: float
    height: float
    z_index: int
    title: str
    content_html: str
    content_plain: str
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Tile":
        return cls(
            id=row["id"],
            note_id=row["note_id"],
            x=row["x"],
            y=row["y"],
            width=row["width"],
            height=row["height"],
            z_index=row["z_index"],
            title=row["title"],
            content_html=row["content_html"],
            content_plain=row["content_plain"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
