import pytest
from peewee import IntegrityError
from app.model.user import User
from app.repository.user import UserRepository


@pytest.fixture
def user_repo():
    return UserRepository()


def test_create_user_success(test_database, user_repo):
    """Yeni bir kullanıcı başarıyla DB'ye kaydedilmeli."""
    user = user_repo.create(login="kaan", password_hash="hashed_secret")
    assert user.id is not None
    assert user.login == "kaan"
    assert user.password_hash == "hashed_secret"


def test_create_user_duplicate_login_raises_integrity_error(test_database, user_repo):
    """Aynı login ile ikinci kullanıcı eklenmeye çalışıldığında IntegrityError fırlatmalı."""
    user_repo.create(login="kaan", password_hash="hash1")
    with pytest.raises(IntegrityError):
        user_repo.create(login="kaan", password_hash="hash2")


def test_get_by_login_found(test_database, user_repo):
    """Var olan kullanıcı login bilgisiyle sorgulandığında dönmeli."""
    user_repo.create(login="kaan", password_hash="hash1")
    user = user_repo.get_by_login("kaan")
    assert user is not None
    assert user.login == "kaan"


def test_get_by_login_not_found(test_database, user_repo):
    """Olmayan kullanıcı sorgulandığında None dönmeli."""
    user = user_repo.get_by_login("non_existing_user")
    assert user is None


def test_get_by_id_found(test_database, user_repo):
    """Var olan kullanıcı id ile sorgulandığında dönmeli."""
    created = user_repo.create(login="kaan", password_hash="hash1")
    user = user_repo.get_by_id(created.id)
    assert user is not None
    assert user.id == created.id