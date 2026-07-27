from datetime import timedelta

import pytest

from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.exception.security import InvalidAccessTokenError


def test_hash_and_verify_password():
    plain_password = "StrongPassword123!"

    hashed_password = hash_password(plain_password)

    assert hashed_password != plain_password
    assert verify_password(plain_password, hashed_password) is True
    assert verify_password("WrongPassword", hashed_password) is False


def test_create_and_decode_access_token_returns_subject():
    subject = "377"
    token = create_access_token(subject)
    decoded_subject = decode_access_token(token)
    assert subject == decoded_subject


def test_decode_invalid_access_token_raises_error():
    with pytest.raises(InvalidAccessTokenError):
        decode_access_token("invalid-token")


def test_decode_expired_access_token_raises_error():
    token = create_access_token("expired",
                                timedelta(seconds=-1))

    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(token)

@pytest.mark.parametrize("subject", [None, "", "   "])
def test_create_access_token_with_invalid_subject_raises_value_error(subject):
    with pytest.raises(ValueError):
        create_access_token(subject)