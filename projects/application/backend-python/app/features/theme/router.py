from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.dependencies import get_current_user
from app.features.auth.models import UserProfile
from app.features.database.session import get_db_session
from app.features.theme import service
from app.features.theme.models import ThemeResponse, UpdateThemeRequest

router = APIRouter(tags=["theme"])


@router.get("/users/me/preferences", response_model=ThemeResponse)
async def get_preferences(
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ThemeResponse:
    """Return the current user's theme preference."""
    return await service.get_theme(current_user.id, db)


@router.patch("/users/me/preferences", response_model=ThemeResponse)
async def update_preferences(
    body: UpdateThemeRequest,
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ThemeResponse:
    """Update the current user's theme preference."""
    return await service.update_theme(current_user.id, body.theme, db)
