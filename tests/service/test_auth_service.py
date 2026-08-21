from unittest.mock import MagicMock
import pytest

from app.exception.auth import InvalidCredentialsError, UserAlreadyExistsError
from app.schema.user import UserCreate
from app.service.auth import AuthService


@pytest.fixture
def mock_user_repo():
    return MagicMock()


@pytest.fixture
def auth_service(mock_user_repo):
    return AuthService(user_repo=mock_user_repo)


def test_register_success(auth_service, mock_user_repo):
    """Kullanıcı adı boşsa şifreyi hashleyip kaydetmeli ve UserResponse dönmeli."""
    mock_user_repo.get_by_login.return_value = None

    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.login = "kaan"
    mock_user_repo.create.return_value = mock_user

    request = UserCreate(login="kaan", password="StrongPassword123")
    result = auth_service.register(request)

    assert result.id == 1
    assert result.login == "kaan"
    mock_user_repo.create.assert_called_once()


def test_register_duplicate_login_raises_error(auth_service, mock_user_repo):
    """Kullanıcı adı zaten varsa UserAlreadyExistsError fırlatmalı."""
    mock_user_repo.get_by_login.return_value = MagicMock()  # Kullanıcı zaten var

    request = UserCreate(login="kaan", password="StrongPassword123")
    with pytest.raises(UserAlreadyExistsError):
        auth_service.register(request)


def test_login_success(auth_service, mock_user_repo):
    """Geçerli kullanıcı ve şifre ile TokenResponse dönmeli."""
    from app.core.security import hash_password

    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.login = "kaan"
    mock_user.password_hash = hash_password("CorrectPassword123")
    mock_user_repo.get_by_login.return_value = mock_user

    token_data = auth_service.login(login="kaan", password="CorrectPassword123")

    assert token_data.access_token is not None
    assert token_data.token_type == "bearer"


def test_login_user_not_found_raises_error(auth_service, mock_user_repo):
    """Kullanıcı bulunamadığında InvalidCredentialsError fırlatmalı."""
    mock_user_repo.get_by_login.return_value = None

    with pytest.raises(InvalidCredentialsError):
        auth_service.login(login="nonexistent", password="AnyPassword123")


def test_login_wrong_password_raises_error(auth_service, mock_user_repo):
    """Şifre yanlış olduğunda InvalidCredentialsError fırlatmalı."""
    from app.core.security import hash_password

    mock_user = MagicMock()
    mock_user.login = "kaan"
    mock_user.password_hash = hash_password("RealPassword123")
    mock_user_repo.get_by_login.return_value = mock_user

    with pytest.raises(InvalidCredentialsError):
        auth_service.login(login="kaan", password="WrongPassword123")