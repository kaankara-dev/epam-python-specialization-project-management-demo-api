import pytest
from app.model.user import User
from app.model.project import Project
from app.repository.document import DocumentRepository


@pytest.fixture
def db_setup(test_database):
    user = User.create(login="kaan_doc_user", password_hash="hash")
    project = Project.create(name="Doc Project", created_by=user)
    return user, project


def test_create_and_get_document(db_setup):
    user, project = db_setup
    repo = DocumentRepository()

    doc = repo.create(
        project_id=project.id,
        uploaded_by_id=user.id,
        file_name="mimari.pdf",
        s3_key="projects/1/uuid_mimari.pdf",
        mime_type="application/pdf"
    )

    assert doc.id is not None
    assert doc.file_name == "mimari.pdf"

    fetched = repo.get_by_id(doc.id)
    assert fetched is not None
    assert fetched.id == doc.id
    assert fetched.project.id == project.id


def test_list_by_project(db_setup):
    user, project = db_setup
    repo = DocumentRepository()

    repo.create(
        project_id=project.id,
        uploaded_by_id=user.id,
        file_name="doc1.pdf",
        s3_key="k1",
        mime_type="application/pdf"
    )
    repo.create(
        project_id=project.id,
        uploaded_by_id=user.id,
        file_name="doc2.pdf",
        s3_key="k2",
        mime_type="application/pdf"
    )

    docs = repo.list_by_project(project.id)
    assert len(docs) == 2


def test_delete_document(db_setup):
    user, project = db_setup
    repo = DocumentRepository()

    doc = repo.create(
        project_id=project.id,
        uploaded_by_id=user.id,
        file_name="silinecek.pdf",
        s3_key="k_sil",
        mime_type="application/pdf"
    )

    assert repo.delete(doc.id) is True
    assert repo.get_by_id(doc.id) is None