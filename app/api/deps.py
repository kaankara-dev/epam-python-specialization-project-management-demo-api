from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import decode_access_token
from app.model.user import User
from app.service.auth import AuthService
from app.service.invitation import InvitationService
from app.service.project import ProjectService
from app.service.document import DocumentService

http_bearer = HTTPBearer()


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(http_bearer)]
) -> User:
    token = credentials.credentials
    try:
        login = decode_access_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = User.get_or_none(User.login == login)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_project_service() -> ProjectService:
    return ProjectService()


def get_document_service() -> DocumentService:
    return DocumentService()


def get_auth_service() -> AuthService:
    return AuthService()


def get_invitation_service() -> InvitationService:
    return InvitationService()