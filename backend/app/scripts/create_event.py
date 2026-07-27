import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.db import async_session_factory
from app.models import Event
from app.models.enums import EventStatus

SLUG = "freshman-day-2026"


async def create_event() -> None:
    timezone = ZoneInfo("Europe/Moscow")
    async with async_session_factory() as session:
        if await session.scalar(select(Event.id).where(Event.slug == SLUG)):
            print("Мероприятие уже существует")
            return
        session.add(
            Event(
                name="День первокурсника РТУ МИРЭА 2026",
                slug=SLUG,
                starts_at=datetime(2026, 9, 1, 8, 0, tzinfo=timezone),
                ends_at=datetime(2026, 9, 1, 22, 0, tzinfo=timezone),
                timezone="Europe/Moscow",
                status=EventStatus.ACTIVE,
                registration_enabled=True,
                scanning_enabled=True,
            )
        )
        await session.commit()
    print("Мероприятие создано")


if __name__ == "__main__":
    asyncio.run(create_event())
