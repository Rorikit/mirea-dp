from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.time import utc_now
from app.exceptions import AppError
from app.models import QrToken, Registration
from app.models.enums import PresenceStatus, QrPurpose, QrStatus
from app.security.crypto import random_token, token_hash
from app.settings import settings


async def issue_qr(
    session: AsyncSession, registration: Registration, purpose: QrPurpose | None = None
) -> tuple[QrToken, str]:
    now = utc_now()
    desired = purpose or (
        QrPurpose.EXIT if registration.presence_status == PresenceStatus.INSIDE else QrPurpose.ENTRY
    )
    expected = (
        QrPurpose.EXIT if registration.presence_status == PresenceStatus.INSIDE else QrPurpose.ENTRY
    )
    if desired != expected:
        raise AppError("QR_PURPOSE_MISMATCH", "QR не соответствует текущему статусу", 409)
    await session.execute(
        update(QrToken)
        .where(QrToken.registration_id == registration.id, QrToken.status == QrStatus.ACTIVE)
        .values(status=QrStatus.REVOKED, revoked_at=now)
    )
    raw = random_token()
    qr = QrToken(
        registration_id=registration.id,
        token_hash=token_hash(raw, settings.qr_pepper),
        purpose=desired,
        status=QrStatus.ACTIVE,
        created_at=now,
        expires_at=now + timedelta(minutes=settings.qr_ttl_minutes),
    )
    session.add(qr)
    await session.flush()
    return qr, raw


async def active_qr(session: AsyncSession, registration_id: object) -> QrToken | None:
    result: QrToken | None = await session.scalar(
        select(QrToken)
        .where(QrToken.registration_id == registration_id, QrToken.status == QrStatus.ACTIVE)
        .order_by(QrToken.created_at.desc())
    )
    return result
