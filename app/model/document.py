from datetime import datetime, timezone
from enum import unique

from peewee import CharField, BigIntegerField, DateTimeField, ForeignKeyField

from app.db.base import BaseModel
from app.model.project import Project
from app.model.user import User


class Document(BaseModel):
    project = ForeignKeyField(Project, backref="documents", on_delete="CASCADE")
    uploaded_by = ForeignKeyField(User, backref="uploaded_documents", on_delete="SET NULL", null=True)
    file_name = CharField(max_length=255)
    s3_key = CharField(max_length=512, unique=True)
    file_size_bytes = BigIntegerField(default= 0)
    mime_type = CharField(max_length=100)
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    class Meta:
        table_name = "documents"