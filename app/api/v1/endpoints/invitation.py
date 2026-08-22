from fastapi import APIRouter, Depends, HTTPException, status
from peewee import Model

from app.api.deps import get_current_user, get_invitation_service
from app.exception.invitation import (
    InvitationExpiredError,
    InvitationInvalidStatusError,
    InvitationNotFoundError,
    UserNotFoundError,
)
from app.exception.project import (
    ProjectNotFoundError,
    ProjectPermissionDeniedError,
    UserAlreadyMemberError,
)
from app.model.user import User
from app.schema.invitation import InvitationCreateRequest, InvitationResponse
from app.schema.project import ProjectResponse
from app.service.invitation import InvitationService

router = APIRouter(tags=["invitations"])


@router.post(
    "/projects/{project_id}/invitations",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invite a user to the project",
)
def invite_user(
    project_id: int,
    request_data: InvitationCreateRequest,
    current_user: User = Depends(get_current_user),
    invitation_service: InvitationService = Depends(get_invitation_service),
) -> InvitationResponse:
    try:
        return invitation_service.invite_user(project_id=project_id, invited_login=request_data.invited_login, current_user_id=current_user.id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ProjectPermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except UserAlreadyMemberError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post(
    "/invitations/{token}/accept",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Accept project invitation using token",
)
def accept_invitation(
    token: str,
    current_user: User = Depends(get_current_user),
    invitation_service: InvitationService = Depends(get_invitation_service),
) -> ProjectResponse:
    try:
        return invitation_service.accept_invitation(token=token, current_user_id=current_user.id)
    except InvitationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvitationInvalidStatusError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except InvitationExpiredError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ProjectPermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc