"""Theme preference service — reads/writes user_theme in example_schema."""
import logging
import os
from typing import Literal

from sqlalchemy import String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Mapped, mapped_column

from app.features.database.base import Base
from app.features.theme.models import ThemeResponse, ThemeValue

logger = logging.getLogger(__name__)

# Only apply named schema when running against PostgreSQL.
# SQLite (used in tests) does not support named schemas.
_db_url = os.getenv("DATABASE_URL", "")
_schema = "example_schema" if "postgresql" in _db_url else None


class UserTheme(Base):
    """ORM model matching the user_theme table created by the NestJS migrations."""

    __tablename__ = "user_theme"
    __table_args__ = ({"schema": _schema} if _schema else {})

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    theme: Mapped[str] = mapped_column(
        String(10), nullable=False, server_default="dark"
    )


async def get_theme(user_id: str, session: AsyncSession) -> ThemeResponse:
    """Return the stored theme for a user, creating a default if absent."""
    result = await session.execute(
        select(UserTheme).where(UserTheme.user_id == user_id)
    )
    row: UserTheme | None = result.scalar_one_or_none()

    if row is None:
        logger.info("No theme found for user %s, creating default", user_id)
        row = UserTheme(user_id=user_id, theme="dark")
        session.add(row)
        await session.flush()

    return ThemeResponse(theme=row.theme, userId=row.user_id)  # type: ignore[arg-type]


async def update_theme(
    user_id: str, theme: ThemeValue, session: AsyncSession
) -> ThemeResponse:
    """Upsert the theme preference for a user."""
    result = await session.execute(
        select(UserTheme).where(UserTheme.user_id == user_id)
    )
    row: UserTheme | None = result.scalar_one_or_none()

    if row is None:
        row = UserTheme(user_id=user_id, theme=theme)
        session.add(row)
    else:
        row.theme = theme

    await session.flush()
    return ThemeResponse(theme=row.theme, userId=row.user_id)  # type: ignore[arg-type]
