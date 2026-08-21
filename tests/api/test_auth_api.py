from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_auth_service
from app.exception.auth import InvalidCredentialsError, UserAlreadyExistsError
from app.main import app
from app.schema.user import TokenResponse, UserResponse


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_auth_service():
    return MagicMock()


@pytest.fixture(autouse=True)
def cleanup_overrides():
    yield
    app.dependency_overrides.clear()


# ==========================================
# 1. REGISTER ENDPOINT TESTLERİ
# ==========================================


def test_register_success(client, mock_auth_service):
    """Geçerli kullanıcı bilgisiyle 201 Created ve UserResponse dönmeli."""
    mock_auth_service.register.return_value = UserResponse(id=1, login="kaan")
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service

    payload = {"login": "kaan", "password": "StrongPassword123"}
    res = client.post("/api/v1/auth/register", json=payload)

    assert res.status_code == 201
    data = res.json()
    assert data["id"] == 1
    assert data["login"] == "kaan"


def test_register_duplicate_login_returns_409(client, mock_auth_service):
    """Zaten var olan bir kullanıcı adı ile kayıt olmaya çalışıldığında 409 Conflict dönmeli."""
    mock_auth_service.register.side_effect = UserAlreadyExistsError("User already exists")
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service

    payload = {"login": "kaan", "password": "StrongPassword123"}
    res = client.post("/api/v1/auth/register", json=payload)

    assert res.status_code == 409
    assert "User already exists" in res.json()["detail"]


# ==========================================
# 2. LOGIN ENDPOINT TESTLERİ
# ==========================================


def test_login_success(client, mock_auth_service):
    """Doğru kullanıcı adı ve şifre ile 200 OK ve TokenResponse dönmeli."""
    mock_auth_service.login.return_value = TokenResponse(
        access_token="fake_jwt_token",
        token_type="bearer",
    )
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service

    payload = {"login": "kaan", "password": "StrongPassword123"}
    res = client.post("/api/v1/auth/login", json=payload)

    assert res.status_code == 200
    data = res.json()
    assert data["access_token"] == "fake_jwt_token"
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials_returns_401(client, mock_auth_service):
    """Hatalı şifre veya kullanıcı adında 401 Unauthorized dönmeli."""
    mock_auth_service.login.side_effect = InvalidCredentialsError("Invalid credentials")
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service

    payload = {"login": "kaan", "password": "WrongPassword"}
    res = client.post("/api/v1/auth/login", json=payload)

    assert res.status_code == 401
    assert "Invalid credentials" in res.json()["detail"]