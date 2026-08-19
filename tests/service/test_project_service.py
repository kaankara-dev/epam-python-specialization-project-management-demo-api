import pytest
from app.model.user import User
from app.model.enums import ProjectRole
from app.schema.project import ProjectCreate, ProjectMemberAdd
from app.repository.project import ProjectRepository
from app.service.project import ProjectService
from app.exception.project import ProjectPermissionDeniedError, ProjectNotFoundError


@pytest.fixture
def project_service(test_database):
    repo = ProjectRepository()
    return ProjectService(project_repo=repo)


@pytest.fixture
def owner_user(test_database):
    return User.create(login="kaan_owner", password_hash="hash1")


@pytest.fixture
def member_user(test_database):
    return User.create(login="kaan_member", password_hash="hash2")


@pytest.fixture
def outsider_user(test_database):
    return User.create(login="kaan_outsider", password_hash="hash3")


def test_create_project_auto_assigns_owner(test_database, project_service, owner_user):
    """Proje oluşturulduğunda oluşturan kişi otomatik olarak OWNER üye olmalıdır."""
    data = ProjectCreate(name="Cloud Projesi", description="Test Açıklaması")
    project_dto = project_service.create_project(data=data, current_user_id=owner_user.id)

    assert project_dto.id is not None
    assert project_dto.name == "Cloud Projesi"
    assert project_dto.created_by_id == owner_user.id

    # Repository üzerinden OWNER üyeliğini doğrulayalım
    member = project_service.project_repo.get_member(project_id=project_dto.id, user_id=owner_user.id)
    assert member is not None
    assert member.role == ProjectRole.OWNER


def test_add_member_by_owner_success(test_database, project_service, owner_user, member_user):
    """Proje sahibi (OWNER) projeye başarıyla yeni üye ekleyebilmelidir."""
    project_dto = project_service.create_project(
        data=ProjectCreate(name="Takım Projesi"),
        current_user_id=owner_user.id
    )

    member_data = ProjectMemberAdd(user_id=member_user.id, role=ProjectRole.PARTICIPANT)
    project_service.add_member(
        project_id=project_dto.id,
        member_data=member_data,
        current_user_id=owner_user.id
    )

    member = project_service.project_repo.get_member(project_id=project_dto.id, user_id=member_user.id)
    assert member is not None
    assert member.role == ProjectRole.PARTICIPANT


def test_add_member_by_non_owner_forbidden(test_database, project_service, owner_user, member_user, outsider_user):
    """Owner olmayan biri üye eklemeye çalışırsa ProjectPermissionDeniedError fırlatılmalıdır."""
    project_dto = project_service.create_project(
        data=ProjectCreate(name="Gizli Proje"),
        current_user_id=owner_user.id
    )

    member_data = ProjectMemberAdd(user_id=outsider_user.id, role=ProjectRole.PARTICIPANT)

    with pytest.raises(ProjectPermissionDeniedError):
        project_service.add_member(
            project_id=project_dto.id,
            member_data=member_data,
            current_user_id=member_user.id  # Yetkisiz kişi
        )


def test_add_member_to_non_existent_project_raises_error(test_database, project_service, owner_user, member_user, outsider_user):
    non_existent_project_id = 999
    member_data = ProjectMemberAdd(user_id=outsider_user.id, role=ProjectRole.PARTICIPANT)
    with pytest.raises(ProjectNotFoundError):
        project_service.add_member(
            project_id=non_existent_project_id,
            member_data=member_data,
            current_user_id=member_user.id
        )