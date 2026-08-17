import pytest
from pydantic import ValidationError
from app.schema.user import UserCreate, UserResponse, TokenResponse


def test_user_create_valid():
    user = UserCreate(login="kaan_dev", password="SuperSecretPassword123!")
    assert user.login == "kaan_dev"
    assert user.password == "SuperSecretPassword123!"


def test_user_create_short_password():
    """Güvenlik kuralı: Şifre en az 8 karakter olmalıdır."""
    with pytest.raises(ValidationError):
        UserCreate(login="kaan_dev", password="123")


def test_user_response_does_not_contain_password():
    """UserResponse'ta password veya password_hash alanı bulunamaz."""
    res = UserResponse(id=1, login="kaan_dev")
    assert res.id == 1
    assert res.login == "kaan_dev"
    assert not hasattr(res, "password")
    assert not hasattr(res, "password_hash")