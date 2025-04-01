from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    name: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserSchema(UserBase):
    id: str
    is_admin: bool = False
    is_suspended: bool = False
    suspension_reason: Optional[str] = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class UserUpdateAdmin(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_admin: Optional[bool] = None
    is_suspended: Optional[bool] = None
    suspension_reason: Optional[str] = None


class UserSuspend(BaseModel):
    suspension_reason: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None
    is_admin: Optional[bool] = None


class UserListResponse(BaseModel):
    users: List[UserSchema]
    total: int
    page: int
    limit: int
