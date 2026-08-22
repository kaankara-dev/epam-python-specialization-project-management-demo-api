from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.model.enums import InvitationStatus


class InvitationCreateRequest(BaseModel):
    """Kullanıcının davet gönderirken yolladığı gövde."""
    invited_login: str = Field(min_length=3, max_length=100)

    model_config = ConfigDict(str_strip_whitespace=True)


class InvitationResponse(BaseModel):
    """API'den döneceğimiz güvenli davet DTO'su."""
    id: int
    project_id: int
    invited_login: str
    token: str
    status: InvitationStatus
    created_at: datetime
    expired_at: datetime

    model_config = ConfigDict(from_attributes=True)