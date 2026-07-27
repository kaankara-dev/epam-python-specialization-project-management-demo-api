from app.db.database import database_proxy
from app.model.user import User


def test_base_model_is_database_proxy():
    assert User._meta.database is database_proxy