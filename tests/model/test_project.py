import pytest
from peewee import IntegrityError
from app.model.user import User
from app.model.project import Project, ProjectMember
from app.model.enums import ProjectRole


def test_project_and_member_can_be_persisted(test_database):
    # 1. Önce projeyi açacak bir kullanıcı oluşturalım
    owner_user = User.create(login="kaan_owner", password_hash="hash123")

    # 2. Projeyi oluşturalım
    project = Project.create(
        name="Cloud Native Microservice",
        description="AWS Entegrasyonlu Proje",
        created_by=owner_user
    )

    assert project.id is not None
    assert project.created_by.login == "kaan_owner"

    # 3. İkinci bir kullanıcı ve üyelik oluşturalım
    member_user = User.create(login="kaan_member", password_hash="hash456")
    membership = ProjectMember.create(
        project=project,
        user=member_user,
        role=ProjectRole.PARTICIPANT
    )

    assert membership.id is not None
    assert membership.role == ProjectRole.PARTICIPANT


def test_project_member_unique_constraint(test_database):
    """Aynı kullanıcı aynı projeye iki kez eklenemez."""
    user = User.create(login="unique_test_user", password_hash="hash123")
    project = Project.create(name="Proje 1", created_by=user)

    # İlk ekleme başarılı olmalı
    ProjectMember.create(project=project, user=user, role=ProjectRole.PARTICIPANT)

    # İkinci eklemede Unique constraint patlamalı (IntegrityError)
    with pytest.raises(IntegrityError):
        ProjectMember.create(project=project, user=user, role=ProjectRole.PARTICIPANT)


def test_project_and_member_creation(test_database):
    """Proje ve üye kaydı veritabanına başarıyla yazılabilmeli."""
    owner = User.create(login="owner_usr", password_hash="hash1")
    project = Project.create(
        name="Backend Core",
        description="Core API",
        created_by=owner
    )

    assert project.id is not None
    assert project.created_by.login == "owner_usr"

    member_user = User.create(login="member_usr", password_hash="hash2")
    membership = ProjectMember.create(
        project=project,
        user=member_user,
        role=ProjectRole.PARTICIPANT
    )

    assert membership.id is not None
    assert membership.role == ProjectRole.PARTICIPANT


def test_project_member_unique_together(test_database):
    """Aynı kullanıcı aynı projeye iki defa eklenemez."""
    user = User.create(login="usr_dup", password_hash="hash1")
    project = Project.create(name="Proje", created_by=user)

    ProjectMember.create(project=project, user=user, role=ProjectRole.PARTICIPANT)

    with pytest.raises(IntegrityError):
        ProjectMember.create(project=project, user=user, role=ProjectRole.PARTICIPANT)


def test_project_cascade_delete_with_user(test_database):
    """Projeyi oluşturan kullanıcı silindiğinde proje de CASCADE ile silinmeli."""
    user = User.create(login="temp_owner", password_hash="hash1")
    project = Project.create(name="Silinecek Proje", created_by=user)
    proj_id = project.id

    user.delete_instance()

    # Proje artık DB'de bulunamamalı
    assert Project.get_or_none(Project.id == proj_id) is None