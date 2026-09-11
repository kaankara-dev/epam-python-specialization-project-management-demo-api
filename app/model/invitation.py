from datetime import UTC, datetime

from peewee import CharField, DateTimeField, ForeignKeyField

from app.db.base import BaseModel
from app.model.enums import InvitationStatus
from app.model.project import Project


class Invitation(BaseModel):
    project = ForeignKeyField(Project, backref="invitations", on_delete="CASCADE")
    invited_login = CharField()
    token = CharField(unique=True)
    status = CharField(default=InvitationStatus.PENDING.value)
    created_at = DateTimeField(default=lambda: datetime.now(UTC))
    expired_at = DateTimeField()

    class Meta:
        table_name = "invitations"
        indexes = (
        (("token",), True),
        )