import pytest

from app.db.connection import open_database
from app.repositories.folders_repo import FoldersRepository
from app.repositories.notes_repo import NotesRepository
from app.repositories.reminders_repo import RemindersRepository
from app.repositories.tags_repo import TagsRepository


@pytest.fixture
def conn():
    """A fresh in-memory database with the full schema applied, isolated per test."""
    connection = open_database(":memory:")
    yield connection
    connection.close()


@pytest.fixture
def notes_repo(conn) -> NotesRepository:
    return NotesRepository(conn)


@pytest.fixture
def folders_repo(conn) -> FoldersRepository:
    return FoldersRepository(conn)


@pytest.fixture
def tags_repo(conn) -> TagsRepository:
    return TagsRepository(conn)


@pytest.fixture
def reminders_repo(conn) -> RemindersRepository:
    return RemindersRepository(conn)
