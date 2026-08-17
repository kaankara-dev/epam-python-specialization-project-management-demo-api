import pytest
from peewee import IntegrityError
from app.model.user import User
from app.model.project import Project
from app.model.document import Document


def test_document_creation(test_database):
    """Doküman başarıyla kaydedilmeli."""
    user = User.create(login="uploader", password_hash="hash")
    project = Project.create(name="Test Proje", created_by=user)

    doc = Document.create(
        project=project,
        uploaded_by=user,
        file_name="spec.pdf",
        s3_key="projects/1/spec.pdf",
        file_size_bytes=2048,
        mime_type="application/pdf"
    )

    assert doc.id is not None
    assert doc.file_name == "spec.pdf"
    assert doc.uploaded_by.login == "uploader"


def test_document_s3_key_must_be_unique(test_database):
    """Aynı S3 key ile ikinci doküman eklenemez."""
    user = User.create(login="uploader2", password_hash="hash")
    project = Project.create(name="Test Proje 2", created_by=user)

    Document.create(
        project=project,
        uploaded_by=user,
        file_name="a.pdf",
        s3_key="unique_key_123",
        mime_type="application/pdf"
    )

    with pytest.raises(IntegrityError):
        Document.create(
            project=project,
            uploaded_by=user,
            file_name="b.pdf",
            s3_key="unique_key_123",
            mime_type="application/pdf"
        )


def test_document_set_null_on_user_delete(test_database):
    """Yükleyen kullanıcı silindiğinde doküman SİLİNMEMELİ, uploaded_by alanı NULL olmalı."""
    # 1. Projenin sahibi ayrı bir kullanıcı olsun
    owner = User.create(login="project_owner", password_hash="hash")
    project = Project.create(name="Proje X", created_by=owner)

    # 2. Dokümanı yükleyen ayrı bir kullanıcı olsun
    uploader = User.create(login="temporary_uploader", password_hash="hash")
    doc = Document.create(
        project=project,
        uploaded_by=uploader,
        file_name="arsiv.pdf",
        s3_key="docs/arsiv.pdf",
        mime_type="application/pdf",
    )
    doc_id = doc.id

    # 3. Sadece yükleyen kullanıcıyı siliyoruz (Proje ve Sahibi duruyor)
    uploader.delete_instance()

    # Doküman hâlâ veritabanında olmalı ve uploaded_by None olmalı
    stored_doc = Document.get_by_id(doc_id)
    assert stored_doc is not None
    assert stored_doc.uploaded_by is None


def test_document_cascade_on_project_delete(test_database):
    """Proje silindiğinde ona ait dokümanlar da CASCADE ile silinmeli."""
    user = User.create(login="owner3", password_hash="hash")
    project = Project.create(name="Silinecek Proje", created_by=user)

    doc = Document.create(
        project=project,
        uploaded_by=user,
        file_name="temp.pdf",
        s3_key="temp/key",
        mime_type="application/pdf"
    )
    doc_id = doc.id

    project.delete_instance()

    assert Document.get_or_none(Document.id == doc_id) is None