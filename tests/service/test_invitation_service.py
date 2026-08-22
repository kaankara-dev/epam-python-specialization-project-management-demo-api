from datetime import datetime, timedelta, timezone
import pytest

from app.exception.invitation import (
    InvitationExpiredError,
    InvitationInvalidStatusError,
    InvitationNotFoundError,
    UserNotFoundError,
)
from app.exception.project import ProjectPermissionDeniedError, UserAlreadyMemberError
from app.model.enums import InvitationStatus, ProjectRole
from app.model.project import ProjectMember
from app.model.user import User
from app.repository.invitation import InvitationRepository
from app.repository.project import ProjectRepository
from app.repository.user import UserRepository
from app.schema.project import ProjectCreate
from app.service.invitation import InvitationService
from app.service.project import ProjectService


@pytest.fixture
def project_repo(test_database):
    return ProjectRepository()


@pytest.fixture
def owner_user(test_database):
    return User.create(login="kaan_owner", password_hash="hash1")


@pytest.fixture
def member_user(test_database, project, project_repo):
    user = User.create(login="kaan_member", password_hash="hash2")
    project_repo.add_member(project_id=project.id, user_id=user.id, role=ProjectRole.PARTICIPANT)
    return user


@pytest.fixture
def outsider_user(test_database):
    return User.create(login="kaan_outsider", password_hash="hash3")


@pytest.fixture
def other_outsider_user(test_database):
    return User.create(login="kaan_outsider_2", password_hash="hash4")


@pytest.fixture
def project(test_database, project_repo, owner_user):
    proj = project_repo.create(
        name="Test Projesi",
        created_by_id=owner_user.id,
        description="Test açıklaması"
    )
    # Proje sahibini ProjectMember tablosuna OWNER olarak kaydediyoruz:
    project_repo.add_member(project_id=proj.id, user_id=owner_user.id, role=ProjectRole.OWNER)
    return proj


@pytest.fixture
def invitation_service(test_database):
    return InvitationService(
        invitation_repo=InvitationRepository(),
        project_repo=ProjectRepository(),
        user_repo=UserRepository(),
    )


@pytest.fixture
def valid_invitation(test_database, invitation_service, owner_user, outsider_user, project):
    return invitation_service.invite_user(
        project_id=project.id,
        invited_login=outsider_user.login,
        current_user_id=owner_user.id,
    )


# ==========================================
# 1. DAVET GÖNDERME (INVITE) TESTLERİ
# ==========================================


def test_invite_member_by_someone_not_owner_raises_error(invitation_service, member_user, outsider_user, project):
    """Proje sahibi (OWNER) haricinde biri davet göndermeye çalışırsa 403 / Hata fırlatmalı."""
    with pytest.raises(ProjectPermissionDeniedError):
        invitation_service.invite_user(
            project_id=project.id,
            invited_login=outsider_user.login,
            current_user_id=member_user.id,
        )


def test_invite_member_does_not_exist_raises_error(invitation_service, owner_user, project):
    """Sistemde kayıtlı olmayan kullanıcı adına davet gönderilmeye çalışırsa hata oluşmalı."""
    with pytest.raises(UserNotFoundError):
        invitation_service.invite_user(
            project_id=project.id,
            invited_login="non_existing_login",
            current_user_id=owner_user.id,
        )


def test_invite_member_already_member_raises_error(invitation_service, owner_user, project):
    """Zaten projede üye olan birine davet gönderilmeye çalışırsa hata oluşmalı."""
    with pytest.raises(UserAlreadyMemberError):
        invitation_service.invite_user(
            project_id=project.id,
            invited_login=owner_user.login,
            current_user_id=owner_user.id,
        )


def test_invite_user_success(invitation_service, owner_user, outsider_user, project):
    """Başarılı davet senaryosunda token üretilmeli ve status PENDING olmalı."""
    inv = invitation_service.invite_user(
        project_id=project.id,
        invited_login=outsider_user.login,
        current_user_id=owner_user.id,
    )
    assert inv.id is not None
    assert inv.token is not None
    assert inv.status == InvitationStatus.PENDING
    assert inv.invited_login == outsider_user.login


# ==========================================
# 2. DAVETİ KABUL ETME (ACCEPT) TESTLERİ
# ==========================================


def test_accept_invitation_without_valid_token_raises_error(invitation_service, outsider_user):
    """Var olmayan bir token ile kabul edilmeye çalışıldığında InvitationNotFoundError fırlatmalı."""
    with pytest.raises(InvitationNotFoundError):
        invitation_service.accept_invitation(
            token="invalid_random_token",
            current_user_id=outsider_user.id,
        )


def test_accept_invitation_with_invalid_status_raises_error(invitation_service, valid_invitation, outsider_user):
    """Zaten kabul edilmiş (ACCEPTED) veya iptal edilmiş davet tekrar kabul edilemez."""
    # Daveti kabul ediyoruz
    invitation_service.accept_invitation(token=valid_invitation.token, current_user_id=outsider_user.id)

    # İkinci kez aynı token ile kabul etmeye çalışıyoruz -> Hata vermeli
    with pytest.raises(InvitationInvalidStatusError):
        invitation_service.accept_invitation(token=valid_invitation.token, current_user_id=outsider_user.id)


def test_accept_invitation_expired_raises_error(invitation_service, owner_user, outsider_user, project):
    """Süresi dolmuş (expired) bir token ile kabul edilmeye çalışılırsa hata vermeli."""
    # Süresi geçmiş bir davet üretiyoruz
    inv = invitation_service.invite_user(
        project_id=project.id,
        invited_login=outsider_user.login,
        current_user_id=owner_user.id,
    )
    # DB'de süresini geçmişe alıyoruz
    from app.model.invitation import Invitation
    db_inv = Invitation.get_by_id(inv.id)
    db_inv.expired_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db_inv.save()

    with pytest.raises(InvitationExpiredError):
        invitation_service.accept_invitation(token=inv.token, current_user_id=outsider_user.id)


def test_accept_invitation_someone_else_tries_accept_raises_error(
    invitation_service, valid_invitation, other_outsider_user
):
    """Davetiyenin sahibi olmayan başka bir kullanıcı kabul etmeye kalkarsa 403 fırlatmalı."""
    with pytest.raises(ProjectPermissionDeniedError):
        invitation_service.accept_invitation(
            token=valid_invitation.token,
            current_user_id=other_outsider_user.id,
        )


def test_accept_invitation_success_flow(invitation_service, valid_invitation, outsider_user, project):
    """Başarılı kabul akışında: Kullanıcı PARTICIPANT olarak projeye eklenmeli ve status ACCEPTED olmalı."""
    result = invitation_service.accept_invitation(
        token=valid_invitation.token,
        current_user_id=outsider_user.id,
    )

    # Dönen nesne proje detayı olmalı
    assert result.id == project.id

    # DB kontrolü: Kullanıcı artık projenin üyesi mi?
    member = ProjectMember.get_or_none(
        ProjectMember.project == project.id,
        ProjectMember.user == outsider_user.id,
    )
    assert member is not None
    assert member.role == ProjectRole.PARTICIPANT.value