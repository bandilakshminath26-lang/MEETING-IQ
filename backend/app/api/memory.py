"""API routes for Hindsight memory inspection."""

from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.db.models.models import Event
from app.hindsight import get_memory_service
from app.schemas.schemas import MemoryRecallRequest, MemoryRecallResponse, MemoryItem, TimelineEvent

router = APIRouter(prefix="/memory", tags=["memory"])


@router.post("/recall", response_model=MemoryRecallResponse)
async def recall_memory(req: MemoryRecallRequest):
    memory_service = get_memory_service()
    memories = await memory_service.recall_for_contact(
        req.query, req.customer_id or "", req.contact_id, limit=req.limit,
    )
    items = []
    for mem in memories:
        items.append(MemoryItem(
            content=mem.get("content", mem.get("fact", str(mem))),
            category=mem.get("metadata", {}).get("event_type"),
            customer_id=mem.get("metadata", {}).get("customer_id"),
            contact_id=mem.get("metadata", {}).get("contact_id"),
            event_type=mem.get("metadata", {}).get("event_type"),
            event_date=mem.get("metadata", {}).get("event_date"),
            source=mem.get("metadata", {}).get("source"),
            relevance_score=mem.get("score", mem.get("relevance_score")),
        ))
    return MemoryRecallResponse(memories=items, total=len(items))


@router.get("/contact/{customer_id}", response_model=list[TimelineEvent])
async def get_contact_memories(customer_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Event)
        .where(Event.customer_id == customer_id)
        .order_by(Event.event_date)
    )
    return result.scalars().all()
