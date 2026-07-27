from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Header, Request, Response
from sqlalchemy import select

from app.core.time import utc_now
from app.exceptions import AppError, AuthenticationError
from app.models import User, UserSession
from app.schemas.auth import AuthResponse, LoginRequest, UserResponse
from app.security.crypto import create_access_token, random_token, token_hash, verify_password
from app.security.dependencies import SessionDep, get_current_user
from app.services.audit import add_audit
from app.services.rate_limit import enforce_rate_limit
from app.settings import settings

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        "refresh_token",
        token,
        max_age=settings.refresh_token_days * 86400,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="strict",
        path="/api/v1/auth",
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: LoginRequest, request: Request, response: Response, session: SessionDep
) -> AuthResponse:
    client = request.client.host if request.client else "unknown"
    enforce_rate_limit(
        f"login:{client}:{payload.username.casefold()}",
        settings.login_rate_limit,
        settings.login_rate_limit_window_seconds,
    )
    user = await session.scalar(select(User).where(User.username == payload.username))
    if not user or not user.is_active or not verify_password(user.password_hash, payload.password):
        raise AuthenticationError("Неверный логин или пароль")
    now, refresh, csrf = utc_now(), random_token(), random_token(24)
    staff_session = UserSession(
        user_id=user.id,
        token_hash=token_hash(refresh),
        csrf_token_hash=token_hash(csrf),
        expires_at=now + timedelta(days=settings.refresh_token_days),
        created_at=now,
        last_used_at=now,
        ip_address=client,
        user_agent=request.headers.get("user-agent", "")[:300],
    )
    session.add(staff_session)
    user.last_login_at = now
    await session.flush()
    add_audit(session, request, "AUTH_LOGIN", "UserSession", str(staff_session.id), user.id)
    await session.commit()
    _set_refresh_cookie(response, refresh)
    return AuthResponse(
        access_token=create_access_token(str(user.id), user.role.value, str(staff_session.id)),
        expires_in=settings.access_token_minutes * 60,
        csrf_token=csrf,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=AuthResponse)
async def refresh(
    request: Request,
    response: Response,
    session: SessionDep,
    refresh_token: Annotated[str | None, Cookie()] = None,
    x_csrf_token: Annotated[str | None, Header()] = None,
) -> AuthResponse:
    if not refresh_token or not x_csrf_token:
        raise AuthenticationError("Refresh-сессия отсутствует")
    staff_session = await session.scalar(
        select(UserSession)
        .where(UserSession.token_hash == token_hash(refresh_token))
        .with_for_update()
    )
    if (
        not staff_session
        or staff_session.revoked_at
        or staff_session.expires_at <= utc_now()
        or staff_session.csrf_token_hash != token_hash(x_csrf_token)
    ):
        raise AuthenticationError("Refresh-сессия недействительна")
    user = await session.get(User, staff_session.user_id)
    if not user or not user.is_active:
        raise AuthenticationError("Пользователь неактивен")
    new_refresh, new_csrf = random_token(), random_token(24)
    staff_session.token_hash = token_hash(new_refresh)
    staff_session.csrf_token_hash = token_hash(new_csrf)
    staff_session.last_used_at = utc_now()
    await session.commit()
    _set_refresh_cookie(response, new_refresh)
    return AuthResponse(
        access_token=create_access_token(str(user.id), user.role.value, str(staff_session.id)),
        expires_in=settings.access_token_minutes * 60,
        csrf_token=new_csrf,
        user=UserResponse.model_validate(user),
    )


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    response: Response,
    session: SessionDep,
    refresh_token: Annotated[str | None, Cookie()] = None,
    x_csrf_token: Annotated[str | None, Header()] = None,
) -> None:
    if refresh_token:
        staff_session = await session.scalar(
            select(UserSession)
            .where(UserSession.token_hash == token_hash(refresh_token))
            .with_for_update()
        )
        if staff_session and not staff_session.revoked_at:
            if not x_csrf_token or staff_session.csrf_token_hash != token_hash(x_csrf_token):
                raise AppError("CSRF_INVALID", "CSRF-токен недействителен", 403)
            staff_session.revoked_at = utc_now()
            add_audit(
                session,
                request,
                "AUTH_LOGOUT",
                "UserSession",
                str(staff_session.id),
                staff_session.user_id,
            )
            await session.commit()
    response.delete_cookie("refresh_token", path="/api/v1/auth")


@router.get("/me", response_model=UserResponse)
async def me(user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    return UserResponse.model_validate(user)
