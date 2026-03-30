"""
Shared pytest fixtures for the FastAPI backend test suite.

All external dependencies (Keycloak HTTP calls, PostgreSQL) are mocked so
that tests run without any running services.
"""
from __future__ import annotations

import base64
import json
import time
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def _b64url(data: bytes) -> str:
    """URL-safe base64 without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def make_access_token(
    sub: str = "user-uuid-123",
    preferred_username: str = "testuser",
    email: str = "testuser@example.com",
    given_name: str = "Test",
    family_name: str = "User",
    realm_roles: list[str] | None = None,
    client_id: str = "backend",
    exp_offset: int = 3600,
) -> str:
    """Build a minimal unsigned JWT that ``decode_user_profile`` accepts."""
    header = _b64url(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    payload = {
        "sub": sub,
        "preferred_username": preferred_username,
        "email": email,
        "given_name": given_name,
        "family_name": family_name,
        "exp": int(time.time()) + exp_offset,
        "realm_access": {"roles": realm_roles or ["user"]},
        "resource_access": {client_id: {"roles": []}},
    }
    payload_b64 = _b64url(json.dumps(payload).encode())
    signature = _b64url(b"fake-signature")
    return f"{header}.{payload_b64}.{signature}"


VALID_ACCESS_TOKEN = make_access_token()
VALID_REFRESH_TOKEN = "refresh-token-xyz"


# ---------------------------------------------------------------------------
# In-memory SQLite async engine
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def sqlite_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an in-memory SQLite async session with all ORM tables created."""
    # Import Base after app is importable so all models are registered.
    from app.features.database.base import Base
    # Import ORM models so their tables are registered with Base.metadata.
    import app.features.theme.service  # noqa: F401  – registers UserTheme

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=True)
    async with factory() as session:
        yield session

    await engine.dispose()


# ---------------------------------------------------------------------------
# FastAPI test client
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def app_client(sqlite_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Async HTTP test client backed by the FastAPI app.

    - DB dependency overridden to use the in-memory SQLite session.
    - ``init_engine`` / ``close_engine`` lifespan hooks are bypassed so no
      real Postgres connection is attempted.
    """
    from app.features.database.session import get_db_session

    async def _override_db() -> AsyncGenerator[AsyncSession, None]:
        yield sqlite_session

    # Patch out the lifespan engine calls so the app starts without Postgres.
    with (
        patch("app.features.database.engine.init_engine", new_callable=AsyncMock),
        patch("app.features.database.engine.close_engine", new_callable=AsyncMock),
    ):
        from app.main import app as fastapi_app

        fastapi_app.dependency_overrides[get_db_session] = _override_db
        transport = ASGITransport(app=fastapi_app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            yield client
        fastapi_app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def auth_cookies() -> dict[str, str]:
    """Return HTTP cookie dict with a valid (fake) access token."""
    return {"access_token": VALID_ACCESS_TOKEN}


@pytest.fixture
def auth_cookies_with_refresh() -> dict[str, str]:
    """Return HTTP cookie dict with both access and refresh tokens."""
    return {
        "access_token": VALID_ACCESS_TOKEN,
        "refresh_token": VALID_REFRESH_TOKEN,
    }
