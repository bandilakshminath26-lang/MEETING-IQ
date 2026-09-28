"""API routes for customers/companies."""

from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.db.models.models import Company
from app.schemas.schemas import CompanyOut

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("/", response_model=list[CompanyOut])
async def list_customers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Company).order_by(Company.company_name))
    return result.scalars().all()


@router.get("/{customer_id}", response_model=CompanyOut)
async def get_customer(customer_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Company).where(Company.customer_id == customer_id))
    company = result.scalar_one_or_none()
    if not company:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Customer not found")
    return company
