import hashlib
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy import select

from app.core.time import utc_now
from app.exceptions import AppError
from app.models import (
    AttendanceEvent,
    Event,
    QrToken,
    Registration,
    ScanAttempt,
    SourceStudent,
    User,
)
from app.models.enums import AttendanceType, EventStatus, PresenceStatus, QrPurpose, QrStatus
from app.schemas.operator import ScanRequest, ScanResponse
from app.security.crypto import token_hash
from app.security.dependencies import SessionDep, require_operator
from app.services.qr import issue_qr
from app.settings import settings

router = APIRouter(prefix="/operator", tags=["operator"])


@router.post("/scans", response_model=ScanResponse)
async def scan(
    payload: ScanRequest,
    request: Request,
    session: SessionDep,
    user: Annotated[User, Depends(require_operator)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=100)],
) -> ScanResponse:
    fingerprint = hashlib.sha256(payload.model_dump_json().encode()).hexdigest()
    previous = await session.scalar(
        select(ScanAttempt).where(
            ScanAttempt.operator_id == user.id, ScanAttempt.idempotency_key == idempotency_key
        )
    )
    if previous:
        if previous.request_fingerprint != fingerprint:
            raise AppError("IDEMPOTENCY_CONFLICT", "Ключ уже использован для другого запроса", 409)
        if previous.response_data:
            return ScanResponse.model_validate(previous.response_data)
        raise AppError(previous.error_code or "SCAN_REJECTED", "Сканирование уже обработано", 409)
    event = await session.scalar(
        select(Event)
        .where(Event.status == EventStatus.ACTIVE, Event.scanning_enabled.is_(True))
        .order_by(Event.starts_at.desc())
        .limit(1)
    )
    if not event:
        raise AppError("EVENT_SCANNING_DISABLED", "Сканирование отключено", 409)
    qr = await session.scalar(
        select(QrToken)
        .where(QrToken.token_hash == token_hash(payload.token, settings.qr_pepper))
        .with_for_update()
    )
    if not qr:
        session.add(
            ScanAttempt(
                event_id=event.id,
                operator_id=user.id,
                result="ERROR",
                error_code="QR_INVALID",
                request_id=request.state.request_id,
                idempotency_key=idempotency_key,
                request_fingerprint=fingerprint,
                occurred_at=utc_now(),
                device_info=payload.device_info,
            )
        )
        await session.commit()
        raise AppError("QR_INVALID", "QR-код недействителен", 400)
    registration = await session.scalar(
        select(Registration).where(Registration.id == qr.registration_id).with_for_update()
    )
    if not registration or registration.event_id != event.id or registration.revoked_at:
        raise AppError("REGISTRATION_REVOKED", "Регистрация отозвана", 410)
    error_code = None
    if qr.status != QrStatus.ACTIVE:
        error_code = "QR_ALREADY_USED" if qr.status == QrStatus.USED else "QR_REVOKED"
    elif qr.expires_at <= utc_now():
        qr.status, error_code = QrStatus.EXPIRED, "QR_EXPIRED"
    expected_purpose = (
        QrPurpose.ENTRY
        if registration.presence_status == PresenceStatus.OUTSIDE
        else QrPurpose.EXIT
    )
    if not error_code and qr.purpose != expected_purpose:
        error_code = "PRESENCE_STATE_MISMATCH"
    if error_code:
        session.add(
            ScanAttempt(
                event_id=event.id,
                operator_id=user.id,
                qr_token_id=qr.id,
                registration_id=registration.id,
                result="ERROR",
                error_code=error_code,
                request_id=request.state.request_id,
                idempotency_key=idempotency_key,
                request_fingerprint=fingerprint,
                occurred_at=utc_now(),
                device_info=payload.device_info,
            )
        )
        await session.commit()
        raise AppError(error_code, "QR-код нельзя использовать", 409)
    now = utc_now()
    previous_status = registration.presence_status
    new_status = PresenceStatus.INSIDE if qr.purpose == QrPurpose.ENTRY else PresenceStatus.OUTSIDE
    event_type = AttendanceType(qr.purpose.value)
    attendance = AttendanceEvent(
        event_id=event.id,
        registration_id=registration.id,
        operator_id=user.id,
        qr_token_id=qr.id,
        event_type=event_type,
        previous_status=previous_status,
        new_status=new_status,
        occurred_at=now,
        request_id=request.state.request_id,
        device_info=payload.device_info,
        created_at=now,
    )
    registration.presence_status, registration.last_activity_at = new_status, now
    qr.status, qr.used_at, qr.used_by_operator_id = QrStatus.USED, now, user.id
    session.add(attendance)
    if new_status == PresenceStatus.INSIDE:
        await issue_qr(session, registration, QrPurpose.EXIT)
    student = await session.get(SourceStudent, registration.source_student_id)
    if not student:
        raise AppError("STUDENT_NOT_FOUND", "Запись студента не найдена", 409)
    result = ScanResponse(
        result="SUCCESS",
        full_name=student.full_name,
        study_group=student.study_group,
        institute=student.institute,
        event_type=event_type,
        previous_status=previous_status,
        new_status=new_status,
        occurred_at=now,
        request_id=request.state.request_id,
    )
    session.add(
        ScanAttempt(
            event_id=event.id,
            operator_id=user.id,
            qr_token_id=qr.id,
            registration_id=registration.id,
            result="SUCCESS",
            request_id=request.state.request_id,
            idempotency_key=idempotency_key,
            request_fingerprint=fingerprint,
            response_data=result.model_dump(mode="json"),
            occurred_at=now,
            device_info=payload.device_info,
        )
    )
    await session.commit()
    return result


@router.get("/scans/recent")
async def recent_scans(
    session: SessionDep, user: Annotated[User, Depends(require_operator)], limit: int = 20
) -> dict[str, object]:
    attempts = (
        await session.scalars(
            select(ScanAttempt)
            .where(ScanAttempt.operator_id == user.id)
            .order_by(ScanAttempt.occurred_at.desc())
            .limit(min(limit, 50))
        )
    ).all()
    return {
        "items": [
            {
                "id": item.id,
                "result": item.result,
                "error_code": item.error_code,
                "occurred_at": item.occurred_at,
                "response": item.response_data,
            }
            for item in attempts
        ]
    }
