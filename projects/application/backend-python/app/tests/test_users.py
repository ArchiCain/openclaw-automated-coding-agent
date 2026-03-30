"""Tests for user management endpoints: /users and /users/{id}."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.features.user_management.models import PaginationMeta, UserListResponse, UserResponse
from app.tests.conftest import VALID_ACCESS_TOKEN


def _make_user(
    user_id: str = "user-uuid-123",
    username: str = "testuser",
    email: str = "testuser@example.com",
    roles: list[str] | None = None,
) -> UserResponse:
    return UserResponse(
        id=user_id,
        username=username,
        email=email,
        firstName="Test",
        lastName="User",
        enabled=True,
        roles=roles or ["user"],
    )


AUTH_COOKIES = {"access_token": VALID_ACCESS_TOKEN}


# ---------------------------------------------------------------------------
# GET /users
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_users_returns_200(app_client: AsyncClient) -> None:
    """Authenticated request to /users must return 200."""
    user = _make_user()
    list_response = UserListResponse(
        users=[user],
        pagination=PaginationMeta(page=1, pageSize=10, total=1, totalPages=1),
    )
    with patch(
        "app.features.user_management.router.keycloak_admin.list_users",
        new_callable=AsyncMock,
        return_value=([user], 1),
    ):
        response = await app_client.get("/users", cookies=AUTH_COOKIES)

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_users_returns_pagination(app_client: AsyncClient) -> None:
    """Response must include pagination metadata."""
    user = _make_user()
    with patch(
        "app.features.user_management.router.keycloak_admin.list_users",
        new_callable=AsyncMock,
        return_value=([user], 1),
    ):
        response = await app_client.get("/users", cookies=AUTH_COOKIES)

    data = response.json()
    assert "pagination" in data
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["total"] == 1


@pytest.mark.asyncio
async def test_list_users_requires_auth(app_client: AsyncClient) -> None:
    """Unauthenticated request to /users must return 401."""
    response = await app_client.get("/users")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_users_passes_search_param(app_client: AsyncClient) -> None:
    """Search parameter must be forwarded to keycloak_admin.list_users."""
    user = _make_user()
    mock_list = AsyncMock(return_value=([user], 1))
    with patch(
        "app.features.user_management.router.keycloak_admin.list_users",
        mock_list,
    ):
        await app_client.get("/users?search=test", cookies=AUTH_COOKIES)

    mock_list.assert_called_once()
    _args, kwargs = mock_list.call_args
    assert kwargs.get("search") == "test"


@pytest.mark.asyncio
async def test_list_users_keycloak_error_returns_500(app_client: AsyncClient) -> None:
    """RuntimeError from keycloak_admin must map to 500."""
    with patch(
        "app.features.user_management.router.keycloak_admin.list_users",
        new_callable=AsyncMock,
        side_effect=RuntimeError("Keycloak down"),
    ):
        response = await app_client.get("/users", cookies=AUTH_COOKIES)

    assert response.status_code == 500


# ---------------------------------------------------------------------------
# POST /users
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_user_returns_201(app_client: AsyncClient) -> None:
    """Creating a user must return 201 Created."""
    user = _make_user(user_id="new-user-id", email="new@example.com", username="new@example.com")
    with patch(
        "app.features.user_management.router.keycloak_admin.create_user",
        new_callable=AsyncMock,
        return_value=user,
    ):
        response = await app_client.post(
            "/users",
            cookies=AUTH_COOKIES,
            json={
                "email": "new@example.com",
                "firstName": "New",
                "lastName": "User",
                "temporaryPassword": "P@ssw0rd",
                "role": "user",
            },
        )

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_user_returns_409_on_conflict(app_client: AsyncClient) -> None:
    """Duplicate email should result in 409 Conflict."""
    with patch(
        "app.features.user_management.router.keycloak_admin.create_user",
        new_callable=AsyncMock,
        side_effect=ValueError("User with this email already exists"),
    ):
        response = await app_client.post(
            "/users",
            cookies=AUTH_COOKIES,
            json={
                "email": "exists@example.com",
                "firstName": "Dup",
                "lastName": "User",
                "temporaryPassword": "P@ssw0rd",
                "role": "user",
            },
        )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_user_requires_auth(app_client: AsyncClient) -> None:
    """Creating a user without auth must return 401."""
    response = await app_client.post(
        "/users",
        json={
            "email": "a@b.com",
            "temporaryPassword": "P@ss",
            "role": "user",
        },
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /users/me
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_me_returns_current_user(app_client: AsyncClient) -> None:
    """GET /users/me must return the authenticated user's profile."""
    response = await app_client.get("/users/me", cookies=AUTH_COOKIES)

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "testuser@example.com"


