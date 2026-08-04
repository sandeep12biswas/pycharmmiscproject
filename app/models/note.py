import sqlite3
from dataclasses import dataclass
from typing import Optional


@dataclass
class Note:
    id: Optional[int]
    title: str
    content_html: str
    content_plain: str
    folder_id: Optional[int]
    is_pinned: bool
    is_favorite: bool
    is_trashed: bool
    is_canvas: bool
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Note":
        return cls(
            id=row["id"],
            title=row["title"],
            content_html=row["content_html"],
            content_plain=row["content_plain"],
            folder_id=row["folder_id"],
            is_pinned=bool(row["is_pinned"]),
            is_favorite=bool(row["is_favorite"]),
            is_trashed=bool(row["is_trashed"]),
            is_canvas=bool(row["is_canvas"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
