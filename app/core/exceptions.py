from fastapi import Request
from fastapi.responses import JSONResponse


class BidPilotError(Exception):
    status_code: int = 500
    detail: str = "internal error"

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.__class__.detail
        super().__init__(self.detail)


class NotFoundError(BidPilotError):
    status_code = 404
    detail = "resource not found"


class ValidationError(BidPilotError):
    status_code = 422
    detail = "validation failed"


class TenderIngestionError(BidPilotError):
    status_code = 500
    detail = "tender ingestion failed"


class SourceUnavailableError(BidPilotError):
    status_code = 503
    detail = "upstream tender source unavailable"


class MatchingError(BidPilotError):
    status_code = 500
    detail = "matching pipeline failed"


async def bidpilot_exception_handler(request: Request, exc: BidPilotError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
