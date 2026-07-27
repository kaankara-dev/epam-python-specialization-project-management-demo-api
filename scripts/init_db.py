from app.db.database import initialize_database
from app.db.registry import MODELS


def main() -> None:
    target_database = initialize_database()

    with target_database:
        target_database.create_tables(MODELS, safe=True,)


if __name__ == "__main__":
    main()