from datetime import datetime, timedelta, timezone
import pytest
from peewee import IntegrityError

from app.model.enums import InvitationStatus, ProjectRole
from app.model.invitation import Invitation
from app.model.project import Project, ProjectMember
from app.model.user import User


@pytest.fixture
def owner_user(test_database):
    return User.create(login="project_owner", password_hash="hash123")


@pytest.fixture
def sample_project(owner_user):
    project = Project.create(
        name="Security Architecture",
        description="Demo",
        created_by=owner_user,
    )
    ProjectMember.create(
        project=project,
        user=owner_user,
        role=ProjectRole.OWNER,
    )
    return project


def test_create_invitation_success(test_database, sample_project):
    """Davet oluşturulduğunda varsayılan status PENDING olmalı ve alanlar doğru kaydedilmeli."""
    expires = datetime.now(timezone.utc) + timedelta(hours=24)
    invitation = Invitation.create(
        project=sample_project,
        invited_login="new_member",
        token="secure-random-uuid-12345",
        expired_at=expires,
    )

    assert invitation.id is not None
    assert invitation.project.id == sample_project.id
    assert invitation.invited_login == "new_member"
    assert invitation.token == "secure-random-uuid-12345"
    assert invitation.status == InvitationStatus.PENDING.value
    assert invitation.created_at is not None


def test_invitation_token_unique_constraint(test_database, sample_project):
    """Aynı token ile ikinci bir davet oluşturulmaya çalışıldığında IntegrityError fırlatmalı."""
    expires = datetime.now(timezone.utc) + timedelta(hours=24)
    Invitation.create(
        project=sample_project,
        invited_login="user1",
        token="duplicate-token-xyz",
        expired_at=expires,
    )

    with pytest.raises(IntegrityError):
        Invitation.create(
            project=sample_project,
            invited_login="user2",
            token="duplicate-token-xyz",
            expired_at=expires,
        )


def test_cascade_delete_with_project(test_database, sample_project):
    """Proje silindiğinde ona bağlı tüm davetler de CASCADE ile silinmeli."""
    expires = datetime.now(timezone.utc) + timedelta(hours=24)
    Invitation.create(
        project=sample_project,
        invited_login="user1",
        token="token-to-delete",
        expired_at=expires,
    )

    assert Invitation.select().count() == 1

    # Projeyi siliyoruz
    sample_project.delete_instance(recursive=True)

    # Davet de silinmiş olmalı
    assert Invitation.select().count() == 0