from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user, get_project_service
from app.model.user import User
from app.schema.project import ProjectCreate, ProjectResponse, ProjectMemberAdd
from app.service.project import ProjectService
from app.exception.project import (
    ProjectNotFoundError,
    ProjectPermissionDeniedError,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectResponse:
    """Yeni bir proje oluşturur ve istek atan kullanıcıyı otomatik OWNER yapar."""
    return project_service.create_project(
        data=project_data,
        current_user_id=current_user.id,
    )


@router.post("/{project_id}/members", status_code=status.HTTP_204_NO_CONTENT)
async def add_project_member(
    project_id: int,
    member_data: ProjectMemberAdd,
    current_user: Annotated[User, Depends(get_current_user)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> None:
    """Projeye yeni bir katılımcı ekler (Sadece OWNER yetkilidir)."""
    try:
        project_service.add_member(
            project_id=project_id,
            member_data=member_data,
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