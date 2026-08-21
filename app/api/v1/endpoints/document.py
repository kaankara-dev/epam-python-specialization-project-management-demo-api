from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user, get_document_service
from app.exception.document import DocumentNotFoundError
from app.exception.project import ProjectNotFoundError, ProjectPermissionDeniedError
from app.model.user import User
from app.schema.document import (
    DocumentCreateRequest,
    DocumentResponse,
    DocumentUploadResponse,
)
from app.service.document import DocumentService

router = APIRouter(tags=["documents"])


@router.post(
    "/projects/{project_id}/documents/upload-url",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Request Presigned Upload URL for a Project Document",
)
def request_upload_url(
    project_id: int,
    request_data: DocumentCreateRequest,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
) -> DocumentUploadResponse:
    try:
        return document_service.request_upload(
            project_id=project_id,
            request_data=request_data,
            current_user_id=current_user.id,
        )
    except ProjectNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ProjectPermissionDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


@router.get(
    "/documents/{document_id}/download-url",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Presigned Download URL for a Document",
)
def get_download_url(
    document_id: int,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
) -> DocumentResponse:
    try:
        return document_service.get_download_url(
            document_id=document_id,
            current_user_id=current_user.id,
        )
    except DocumentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ProjectPermissionDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc