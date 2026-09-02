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


def test_list_projects_unauthorized(client):
    """Token olmadan 401 dönmeli."""
    app.dependency_overrides.clear()
    res = client.get("/api/v1/projects/")
    assert res.status_code == 401


def test_list_projects_success(client, mock_user, mock_project_service):
    """Kullanıcının projeleri 200 OK ile dönmeli."""
    mock_project_service.list_projects.return_value = [
        ProjectResponse(
            id=1, name="Proje A", description=None,
            created_by_id=mock_user.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    ]

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_project_service] = lambda: mock_project_service

    res = client.get("/api/v1/projects/")

    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["name"] == "Proje A"


def test_get_project_unauthorized(client):
    """Token olmadan 401 dönmeli."""
    app.dependency_overrides.clear()
    res = client.get("/api/v1/projects/1")
    assert res.status_code == 401


def test_get_project_success(client, mock_user, mock_project_service):
    """Üye kullanıcı proje detayına 200 OK ile ulaşmalı."""
    mock_project_service.get_project.return_value = ProjectResponse(
        id=5, name="Detay Projesi", description=None,
        created_by_id=mock_user.id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_project_service] = lambda: mock_project_service

    res = client.get("/api/v1/projects/5")

    assert res.status_code == 200
    assert res.json()["id"] == 5


def test_get_project_not_found(client, mock_user, mock_project_service):
    """Proje bulunamazsa 404 dönmeli."""
    mock_project_service.get_project.side_effect = ProjectNotFoundError("Proje bulunamadı")
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_project_service] = lambda: mock_project_service

    res = client.get("/api/v1/projects/9999")

    assert res.status_code == 404
    assert "Proje bulunamadı" in res.json()["detail"]


def test_get_project_forbidden(client, mock_user, mock_project_service):
    """Üyesi olmayan kullanıcı için 403 dönmeli."""
    mock_project_service.get_project.side_effect = ProjectPermissionDeniedError("Yetkisiz erişim")
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_project_service] = lambda: mock_project_service

    res = client.get("/api/v1/projects/5")

    assert res.status_code == 403


def test_update_project_unauthorized(client):
    app.dependency_overrides.clear()
    res = client.patch("/api/v1/projects/1", json={"name": "Fark Etmez"})
    assert res.status_code == 401


def test_update_project_success(client, mock_user, mock_project_service):
    mock_project_service.update_project.return_value = ProjectResponse(
        id=5, name="Güncel Ad", description=None,
        created_by_id=mock_user.id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_project_service] = lambda: mock_project_service

    res = client.patch("/api/v1/projects/5", json={"name": "Güncel Ad"})

    assert res.status_code == 200
    assert res.json()["name"] == "Güncel Ad"


def test_update_project_not_found(client, mock_user, mock_project_service):
    mock_project_service.update_project.side_effect = ProjectNotFoundError("Proje bulunamadı")
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_project_service] = lambda: mock_project_service

    res = client.patch("/api/v1/projects/9999", json={"name": "Fark Etmez"})

    assert res.status_code == 404


def test_update_project_forbidden(client, mock_user, mock_project_service):
    mock_project_service.update_project.side_effect = ProjectPermissionDeniedError("Yetkisiz işlem")
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_project_service] = lambda: mock_project_service

    res = client.patch("/api/v1/projects/5", json={"name": "İzinsiz"})

    assert res.status_code == 403


def test_delete_project_unauthorized(client):
    app.dependency_overrides.clear()
    res = client.delete("/api/v1/projects/1")
    assert res.status_code == 401


def test_delete_project_success(client, mock_user, mock_project_service):
    mock_project_service.delete_project.return_value = True

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_project_service] = lambda: mock_project_service

    res = client.delete("/api/v1/projects/5")

    assert res.status_code == 200
    assert res.content == b'true'


def test_delete_project_not_found(client, mock_user, mock_project_service):
    mock_project_service.delete_project.side_effect = ProjectNotFoundError("Proje bulunamadı")
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_project_service] = lambda: mock_project_service

    res = client.delete("/api/v1/projects/9999")

    assert res.status_code == 404


def test_delete_project_forbidden(client, mock_user, mock_project_service):
    mock_project_service.delete_project.side_effect = ProjectPermissionDeniedError("Yetkisiz işlem")
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_project_service] = lambda: mock_project_service

    res = client.delete("/api/v1/projects/5")

    assert res.status_code == 403