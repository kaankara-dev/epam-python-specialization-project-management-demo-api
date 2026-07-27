from pwdlib import PasswordHash
from typing import Final
from datetime import datetime, timedelta, timezone
import app.exception.security

import jwt
from jwt.exceptions import InvalidTokenError

from app.core.config import get_settings

JWT_ALGORITHM: Final[str] = "HS256"
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(subject: str) -> str:
    now = datetime.now(timezone.utc)

    settings = get_settings()

    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(
            minutes=settings.access_token_expire_minutes
        ),
    }
    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=JWT_ALGORITHM,
    )

    return token


def decode_access_token(token: str) -> str:
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["sub", "iat", "exp"]},
        )

        subject = payload["sub"]

        if not isinstance(subject, str) or not subject:
            raise app.exception.security.InvalidAccessTokenError("Invalid token subject")

        return subject

    except InvalidTokenError as exc:
        raise app.exception.security.InvalidAccessTokenError(
            "Invalid or expired access token"
        ) from exc