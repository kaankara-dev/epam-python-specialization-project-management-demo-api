from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user, get_invitation_service
from app.exception.invitation import (
    InvitationExpiredError,
    InvitationNotFoundError,
    UserNotFoundError, InvitationInvalidStatusError,
)
from app.exception.project import ProjectPermissionDeniedError, UserAlreadyMemberError
from app.main import app
from app.model.enums import InvitationStatus
from app.schema.invitation import InvitationResponse
from app.schema.project import ProjectResponse


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_invitation_service():
    return MagicMock()


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = 1
    user.login = "kaan_owner"
    return user


@pytest.fixture(autouse=True)
def cleanup_overrides():
    yield
    app.dependency_overrides.clear()


# ==========================================
# 1. INVITE USER ENDPOINT TESTLERİ
# ==========================================


def test_invite_user_unauthorized(client):
    """Giriş yapılmadan davet atılırsa 401 dönmeli."""
    app.dependency_overrides.clear()
    res = client.post("/api/v1/projects/1/invitations", json={"invited_login": "dev1"})
    assert res.status_code == 401


def test_invite_user_success(client, mock_user, mock_invitation_service):
    """Başarılı davet isteğinde 201 Created ve InvitationResponse dönmeli."""
    mock_invitation_service.invite_user.return_value = InvitationResponse(
        id=10,
        project_id=1,
        invited_login="dev1",
        token="uuid-token-xyz",
        status=InvitationStatus.PENDING,
        created_at=datetime.now(timezone.utc),
        expired_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_invitation_service] = lambda: mock_invitation_service

    res = client.post("/api/v1/projects/1/invitations", json={"invited_login": "dev1"})
    assert res.status_code == 201
    data = res.json()
    assert data["id"] == 10
    assert data["token"] == "uuid-token-xyz"
    assert data["status"] == "PENDING"


def test_invite_user_forbidden(client, mock_user, mock_invitation_service):
    """Proje sahibi olmayan davet etmeye çalışırsa 403 Forbidden dönmeli."""
    mock_invitation_service.invite_user.side_effect = ProjectPermissionDeniedError("Yetkisiz işlem")
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_invitation_service] = lambda: mock_invitation_service

    res = client.post("/api/v1/projects/1/invitations", json={"invited_login": "dev1"})
    assert res.status_code == 403


def test_invite_user_not_found(client, mock_user, mock_invitation_service):
    """Sistemde kayıtlı olmayan kullanıcı davet edilirse 404 dönmeli."""
    mock_invitation_service.invite_user.side_effect = UserNotFoundError("Kullanıcı bulunamadı")
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_invitation_service] = lambda: mock_invitation_service

    res = client.post("/api/v1/projects/1/invitations", json={"invited_login": "ghost"})
    assert res.status_code == 404


def test_invite_user_already_member_conflict(client, mock_user, mock_invitation_service):
    """Zaten üye olan kullanıcı davet edilirse 409 Conflict dönmeli."""
    mock_invitation_service.invite_user.side_effect = UserAlreadyMemberError("Zaten üye")
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_invitation_service] = lambda: mock_invitation_service

    res = client.post("/api/v1/projects/1/invitations", json={"invited_login": "existing_user"})
    assert res.status_code == 409


# ==========================================
# 2. ACCEPT INVITATION ENDPOINT TESTLERİ
# ==========================================


def test_accept_invitation_success(client, mock_user, mock_invitation_service):
    """Geçerli token ile kabul edildiğinde 200 OK ve ProjectResponse dönmeli."""
    mock_invitation_service.accept_invitation.return_value = ProjectResponse(
        id=1,
        name="Architecture Project",
        description="Demo",
        created_by_id=mock_user.id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_invitation_service] = lambda: mock_invitation_service

    res = client.post("/api/v1/invitations/uuid-token-xyz/accept")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == 1
    assert data["name"] == "Architecture Project"


def test_accept_invitation_not_found(client, mock_user, mock_invitation_service):
    """Geçersiz token için 404 Not Found dönmeli."""
    mock_invitation_service.accept_invitation.side_effect = InvitationNotFoundError("Token bulunamadı")
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_invitation_service] = lambda: mock_invitation_service

    res = client.post("/api/v1/invitations/invalid-token/accept")
    assert res.status_code == 404


def test_accept_invitation_expired(client, mock_user, mock_invitation_service):
    """Süresi dolmuş token için 400 Bad Request dönmeli."""
    mock_invitation_service.accept_invitation.side_effect = InvitationExpiredError("Süre doldu")
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_invitation_service] = lambda: mock_invitation_service

    res = client.post("/api/v1/invitations/expired-token/accept")
    assert res.status_code == 400


def test_accept_invitation_unauthorized(client):
    """Giriş yapılmadan davet kabul edilmeye çalışılırsa 401 Unauthorized dönmeli."""
    app.dependency_overrides.clear()
    res = client.post("/api/v1/invitations/some-token/accept")
    assert res.status_code == 401


def test_accept_invitation_invalid_status(client, mock_user, mock_invitation_service):
    """Daha önce kullanılmış veya iptal edilmiş davet için 400 Bad Request dönmeli."""
    mock_invitation_service.accept_invitation.side_effect = InvitationInvalidStatusError("Bu davet daha önce kullanılmış.")
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_invitation_service] = lambda: mock_invitation_service

    res = client.post("/api/v1/invitations/already-used-token/accept")
    assert res.status_code == 400
    assert "Bu davet daha önce kullanılmış." in res.json()["detail"]


def test_accept_invitation_forbidden(client, mock_user, mock_invitation_service):
    """Başkasının adına olan davet kabul edilmeye çalışıldığında 403 Forbidden dönmeli."""
    mock_invitation_service.accept_invitation.side_effect = ProjectPermissionDeniedError("Bu davet sizin hesabınıza ait değil.")
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_invitation_service] = lambda: mock_invitation_service

    res = client.post("/api/v1/invitations/other-user-token/accept")
    assert res.status_code == 403
    assert "Bu davet sizin hesabınıza ait değil." in res.json()["detail"]