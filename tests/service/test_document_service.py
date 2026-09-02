import pytest
from app.model.user import User
from app.model.enums import ProjectRole
from app.schema.document import DocumentCreateRequest
from app.repository.project import ProjectRepository
from app.repository.document import DocumentRepository
from app.service.auth import AuthService
from app.service.document import DocumentService
from app.exception.project import ProjectPermissionDeniedError, ProjectNotFoundError
from app.exception.document import DocumentNotFoundError


class DummyS3Client:
    """Testlerde S3'ü taklit eden sahte istemci."""

    def generate_presigned_upload_url(self, s3_key: str, mime_type: str, expires_in: int = 300) -> str:
        return f"https://s3.mock.com/{s3_key}?upload=true"

    def generate_presigned_download_url(self, s3_key: str, expires_in: int = 300) -> str:
        return f"https://s3.mock.com/{s3_key}?download=true"


@pytest.fixture
def project_repository(test_database):
    return ProjectRepository()


@pytest.fixture
def document_service(test_database, project_repository):
    return DocumentService(
        project_repo=project_repository,
        document_repo=DocumentRepository(),
        s3_client=DummyS3Client(),
    )


@pytest.fixture
def test_data(test_database, project_repository):
    owner = User.create(login="doc_owner", password_hash="hash")
    outsider = User.create(login="doc_outsider", password_hash="hash")

    project = project_repository.create(name="Secure Docs", created_by_id=owner.id)
    project_repository.add_member(project_id=project.id, user_id=owner.id, role=ProjectRole.OWNER)

    return owner, outsider, project


def test_request_upload_success(test_database, document_service, test_data):
    """Proje üyesi başarıyla dosya yükleme izni (Presigned URL) alabilmelidir."""
    owner, _, project = test_data
    req = DocumentCreateRequest(file_name="mimari.pdf", mime_type="application/pdf")

    res = document_service.request_upload(
        project_id=project.id,
        request_data=req,
        current_user_id=owner.id
    )

    assert res.document_id is not None
    assert "mimari.pdf" in res.s3_key
    assert "upload=true" in res.upload_url


def test_request_upload_forbidden_for_outsider(test_database, document_service, test_data):
    """Projeye üye olmayan kişi dosya yükleme izni istediğinde hata almalıdır."""
    _, outsider, project = test_data
    req = DocumentCreateRequest(file_name="hack.pdf", mime_type="application/pdf")

    with pytest.raises(ProjectPermissionDeniedError):
        document_service.request_upload(
            project_id=project.id,
            request_data=req,
            current_user_id=outsider.id
        )


def test_get_download_url_success(test_database, document_service, test_data):
    """Üye kullanıcı doküman için indirme linki alabilmelidir."""
    owner, _, project = test_data
    req = DocumentCreateRequest(file_name="plan.pdf", mime_type="application/pdf")
    upload_res = document_service.request_upload(project.id, req, owner.id)

    doc_res = document_service.get_download_url(
        document_id=upload_res.document_id,
        current_user_id=owner.id
    )

    assert doc_res.id == upload_res.document_id
    assert "download=true" in doc_res.download_url


def test_get_download_url_forbidden_for_outsider(test_database, document_service, test_data):
    """Projeye üye olmayan kişi dosya indirme linki istediğinde hata almalıdır."""
    owner, outsider, project = test_data
    req = DocumentCreateRequest(file_name="plan.pdf", mime_type="application/pdf")
    upload_res = document_service.request_upload(project.id, req, owner.id)

    with pytest.raises(ProjectPermissionDeniedError):
        doc_res = document_service.get_download_url(
            document_id=upload_res.document_id,
            current_user_id=outsider.id
        )


def test_get_download_url_raises_error_for_document_doesnt_exists(test_database, document_service, test_data):
    """Olmayan döküman istenildiğinde hata dönmelidir."""
    owner, outsider, project = test_data

    with pytest.raises(DocumentNotFoundError):
        doc_res = document_service.get_download_url(
            document_id=999,
            current_user_id=owner.id
        )


def test_get_documents_forbidden_for_outsider(test_database, document_service, test_data):
    """Projeye üye olmayan kişi dökümanları listelemek istediğinde hata almalıdır."""
    owner, outsider, project = test_data

    with pytest.raises(ProjectPermissionDeniedError):
        doc_res = document_service.get_documents_of_project(
            project_id=project.id,
            current_user_id=outsider.id
        )


def test_get_documents_raises_error_for_project_doesnt_exists(test_database, document_service, test_data):
    """Olmayan projenin dökümanları listelenmek istediğinde hata almalıdır."""
    owner, outsider, project = test_data

    with pytest.raises(ProjectNotFoundError):
        doc_res= document_service.get_documents_of_project(
            project_id=9999,
            current_user_id=owner.id
        )


def test_get_documents_of_project_success(test_database, document_service, test_data, project_repository):
    """Proje üyesi dökümanları listeleyebilmelidir"""
    owner, outsider, project = test_data
    member = User.create(login="doc_member", password_hash="hash")
    project_repository.add_member(project_id=project.id, user_id=member.id, role=ProjectRole.PARTICIPANT)
    docs = document_service.get_documents_of_project(project_id=project.id, current_user_id=member.id)

    assert isinstance(docs, list)
