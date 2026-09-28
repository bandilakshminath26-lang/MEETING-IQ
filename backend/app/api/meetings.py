"""API routes for meetings — upcoming, past, details, memory preview, and preparation."""

from __future__ import annotations
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.db.database import get_db
from app.db.models.models import (
    Meeting, Company, Contact, Commitment, Decision, Concern, HindsightMemory,
)
from app.schemas.schemas import (
    MeetingOut, MeetingDetailOut, MeetingMemoryPreview,
)

router = APIRouter(prefix="/meetings", tags=["meetings"])


def _meeting_status(meeting: Meeting) -> str:
    """Compute meeting status dynamically from scheduled_at or date."""
    if meeting.status and meeting.status in ("cancelled",):
        return meeting.status
    now = datetime.now(timezone.utc)
    if meeting.scheduled_at:
        return "upcoming" if meeting.scheduled_at.replace(tzinfo=timezone.utc) > now else "completed"
    # Fallback: parse the date string
    try:
        d = datetime.strptime(meeting.date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return "upcoming" if d > now else "completed"
    except Exception:
        return meeting.status or "completed"


def _serialize_meeting(m: Meeting) -> dict:
    """Convert a Meeting ORM object to a serializable dict with computed status."""
    return {
        "meeting_id": m.meeting_id,
        "customer_id": m.customer_id,
        "contact_id": m.contact_id,
        "date": m.date,
        "title": m.title,
        "participants": m.participants,
        "summary": m.summary,
        "topics": m.topics,
        "transcript": m.transcript,
        "source": m.source,
        "scheduled_at": m.scheduled_at.isoformat() if m.scheduled_at else None,
        "status": _meeting_status(m),
        "location": m.location,
        "agenda": m.agenda,
    }


@router.get("/", response_model=list[MeetingOut])
async def list_meetings(
    customer_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Meeting)
    if customer_id:
        stmt = stmt.where(Meeting.customer_id == customer_id)
    stmt = stmt.order_by(desc(Meeting.date))
    result = await db.execute(stmt)
    meetings = result.scalars().all()
    return [_serialize_meeting(m) for m in meetings]


@router.get("/upcoming", response_model=list[MeetingOut])
async def list_upcoming_meetings(
    customer_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Meeting)
    if customer_id:
        stmt = stmt.where(Meeting.customer_id == customer_id)
    stmt = stmt.order_by(Meeting.date)
    result = await db.execute(stmt)
    meetings = result.scalars().all()
    upcoming = [m for m in meetings if _meeting_status(m) == "upcoming"]
    return [_serialize_meeting(m) for m in upcoming]


@router.get("/past", response_model=list[MeetingOut])
async def list_past_meetings(
    customer_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Meeting)
    if customer_id:
        stmt = stmt.where(Meeting.customer_id == customer_id)
    stmt = stmt.order_by(desc(Meeting.date))
    result = await db.execute(stmt)
    meetings = result.scalars().all()
    past = [m for m in meetings if _meeting_status(m) == "completed"]
    return [_serialize_meeting(m) for m in past]


@router.get("/{meeting_id}", response_model=MeetingDetailOut)
async def get_meeting_detail(
    meeting_id: str,
    date: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Get full meeting details with decisions, commitments, concerns, related meetings, memory count."""
    stmt = select(Meeting).where(Meeting.meeting_id == meeting_id)
    if date:
        stmt = stmt.where(Meeting.date == date)
    stmt = stmt.limit(1)
    result = await db.execute(stmt)
    meeting = result.scalar_one_or_none()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Fetch company + contact
    co = await db.execute(select(Company).where(Company.customer_id == meeting.customer_id))
    company = co.scalar_one_or_none()
    ct = await db.execute(select(Contact).where(Contact.contact_id == meeting.contact_id))
    contact = ct.scalar_one_or_none()

    # Decisions for this customer
    dec_result = await db.execute(
        select(Decision)
        .where(Decision.customer_id == meeting.customer_id)
        .order_by(desc(Decision.date))
    )
    decisions = [
        {"decision_id": d.decision_id, "date": d.date, "decision": d.decision, "status": d.status}
        for d in dec_result.scalars().all()
    ]

    # Commitments for this customer
    comm_result = await db.execute(
        select(Commitment)
        .where(Commitment.customer_id == meeting.customer_id)
        .order_by(desc(Commitment.date_created))
    )
    commitments_list = [
        {
            "commitment_id": c.commitment_id, "commitment": c.commitment,
            "owner": c.owner, "status": c.status, "due_date": c.due_date,
            "date_created": c.date_created,
        }
        for c in comm_result.scalars().all()
    ]

    # Concerns for this customer
    conc_result = await db.execute(
        select(Concern)
        .where(Concern.customer_id == meeting.customer_id)
        .order_by(desc(Concern.date))
    )
    concerns_list = [
        {"concern_id": c.concern_id, "date": c.date, "concern": c.concern, "severity": c.severity, "status": c.status}
        for c in conc_result.scalars().all()
    ]

    # Related meetings (same customer, different date)
    rel_result = await db.execute(
        select(Meeting)
        .where(Meeting.customer_id == meeting.customer_id, Meeting.date != meeting.date)
        .order_by(desc(Meeting.date))
        .limit(10)
    )
    related = [
        {"meeting_id": r.meeting_id, "date": r.date, "title": r.title, "status": _meeting_status(r)}
        for r in rel_result.scalars().all()
    ]

    # Memory count from Hindsight
    mem_result = await db.execute(
        select(HindsightMemory)
        .where(HindsightMemory.customer_id == meeting.customer_id)
    )
    memory_count = len(mem_result.scalars().all())

    data = _serialize_meeting(meeting)
    data.update({
        "company_name": company.company_name if company else None,
        "contact_name": contact.name if contact else None,
        "contact_role": contact.role if contact else None,
        "decisions": decisions,
        "commitments": commitments_list,
        "concerns": concerns_list,
        "related_meetings": related,
        "memory_count": memory_count,
    })
    return data


@router.get("/{meeting_id}/memory-preview", response_model=MeetingMemoryPreview)
async def get_meeting_memory_preview(
    meeting_id: str,
    date: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Get Hindsight-powered memory preview for an upcoming meeting."""
    stmt = select(Meeting).where(Meeting.meeting_id == meeting_id)
    if date:
        stmt = stmt.where(Meeting.date == date)
    stmt = stmt.limit(1)
    result = await db.execute(stmt)
    meeting = result.scalar_one_or_none()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    customer_id = meeting.customer_id

    # ── Use real Hindsight recall ──
    from app.hindsight.memory_service import get_memory_service
    memory = get_memory_service()

    # 1. Last discussed — most recent meeting memory
    recent_memories = await memory.recall_for_contact(
        f"most recent discussion topics with customer {customer_id}",
        customer_id, meeting.contact_id, limit=5,
    )
    last_discussed = None
    if recent_memories:
        for mem in recent_memories:
            meta = mem.get("metadata", {})
            if meta.get("event_type") == "meeting":
                content = mem.get("content", "")
                # Extract a concise summary
                lines = content.split("\n")
                for line in lines:
                    if line.startswith("Summary:"):
                        last_discussed = line.replace("Summary:", "").strip()
                        break
                if not last_discussed and len(lines) > 0:
                    last_discussed = lines[0][:200]
                break
        if not last_discussed and recent_memories:
            last_discussed = recent_memories[0].get("content", "")[:200]

    # 2. Open commitment
    commitment_memories = await memory.recall_commitments(customer_id, limit=5)
    open_commitment = None
    open_commitment_source = None
    for mem in commitment_memories:
        content = mem.get("content", "")
        if "open" in content.lower() or "Status: open" in content:
            lines = content.split("\n")
            for line in lines:
                if line.startswith("Commitment:"):
                    open_commitment = line.replace("Commitment:", "").strip()
                    break
            if not open_commitment:
                open_commitment = lines[0][:200]
            meta = mem.get("metadata", {})
            open_commitment_source = f"Meeting — {meta.get('event_date', 'Unknown date')}"
            break

    # 3. Recurring concern
    concern_memories = await memory.recall_concerns(customer_id, limit=10)
    concern_counter: dict[str, list[str]] = {}
    for mem in concern_memories:
        content = mem.get("content", "")
        meta = mem.get("metadata", {})
        lines = content.split("\n")
        concern_text = None
        for line in lines:
            if line.startswith("Concern:"):
                concern_text = line.replace("Concern:", "").strip()
                break
        if concern_text:
            key = concern_text.lower().strip()
            concern_counter.setdefault(key, []).append(meta.get("event_date", ""))
    recurring_concern = None
    recurring_concern_sources: list[str] = []
    for concern, dates in sorted(concern_counter.items(), key=lambda x: len(x[1]), reverse=True):
        if len(dates) > 1:
            recurring_concern = concern.capitalize()
            recurring_concern_sources = [f"Meeting — {d}" for d in dates if d]
            break
    if not recurring_concern and concern_memories:
        content = concern_memories[0].get("content", "")
        lines = content.split("\n")
        for line in lines:
            if line.startswith("Concern:"):
                recurring_concern = line.replace("Concern:", "").strip()
                break

    # 4. Previous decision
    decision_memories = await memory.recall_decisions(customer_id, limit=3)
    previous_decision = None
    for mem in decision_memories:
        content = mem.get("content", "")
        lines = content.split("\n")
        for line in lines:
            if line.startswith("Decision:"):
                previous_decision = line.replace("Decision:", "").strip()
                break
        if previous_decision:
            break

    # 5. What changed — recent changes
    changes = await memory.recall_recent_changes(customer_id, limit=5)
    what_changed = None
    if changes:
        content = changes[0].get("content", "")
        what_changed = content[:200]

    # 6. Suggested question — synthesize from open items
    suggested_question = None
    if open_commitment:
        suggested_question = f"Have you had a chance to review the {open_commitment.lower().rstrip('.')}?"
    elif recurring_concern:
        suggested_question = f"Has your team made progress on the {recurring_concern.lower().rstrip('.')} concern?"
    elif last_discussed:
        suggested_question = f"What has changed since we last discussed {last_discussed[:60].lower().rstrip('.')}?"

    return MeetingMemoryPreview(
        last_discussed=last_discussed,
        open_commitment=open_commitment,
        open_commitment_source=open_commitment_source,
        recurring_concern=recurring_concern,
        recurring_concern_sources=recurring_concern_sources,
        previous_decision=previous_decision,
        what_changed=what_changed,
        suggested_question=suggested_question,
    )
