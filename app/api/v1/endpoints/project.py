from http.client import HTTPResponse
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user, get_project_service
from app.model.user import User
from app.schema.project import ProjectCreate, ProjectResponse, ProjectMemberAdd, ProjectUpdate
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


@router.get("/", response_model=list[ProjectResponse], status_code=status.HTTP_200_OK)
async def list_projects(
    current_user: Annotated[User, Depends(get_current_user)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> list[ProjectResponse]:
    """Kullanıcının üyesi olduğu projeleri listeler."""
    return project_service.list_projects(current_user_id=current_user.id)


@router.get("/{project_id}", response_model=ProjectResponse, status_code=status.HTTP_200_OK)
async def get_project(
    project_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectResponse:
    """Proje detayını döner (sadece üyeler)."""
    try:
        return project_service.get_project(project_id=project_id, current_user_id=current_user.id)
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


@router.patch("/{project_id}", response_model=ProjectResponse, status_code=status.HTTP_200_OK)
async def update_project(
        project_id: int,
        update_data: ProjectUpdate,
        current_user: Annotated[User, Depends(get_current_user)],
        project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectResponse:
    """Proje bilgilerini günceller (sadece OWNER)."""
    try:
        project = project_service.update_project(project_id=project_id, current_user_id=current_user.id)
        return project
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ProjectPermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc