from typing import Any
from uuid import UUID

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.time import utc_now
from app.models import AuditLog


def add_audit(
    session: AsyncSession,
    request: Request,
    action: str,
    object_type: str,
    object_id: str | None,
    user_id: UUID | None,
    changes: dict[str, Any] | None = None,
) -> None:
    session.add(
        AuditLog(
            user_id=user_id,
            action=action,
            object_type=object_type,
            object_id=object_id,
            changes=changes,
            request_id=request.state.request_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent", "")[:300],
            occurred_at=utc_now(),
        )
    )
