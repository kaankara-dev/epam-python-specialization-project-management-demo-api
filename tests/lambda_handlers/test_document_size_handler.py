import pytest

from app.lambda_handlers.document_size_handler import handler
from app.model.project import Project
from app.model.user import User
from app.repository.document import DocumentRepository


@pytest.fixture
def db_setup(test_database):
    user = User.create(login="lambda_user", password_hash="hash")
    project = Project.create(name="Lambda Test Project", created_by=user)
    return user, project


def make_s3_put_event(bucket: str, key: str, size: int) -> dict:
    """Gerçek bir AWS S3 ObjectCreated event notification yapısını taklit eder."""
    return {
        "Records": [
            {
                "eventVersion": "2.1",
                "eventSource": "aws:s3",
                "awsRegion": "eu-central-1",
                "eventName": "ObjectCreated:Put",
                "s3": {
                    "s3SchemaVersion": "1.0",
                    "bucket": {"name": bucket},
                    "object": {"key": key, "size": size, "eTag": "fake-etag"},
                },
            }
        ]
    }


def test_handler_updates_existing_document_file_size(db_setup):
    """Event'teki s3_key veritabanında eşleşiyorsa file_size_bytes güncellenmeli."""
    user, project = db_setup
    repo = DocumentRepository()
    doc = repo.create(
        project_id=project.id,
        uploaded_by_id=user.id,
        file_name="buyuk_dosya.pdf",
        s3_key="projects/1/uuid_buyuk.pdf",
        mime_type="application/pdf",
    )
    assert doc.file_size_bytes == 0

    event = make_s3_put_event(
        bucket="project-management-documents",
        key="projects/1/uuid_buyuk.pdf",
        size=5242880,
    )

    result = handler(event, context=None)

    updated_doc = repo.get_by_id(doc.id)
    assert updated_doc.file_size_bytes == 5242880
    assert result["updated"] == [doc.id]
    assert result["not_found"] == []


def test_handler_skips_unknown_s3_key_without_raising(db_setup):
    """DB'de eşleşen doküman bulunamazsa hata fırlatmadan atlanmalı."""
    event = make_s3_put_event(
        bucket="project-management-documents",
        key="projects/999/ghost.pdf",
        size=1024,
    )

    result = handler(event, context=None)

    assert result["updated"] == []
    assert result["not_found"] == ["projects/999/ghost.pdf"]


def test_handler_processes_multiple_records_in_single_event(db_setup):
    """Tek bir event içinde birden fazla Record varsa hepsi işlenmeli."""
    user, project = db_setup
    repo = DocumentRepository()
    doc1 = repo.create(
        project_id=project.id, uploaded_by_id=user.id,
        file_name="a.pdf", s3_key="projects/1/a.pdf", mime_type="application/pdf",
    )
    doc2 = repo.create(
        project_id=project.id, uploaded_by_id=user.id,
        file_name="b.pdf", s3_key="projects/1/b.pdf", mime_type="application/pdf",
    )

    event = {
        "Records": [
            make_s3_put_event("bucket", "projects/1/a.pdf", 1000)["Records"][0],
            make_s3_put_event("bucket", "projects/1/b.pdf", 2000)["Records"][0],
        ]
    }

    result = handler(event, context=None)

    assert sorted(result["updated"]) == sorted([doc1.id, doc2.id])
    assert repo.get_by_id(doc1.id).file_size_bytes == 1000
    assert repo.get_by_id(doc2.id).file_size_bytes == 2000


def test_handler_decodes_url_encoded_s3_key(db_setup):
    """Gerçek AWS S3 event'i key'i URL-encode eder (boşluk -> '+'); handler
    bunu decode edip DB'deki ham s3_key ile eşleştirebilmeli."""
    user, project = db_setup
    repo = DocumentRepository()
    doc = repo.create(
        project_id=project.id,
        uploaded_by_id=user.id,
        file_name="rapor dosyasi.pdf",
        s3_key="projects/1/uuid_rapor dosyasi.pdf",  # DB'de ham hâliyle
        mime_type="application/pdf",
    )

    # AWS'nin gerçekte göndereceği encode edilmiş event:
    event = make_s3_put_event(
        bucket="bucket",
        key="projects/1/uuid_rapor+dosyasi.pdf",  # '+' = encode edilmiş boşluk
        size=4096,
    )

    result = handler(event, context=None)

    updated_doc = repo.get_by_id(doc.id)
    assert updated_doc.file_size_bytes == 4096
    assert result["updated"] == [doc.id]
    assert result["not_found"] == []