from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentCreateRequest(BaseModel):
    """Kullanıcının S3 yükleme izni talep ederken yolladığı DTO."""
    file_name: str = Field(min_length=1, max_length=255)
    mime_type: str = Field(min_length=3, max_length=100)

    model_config = ConfigDict(str_strip_whitespace=True)


class DocumentUploadResponse(BaseModel):
    """S3 Presigned Upload URL dönüş DTO'su."""
    document_id: int
    upload_url: str
    s3_key: str
    expires_in_seconds: int = 300


class DocumentResponse(BaseModel):
    """Doküman listeleme/detay sorgusunda döndüğümüz güvenli DTO."""
    id: int
    project_id: int
    uploaded_by_id: int | None
    file_name: str
    file_size_bytes: int
    mime_type: str
    download_url: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

