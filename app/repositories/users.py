from __future__ import annotations

from typing import Any

from app.models.user import User
from app.repositories.mongo import get_db

COLLECTION = "users"


def _from_doc(doc: dict[str, Any]) -> User:
    doc["id"] = doc.pop("_id")
    return User.model_validate(doc)


async def get_user_by_id(user_id: str) -> User | None:
    doc = await get_db()[COLLECTION].find_one({"_id": user_id})
    return _from_doc(doc) if doc else None


async def get_user_by_email(email: str) -> User | None:
    doc = await get_db()[COLLECTION].find_one({"email": email.strip().lower()})
    return _from_doc(doc) if doc else None


async def create_user(user: User) -> User:
    doc = user.model_dump()
    doc["_id"] = doc.pop("id")
    doc["email"] = doc["email"].strip().lower()
    await get_db()[COLLECTION].insert_one(doc)
    return user


async def ensure_user_indexes() -> None:
    await get_db()[COLLECTION].create_index("email", unique=True)
