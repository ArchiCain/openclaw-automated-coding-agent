import logging

from fastapi import Cookie, HTTPException, status

from app.features.auth.keycloak_client import decode_user_profile
from app.features.auth.models import UserProfile

logger = logging.getLogger(__name__)


async def get_current_user(
    access_token: str | None = Cookie(default=None),
) -> UserProfile:
    """FastAPI dependency that extracts and validates the JWT from the access_token cookie."""
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    try:
        return decode_user_profile(access_token)
    except ValueError as exc:
        logger.warning("JWT validation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc
