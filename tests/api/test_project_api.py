from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user, get_project_service
from app.exception.project import ProjectNotFoundError, ProjectPermissionDeniedError
from app.main import app
from app.model.enums import ProjectRole
from app.schema.project import ProjectResponse


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_project_service():
    """Veritabanına gitmeyen sahte ProjectService."""
    return MagicMock()


@pytest.fixture
def mock_user():
    """Sahte kullanıcı nesnesi."""
    user = MagicMock()
    user.id = 1
    user.login = "test_user"
    return user


def test_create_project_unauthorized(client):
    """Token/Kullanıcı doğrulaması olmadan 401 dönmeli."""
    app.dependency_overrides.clear()
    res = client.post("/api/v1/projects/", json={"name": "Yetkisiz Proje"})
    assert res.status_code == 401


def test_create_project_success(client, mock_user, mock_project_service):
    """Başarılı proje oluşturma durumunda 201 Created ve doğru JSON dönmeli."""
    # Servisin döneceği sahte cevabı ayarlıyoruz
    mock_project_service.create_project.return_value = ProjectResponse(
        id=10,
        name="EPAM Cloud API Projesi",
        description="API Testi",
        created_by_id=mock_user.id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_project_service] = lambda: mock_project_service

    payload = {"name": "EPAM Cloud API Projesi", "description": "API Testi"}
    res = client.post("/api/v1/projects/", json=payload)

    assert res.status_code == 201
    data = res.json()
    assert data["id"] == 10
    assert data["name"] == "EPAM Cloud API Projesi"
    assert data["created_by_id"] == mock_user.id


def test_add_member_success(client, mock_user, mock_project_service):
    """Üye ekleme başarılı olduğunda 204 No Content dönmeli."""
    mock_project_service.add_member.return_value = None

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_project_service] = lambda: mock_project_service

    member_payload = {"user_id": 2, "role": "participant"}
    res = client.post("/api/v1/projects/10/members", json=member_payload)
    assert res.status_code == 204


def test_add_member_forbidden(client, mock_user, mock_project_service):
    """Yetkisiz kullanıcı işlem yaparsa 403 Forbidden dönmeli."""
    # Servis yetki hatası fırlattığında API'nin 403 döndüğünü sınıyoruz
    mock_project_service.add_member.side_effect = ProjectPermissionDeniedError("Yetkisiz işlem")

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_project_service] = lambda: mock_project_service

    member_payload = {"user_id": 99, "role": "participant"}
    res = client.post("/api/v1/projects/10/members", json=member_payload)
    assert res.status_code == 403
    assert "Yetkisiz işlem" in res.json()["detail"]


def test_add_member_not_found(client, mock_user, mock_project_service):
    """Proje bulunamadığında 404 Not Found dönmeli."""
    # Servis bulunamadı hatası fırlattığında API'nin 404 döndüğünü sınıyoruz
    mock_project_service.add_member.side_effect = ProjectNotFoundError("Proje bulunamadı")

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_project_service] = lambda: mock_project_service

    member_payload = {"user_id": 2, "role": "participant"}
    res = client.post("/api/v1/projects/9999/members", json=member_payload)
    assert res.status_code == 404
    assert "Proje bulunamadı" in res.json()["detail"]


@pytest.fixture(autouse=True)
def cleanup_overrides():
    yield
    app.dependency_overrides.clear()