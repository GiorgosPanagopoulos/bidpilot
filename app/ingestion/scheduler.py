from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.settings import settings
from app.ingestion.diavgeia import DiavgeiaSource
from app.ingestion.ted import TEDSource
from app.repositories.awards import upsert_award
from app.repositories.tenders import upsert_tender
from app.vectorstore.chroma import upsert_tender_embedding

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def ingest_pipeline(since: datetime | None = None) -> int:
    if since is None:
        since = datetime.now(UTC) - timedelta(days=1)
    source = TEDSource()
    raw_list = await source.fetch(since)
    count = 0
    for raw in raw_list:
        try:
            tender = source.normalize(raw)
            await upsert_tender(tender)
            upsert_tender_embedding(tender)
            count += 1
        except Exception as exc:
            logger.warning("skipping notice: %s", exc)
    logger.info("ingested %d tenders", count)
    return count


async def ingest_awards_pipeline(since: datetime | None = None) -> int:
    if since is None:
        since = datetime.now(UTC) - timedelta(days=1)
    source = DiavgeiaSource()
    raw_list = await source.fetch(since)
    count = 0
    for raw in raw_list:
        try:
            award = source.normalize(raw)
            await upsert_award(award)
            count += 1
        except Exception as exc:
            logger.warning("skipping award record: %s", exc)
    logger.info("ingested %d awards", count)
    return count


async def _run_tenders_job() -> None:
    """APScheduler entry-point for tender ingestion. Exceptions are logged, never re-raised."""
    try:
        count = await ingest_pipeline()
        logger.info("scheduled tender ingestion completed: %d records", count)
    except Exception as exc:
        logger.error(
            "scheduled tender ingestion failed: %s: %s",
            type(exc).__name__,
            exc,
        )


async def _run_awards_job() -> None:
    """APScheduler entry-point for award ingestion. Exceptions are logged, never re-raised."""
    try:
        count = await ingest_awards_pipeline()
        logger.info("scheduled award ingestion completed: %d records", count)
    except Exception as exc:
        logger.error(
            "scheduled award ingestion failed: %s: %s",
            type(exc).__name__,
            exc,
        )


def start_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        return
    _scheduler = AsyncIOScheduler()
    cron_parts = settings.ingest_cron.split()
    minute, hour, day, month, day_of_week = cron_parts
    _scheduler.add_job(
        _run_tenders_job,
        "cron",
        minute=minute,
        hour=hour,
        day=day,
        month=month,
        day_of_week=day_of_week,
        id="ingest_tenders",
    )
    _scheduler.add_job(
        _run_awards_job,
        "cron",
        minute=minute,
        hour=hour,
        day=day,
        month=month,
        day_of_week=day_of_week,
        id="ingest_awards",
    )
    _scheduler.start()
    logger.info("scheduler started with cron=%s", settings.ingest_cron)


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
    _scheduler = None
