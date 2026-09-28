"""API routes for contacts."""

from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.db.models.models import Contact, Company, Meeting, Email, Commitment, Decision, Concern, Preference, Event
from app.schemas.schemas import (
    ContactOut, MeetingOut, EmailOut, CommitmentOut, DecisionOut,
    ConcernOut, PreferenceOut, TimelineEvent,
)

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("/", response_model=list[ContactOut])
async def list_contacts(customer_id: str | None = None, db: AsyncSession = Depends(get_db)):
    stmt = select(Contact).join(Company, Contact.customer_id == Company.customer_id)
    if customer_id:
        stmt = stmt.where(Contact.customer_id == customer_id)
    stmt = stmt.order_by(Contact.name)
    result = await db.execute(stmt)
    contacts = result.scalars().all()
    # Fetch company names
    out = []
    for c in contacts:
        co = await db.execute(select(Company).where(Company.customer_id == c.customer_id))
        company = co.scalar_one_or_none()
        out.append(ContactOut(
            contact_id=c.contact_id,
            customer_id=c.customer_id,
            name=c.name,
            role=c.role,
            email=c.email,
            company_name=company.company_name if company else None,
        ))
    return out


@router.get("/{contact_id}", response_model=ContactOut)
async def get_contact(contact_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Contact).where(Contact.contact_id == contact_id))
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    co = await db.execute(select(Company).where(Company.customer_id == contact.customer_id))
    company = co.scalar_one_or_none()
    return ContactOut(
        contact_id=contact.contact_id,
        customer_id=contact.customer_id,
        name=contact.name,
        role=contact.role,
        email=contact.email,
        company_name=company.company_name if company else None,
    )


@router.get("/{contact_id}/meetings", response_model=list[MeetingOut])
async def get_contact_meetings(contact_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Meeting).where(Meeting.contact_id == contact_id).order_by(Meeting.date.desc())
    )
    return result.scalars().all()


@router.get("/{contact_id}/emails", response_model=list[EmailOut])
async def get_contact_emails(contact_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Email).where(Email.contact_id == contact_id).order_by(Email.date.desc())
    )
    return result.scalars().all()


@router.get("/{contact_id}/commitments", response_model=list[CommitmentOut])
async def get_contact_commitments(contact_id: str, db: AsyncSession = Depends(get_db)):
    # Get customer_id from contact
    cr = await db.execute(select(Contact).where(Contact.contact_id == contact_id))
    contact = cr.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    result = await db.execute(
        select(Commitment).where(Commitment.customer_id == contact.customer_id).order_by(Commitment.date_created.desc())
    )
    return result.scalars().all()


@router.get("/{contact_id}/decisions", response_model=list[DecisionOut])
async def get_contact_decisions(contact_id: str, db: AsyncSession = Depends(get_db)):
    cr = await db.execute(select(Contact).where(Contact.contact_id == contact_id))
    contact = cr.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    result = await db.execute(
        select(Decision).where(Decision.customer_id == contact.customer_id).order_by(Decision.date.desc())
    )
    return result.scalars().all()


@router.get("/{contact_id}/concerns", response_model=list[ConcernOut])
async def get_contact_concerns(contact_id: str, db: AsyncSession = Depends(get_db)):
    cr = await db.execute(select(Contact).where(Contact.contact_id == contact_id))
    contact = cr.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    result = await db.execute(
        select(Concern).where(Concern.customer_id == contact.customer_id).order_by(Concern.date.desc())
    )
    return result.scalars().all()


@router.get("/{contact_id}/timeline", response_model=list[TimelineEvent])
async def get_contact_timeline(contact_id: str, db: AsyncSession = Depends(get_db)):
    cr = await db.execute(select(Contact).where(Contact.contact_id == contact_id))
    contact = cr.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    result = await db.execute(
        select(Event)
        .where(Event.customer_id == contact.customer_id)
        .order_by(Event.event_date)
    )
    return result.scalars().all()
