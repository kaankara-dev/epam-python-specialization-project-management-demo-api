import pytest
from pydantic import ValidationError
from datetime import datetime, timezone
from app.schema.document import (
    DocumentCreateRequest,
    DocumentUploadResponse,
    DocumentResponse,
)


def test_document_create_request_valid():
    """Geçerli dosya adı ve MIME type kabul edilmeli."""
    data = {"file_name": "mimari_dokuman.pdf", "mime_type": "application/pdf"}
    doc = DocumentCreateRequest(**data)
    assert doc.file_name == "mimari_dokuman.pdf"
    assert doc.mime_type == "application/pdf"


@pytest.mark.parametrize("invalid_name", ["", "   "])
def test_document_create_request_empty_filename(invalid_name):
    """Boş dosya adı verildiğinde hata fırlatmalı."""
    with pytest.raises(ValidationError):
        DocumentCreateRequest(file_name=invalid_name, mime_type="application/pdf")


def test_document_upload_response_defaults():
    """Presigned URL yanıtında expires_in_seconds varsayılan 300 saniye olmalı."""
    res = DocumentUploadResponse(
        document_id=1,
        upload_url="https://s3.amazonaws.com/bucket/key?signature=xyz",
        s3_key="projects/1/mimari.pdf"
    )
    assert res.expires_in_seconds == 300
    assert res.document_id == 1


def test_document_response_serialization():
    """DocumentResponse'un tüm alanları doğru taşımalı (download_url opsiyonel)."""
    now = datetime.now(timezone.utc)
    res = DocumentResponse(
        id=1,
        project_id=10,
        uploaded_by_id=2,
        file_name="plan.docx",
        s3_key="projects/10/plan.docx",
        file_size_bytes=1048576,
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        download_url="https://s3.amazonaws.com/download-link",
        created_at=now,
    )
    assert res.file_size_bytes == 1048576
    assert res.download_url is not None