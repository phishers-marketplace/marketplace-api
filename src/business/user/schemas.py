from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    name: str
    email: EmailStr
    photo_url: str | None = None


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    photo_url: str | None = None


class UserSchema(UserBase):
    id: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None
