from peewee import SqliteDatabase

from app.db.database import database_proxy, initialize_database


def test_initialize_database_binds_proxy_and_returns_target():
    target_database = SqliteDatabase(":memory:")

    returned_database = initialize_database(target_database)

    assert returned_database is target_database
    assert database_proxy.obj is returned_database
    assert target_database.is_closed()