import logging
import math

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.features.auth.dependencies import get_current_user
from app.features.auth.models import UserProfile
from app.features.user_management import keycloak_admin
from app.features.user_management.models import (
    CreateUserRequest,
    PaginationMeta,
    UpdateUserRequest,
    UserListResponse,
    UserResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["users"])


@router.get("/users", response_model=UserListResponse)
async def list_users(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=10, ge=1, le=100),
    search: str | None = Query(default=None),
    _current_user: UserProfile = Depends(get_current_user),
) -> UserListResponse:
    """List users from Keycloak with pagination."""
    try:
        users, total = await keycloak_admin.list_users(
            page=page, page_size=pageSize, search=search
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return UserListResponse(
        users=users,
        pagination=PaginationMeta(
            page=page,
            pageSize=pageSize,
            total=total,
            totalPages=math.ceil(total / pageSize) if total > 0 else 1,
        ),
    )


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: CreateUserRequest,
    _current_user: UserProfile = Depends(get_current_user),
) -> UserResponse:
    """Create a new user in Keycloak."""
    try:
        return await keycloak_admin.create_user(
            email=body.email,
            first_name=body.firstName,
            last_name=body.lastName,
            temporary_password=body.temporaryPassword,
            role=body.role,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc


@router.get("/users/me", response_model=UserResponse)
async def get_me(
    current_user: UserProfile = Depends(get_current_user),
) -> UserResponse:
    """Return the current authenticated user's profile."""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        firstName=current_user.firstName,
        lastName=current_user.lastName,
        enabled=True,
        roles=current_user.roles,
    )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    _current_user: UserProfile = Depends(get_current_user),
) -> UserResponse:
    """Get a user by ID from Keycloak."""
    try:
        return await keycloak_admin.get_user(user_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    body: UpdateUserRequest,
    _current_user: UserProfile = Depends(get_current_user),
) -> UserResponse:
    """Update a user in Keycloak."""
    try:
        return await keycloak_admin.update_user(
            user_id=user_id,
            first_name=body.firstName,
            last_name=body.lastName,
            role=body.role,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc


@router.delete("/users/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(
    user_id: str,
    _current_user: UserProfile = Depends(get_current_user),
) -> dict:
    """Soft-delete (disable) a user in Keycloak."""
    try:
        await keycloak_admin.delete_user(user_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc
    return {"message": "User deleted successfully"}
