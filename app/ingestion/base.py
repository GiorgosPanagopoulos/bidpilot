from datetime import datetime
from typing import Protocol, runtime_checkable

from app.models.tender import RawTender, Tender


@runtime_checkable
class TenderSource(Protocol):
    async def fetch(self, since: datetime) -> list[RawTender]: ...
    def normalize(self, raw: RawTender) -> Tender: ...
