"""Meeting Intelligence Agent — FastAPI application entry point."""

from __future__ import annotations
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.database import init_db
from app.hindsight import get_hindsight_client
from app.api import customers, contacts, commitments, agent, memory, meetings, system

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-30s | %(levelname)-7s | %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create tables, ensure Hindsight bank. Shutdown: close clients."""
    logger.info("Starting Meeting Intelligence Agent (%s mode)", settings.app_env)
    await init_db()
    logger.info("Database tables created")

    hindsight = get_hindsight_client()
    await hindsight.ensure_bank()

    yield

    await hindsight.close()
    logger.info("Shutdown complete")


app = FastAPI(
    title="Meeting Intelligence Agent",
    description="Memory-Powered Meeting Intelligence & Preparation Agent — Built for the Hindsight Hackathon",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(customers.router, prefix="/api")
app.include_router(contacts.router, prefix="/api")
app.include_router(commitments.router, prefix="/api")
app.include_router(agent.router, prefix="/api")
app.include_router(memory.router, prefix="/api")
app.include_router(meetings.router, prefix="/api")
app.include_router(system.router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": "Meeting Intelligence Agent",
        "version": "1.0.0",
        "description": "Memory-Powered Meeting Preparation Agent",
        "hindsight_configured": get_hindsight_client().is_configured,
        "llm_provider": settings.llm_provider,
    }


@app.get("/health")
@app.get("/api/health")
async def health():
    return {"status": "healthy", "env": settings.app_env}


# ── Data seeding endpoint (development only) ─────────────────
@app.post("/datasets/ingest-synthetic")
async def ingest_synthetic():
    """Load the synthetic dataset into PostgreSQL + Hindsight."""
    from app.db.database import async_session_factory
    from app.ingestion.dataset_loader import load_synthetic_dataset
    from app.hindsight import get_memory_service

    async with async_session_factory() as session:
        try:
            memory = get_memory_service()
            counts = await load_synthetic_dataset(session, memory)
            return {"status": "success", "counts": counts}
        except Exception as e:
            logger.error("Ingestion failed: %s", e)
            return {"status": "error", "message": str(e)}


# ── App init ──────────────────────────────────────────────────
# app/__init__.py
