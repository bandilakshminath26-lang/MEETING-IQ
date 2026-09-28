"""System status and diagnostics API endpoint."""

from __future__ import annotations
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.config import get_settings
from app.db.database import get_db
from app.db.models.models import Company, Meeting, Commitment, HindsightMemory
from app.hindsight import get_hindsight_client

router = APIRouter(prefix="/system", tags=["System"])
settings = get_settings()


@router.get("/status")
async def get_system_status(db: AsyncSession = Depends(get_db)):
    """Return live system integration health (Hindsight Cloud, LLM, and Database)."""
    hindsight = get_hindsight_client()
    hs_health = await hindsight.check_health()

    # Query database counts
    companies_count = (await db.execute(select(func.count(Company.id)))).scalar() or 0
    meetings_count = (await db.execute(select(func.count(Meeting.id)))).scalar() or 0
    commitments_count = (await db.execute(select(func.count(Commitment.id)))).scalar() or 0
    memories_count = (await db.execute(select(func.count(HindsightMemory.id)))).scalar() or 0

    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hindsight": {
            "configured": hs_health["is_configured"],
            "connected": hs_health["cloud_connected"],
            "mode": hs_health["mode"],  # "hindsight_cloud" or "local_fallback"
            "bank_id": hs_health["bank_id"],
            "base_url": hs_health["base_url"],
            "details": hs_health["details"],
            "fact_count": hs_health.get("fact_count", 0),
        },
        "llm": {
            "provider": settings.llm_provider,
            "model": settings.llm_model,
            "configured": bool(settings.groq_api_key or settings.openai_api_key),
            "status": "live" if settings.llm_provider in ("groq", "openai") else "mock",
        },
        "database": {
            "status": "connected",
            "type": "sqlite" if "sqlite" in settings.database_url else "postgresql",
            "counts": {
                "companies": companies_count,
                "meetings": meetings_count,
                "commitments": commitments_count,
                "memories": memories_count,
            },
        },
    }
