import pytest
from peewee import SqliteDatabase

from app.db.database import initialize_database
from app.db.registry import MODELS


@pytest.fixture
def test_database():
    temporary_database = SqliteDatabase(
        ":memory:",
        pragmas={"foreign_keys": 1},
    )

    initialize_database(temporary_database)

    with temporary_database.connection_context():
        temporary_database.create_tables(MODELS, safe=True)

        yield temporary_database

        temporary_database.drop_tables(MODELS, safe=True)