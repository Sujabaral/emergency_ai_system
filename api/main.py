
# api/main.py
import logging
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.ingest import router as ingest_router
from config.settings import settings


# Logging setup

logging.basicConfig(
    stream=sys.stdout,  #print logs to terminal
    # In development, show DEBUG messages and production show INFO+
    level=logging.DEBUG if settings.APP_ENV == "development" else logging.INFO,

    # Timestamp | level | logger name | message
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)

logger = logging.getLogger(__name__)

# App initialization

app = FastAPI(
    title="Emergency Detection API",
    description="Ingests monitoring events, deduplicates them, and classifies severity.",
    version="0.1.0",  # Phase 1 MVP
)

# Allow requests from any origin in development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.APP_ENV == "development" else [],
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)

# Register the ingest route — prefix keeps all v1 routes grouped
app.include_router(ingest_router, prefix="/api/v1")

# Lifecycle events
@app.on_event("startup")
async def on_startup() -> None:
    logger.info(
        "Emergency Detection API starting up | env=%s | dedup_window=%ds",
        settings.APP_ENV,
        settings.DEDUP_WINDOW_SECONDS,
    )

@app.on_event("shutdown")
async def on_shutdown() -> None:
    logger.info("Emergency Detection API shutting down")

# Health check 
@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok", "env": settings.APP_ENV}
