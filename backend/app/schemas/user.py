from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums import Role


class BusinessOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str


class UserOut(BaseModel):
    """Response user. Sengaja TIDAK punya field password."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    business_id: int
    name: str
    email: str
    role: Role
    created_at: datetime


class MeOut(UserOut):
    business: BusinessOut


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    # Admin boleh membuat agent atau customer
    role: Literal[Role.agent, Role.customer]

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        return v.lower()