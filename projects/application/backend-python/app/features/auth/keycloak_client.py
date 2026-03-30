import logging

import httpx

from app.config import settings
from app.features.auth.models import UserProfile

logger = logging.getLogger(__name__)

KEYCLOAK_TOKEN_URL = (
    "{base}/realms/{realm}/protocol/openid-connect/token"
)
KEYCLOAK_LOGOUT_URL = (
    "{base}/realms/{realm}/protocol/openid-connect/logout"
)


def _token_url() -> str:
    return KEYCLOAK_TOKEN_URL.format(
        base=settings.KEYCLOAK_URL, realm=settings.KEYCLOAK_REALM
    )


def _logout_url() -> str:
    return KEYCLOAK_LOGOUT_URL.format(
        base=settings.KEYCLOAK_URL, realm=settings.KEYCLOAK_REALM
    )


async def keycloak_login(username: str, password: str) -> dict:
    """Exchange username/password with Keycloak for tokens."""
    data = {
        "client_id": settings.KEYCLOAK_CLIENT_ID,
        "client_secret": settings.KEYCLOAK_CLIENT_SECRET,
        "grant_type": "password",
        "username": username,
        "password": password,
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(_token_url(), data=data)
    if response.status_code != 200:
        logger.error("Keycloak login failed: %s", response.text)
        raise ValueError("Invalid credentials")
    return response.json()


async def keycloak_refresh(refresh_token: str) -> dict:
    """Exchange a refresh token for new tokens."""
    data = {
        "client_id": settings.KEYCLOAK_CLIENT_ID,
        "client_secret": settings.KEYCLOAK_CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(_token_url(), data=data)
    if response.status_code != 200:
        logger.error("Keycloak token refresh failed: %s", response.text)
        raise ValueError("Invalid refresh token")
    return response.json()


async def keycloak_logout(refresh_token: str) -> None:
    """Call Keycloak logout endpoint to invalidate the session."""
    data = {
        "client_id": settings.KEYCLOAK_CLIENT_ID,
        "client_secret": settings.KEYCLOAK_CLIENT_SECRET,
        "refresh_token": refresh_token,
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(_logout_url(), data=data)
    if response.status_code not in (200, 204):
        logger.warning("Keycloak logout returned non-OK status: %s", response.status_code)


def decode_user_profile(access_token: str) -> UserProfile:
    """Decode JWT payload (no signature verification) and return UserProfile."""
    import base64
    import json

    parts = access_token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT format")

    # Add padding if needed
    payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
    payload = json.loads(base64.urlsafe_b64decode(payload_b64))

    import time

    exp = payload.get("exp", 0)
    if exp < time.time():
        raise ValueError("Token expired")

    realm_roles: list[str] = payload.get("realm_access", {}).get("roles", [])
    client_roles: list[str] = (
        payload.get("resource_access", {})
        .get(settings.KEYCLOAK_CLIENT_ID, {})
        .get("roles", [])
    )

    return UserProfile(
        id=payload.get("sub", ""),
        username=payload.get("preferred_username", ""),
        email=payload.get("email", ""),
        firstName=payload.get("given_name"),
        lastName=payload.get("family_name"),
        roles=realm_roles + client_roles,
    )
