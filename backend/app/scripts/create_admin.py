import asyncio
import getpass
import os
import re

from sqlalchemy import select

from app.db import async_session_factory
from app.models import User
from app.models.enums import UserRole
from app.security.crypto import hash_password

USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{3,64}$")


def read_username() -> str:
    # Docker Desktop's Windows TTY may corrupt input after a non-ASCII prompt.
    username = (os.getenv("ADMIN_USERNAME") or input("Admin username: ")).strip()
    if not USERNAME_PATTERN.fullmatch(username):
        raise SystemExit("Username must contain 3-64 Latin letters, digits, '.', '_' or '-'.")
    return username


async def create_admin() -> None:
    username = read_username()
    password = os.getenv("ADMIN_PASSWORD") or getpass.getpass("Password (at least 12 characters): ")
    if len(password) < 12:
        raise SystemExit("Password must contain at least 12 characters.")
    async with async_session_factory() as session:
        if await session.scalar(select(User.id).where(User.username == username)):
            raise SystemExit("User already exists.")
        session.add(
            User(
                username=username,
                password_hash=hash_password(password),
                role=UserRole.ADMIN,
                is_active=True,
            )
        )
        await session.commit()
    print("Administrator created.")


if __name__ == "__main__":
    asyncio.run(create_admin())
