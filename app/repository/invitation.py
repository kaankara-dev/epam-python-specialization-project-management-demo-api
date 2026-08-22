from app.model.enums import InvitationStatus
from app.model.invitation import Invitation


class InvitationRepository:
    def create(
        self,
        project_id: int,
        invited_login: str,
        token: str,
        expired_at,
    ) -> Invitation:
        return Invitation.create(
            project_id=project_id,
            invited_login=invited_login,
            token=token,
            expired_at=expired_at,
            status=InvitationStatus.PENDING.value,
        )

    def get_by_token(self, token: str) -> Invitation | None:
        return Invitation.get_or_none(Invitation.token == token)

    def get_by_id(self, invitation_id: int) -> Invitation | None:
        return Invitation.get_or_none(Invitation.id == invitation_id)

    def list_by_project(self, project_id: int) -> list[Invitation]:
        return list(Invitation.select().where(Invitation.project == project_id))

    def update_status(self, invitation: Invitation, status: InvitationStatus) -> Invitation:
        if not isinstance(status, InvitationStatus):
            raise TypeError(f"Expected InvitationStatus, got {type(status).__name__}")
        invitation.status = status.value
        invitation.save()
        return invitation