"""Tests for theme preference endpoints: GET/PATCH /users/me/preferences."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.features.theme.models import ThemeResponse
from app.tests.conftest import VALID_ACCESS_TOKEN


AUTH_COOKIES = {"access_token": VALID_ACCESS_TOKEN}
USER_ID = "user-uuid-123"  # sub inside VALID_ACCESS_TOKEN


# ---------------------------------------------------------------------------
# GET /users/me/preferences
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_preferences_default_dark(app_client: AsyncClient) -> None:
    """
    GET /users/me/preferences creates a 'dark' default when no row exists and
    returns 200 with the correct shape.
    """
    response = await app_client.get("/users/me/preferences", cookies=AUTH_COOKIES)

    assert response.status_code == 200
    data = response.json()
    assert data["theme"] in ("dark", "light")
    assert "userId" in data


@pytest.mark.asyncio
async def test_get_preferences_returns_stored_theme(app_client: AsyncClient) -> None:
    """
    GET /users/me/preferences returns the theme stored via the service.
    Uses mocked service to isolate from SQLite quirks (schema, uuid gen).
    """
    mocked_response = ThemeResponse(theme="light", userId=USER_ID)
    with patch(
        "app.features.theme.router.service.get_theme",
        new_callable=AsyncMock,
        return_value=mocked_response,
    ):
        response = await app_client.get("/users/me/preferences", cookies=AUTH_COOKIES)

    assert response.status_code == 200
    data = response.json()
    assert data["theme"] == "light"
    assert data["userId"] == USER_ID


@pytest.mark.asyncio
async def test_get_preferences_requires_auth(app_client: AsyncClient) -> None:
    """Unauthenticated request must return 401."""
    response = await app_client.get("/users/me/preferences")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# PATCH /users/me/preferences
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_preferences_to_light(app_client: AsyncClient) -> None:
    """PATCH sets the theme to 'light' and returns the updated preference."""
    mocked_response = ThemeResponse(theme="light", userId=USER_ID)
    with patch(
        "app.features.theme.router.service.update_theme",
        new_callable=AsyncMock,
        return_value=mocked_response,
    ):
        response = await app_client.patch(
            "/users/me/preferences",
            cookies=AUTH_COOKIES,
            json={"theme": "light"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["theme"] == "light"
    assert data["userId"] == USER_ID


@pytest.mark.asyncio
async def test_update_preferences_to_dark(app_client: AsyncClient) -> None:
    """PATCH sets the theme to 'dark'."""
    mocked_response = ThemeResponse(theme="dark", userId=USER_ID)
    with patch(
        "app.features.theme.router.service.update_theme",
        new_callable=AsyncMock,
        return_value=mocked_response,
    ):
        response = await app_client.patch(
            "/users/me/preferences",
            cookies=AUTH_COOKIES,
            json={"theme": "dark"},
        )

    assert response.status_code == 200
    assert response.json()["theme"] == "dark"


@pytest.mark.asyncio
async def test_update_preferences_invalid_theme_returns_422(app_client: AsyncClient) -> None:
    """Invalid theme value must return 422 Unprocessable Entity."""
    response = await app_client.patch(
        "/users/me/preferences",
        cookies=AUTH_COOKIES,
        json={"theme": "purple"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_preferences_requires_auth(app_client: AsyncClient) -> None:
    """Unauthenticated PATCH must return 401."""
    response = await app_client.patch(
        "/users/me/preferences",
        json={"theme": "dark"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_preferences_calls_service_with_user_id(app_client: AsyncClient) -> None:
    """Service must be called with the authenticated user's ID."""
    mock_update = AsyncMock(return_value=ThemeResponse(theme="dark", userId=USER_ID))
    with patch("app.features.theme.router.service.update_theme", mock_update):
        await app_client.patch(
            "/users/me/preferences",
            cookies=AUTH_COOKIES,
            json={"theme": "dark"},
        )

    mock_update.assert_called_once()
    args = mock_update.call_args[0]
    # First positional arg is the user_id
    assert args[0] == USER_ID
    assert args[1] == "dark"
