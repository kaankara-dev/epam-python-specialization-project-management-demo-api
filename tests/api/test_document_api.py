from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user, get_document_service
from app.exception.document import DocumentNotFoundError
from app.exception.project import ProjectNotFoundError, ProjectPermissionDeniedError
from app.main import app
from app.schema.document import DocumentResponse, DocumentUploadResponse


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_document_service():
    """Veritabanı veya AWS S3'e gitmeyen sahte DocumentService."""
    return MagicMock()


@pytest.fixture
def mock_user():
    """Sahte kullanıcı nesnesi."""
    user = MagicMock()
    user.id = 1
    user.login = "test_user"
    return user


@pytest.fixture(autouse=True)
def cleanup_overrides():
    yield
    app.dependency_overrides.clear()


# ==========================================
# 1. REQUEST UPLOAD URL ENDPOINT TESTLERİ
# ==========================================


def test_request_upload_url_unauthorized(client):
    """Token/Kullanıcı doğrulaması olmadan 401 Unauthorized dönmeli."""
    app.dependency_overrides.clear()
    payload = {"file_name": "test.pdf", "mime_type": "application/pdf"}
    res = client.post("/api/v1/projects/1/documents/upload-url", json=payload)
    assert res.status_code == 401


def test_request_upload_url_success(client, mock_user, mock_document_service):
    """Başarılı yükleme talebinde 201 Created ve S3 Presigned Upload verileri dönmeli."""
    mock_document_service.request_upload.return_value = DocumentUploadResponse(
        document_id=101,
        upload_url="https://test-bucket.s3.amazonaws.com/projects/1/uuid_test.pdf?signature=xyz",
        s3_key="projects/1/uuid_test.pdf",
        expires_in_seconds=300,
    )

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_document_service] = lambda: mock_document_service

    payload = {"file_name": "test.pdf", "mime_type": "application/pdf"}
    res = client.post("/api/v1/projects/1/documents/upload-url", json=payload)

    assert res.status_code == 201
    data = res.json()
    assert data["document_id"] == 101
    assert "upload_url" in data
    assert data["s3_key"] == "projects/1/uuid_test.pdf"
    assert data["expires_in_seconds"] == 300


def test_request_upload_url_project_not_found(client, mock_user, mock_document_service):
    """Proje bulunamadığında 404 Not Found dönmeli."""
    mock_document_service.request_upload.side_effect = ProjectNotFoundError("Proje bulunamadı")

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_document_service] = lambda: mock_document_service

    payload = {"file_name": "test.pdf", "mime_type": "application/pdf"}
    res = client.post("/api/v1/projects/9999/documents/upload-url", json=payload)

    assert res.status_code == 404
    assert "Proje bulunamadı" in res.json()["detail"]


def test_request_upload_url_forbidden(client, mock_user, mock_document_service):
    """Proje üyesi olmayan kullanıcı talep ettiğinde 403 Forbidden dönmeli."""
    mock_document_service.request_upload.side_effect = ProjectPermissionDeniedError("Projeye erişim izniniz yok")

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_document_service] = lambda: mock_document_service

    payload = {"file_name": "test.pdf", "mime_type": "application/pdf"}
    res = client.post("/api/v1/projects/1/documents/upload-url", json=payload)

    assert res.status_code == 403
    assert "Projeye erişim izniniz yok" in res.json()["detail"]


# ==========================================
# 2. GET DOWNLOAD URL ENDPOINT TESTLERİ
# ==========================================


def test_get_download_url_unauthorized(client):
    """Token/Kullanıcı doğrulaması olmadan 401 Unauthorized dönmeli."""
    app.dependency_overrides.clear()
    res = client.get("/api/v1/documents/101/download-url")
    assert res.status_code == 401


def test_get_download_url_success(client, mock_user, mock_document_service):
    """Başarılı indirme URL talebinde 200 OK ve imzalı download_url dönmeli."""
    mock_document_service.get_download_url.return_value = DocumentResponse(
        id=101,
        project_id=1,
        uploaded_by_id=mock_user.id,
        file_name="test.pdf",
        file_size_bytes=2048,
        mime_type="application/pdf",
        download_url="https://test-bucket.s3.amazonaws.com/projects/1/uuid_test.pdf?download-signature=abc",
        created_at=datetime.now(timezone.utc),
    )

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_document_service] = lambda: mock_document_service

    res = client.get("/api/v1/documents/101/download-url")

    assert res.status_code == 200
    data = res.json()
    assert data["id"] == 101
    assert data["file_name"] == "test.pdf"
    assert data["download_url"] is not None
    assert "download-signature" in data["download_url"]


def test_get_download_url_document_not_found(client, mock_user, mock_document_service):
    """Doküman bulunamadığında 404 Not Found dönmeli."""
    mock_document_service.get_download_url.side_effect = DocumentNotFoundError("Doküman bulunamadı")

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_document_service] = lambda: mock_document_service

    res = client.get("/api/v1/documents/9999/download-url")

    assert res.status_code == 404
    assert "Doküman bulunamadı" in res.json()["detail"]


def test_get_download_url_forbidden(client, mock_user, mock_document_service):
    """Dokümanın ait olduğu projede yetkisi olmayan kullanıcı için 403 Forbidden dönmeli."""
    mock_document_service.get_download_url.side_effect = ProjectPermissionDeniedError("Bu dokümanı indirme yetkiniz yok")

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_document_service] = lambda: mock_document_service

    res = client.get("/api/v1/documents/101/download-url")

    assert res.status_code == 403
    assert "Bu dokümanı indirme yetkiniz yok" in res.json()["detail"]