import asyncio
from datetime import timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.core.time import utc_now
from app.db import Base, async_session_factory
from app.main import app
from app.models import Event, SourceStudent, User
from app.models.enums import EventStatus, UserRole
from app.security.crypto import hash_password


@pytest.fixture(autouse=True)
async def clean_database() -> None:
    table_names = ", ".join(f'"{table.name}"' for table in reversed(Base.metadata.sorted_tables))
    async with async_session_factory() as session:
        await session.execute(text(f"TRUNCATE {table_names} CASCADE"))
        await session.commit()


@pytest.mark.asyncio
async def test_registration_and_concurrent_scan() -> None:
    now = utc_now()
    async with async_session_factory() as session:
        event = Event(
            name="Тестовое мероприятие",
            slug="integration-event",
            starts_at=now - timedelta(hours=1),
            ends_at=now + timedelta(hours=8),
            timezone="Europe/Moscow",
            status=EventStatus.ACTIVE,
            registration_enabled=True,
            scanning_enabled=True,
        )
        operator = User(
            username="operator",
            password_hash=hash_password("Надёжный пароль 2026!"),
            role=UserRole.OPERATOR,
            is_active=True,
        )
        session.add_all([event, operator])
        await session.flush()
        session.add(
            SourceStudent(
                event_id=event.id,
                source_id="001",
                full_name="Иванов Иван Иванович",
                normalized_full_name="иванов иван иванович",
                study_group="ИКБО-11-26",
                normalized_study_group="ИКБО-11-26",
                institute="ИИИ",
                normalized_institute="иии",
                is_active=True,
            )
        )
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as student_client:
        lookup = await student_client.post(
            "/api/v1/public/registrations/lookup",
            json={
                "event_slug": "integration-event",
                "full_name": "  Иванов   Иван Иванович ",
                "study_group": "икбо-11-26",
            },
        )
        assert lookup.status_code == 200
        registration = await student_client.post(
            "/api/v1/public/registrations",
            json={"lookup_token": lookup.json()["lookup_token"]},
            headers={"Idempotency-Key": "registration-test-key"},
        )
        assert registration.status_code == 200
        qr_token = registration.json()["qr"]["token"]

    async with AsyncClient(transport=transport, base_url="http://test") as operator_client:
        login = await operator_client.post(
            "/api/v1/auth/login",
            json={"username": "operator", "password": "Надёжный пароль 2026!"},
        )
        assert login.status_code == 200
        authorization = {"Authorization": f"Bearer {login.json()['access_token']}"}
        first, second = await asyncio.gather(
            operator_client.post(
                "/api/v1/operator/scans",
                json={"token": qr_token},
                headers={**authorization, "Idempotency-Key": "scan-concurrent-1"},
            ),
            operator_client.post(
                "/api/v1/operator/scans",
                json={"token": qr_token},
                headers={**authorization, "Idempotency-Key": "scan-concurrent-2"},
            ),
        )
    assert sorted((first.status_code, second.status_code)) == [200, 409]
    rejected = first if first.status_code == 409 else second
    assert rejected.json()["error"]["code"] == "QR_ALREADY_USED"

    async with async_session_factory() as session:
        attendance_count = await session.scalar(text("SELECT count(*) FROM attendance_events"))
        assert attendance_count == 1
