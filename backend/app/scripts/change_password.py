import asyncio
import getpass
import os

from sqlalchemy import select

from app.core.time import utc_now
from app.db import async_session_factory
from app.models import User, UserSession
from app.scripts.create_admin import read_username
from app.security.crypto import hash_password


async def change_password() -> None:
    username = read_username()
    password = os.getenv("ADMIN_PASSWORD") or getpass.getpass("New password: ")
    if len(password) < 12:
        raise SystemExit("Password must contain at least 12 characters.")
    async with async_session_factory() as session:
        user = await session.scalar(select(User).where(User.username == username).with_for_update())
        if not user:
            raise SystemExit("User not found.")
        user.password_hash = hash_password(password)
        sessions = (
            await session.scalars(
                select(UserSession).where(
                    UserSession.user_id == user.id,
                    UserSession.revoked_at.is_(None),
                )
            )
        ).all()
        for item in sessions:
            item.revoked_at = utc_now()
        await session.commit()
    print("Password changed; active sessions revoked.")


if __name__ == "__main__":
    asyncio.run(change_password())
