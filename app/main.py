from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routers import companies, drafts, matches, tenders
from app.core.exceptions import BidPilotError, bidpilot_exception_handler
from app.core.logging import configure_logging
from app.ingestion.scheduler import start_scheduler, stop_scheduler
from app.repositories.mongo import close_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    start_scheduler()
    yield
    stop_scheduler()
    await close_client()


app = FastAPI(title="BidPilot", version="0.1.0", lifespan=lifespan)

app.add_exception_handler(BidPilotError, bidpilot_exception_handler)  # type: ignore[arg-type]

app.include_router(companies.router)
app.include_router(tenders.router)
app.include_router(matches.router)
app.include_router(drafts.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
