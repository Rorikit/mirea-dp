from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.time import utc_now
from app.db import get_session
from app.exceptions import AuthenticationError, PermissionDenied
from app.models import Registration, StudentSession, User, UserSession
from app.models.enums import UserRole
from app.security.crypto import decode_token, token_hash

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(
    session: SessionDep, authorization: Annotated[str | None, Header()] = None
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthenticationError()
    try:
        payload = decode_token(authorization[7:], "access")
        user_id, session_id = UUID(payload["sub"]), UUID(payload["sid"])
    except (jwt.InvalidTokenError, KeyError, ValueError) as exc:
        raise AuthenticationError("Сессия недействительна") from exc
    user = await session.scalar(select(User).where(User.id == user_id, User.is_active.is_(True)))
    staff_session = await session.scalar(
        select(UserSession).where(
            UserSession.id == session_id,
            UserSession.user_id == user_id,
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > utc_now(),
        )
    )
    if not user or not staff_session:
        raise AuthenticationError("Сессия завершена")
    return user


async def require_operator(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role not in (UserRole.OPERATOR, UserRole.ADMIN):
        raise PermissionDenied()
    return user


async def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != UserRole.ADMIN:
        raise PermissionDenied()
    return user


async def get_student_registration(request: Request, session: SessionDep) -> Registration:
    raw = request.cookies.get("student_session")
    if not raw:
        raise AuthenticationError("Требуется студенческая сессия")
    student_session = await session.scalar(
        select(StudentSession).where(
            StudentSession.token_hash == token_hash(raw),
            StudentSession.revoked_at.is_(None),
            StudentSession.expires_at > utc_now(),
        )
    )
    if not student_session:
        raise AuthenticationError("Студенческая сессия завершена")
    registration = await session.get(Registration, student_session.registration_id)
    if not registration or registration.revoked_at:
        raise AuthenticationError("Регистрация отозвана")
    return registration
