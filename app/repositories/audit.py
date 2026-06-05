import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from app.core.context import current_tenant
from app.repositories.mongo import get_db

logger = logging.getLogger(__name__)
COLLECTION = "audit_log"


async def _write(action: str, payload: dict[str, Any]) -> None:
    try:
        doc = {
            "tenant": current_tenant.get(),
            "action": action,
            "payload": payload,
            "ts": datetime.now(UTC).isoformat(),
        }
        await get_db()[COLLECTION].insert_one(doc)
    except Exception as exc:
        logger.warning("audit write failed: %s", exc)


def fire_and_forget(action: str, payload: dict[str, Any]) -> None:
    asyncio.ensure_future(_write(action, payload))
