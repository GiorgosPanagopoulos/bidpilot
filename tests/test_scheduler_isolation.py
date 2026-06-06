from __future__ import annotations

import logging
from unittest.mock import patch

import pytest

from app.core.exceptions import SourceUnavailableError


@pytest.mark.asyncio
async def test_tenders_failure_does_not_block_awards(caplog):
    """A SourceUnavailableError in the tenders pipeline must not prevent the awards job from running."""
    from app.ingestion.scheduler import _run_awards_job, _run_tenders_job

    awards_ran: list[int] = []

    async def fail_tenders(since=None) -> int:
        raise SourceUnavailableError("TED unavailable")

    async def succeed_awards(since=None) -> int:
        awards_ran.append(1)
        return 5

    with caplog.at_level(logging.ERROR, logger="app.ingestion.scheduler"):
        with patch("app.ingestion.scheduler.ingest_pipeline", fail_tenders):
            await _run_tenders_job()

        with patch("app.ingestion.scheduler.ingest_awards_pipeline", succeed_awards):
            await _run_awards_job()

    assert len(awards_ran) == 1, "awards pipeline must still run after tenders failure"
    assert any(
        "tender" in r.message.lower() and "failed" in r.message.lower() for r in caplog.records
    )


@pytest.mark.asyncio
async def test_awards_failure_does_not_block_tenders(caplog):
    """A SourceUnavailableError in the awards pipeline must not prevent the tenders job from running."""
    from app.ingestion.scheduler import _run_awards_job, _run_tenders_job

    tenders_ran: list[int] = []

    async def succeed_tenders(since=None) -> int:
        tenders_ran.append(1)
        return 3

    async def fail_awards(since=None) -> int:
        raise SourceUnavailableError("DIAVGEIA unavailable")

    with caplog.at_level(logging.ERROR, logger="app.ingestion.scheduler"):
        with patch("app.ingestion.scheduler.ingest_pipeline", succeed_tenders):
            await _run_tenders_job()

        with patch("app.ingestion.scheduler.ingest_awards_pipeline", fail_awards):
            await _run_awards_job()

    assert len(tenders_ran) == 1, "tenders pipeline must still run after awards failure"
    assert any(
        "award" in r.message.lower() and "failed" in r.message.lower() for r in caplog.records
    )


@pytest.mark.asyncio
async def test_tenders_job_does_not_propagate_exception():
    """_run_tenders_job must not raise even when the pipeline raises."""
    from app.ingestion.scheduler import _run_tenders_job

    async def always_raise(since=None) -> int:
        raise RuntimeError("unexpected crash")

    with patch("app.ingestion.scheduler.ingest_pipeline", always_raise):
        await _run_tenders_job()  # must not raise


@pytest.mark.asyncio
async def test_awards_job_does_not_propagate_exception():
    """_run_awards_job must not raise even when the pipeline raises."""
    from app.ingestion.scheduler import _run_awards_job

    async def always_raise(since=None) -> int:
        raise RuntimeError("unexpected crash")

    with patch("app.ingestion.scheduler.ingest_awards_pipeline", always_raise):
        await _run_awards_job()  # must not raise
