import hashlib
import hmac
import secrets
from datetime import timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.time import utc_now
from app.settings import settings

password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def random_token(bytes_count: int = 32) -> str:
    return secrets.token_urlsafe(bytes_count)


def token_hash(token: str, pepper: str | None = None) -> str:
    key = (pepper or settings.secret_key).encode()
    return hmac.new(key, token.encode(), hashlib.sha256).hexdigest()


def create_access_token(subject: str, role: str, session_id: str) -> str:
    now = utc_now()
    payload = {
        "sub": subject,
        "role": role,
        "sid": session_id,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_minutes),
        "type": "access",
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def create_lookup_token(student_id: str, event_id: str) -> str:
    now = utc_now()
    return jwt.encode(
        {
            "sub": student_id,
            "event_id": event_id,
            "iat": now,
            "exp": now + timedelta(minutes=5),
            "type": "lookup",
        },
        settings.secret_key,
        algorithm="HS256",
    )


def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError("Неверный тип токена")
    return payload
