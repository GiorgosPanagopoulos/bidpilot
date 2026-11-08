from __future__ import annotations

import logging
from datetime import UTC, datetime

from app.core.exceptions import DemoQuotaExceededError
from app.core.settings import settings
from app.models.user import User
from app.repositories.demo_usage import decrement_usage, increment_usage

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(UTC)


async def consume_draft_quota(user: User) -> str | None:
    """Count one draft run against a demo user's daily budget.

    Returns the UTC day that was charged (for refunds), or None for non-demo users.
    """
    if not user.is_demo:
        return None
    now = _utc_now()
    day = now.strftime("%Y-%m-%d")
    count = await increment_usage(user.id, day, now)
    if count > settings.demo_daily_drafts:
        # Over-limit attempts don't count, so the stored value stays meaningful.
        await decrement_usage(user.id, day)
        logger.info("demo quota exceeded user=%s day=%s", user.id, day)
        raise DemoQuotaExceededError()
    return day


async def refund_draft_quota(user: User, day: str) -> None:
    try:
        await decrement_usage(user.id, day)
    except Exception as exc:
        logger.warning("demo quota refund failed: %s", exc)
