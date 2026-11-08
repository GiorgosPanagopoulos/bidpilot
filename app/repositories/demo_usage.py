from __future__ import annotations

from datetime import datetime

from pymongo import ReturnDocument

from app.repositories.mongo import get_db

COLLECTION = "demo_usage"
# Counters only matter for the current UTC day; keep a day of slack before Mongo reaps them.
TTL_SECONDS = 48 * 60 * 60


def _key(user_id: str, day: str) -> str:
    return f"{user_id}:{day}"


async def increment_usage(user_id: str, day: str, now: datetime) -> int:
    # Upsert on _id is atomic, so concurrent first-of-day requests share one counter.
    doc = await get_db()[COLLECTION].find_one_and_update(
        {"_id": _key(user_id, day)},
        {
            "$inc": {"count": 1},
            "$setOnInsert": {"user_id": user_id, "day": day, "created_at": now},
        },
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return int(doc["count"])


async def decrement_usage(user_id: str, day: str) -> None:
    await get_db()[COLLECTION].update_one({"_id": _key(user_id, day)}, {"$inc": {"count": -1}})


async def ensure_demo_indexes() -> None:
    await get_db()[COLLECTION].create_index("created_at", expireAfterSeconds=TTL_SECONDS)
