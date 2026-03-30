import logging
import os

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status

from app.features.auth.dependencies import get_current_user
from app.features.auth.keycloak_client import (
    decode_user_profile,
    keycloak_login,
    keycloak_logout,
    keycloak_refresh,
)
from app.features.auth.models import (
    CheckResponse,
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    RefreshResponse,
    UserProfile,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])

_IS_PRODUCTION = os.getenv("NODE_ENV", "development") == "production"
_COOKIE_KWARGS: dict = {
    "httponly": True,
    "secure": _IS_PRODUCTION,
    "samesite": "strict" if _IS_PRODUCTION else "lax",
    "path": "/",
}


@router.post("/auth/login", response_model=LoginResponse)
async def login(body: LoginRequest, response: Response) -> LoginResponse:
    """Authenticate with Keycloak and set HTTP-only cookies."""
    try:
        token_data = await keycloak_login(body.username, body.password)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        ) from exc

    access_token: str = token_data["access_token"]
    refresh_token: str = token_data["refresh_token"]
    expires_in: int = token_data.get("expires_in", 300)

    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=expires_in,
        **_COOKIE_KWARGS,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=30 * 24 * 60 * 60,  # 30 days
        **_COOKIE_KWARGS,
    )

    try:
        user = decode_user_profile(access_token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
        ) from exc

    return LoginResponse(message="Login successful", user=user)


@router.post("/auth/logout", response_model=LogoutResponse)
async def logout(
    response: Response,
    _current_user: UserProfile = Depends(get_current_user),
    refresh_token: str | None = Cookie(default=None),
) -> LogoutResponse:
    """Log out — clears cookies and calls Keycloak logout."""
    if refresh_token:
        await keycloak_logout(refresh_token)

    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")

    return LogoutResponse(message="Logout successful")


@router.post("/auth/check", response_model=CheckResponse)
async def check_auth(
    current_user: UserProfile = Depends(get_current_user),
) -> CheckResponse:
    """Verify current cookie-based JWT and return user profile."""
    return CheckResponse(authenticated=True, user=current_user)


@router.post("/auth/refresh", response_model=RefreshResponse)
async def refresh_token(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
) -> RefreshResponse:
    """Exchange refresh token cookie for a new access token."""
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
        )

    try:
        token_data = await keycloak_refresh(refresh_token)
    except ValueError as exc:
        response.delete_cookie("access_token", path="/")
        response.delete_cookie("refresh_token", path="/")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to refresh token",
        ) from exc

    access_token: str = token_data["access_token"]
    new_refresh_token: str = token_data["refresh_token"]
    expires_in: int = token_data.get("expires_in", 300)

    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=expires_in,
        **_COOKIE_KWARGS,
    )
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        max_age=30 * 24 * 60 * 60,
        **_COOKIE_KWARGS,
    )

    return RefreshResponse(message="Token refreshed successfully")
