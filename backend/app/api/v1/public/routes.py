from datetime import timedelta
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.time import utc_now
from app.exceptions import AppError
from app.models import (
    Event,
    MapAsset,
    Registration,
    ScheduleItem,
    SourceStudent,
    StudentSession,
)
from app.models.enums import EventStatus, QrStatus
from app.schemas.public import (
    LookupResponse,
    QrCreateRequest,
    QrResponse,
    RegistrationCreateRequest,
    RegistrationLookupRequest,
    StudentProfileResponse,
)
from app.security.crypto import create_lookup_token, decode_token, random_token, token_hash
from app.security.dependencies import SessionDep, get_student_registration
from app.services.normalization import normalize_group, normalize_name
from app.services.qr import active_qr, issue_qr
from app.services.rate_limit import enforce_rate_limit
from app.settings import settings

router = APIRouter(prefix="/public", tags=["public"])


def _profile(registration: Registration, qr: QrResponse | None = None) -> StudentProfileResponse:
    student = registration.source_student
    return StudentProfileResponse(
        public_id=registration.public_id,
        full_name=student.full_name,
        study_group=student.study_group,
        institute=student.institute,
        presence_status=registration.presence_status,
        qr=qr,
    )


@router.get("/events/{event_slug}")
async def public_event(event_slug: str, session: SessionDep) -> dict[str, object]:
    event = await session.scalar(select(Event).where(Event.slug == event_slug))
    if not event:
        raise AppError("EVENT_NOT_FOUND", "Мероприятие не найдено", 404)
    return {
        "id": event.id,
        "name": event.name,
        "slug": event.slug,
        "starts_at": event.starts_at,
        "ends_at": event.ends_at,
        "timezone": event.timezone,
        "registration_enabled": event.registration_enabled,
        "scanning_enabled": event.scanning_enabled,
    }


@router.post("/registrations/lookup", response_model=LookupResponse)
async def lookup(
    payload: RegistrationLookupRequest, request: Request, session: SessionDep
) -> LookupResponse:
    client = request.client.host if request.client else "unknown"
    enforce_rate_limit(f"lookup:{client}", 5, 60)
    event = await session.scalar(
        select(Event).where(
            Event.slug == payload.event_slug,
            Event.registration_enabled.is_(True),
            Event.status == EventStatus.ACTIVE,
        )
    )
    if not event:
        raise AppError(
            "REGISTRATION_NOT_FOUND_OR_AMBIGUOUS",
            "Данные не найдены или неоднозначны. Обратитесь к организаторам",
            404,
        )
    students = (
        await session.scalars(
            select(SourceStudent)
            .where(
                SourceStudent.event_id == event.id,
                SourceStudent.normalized_full_name == normalize_name(payload.full_name),
                SourceStudent.normalized_study_group == normalize_group(payload.study_group),
                SourceStudent.is_active.is_(True),
            )
            .limit(2)
        )
    ).all()
    if len(students) != 1:
        raise AppError(
            "REGISTRATION_NOT_FOUND_OR_AMBIGUOUS",
            "Данные не найдены или неоднозначны. Обратитесь к организаторам",
            404,
        )
    return LookupResponse(
        lookup_token=create_lookup_token(str(students[0].id), str(event.id)),
        expires_at=utc_now() + timedelta(minutes=5),
    )


@router.post("/registrations", response_model=StudentProfileResponse)
async def register(
    payload: RegistrationCreateRequest, request: Request, response: Response, session: SessionDep
) -> StudentProfileResponse:
    enforce_rate_limit(f"register:{request.client.host if request.client else 'unknown'}", 3, 60)
    try:
        claims = decode_token(payload.lookup_token, "lookup")
        student_id, event_id = UUID(claims["sub"]), UUID(claims["event_id"])
    except (jwt.InvalidTokenError, KeyError, ValueError) as exc:
        raise AppError(
            "LOOKUP_TOKEN_INVALID", "Результат поиска истёк. Повторите поиск", 409
        ) from exc
    student = await session.scalar(
        select(SourceStudent)
        .where(
            SourceStudent.id == student_id,
            SourceStudent.event_id == event_id,
            SourceStudent.is_active.is_(True),
        )
        .with_for_update()
    )
    if not student:
        raise AppError("REGISTRATION_NOT_AVAILABLE", "Регистрация недоступна", 409)
    registration = await session.scalar(
        select(Registration)
        .where(Registration.event_id == event_id, Registration.source_student_id == student_id)
        .with_for_update()
    )
    if not registration:
        registration = Registration(
            event_id=event_id, source_student_id=student_id, registered_at=utc_now()
        )
        session.add(registration)
        await session.flush()
    registration.source_student = student
    if registration.revoked_at:
        raise AppError("REGISTRATION_REVOKED", "Регистрация отозвана", 410)
    qr, raw_qr = await issue_qr(session, registration)
    raw_session = random_token()
    session.add(
        StudentSession(
            registration_id=registration.id,
            token_hash=token_hash(raw_session),
            expires_at=utc_now() + timedelta(days=settings.student_session_days),
            created_at=utc_now(),
        )
    )
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise AppError("REGISTRATION_CONFLICT", "Повторите регистрацию", 409) from exc
    response.set_cookie(
        "student_session",
        raw_session,
        max_age=settings.student_session_days * 86400,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="strict",
        path="/api/v1/public",
    )
    return _profile(
        registration, QrResponse(token=raw_qr, purpose=qr.purpose, expires_at=qr.expires_at)
    )


@router.get("/registrations/me", response_model=StudentProfileResponse)
async def registration_me(
    registration: Annotated[Registration, Depends(get_student_registration)], session: SessionDep
) -> StudentProfileResponse:
    await session.refresh(registration, ["source_student"])
    current = await active_qr(session, registration.id)
    if current and current.expires_at <= utc_now():
        current.status = QrStatus.EXPIRED
        await session.commit()
    return _profile(registration)


@router.post("/registrations/me/qr", response_model=QrResponse)
async def registration_qr(
    payload: QrCreateRequest,
    registration: Annotated[Registration, Depends(get_student_registration)],
    session: SessionDep,
) -> QrResponse:
    qr, raw = await issue_qr(session, registration, payload.purpose)
    await session.commit()
    return QrResponse(token=raw, purpose=qr.purpose, expires_at=qr.expires_at)


@router.get("/schedule")
async def schedule(session: SessionDep, event_slug: Annotated[str, Query()]) -> dict[str, object]:
    event = await session.scalar(select(Event).where(Event.slug == event_slug))
    if not event:
        raise AppError("EVENT_NOT_FOUND", "Мероприятие не найдено", 404)
    items = (
        await session.scalars(
            select(ScheduleItem)
            .where(ScheduleItem.event_id == event.id, ScheduleItem.is_published.is_(True))
            .order_by(ScheduleItem.starts_at, ScheduleItem.display_order)
        )
    ).all()
    return {
        "server_time": utc_now(),
        "timezone": event.timezone,
        "items": [
            {
                "id": item.id,
                "title": item.title,
                "description": item.description,
                "location": item.location,
                "starts_at": item.starts_at,
                "ends_at": item.ends_at,
            }
            for item in items
        ],
    }


@router.get("/map")
async def event_map(session: SessionDep, event_slug: Annotated[str, Query()]) -> dict[str, object]:
    event = await session.scalar(select(Event).where(Event.slug == event_slug))
    asset = (
        await session.scalar(
            select(MapAsset).where(MapAsset.event_id == event.id, MapAsset.is_active.is_(True))
        )
        if event
        else None
    )
    if not asset:
        raise AppError("MAP_NOT_FOUND", "Карта пока не опубликована", 404)
    return {
        "url": f"/api/v1/public/map/{asset.id}/file",
        "width": asset.width,
        "height": asset.height,
        "sha256": asset.file_hash,
    }


@router.get("/map/{asset_id}/file", response_class=FileResponse)
async def map_file(asset_id: UUID, session: SessionDep) -> FileResponse:
    asset = await session.scalar(
        select(MapAsset).where(MapAsset.id == asset_id, MapAsset.is_active.is_(True))
    )
    if not asset:
        raise AppError("MAP_NOT_FOUND", "Карта не найдена", 404)
    return FileResponse(
        asset.storage_path,
        media_type=asset.mime_type,
        headers={"Cache-Control": "public, max-age=31536000, immutable", "ETag": asset.file_hash},
    )
