from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.model.enums import ProjectRole


class ProjectBase(BaseModel):
    # Proje adı zorunlu olsun, en az 3, en fazla 150 karakter olsun.
    # Açıklama (description) opsiyonel olsun ve varsayılanı None olsun.
    name: str = Field(..., min_length=3, max_length=150, description="Proje adı")
    description: str | None = Field(default=None, max_length=1000)


class ProjectCreate(ProjectBase):
    """Proje oluştururken istemciden (client) beklediğimiz gövde."""
    pass


class ProjectUpdate(BaseModel):
    """Proje güncellerken alanlar opsiyonel olmalı (Partial update)."""
    name: str | None = Field(default=None, min_length=3, max_length=150)
    description: str | None = Field(default=None, max_length=1000)


class ProjectMemberAdd(BaseModel):
    """Projeye katılımcı ekleme şeması."""
    user_id: int = Field()
    role: ProjectRole = Field(default=ProjectRole.PARTICIPANT)


class ProjectResponse(ProjectBase):
    """API'den kullanıcıya döneceğimiz güvenli proje çıktısı."""
    id: int
    created_by_id: int
    created_at: datetime
    updated_at: datetime

    # Peewee ORM nesnelerini Pydantic modeline çevirebilmesi için:
    model_config = ConfigDict(from_attributes=True)