@pytest.mark.asyncio
async def test_get_me_requires_auth(app_client: AsyncClient) -> None:
    """GET /users/me without auth must return 401."""
    response = await app_client.get("/users/me")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /users/{id}
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_user_by_id_returns_200(app_client: AsyncClient) -> None:
    """GET /users/{id} must return the user if found."""
    user = _make_user(user_id="abc-123")
    with patch(
        "app.features.user_management.router.keycloak_admin.get_user",
        new_callable=AsyncMock,
        return_value=user,
    ):
        response = await app_client.get("/users/abc-123", cookies=AUTH_COOKIES)

    assert response.status_code == 200
    assert response.json()["id"] == "abc-123"


@pytest.mark.asyncio
async def test_get_user_not_found_returns_404(app_client: AsyncClient) -> None:
    """Missing user must return 404."""
    with patch(
        "app.features.user_management.router.keycloak_admin.get_user",
        new_callable=AsyncMock,
        side_effect=LookupError("User not found"),
    ):
        response = await app_client.get("/users/missing-id", cookies=AUTH_COOKIES)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_user_requires_auth(app_client: AsyncClient) -> None:
    """GET /users/{id} without auth must return 401."""
    response = await app_client.get("/users/some-id")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# PATCH /users/{id}
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_user_returns_200(app_client: AsyncClient) -> None:
    """Patching a user must return the updated user."""
    updated = _make_user(user_id="abc-123")
    updated.firstName = "Updated"
    with patch(
        "app.features.user_management.router.keycloak_admin.update_user",
        new_callable=AsyncMock,
        return_value=updated,
    ):
        response = await app_client.patch(
            "/users/abc-123",
            cookies=AUTH_COOKIES,
            json={"firstName": "Updated"},
        )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_user_not_found_returns_404(app_client: AsyncClient) -> None:
    """Updating a non-existent user must return 404."""
    with patch(
        "app.features.user_management.router.keycloak_admin.update_user",
        new_callable=AsyncMock,
        side_effect=LookupError("User not found"),
    ):
        response = await app_client.patch(
            "/users/ghost",
            cookies=AUTH_COOKIES,
            json={"firstName": "Ghost"},
        )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /users/{id}
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_delete_user_returns_200(app_client: AsyncClient) -> None:
    """Deleting a user must return 200 with a message."""
    with patch(
        "app.features.user_management.router.keycloak_admin.delete_user",
        new_callable=AsyncMock,
        return_value=None,
    ):
        response = await app_client.delete("/users/abc-123", cookies=AUTH_COOKIES)

    assert response.status_code == 200
    assert "message" in response.json()


@pytest.mark.asyncio
async def test_delete_user_not_found_returns_404(app_client: AsyncClient) -> None:
    """Deleting a non-existent user must return 404."""
    with patch(
        "app.features.user_management.router.keycloak_admin.delete_user",
        new_callable=AsyncMock,
        side_effect=LookupError("User not found"),
    ):
        response = await app_client.delete("/users/ghost", cookies=AUTH_COOKIES)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_user_requires_auth(app_client: AsyncClient) -> None:
    """DELETE /users/{id} without auth must return 401."""
    response = await app_client.delete("/users/some-id")
    assert response.status_code == 401
