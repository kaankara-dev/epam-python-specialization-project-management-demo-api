import pytest
from peewee import IntegrityError

from app.core.security import password_hash
from app.model.user import User


def test_user_can_be_persisted(test_database):
    _password_hash = "test-password-hash"

    created_user = User.create(
        login="test",
        password_hash=_password_hash,
    )

    assert created_user.id is not None

    stored_user = User.get_by_id(created_user.id)

    assert stored_user.login == "test"
    assert stored_user.password_hash == _password_hash


def test_user_login_must_be_unique(test_database):
    _password_hash = "test-password-hash"
    with pytest.raises(IntegrityError):
        User.create(
            login="test",
            password_hash=_password_hash, )
        User.create(
            login="test",
            password_hash=_password_hash, )

@pytest.mark.parametrize("password_param", (None, "", "   "))
def test_user_login_password_hash_must_be_filled(test_database, password_param):
    with pytest.raises(IntegrityError):
        User.create(
            login="test",
            password_hash = password_param
        )