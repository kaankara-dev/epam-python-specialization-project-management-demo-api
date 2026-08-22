from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.exception.invitation import (
    InvitationExpiredError,
    InvitationInvalidStatusError,
    InvitationNotFoundError,
    UserNotFoundError,
)
from app.exception.project import (
    ProjectNotFoundError,
    ProjectPermissionDeniedError,
    UserAlreadyMemberError,
)
from app.model.enums import InvitationStatus, ProjectRole
from app.repository.invitation import InvitationRepository
from app.repository.project import ProjectRepository
from app.repository.user import UserRepository
from app.schema.invitation import InvitationResponse
from app.schema.project import ProjectResponse


class InvitationService:
    def __init__(
        self,
        invitation_repo: InvitationRepository | None = None,
        project_repo: ProjectRepository | None = None,
        user_repo: UserRepository | None = None,
    ) -> None:
        self.invitation_repo = invitation_repo or InvitationRepository()
        self.project_repo = project_repo or ProjectRepository()
        self.user_repo = user_repo or UserRepository()

    def invite_user(
        self,
        project_id: int,
        invited_login: str,
        current_user_id: int,
    ) -> InvitationResponse:
        # 1. Projeyi bul, yoksa -> ProjectNotFoundError
        project = self.project_repo.get_by_id(project_id)
        if not project:
            raise ProjectNotFoundError(f"Project {project_id} not found")

        # 2. İşlemi yapan kişi OWNER mı? (project_repo.get_member kontrolü)
        member = self.project_repo.get_member(project_id=project_id, user_id=current_user_id)
        if not member or member.role != ProjectRole.OWNER.value:
            raise ProjectPermissionDeniedError("Sadece proje sahibi davet gönderebilir.")

        # 3. Davet edilen kullanıcı sistemde kayıtlı mı? (user_repo.get_by_login)
        target_user = self.user_repo.get_by_login(invited_login)
        if not target_user:
            raise UserNotFoundError(f"Kullanıcı '{invited_login}' bulunamadı.")

        # 4. Davet edilen kişi zaten projede üye mi? (project_repo.get_member)
        existing_membership = self.project_repo.get_member(project_id=project_id, user_id=target_user.id)
        if existing_membership:
            raise UserAlreadyMemberError("Bu kullanıcı zaten projenin bir üyesi.")

        # 5. Token üret (uuid4().hex), expire süresini 24 saat sonraya ayarla
        token = uuid4().hex
        expired_at = datetime.now(timezone.utc) + timedelta(hours=24)

        # 6. DB'ye kaydet ve InvitationResponse DTO'su olarak dön
        invitation = self.invitation_repo.create(
            project_id=project_id,
            invited_login=invited_login,
            token=token,
            expired_at=expired_at,
        )
        return InvitationResponse.model_validate(invitation)

    def accept_invitation(
        self,
        token: str,
        current_user_id: int,
    ) -> ProjectResponse:
        # 1. Token ile daveti bul, yoksa -> InvitationNotFoundError
        invitation = self.invitation_repo.get_by_token(token)
        if not invitation:
            raise InvitationNotFoundError("Geçersiz veya bulunamayan davet token'ı.")

        # 2. Davet PENDING durumunda mı? Değilse -> InvitationInvalidStatusError
        if invitation.status != InvitationStatus.PENDING.value:
            raise InvitationInvalidStatusError("Bu davet zaten kullanılmış veya iptal edilmiş.")

        # 3. Süresi dolmuş mu? (datetime.now(timezone.utc) > expired_at) -> InvitationExpiredError
        now = datetime.now(timezone.utc)
        # SQLite timezone farkını engellemek için naive/aware uyumu:
        expired_at = invitation.expired_at.replace(tzinfo=timezone.utc) if invitation.expired_at.tzinfo is None else invitation.expired_at
        if now > expired_at:
            raise InvitationExpiredError("Davetiyenin geçerlilik süresi dolmuş.")

        # 4. Daveti kabul etmeye çalışan kişi davet edilen kişi mi?
        current_user = self.user_repo.get_by_id(current_user_id)
        if not current_user or current_user.login != invitation.invited_login:
            raise ProjectPermissionDeniedError("Bu davet sizin hesabınıza ait değil.")

        # 5. Kullanıcıyı projeye PARTICIPANT olarak ekle (project_repo.add_member)
        self.project_repo.add_member(
            project_id=invitation.project.id,
            user_id=current_user.id,
            role=ProjectRole.PARTICIPANT,
        )

        # 6. Davet statüsünü ACCEPTED yap
        self.invitation_repo.update_status(invitation, InvitationStatus.ACCEPTED)

        # 7. Proje detayını ProjectResponse olarak dön
        project = self.project_repo.get_by_id(invitation.project.id)
        return ProjectResponse.model_validate(project)