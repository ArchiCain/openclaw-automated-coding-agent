from typing import Literal

from pydantic import BaseModel

ThemeValue = Literal["light", "dark"]


class ThemeResponse(BaseModel):
    theme: ThemeValue
    userId: str


class UpdateThemeRequest(BaseModel):
    theme: ThemeValue
