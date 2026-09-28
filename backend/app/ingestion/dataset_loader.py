"""Dataset loader for the synthetic longitudinal dataset.

Reads .jsonl files from data/synthetic/ and populates PostgreSQL + Hindsight.
"""

from __future__ import annotations
import json
import logging
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.models import (
    Company, Contact, Meeting, Email, Commitment,
    Decision, Concern, Preference, Event, RelationshipSnapshot,
)
from app.hindsight.memory_service import MemoryService

logger = logging.getLogger(__name__)


def _read_jsonl(filepath: Path) -> list[dict]:
    items = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


async def load_synthetic_dataset(
    db: AsyncSession,
    memory: MemoryService,
    data_dir: str | Path = "data/synthetic",
) -> dict:
    """Load the synthetic dataset into PostgreSQL and Hindsight.

    Returns a dict of counts.
    """
    data_dir = Path(data_dir)
    counts = {}

    # ── Companies ─────────────────────────────────────────────
    companies_file = data_dir / "companies.jsonl"
    if companies_file.exists():
        companies = _read_jsonl(companies_file)
        for c in companies:
            existing = await db.execute(select(Company).where(Company.customer_id == c["customer_id"]))
            if existing.scalar_one_or_none():
                continue
            db.add(Company(
                customer_id=c["customer_id"],
                company_name=c["company_name"],
                industry=c.get("industry"),
                segment=c.get("segment"),
                country=c.get("country"),
            ))
        await db.flush()
        counts["companies"] = len(companies)
        logger.info("Loaded %d companies", len(companies))

    # ── Contacts ──────────────────────────────────────────────
    contacts_file = data_dir / "contacts.jsonl"
    if contacts_file.exists():
        contacts = _read_jsonl(contacts_file)
        for c in contacts:
            existing = await db.execute(select(Contact).where(Contact.contact_id == c["contact_id"]))
            if existing.scalar_one_or_none():
                continue
            db.add(Contact(
                contact_id=c["contact_id"],
                customer_id=c["customer_id"],
                name=c["name"],
                role=c.get("role"),
                email=c.get("email"),
            ))
        await db.flush()
        counts["contacts"] = len(contacts)
        logger.info("Loaded %d contacts", len(contacts))

    # ── Meetings ──────────────────────────────────────────────
    meetings_file = data_dir / "meetings.jsonl"
    if meetings_file.exists():
        meetings = _read_jsonl(meetings_file)
        for m in meetings:
            # Use a composite unique key
            mid = f"{m['meeting_id']}_{m['customer_id']}_{m['date']}"
            existing = await db.execute(
                select(Meeting).where(
                    Meeting.meeting_id == m["meeting_id"],
                    Meeting.customer_id == m["customer_id"],
                    Meeting.date == m["date"],
                )
            )
            if existing.scalar_one_or_none():
                continue
            db.add(Meeting(
                meeting_id=m["meeting_id"],
                customer_id=m["customer_id"],
                contact_id=m.get("contact_id", ""),
                date=m["date"],
                title=m.get("title", ""),
                participants=m.get("participants"),
                summary=m.get("summary"),
                topics=m.get("topics"),
                transcript=m.get("transcript"),
                source="synthetic",
            ))
            # Retain in Hindsight
            await memory.retain_meeting(
                customer_id=m["customer_id"],
                contact_id=m.get("contact_id", ""),
                meeting_id=m["meeting_id"],
                date=m["date"],
                title=m.get("title", ""),
                summary=m.get("summary", ""),
                topics=m.get("topics"),
                transcript=m.get("transcript"),
                db_session=db,
            )
        await db.flush()
        counts["meetings"] = len(meetings)
        logger.info("Loaded %d meetings", len(meetings))

    # ── Emails ────────────────────────────────────────────────
    emails_file = data_dir / "emails.jsonl"
    if emails_file.exists():
        emails = _read_jsonl(emails_file)
        for e in emails:
            existing = await db.execute(select(Email).where(Email.email_id == e["email_id"]))
            if existing.scalar_one_or_none():
                continue
            db.add(Email(
                email_id=e["email_id"],
                customer_id=e["customer_id"],
                contact_id=e.get("contact_id", ""),
                date=e["date"],
                direction=e.get("direction", "unknown"),
                subject=e.get("subject", ""),
                sender=e.get("from", ""),
                recipient=e.get("to", ""),
                body=e.get("body"),
                related_meeting_id=e.get("related_meeting_id"),
                source="synthetic",
            ))
            # Retain in Hindsight
            await memory.retain_email(
                customer_id=e["customer_id"],
                contact_id=e.get("contact_id", ""),
                email_id=e["email_id"],
                date=e["date"],
                subject=e.get("subject", ""),
                body=e.get("body", ""),
                direction=e.get("direction", "unknown"),
                db_session=db,
            )
        await db.flush()
        counts["emails"] = len(emails)
        logger.info("Loaded %d emails", len(emails))

    # ── Commitments ───────────────────────────────────────────
    commitments_file = data_dir / "commitments.jsonl"
    if commitments_file.exists():
        commitments = _read_jsonl(commitments_file)
        for c in commitments:
            existing = await db.execute(select(Commitment).where(Commitment.commitment_id == c["commitment_id"]))
            if existing.scalar_one_or_none():
                continue
            # Find contact_id from customer_id
            cr = await db.execute(select(Contact).where(Contact.customer_id == c["customer_id"]).limit(1))
            contact = cr.scalar_one_or_none()
            contact_id = contact.contact_id if contact else None

            db.add(Commitment(
                commitment_id=c["commitment_id"],
                customer_id=c["customer_id"],
                contact_id=contact_id,
                meeting_id=c.get("meeting_id"),
                date_created=c["date_created"],
                owner=c["owner"],
                commitment=c["commitment"],
                due_date=c.get("due_date"),
                status=c.get("status", "open"),
                evidence=c.get("evidence"),
            ))
            await memory.retain_commitment(
                customer_id=c["customer_id"],
                contact_id=contact_id,
                commitment_id=c["commitment_id"],
                date=c["date_created"],
                commitment=c["commitment"],
                owner=c["owner"],
                status=c.get("status", "open"),
                due_date=c.get("due_date"),
                db_session=db,
            )
        await db.flush()
        counts["commitments"] = len(commitments)
        logger.info("Loaded %d commitments", len(commitments))

    # ── Decisions ─────────────────────────────────────────────
    decisions_file = data_dir / "decisions.jsonl"
    if decisions_file.exists():
        decisions = _read_jsonl(decisions_file)
        for d in decisions:
            existing = await db.execute(select(Decision).where(Decision.decision_id == d["decision_id"]))
            if existing.scalar_one_or_none():
                continue
            cr = await db.execute(select(Contact).where(Contact.customer_id == d["customer_id"]).limit(1))
            contact = cr.scalar_one_or_none()
            contact_id = contact.contact_id if contact else None

            db.add(Decision(
                decision_id=d["decision_id"],
                customer_id=d["customer_id"],
                contact_id=contact_id,
                meeting_id=d.get("meeting_id"),
                date=d["date"],
                decision=d["decision"],
                owner=d.get("owner"),
                status=d.get("status", "active"),
            ))
            await memory.retain_decision(
                customer_id=d["customer_id"],
                contact_id=contact_id,
                decision_id=d["decision_id"],
                date=d["date"],
                decision=d["decision"],
                owner=d.get("owner"),
                status=d.get("status", "active"),
                db_session=db,
            )
        await db.flush()
        counts["decisions"] = len(decisions)
        logger.info("Loaded %d decisions", len(decisions))

    # ── Concerns ──────────────────────────────────────────────
    concerns_file = data_dir / "concerns.jsonl"
    if concerns_file.exists():
        concerns = _read_jsonl(concerns_file)
        for c in concerns:
            existing = await db.execute(select(Concern).where(Concern.concern_id == c["concern_id"]))
            if existing.scalar_one_or_none():
                continue
            cr = await db.execute(select(Contact).where(Contact.customer_id == c["customer_id"]).limit(1))
            contact = cr.scalar_one_or_none()
            contact_id = contact.contact_id if contact else None

            db.add(Concern(
                concern_id=c["concern_id"],
                customer_id=c["customer_id"],
                contact_id=contact_id,
                meeting_id=c.get("meeting_id"),
                date=c["date"],
                concern=c["concern"],
                severity=c.get("severity", "medium"),
                status=c.get("status", "open"),
            ))
            await memory.retain_concern(
                customer_id=c["customer_id"],
                contact_id=contact_id,
                concern_id=c["concern_id"],
                date=c["date"],
                concern=c["concern"],
                severity=c.get("severity", "medium"),
                db_session=db,
            )
        await db.flush()
        counts["concerns"] = len(concerns)
        logger.info("Loaded %d concerns", len(concerns))

    # ── Preferences ───────────────────────────────────────────
    preferences_file = data_dir / "preferences.jsonl"
    if preferences_file.exists():
        preferences = _read_jsonl(preferences_file)
        for p in preferences:
            existing = await db.execute(select(Preference).where(Preference.preference_id == p["preference_id"]))
            if existing.scalar_one_or_none():
                continue
            db.add(Preference(
                preference_id=p["preference_id"],
                customer_id=p["customer_id"],
                contact_id=p["contact_id"],
                preference=p["preference"],
                source=p.get("source"),
                confidence=p.get("confidence", 0.5),
            ))
            await memory.retain_preference(
                customer_id=p["customer_id"],
                contact_id=p["contact_id"],
                preference_id=p["preference_id"],
                preference=p["preference"],
                pref_source=p.get("source"),
                db_session=db,
            )
        await db.flush()
        counts["preferences"] = len(preferences)
        logger.info("Loaded %d preferences", len(preferences))

    # ── Events ────────────────────────────────────────────────
    events_file = data_dir / "events.jsonl"
    if events_file.exists():
        events = _read_jsonl(events_file)
        for ev in events:
            ref_id = ev.get("meeting_id") or ev.get("email_id") or ev.get("commitment_id") or ev.get("concern_id") or ev.get("decision_id") or ev.get("preference_id")
            db.add(Event(
                event_type=ev["event_type"],
                event_date=ev["event_date"],
                customer_id=ev["customer_id"],
                contact_id=ev.get("contact_id"),
                reference_id=ref_id,
                title=ev.get("title", ev.get("subject", ev.get("commitment", ev.get("concern", ev.get("decision", ""))))),
                summary=ev.get("summary", ev.get("body", ev.get("evidence", ""))),
                metadata_json=ev,
            ))
        await db.flush()
        counts["events"] = len(events)
        logger.info("Loaded %d events", len(events))

    # ── Relationship Snapshots ────────────────────────────────
    snap_file = data_dir / "relationship_snapshots.jsonl"
    if snap_file.exists():
        snapshots = _read_jsonl(snap_file)
        for s in snapshots:
            existing = await db.execute(select(RelationshipSnapshot).where(RelationshipSnapshot.customer_id == s["customer_id"]))
            if existing.scalar_one_or_none():
                continue
            db.add(RelationshipSnapshot(
                customer_id=s["customer_id"],
                company=s["company"],
                contact=s["contact"],
                role=s.get("role"),
                relationship_stage=s.get("relationship_stage", "unknown"),
                primary_concern=s.get("primary_concern"),
                open_commitments=s.get("open_commitments", 0),
                meeting_count=s.get("meeting_count", 0),
                email_count=s.get("email_count", 0),
            ))
        await db.flush()
        counts["relationship_snapshots"] = len(snapshots)
        logger.info("Loaded %d relationship snapshots", len(snapshots))

    await db.commit()
    logger.info("Synthetic dataset loaded successfully: %s", counts)
    return counts
