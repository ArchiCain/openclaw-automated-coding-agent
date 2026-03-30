"""Tests for auth endpoints: /auth/login, /auth/logout, /auth/check, /auth/refresh."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.tests.conftest import VALID_ACCESS_TOKEN, VALID_REFRESH_TOKEN, make_access_token


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_login_success(app_client: AsyncClient) -> None:
    """Successful login returns 200 with user profile and sets cookies."""
    token_response = {
        "access_token": VALID_ACCESS_TOKEN,
        "refresh_token": VALID_REFRESH_TOKEN,
        "expires_in": 300,
        "token_type": "bearer",
    }
    with patch(
        "app.features.auth.router.keycloak_login",
        new_callable=AsyncMock,
        return_value=token_response,
    ):
        response = await app_client.post(
            "/auth/login",
            json={"username": "testuser", "password": "secret"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Login successful"
    assert "user" in data
    assert data["user"]["username"] == "testuser"


@pytest.mark.asyncio
async def test_login_sets_cookies(app_client: AsyncClient) -> None:
    """Login response must set access_token and refresh_token cookies."""
    token_response = {
        "access_token": VALID_ACCESS_TOKEN,
        "refresh_token": VALID_REFRESH_TOKEN,
        "expires_in": 300,
    }
    with patch(
        "app.features.auth.router.keycloak_login",
        new_callable=AsyncMock,
        return_value=token_response,
    ):
        response = await app_client.post(
            "/auth/login",
            json={"username": "testuser", "password": "secret"},
        )

    cookie_names = {c.name for c in response.cookies.jar}
    assert "access_token" in cookie_names
    assert "refresh_token" in cookie_names


@pytest.mark.asyncio
async def test_login_invalid_credentials(app_client: AsyncClient) -> None:
    """Invalid credentials from Keycloak should result in 401."""
    with patch(
        "app.features.auth.router.keycloak_login",
        new_callable=AsyncMock,
        side_effect=ValueError("Invalid credentials"),
    ):
        response = await app_client.post(
            "/auth/login",
            json={"username": "bad", "password": "wrong"},
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_missing_body_fields(app_client: AsyncClient) -> None:
    """Login with missing required fields should return 422 Unprocessable Entity."""
    response = await app_client.post("/auth/login", json={"username": "only"})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /auth/logout
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_logout_success(app_client: AsyncClient) -> None:
    """Authenticated logout with valid refresh token returns 200."""
    with patch(
        "app.features.auth.router.keycloak_logout",
        new_callable=AsyncMock,
        return_value=None,
    ):
        response = await app_client.post(
            "/auth/logout",
            cookies={
                "access_token": VALID_ACCESS_TOKEN,
                "refresh_token": VALID_REFRESH_TOKEN,
            },
        )

    assert response.status_code == 200
    assert response.json()["message"] == "Logout successful"


@pytest.mark.asyncio
async def test_logout_without_auth_returns_401(app_client: AsyncClient) -> None:
    """Logout without authentication cookie should return 401."""
    response = await app_client.post("/auth/logout")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout_clears_cookies(app_client: AsyncClient) -> None:
    """Logout response should clear access_token and refresh_token cookies."""
    with patch(
        "app.features.auth.router.keycloak_logout",
        new_callable=AsyncMock,
        return_value=None,
    ):
        response = await app_client.post(
            "/auth/logout",
            cookies={
                "access_token": VALID_ACCESS_TOKEN,
                "refresh_token": VALID_REFRESH_TOKEN,
            },
        )

    # Cookies with max-age=0 or empty value indicate deletion
    cleared = {
        c.name: c
        for c in response.cookies.jar
    }
    # Either cookie is absent or has an empty / expired value
    for name in ("access_token", "refresh_token"):
        if name in cleared:
            assert cleared[name].value in ("", None) or int(cleared[name].expires or 1) <= 0


# ---------------------------------------------------------------------------
# POST /auth/check
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_check_authenticated(app_client: AsyncClient, auth_cookies: dict) -> None:
    """Valid access_token cookie should return authenticated=True and user profile."""
    response = await app_client.post("/auth/check", cookies=auth_cookies)

    assert response.status_code == 200
    data = response.json()
    assert data["authenticated"] is True
    assert data["user"]["username"] == "testuser"
    assert data["user"]["email"] == "testuser@example.com"


@pytest.mark.asyncio
async def test_check_without_token_returns_401(app_client: AsyncClient) -> None:
    """Missing access_token cookie should return 401."""
    response = await app_client.post("/auth/check")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_check_with_expired_token_returns_401(app_client: AsyncClient) -> None:
    """Expired access_token cookie should return 401."""
    expired_token = make_access_token(exp_offset=-1)  # already expired
    response = await app_client.post(
        "/auth/check", cookies={"access_token": expired_token}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_check_with_invalid_token_returns_401(app_client: AsyncClient) -> None:
    """Malformed JWT should return 401."""
    response = await app_client.post(
        "/auth/check", cookies={"access_token": "not.a.jwt"}
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST /auth/refresh
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_refresh_success(app_client: AsyncClient) -> None:
    """Valid refresh token cookie should return 200 and set new tokens."""
    new_access = make_access_token(sub="user-uuid-123")
    token_response = {
        "access_token": new_access,
        "refresh_token": "new-refresh-token",
        "expires_in": 300,
    }
    with patch(
        "app.features.auth.router.keycloak_refresh",
        new_callable=AsyncMock,
        return_value=token_response,
    ):
        response = await app_client.post(
            "/auth/refresh",
            cookies={"refresh_token": VALID_REFRESH_TOKEN},
        )

    assert response.status_code == 200
    assert response.json()["message"] == "Token refreshed successfully"


@pytest.mark.asyncio
async def test_refresh_without_cookie_returns_401(app_client: AsyncClient) -> None:
    """Missing refresh_token cookie should return 401."""
    response = await app_client.post("/auth/refresh")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_with_invalid_token_returns_401(app_client: AsyncClient) -> None:
    """Keycloak rejecting the refresh token should return 401."""
    with patch(
        "app.features.auth.router.keycloak_refresh",
        new_callable=AsyncMock,
        side_effect=ValueError("Invalid refresh token"),
    ):
        response = await app_client.post(
            "/auth/refresh",
            cookies={"refresh_token": "bad-token"},
        )

    assert response.status_code == 401
