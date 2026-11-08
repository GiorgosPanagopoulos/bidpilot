from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

Role = Literal["admin", "member", "viewer"]


class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    hashed_password: str
    company_id: str
    role: Role = "viewer"
    is_active: bool = True
    is_demo: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class UserPublic(BaseModel):
    id: str
    email: str
    company_id: str
    role: Role
    is_demo: bool

    @classmethod
    def from_user(cls, user: User) -> UserPublic:
        return cls(
            id=user.id,
            email=user.email,
            company_id=user.company_id,
            role=user.role,
            is_demo=user.is_demo,
        )
