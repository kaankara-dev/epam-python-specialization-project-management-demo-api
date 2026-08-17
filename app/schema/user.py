from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    login: str = Field(..., min_length=3, max_length=100)
    model_config = ConfigDict(str_strip_whitespace=True)


class UserCreate(UserBase):
    """Kayıt olurken beklediğimiz gövde."""
    password: str = Field(min_length=8, max_length=128)


class UserResponse(UserBase):
    """API'den güvenle döneceğimiz kullanıcı modeli."""
    id: int

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Login sonrası dönülen JWT token DTO'su."""
    access_token: str
    token_type: str = "bearer"