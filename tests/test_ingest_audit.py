from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_award_ingest_triggers_audit():
    """POST /awards/ingest should fire-and-forget an audit event on success."""
    from app.api.routers.awards import trigger_award_ingest

    mock_fire = MagicMock()

    async def fake_pipeline(since=None) -> int:
        return 7

    with (
        patch("app.api.routers.awards.ingest_awards_pipeline", fake_pipeline),
        patch("app.api.routers.awards.fire_and_forget", mock_fire),
    ):
        result = await trigger_award_ingest(_=None)

    assert result == {"ingested": 7}
    mock_fire.assert_called_once_with("awards.ingest", {"count": 7})


@pytest.mark.asyncio
async def test_award_ingest_zero_count_still_audits():
    from app.api.routers.awards import trigger_award_ingest

    mock_fire = MagicMock()

    async def fake_pipeline(since=None) -> int:
        return 0

    with (
        patch("app.api.routers.awards.ingest_awards_pipeline", fake_pipeline),
        patch("app.api.routers.awards.fire_and_forget", mock_fire),
    ):
        result = await trigger_award_ingest(_=None)

    assert result == {"ingested": 0}
    mock_fire.assert_called_once()


@pytest.mark.asyncio
async def test_award_ingest_pipeline_error_propagates():
    from app.api.routers.awards import trigger_award_ingest
    from app.core.exceptions import AwardIngestionError

    async def failing_pipeline(since=None) -> int:
        raise AwardIngestionError("upstream failure")

    with patch("app.api.routers.awards.ingest_awards_pipeline", failing_pipeline):
        with pytest.raises(AwardIngestionError, match="upstream failure"):
            await trigger_award_ingest(_=None)
