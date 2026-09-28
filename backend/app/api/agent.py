"""API routes for the AI agent (chat, meeting brief, comparison demo)."""

from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.agents.meeting_agent import MeetingAgent
from app.schemas.schemas import (
    ChatRequest, ChatResponse,
    MeetingBriefRequest, MeetingBriefResponse,
    DemoComparisonRequest, DemoComparisonResponse,
    LearningCurveRequest, LearningCurveResponse,
)

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/chat", response_model=ChatResponse)
async def agent_chat(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    agent = MeetingAgent(db)
    result = await agent.chat(req.message, req.customer_id, req.contact_id)
    return ChatResponse(**result)


@router.post("/meeting-brief", response_model=MeetingBriefResponse)
async def meeting_brief(req: MeetingBriefRequest, db: AsyncSession = Depends(get_db)):
    agent = MeetingAgent(db)
    result = await agent.generate_meeting_brief(req.customer_id, req.contact_id)
    return MeetingBriefResponse(**result)


@router.post("/comparison", response_model=DemoComparisonResponse)
async def demo_comparison(req: DemoComparisonRequest, db: AsyncSession = Depends(get_db)):
    agent = MeetingAgent(db)
    result = await agent.generate_comparison(req.customer_id, req.contact_id)
    return DemoComparisonResponse(**result)


@router.post("/learning-curve", response_model=LearningCurveResponse)
async def learning_curve(req: LearningCurveRequest, db: AsyncSession = Depends(get_db)):
    agent = MeetingAgent(db)
    result = await agent.generate_learning_curve(req.customer_id, req.contact_id)
    return LearningCurveResponse(**result)

