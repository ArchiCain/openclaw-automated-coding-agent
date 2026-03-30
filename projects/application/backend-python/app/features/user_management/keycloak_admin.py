"""Keycloak Admin REST API client for user management."""
import logging

import httpx

from app.config import settings
from app.features.user_management.models import UserResponse

logger = logging.getLogger(__name__)

_ADMIN_USERS_URL = "{base}/admin/realms/{realm}/users"
_ADMIN_ROLES_URL = "{base}/admin/realms/{realm}/roles/{role_name}"
_ADMIN_USER_ROLES_URL = (
    "{base}/admin/realms/{realm}/users/{user_id}/role-mappings/realm"
)
_TOKEN_URL = "{base}/realms/{realm}/protocol/openid-connect/token"


def _base() -> str:
    return settings.KEYCLOAK_URL


def _realm() -> str:
    return settings.KEYCLOAK_REALM


async def _get_admin_token() -> str:
    """Obtain an admin access token via client_credentials grant."""
    data = {
        "client_id": settings.KEYCLOAK_CLIENT_ID,
        "client_secret": settings.KEYCLOAK_CLIENT_SECRET,
        "grant_type": "client_credentials",
    }
    url = _TOKEN_URL.format(base=_base(), realm=_realm())
    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=data)
    if response.status_code != 200:
        logger.error("Failed to get admin token: %s", response.text)
        raise RuntimeError("Failed to authenticate with Keycloak")
    return response.json()["access_token"]


async def _get_user_roles(user_id: str, token: str) -> list[str]:
    """Fetch realm roles for a user."""
    url = _ADMIN_USER_ROLES_URL.format(
        base=_base(), realm=_realm(), user_id=user_id
    )
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers={"Authorization": f"Bearer {token}"})
    if not response.is_success:
        logger.warning("Could not fetch roles for user %s", user_id)
        return []
    return [r["name"] for r in response.json()]


def _map_user(raw: dict, roles: list[str]) -> UserResponse:
    return UserResponse(
        id=raw["id"],
        username=raw.get("username", ""),
        email=raw.get("email", ""),
        firstName=raw.get("firstName"),
        lastName=raw.get("lastName"),
        enabled=raw.get("enabled", True),
        createdTimestamp=raw.get("createdTimestamp"),
        roles=roles,
    )


async def list_users(
    page: int = 1,
    page_size: int = 10,
    search: str | None = None,
) -> tuple[list[UserResponse], int]:
    """List users with pagination. Returns (users, total)."""
    token = await _get_admin_token()
    first = (page - 1) * page_size

    params: dict = {"first": str(first), "max": str(page_size)}
    if search:
        params["search"] = search

    base_url = _ADMIN_USERS_URL.format(base=_base(), realm=_realm())
    async with httpx.AsyncClient() as client:
        users_resp = await client.get(
            base_url,
            params=params,
            headers={"Authorization": f"Bearer {token}"},
        )
        if not users_resp.is_success:
            logger.error("Failed to list users: %s", users_resp.text)
            raise RuntimeError("Failed to fetch users")

        count_params: dict = {}
        if search:
            count_params["search"] = search
        count_resp = await client.get(
            f"{base_url}/count",
            params=count_params,
            headers={"Authorization": f"Bearer {token}"},
        )

    raw_users: list[dict] = users_resp.json()
    total: int = count_resp.json() if count_resp.is_success else len(raw_users)

    users = []
    for raw in raw_users:
        roles = await _get_user_roles(raw["id"], token)
        users.append(_map_user(raw, roles))

    return users, total


async def get_user(user_id: str) -> UserResponse:
    """Get a single user by ID."""
    token = await _get_admin_token()
    url = f"{_ADMIN_USERS_URL.format(base=_base(), realm=_realm())}/{user_id}"
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url, headers={"Authorization": f"Bearer {token}"}
        )
    if response.status_code == 404:
        raise LookupError(f"User {user_id} not found")
    if not response.is_success:
        logger.error("Failed to get user %s: %s", user_id, response.text)
        raise RuntimeError("Failed to fetch user")
    raw = response.json()
    roles = await _get_user_roles(user_id, token)
    return _map_user(raw, roles)


