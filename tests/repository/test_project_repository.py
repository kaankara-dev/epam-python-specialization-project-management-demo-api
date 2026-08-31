import pytest
from app.model.user import User
from app.model.enums import ProjectRole
from app.repository.project import ProjectRepository


@pytest.fixture
def sample_user(test_database):
    return User.create(login="kaan_repo_user", password_hash="hash123")


def test_create_and_get_project(test_database, sample_user):
    """Proje oluşturulabilmeli ve ID ile sorgulanabilmeli."""
    repo = ProjectRepository()
    project = repo.create(
        name="Microservice Projesi",
        description="Açıklama",
        created_by_id=sample_user.id
    )

    assert project.id is not None
    assert project.name == "Microservice Projesi"

    fetched = repo.get_by_id(project.id)
    assert fetched is not None
    assert fetched.id == project.id


def test_add_and_get_member(test_database, sample_user):
    """Projeye üye eklenebilmeli ve üyelik rolü sorgulanabilmeli."""
    repo = ProjectRepository()
    project = repo.create(name="Proje 1", created_by_id=sample_user.id)

    other_user = User.create(login="other_user", password_hash="hash")
    member = repo.add_member(
        project_id=project.id,
        user_id=other_user.id,
        role=ProjectRole.PARTICIPANT
    )

    assert member.id is not None
    assert member.role == ProjectRole.PARTICIPANT

    fetched_member = repo.get_member(project_id=project.id, user_id=other_user.id)
    assert fetched_member is not None
    assert fetched_member.role == ProjectRole.PARTICIPANT


def test_delete_project(test_database, sample_user):
    """Proje başarıyla silinebilmeli."""
    repo = ProjectRepository()
    project = repo.create(name="Silinecek Proje", created_by_id=sample_user.id)

    deleted = repo.delete(project.id)
    assert deleted is True

    assert repo.get_by_id(project.id) is None


def test_list_by_user_returns_only_memberships(test_database, sample_user):
    """Kullanıcı sadece üyesi olduğu projeleri görmeli."""
    repo = ProjectRepository()

    my_project = repo.create(name="Benim Projem", created_by_id=sample_user.id)
    repo.add_member(project_id=my_project.id, user_id=sample_user.id, role=ProjectRole.OWNER)

    other_user = User.create(login="baska_user", password_hash="hash")
    other_project = repo.create(name="Başkasının Projesi", created_by_id=other_user.id)
    repo.add_member(project_id=other_project.id, user_id=other_user.id, role=ProjectRole.OWNER)

    result = repo.list_by_user(user_id=sample_user.id)

    assert len(result) == 1
    assert result[0].id == my_project.id


def test_list_by_user_empty_when_no_membership(test_database, sample_user):
    """Hiç üyeliği olmayan kullanıcı için boş liste dönmeli."""
    repo = ProjectRepository()
    assert repo.list_by_user(user_id=sample_user.id) == []