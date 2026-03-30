from pydantic import BaseModel


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    firstName: str | None = None
    lastName: str | None = None
    enabled: bool = True
    createdTimestamp: int | None = None
    roles: list[str] = []


class PaginationMeta(BaseModel):
    page: int
    pageSize: int
    total: int
    totalPages: int


class UserListResponse(BaseModel):
    users: list[UserResponse]
    pagination: PaginationMeta


class CreateUserRequest(BaseModel):
    email: str
    firstName: str | None = None
    lastName: str | None = None
    temporaryPassword: str
    role: str


class UpdateUserRequest(BaseModel):
    firstName: str | None = None
    lastName: str | None = None
    role: str | None = None
