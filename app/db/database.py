from peewee import Database, DatabaseProxy
from playhouse.db_url import connect

from app.core.config import get_settings


database_proxy = DatabaseProxy()


def build_database() -> Database:
    settings = get_settings()
    return connect(settings.database_url)


def initialize_database(
    target_database: Database | None = None,
) -> Database:
    actual_database = (
        target_database
        if target_database is not None
        else build_database()
    )

    database_proxy.initialize(actual_database)

    return actual_database