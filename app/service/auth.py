from datetime import timedelta

from app.core.security import create_access_token, hash_password, verify_password
from app.exception.auth import InvalidCredentialsError, UserAlreadyExistsError
from app.repository.user import UserRepository
from app.schema.user import TokenResponse, UserCreate, UserResponse


class AuthService:
    def __init__(self, user_repo: UserRepository | None = None) -> None:
        self.user_repo = user_repo or UserRepository()

    def register(self, request: UserCreate) -> UserResponse:
        user = self.user_repo.get_by_login(request.login)
        if user is not None:
            raise UserAlreadyExistsError()
        hashed_password = hash_password(request.password)
        user = self.user_repo.create(login=request.login, password_hash=hashed_password)
        return UserResponse(login=user.login, id=user.id)

    def login(self, login: str, password: str) -> TokenResponse:
        user = self.user_repo.get_by_login(login)
        if user is None:
            raise InvalidCredentialsError()
        is_password_correct = verify_password(password, user.password_hash)
        if not is_password_correct:
            raise InvalidCredentialsError()
        access_token = create_access_token(subject= login, expires_delta=timedelta(hours=8))
        return TokenResponse(access_token=access_token)