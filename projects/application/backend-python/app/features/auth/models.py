from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class UserProfile(BaseModel):
    id: str
    username: str
    email: str
    firstName: str | None = None
    lastName: str | None = None
    roles: list[str] = []


class LoginResponse(BaseModel):
    message: str
    user: UserProfile


class CheckResponse(BaseModel):
    authenticated: bool
    user: UserProfile


class RefreshResponse(BaseModel):
    message: str


class LogoutResponse(BaseModel):
    message: str
