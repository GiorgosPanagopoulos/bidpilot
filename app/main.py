import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import analytics, auth, awards, companies, drafts, matches, tenders
from app.core.exceptions import BidPilotError, bidpilot_exception_handler
from app.core.logging import configure_logging
from app.core.settings import settings
from app.ingestion.scheduler import start_scheduler, stop_scheduler
from app.repositories.demo_usage import ensure_demo_indexes
from app.repositories.mongo import close_client
from app.repositories.users import ensure_user_indexes

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    try:
        await ensure_user_indexes()
        await ensure_demo_indexes()
    except Exception as exc:
        # A Mongo hiccup on cold start shouldn't keep the app down; indexes already exist after first boot.
        logger.warning("index setup failed: %s", exc)
    start_scheduler()
    yield
    stop_scheduler()
    await close_client()


app = FastAPI(title="BidPilot", version="0.1.0", lifespan=lifespan)

app.add_exception_handler(BidPilotError, bidpilot_exception_handler)  # type: ignore[arg-type]

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    # Bearer tokens only, no cookies.
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth.router)
app.include_router(companies.router)
app.include_router(tenders.router)
app.include_router(matches.router)
app.include_router(drafts.router)
app.include_router(awards.router)
app.include_router(analytics.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