async def create_user(
    email: str,
    first_name: str | None,
    last_name: str | None,
    temporary_password: str,
    role: str,
) -> UserResponse:
    """Create a new user in Keycloak."""
    token = await _get_admin_token()
    url = _ADMIN_USERS_URL.format(base=_base(), realm=_realm())
    payload = {
        "username": email,
        "email": email,
        "firstName": first_name,
        "lastName": last_name,
        "enabled": True,
        "emailVerified": True,
        "credentials": [
            {"type": "password", "value": temporary_password, "temporary": False}
        ],
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code == 409:
            raise ValueError("User with this email already exists")
        if not response.is_success:
            logger.error("Failed to create user: %s", response.text)
            raise RuntimeError("Failed to create user")

        location = response.headers.get("location", "")
        user_id = location.rstrip("/").split("/")[-1]
        if not user_id:
            raise RuntimeError("Failed to determine created user ID")

        # Assign role
        await _assign_role(user_id, role, token, client)

    return await get_user(user_id)


async def update_user(
    user_id: str,
    first_name: str | None,
    last_name: str | None,
    role: str | None,
) -> UserResponse:
    """Update an existing user."""
    token = await _get_admin_token()
    existing = await get_user(user_id)

    url = f"{_ADMIN_USERS_URL.format(base=_base(), realm=_realm())}/{user_id}"
    patch: dict = {
        "firstName": first_name if first_name is not None else existing.firstName,
        "lastName": last_name if last_name is not None else existing.lastName,
    }
    async with httpx.AsyncClient() as client:
        response = await client.put(
            url,
            json=patch,
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code == 404:
            raise LookupError(f"User {user_id} not found")
        if not response.is_success:
            logger.error("Failed to update user %s: %s", user_id, response.text)
            raise RuntimeError("Failed to update user")

        if role and role not in existing.roles:
            # Remove old app roles and assign new one
            for existing_role in existing.roles:
                await _remove_role(user_id, existing_role, token, client)
            await _assign_role(user_id, role, token, client)

    return await get_user(user_id)


async def delete_user(user_id: str) -> None:
    """Disable a user (soft delete)."""
    token = await _get_admin_token()
    url = f"{_ADMIN_USERS_URL.format(base=_base(), realm=_realm())}/{user_id}"
    # Verify exists first
    await get_user(user_id)
    async with httpx.AsyncClient() as client:
        response = await client.put(
            url,
            json={"enabled": False},
            headers={"Authorization": f"Bearer {token}"},
        )
    if not response.is_success:
        logger.error("Failed to disable user %s: %s", user_id, response.text)
        raise RuntimeError("Failed to delete user")


async def _get_realm_role(role_name: str, token: str, client: httpx.AsyncClient) -> dict | None:
    url = _ADMIN_ROLES_URL.format(base=_base(), realm=_realm(), role_name=role_name)
    response = await client.get(url, headers={"Authorization": f"Bearer {token}"})
    if not response.is_success:
        logger.warning("Role %s not found", role_name)
        return None
    return response.json()


async def _assign_role(
    user_id: str, role_name: str, token: str, client: httpx.AsyncClient
) -> None:
    role = await _get_realm_role(role_name, token, client)
    if not role:
        logger.warning("Cannot assign role %s: not found", role_name)
        return
    url = _ADMIN_USER_ROLES_URL.format(
        base=_base(), realm=_realm(), user_id=user_id
    )
    response = await client.post(
        url, json=[role], headers={"Authorization": f"Bearer {token}"}
    )
    if not response.is_success:
        logger.error("Failed to assign role %s to %s: %s", role_name, user_id, response.text)


async def _remove_role(
    user_id: str, role_name: str, token: str, client: httpx.AsyncClient
) -> None:
    role = await _get_realm_role(role_name, token, client)
    if not role:
        return
    url = _ADMIN_USER_ROLES_URL.format(
        base=_base(), realm=_realm(), user_id=user_id
    )
    response = await client.request(
        "DELETE", url, json=[role], headers={"Authorization": f"Bearer {token}"}
    )
    if not response.is_success:
        logger.error("Failed to remove role %s from %s: %s", role_name, user_id, response.text)
