from datetime import datetime, timedelta, timezone
import pytest

from app.model.enums import InvitationStatus, ProjectRole
from app.model.project import Project, ProjectMember
from app.model.user import User
from app.repository.invitation import InvitationRepository


@pytest.fixture
def invitation_repo():
    return InvitationRepository()


@pytest.fixture
def owner_user(test_database):
    return User.create(login="owner_inviter", password_hash="hash123")


@pytest.fixture
def sample_project(owner_user):
    project = Project.create(
        name="Architecture Hub",
        description="Demo",
        created_by=owner_user,
    )
    ProjectMember.create(project=project, user=owner_user, role=ProjectRole.OWNER)
    return project


def test_create_invitation(test_database, invitation_repo, sample_project):
    """Repository başarıyla yeni bir davet oluşturmalı."""
    expires = datetime.now(timezone.utc) + timedelta(hours=24)
    inv = invitation_repo.create(
        project_id=sample_project.id,
        invited_login="candidate_dev",
        token="token-abc-123",
        expired_at=expires,
    )

    assert inv.id is not None
    assert inv.project.id == sample_project.id
    assert inv.invited_login == "candidate_dev"
    assert inv.token == "token-abc-123"
    assert inv.status == InvitationStatus.PENDING.value


def test_get_by_token(test_database, invitation_repo, sample_project):
    """Token ile sorgulama yapıldığında doğru davet dönmeli."""
    expires = datetime.now(timezone.utc) + timedelta(hours=24)
    created = invitation_repo.create(
        project_id=sample_project.id,
        invited_login="candidate_dev",
        token="unique-token-999",
        expired_at=expires,
    )

    found = invitation_repo.get_by_token("unique-token-999")
    assert found is not None
    assert found.id == created.id
    assert found.invited_login == "candidate_dev"


def test_get_by_token_not_found(test_database, invitation_repo):
    """Olmayan token sorgulandığında None dönmeli."""
    assert invitation_repo.get_by_token("non-existent-token") is None


def test_list_by_project(test_database, invitation_repo, sample_project):
    """Bir projeye ait tüm davetler listelenebilmeli."""
    expires = datetime.now(timezone.utc) + timedelta(hours=24)
    invitation_repo.create(sample_project.id, "user1", "token-1", expires)
    invitation_repo.create(sample_project.id, "user2", "token-2", expires)

    invitations = invitation_repo.list_by_project(sample_project.id)
    assert len(invitations) == 2


def test_update_status(test_database, invitation_repo, sample_project):
    """Davetin statüsü güncellenebilmeli (ACCEPTED / REVOKED)."""
    expires = datetime.now(timezone.utc) + timedelta(hours=24)
    inv = invitation_repo.create(sample_project.id, "user1", "token-status", expires)

    updated = invitation_repo.update_status(inv, InvitationStatus.ACCEPTED.value)
    assert updated.status == InvitationStatus.ACCEPTED.value