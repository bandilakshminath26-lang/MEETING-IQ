"""API routes for commitments."""

from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.db.models.models import Commitment
from app.schemas.schemas import CommitmentOut, CommitmentUpdate

router = APIRouter(prefix="/commitments", tags=["commitments"])


@router.get("/", response_model=list[CommitmentOut])
async def list_commitments(
    customer_id: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Commitment)
    if customer_id:
        stmt = stmt.where(Commitment.customer_id == customer_id)
    if status:
        stmt = stmt.where(Commitment.status == status)
    stmt = stmt.order_by(Commitment.date_created.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.patch("/{commitment_id}", response_model=CommitmentOut)
async def update_commitment(
    commitment_id: str,
    update: CommitmentUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Commitment).where(Commitment.commitment_id == commitment_id))
    commitment = result.scalar_one_or_none()
    if not commitment:
        raise HTTPException(status_code=404, detail="Commitment not found")
    if update.status is not None:
        commitment.status = update.status
    if update.evidence is not None:
        commitment.evidence = update.evidence
    await db.flush()
    return commitment
