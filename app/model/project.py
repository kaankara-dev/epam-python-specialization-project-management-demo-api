from datetime import  datetime, timezone

from peewee import CharField, TextField, DateTimeField, ForeignKeyField, CompositeKey

from app.db.base import BaseModel
from app.model.user import User
from app.model.enums import ProjectRole


class Project(BaseModel):
    name = CharField(max_length=150, index=True)
    description = TextField(null=True)
    created_by = ForeignKeyField(User, backref="created_projects", on_delete="CASCADE")
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    updated_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    class Meta:
        table_name = "projects"


class ProjectMember(BaseModel):
    project = ForeignKeyField(Project, backref="members", on_delete="CASCADE")
    user = ForeignKeyField(User, backref="project_memberships", on_delete="CASCADE")
    role = CharField(max_length=20, default=ProjectRole.PARTICIPANT)
    joined_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    class Meta:
        table_name = "project_members"
        indexes = (
        (("project", "user"), True),
        )