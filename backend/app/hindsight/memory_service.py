"""High-level memory service that sits on top of the Hindsight client.

Provides domain-specific retain operations for meetings, emails, etc.
"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from app.hindsight.client import get_hindsight_client, HindsightClient

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class MemoryService:
    """Domain-aware memory operations built on Hindsight."""

    def __init__(self, client: HindsightClient | None = None):
        self.client = client or get_hindsight_client()

    # ── Retain helpers ────────────────────────────────────────

    async def retain_meeting(
        self,
        customer_id: str,
        contact_id: str,
        meeting_id: str,
        date: str,
        title: str,
        summary: str,
        topics: list[str] | None = None,
        transcript: str | None = None,
        db_session: AsyncSession | None = None,
    ) -> bool:
        content = (
            f"Meeting: {title}\n"
            f"Date: {date}\n"
            f"Summary: {summary}\n"
        )
        if topics:
            content += f"Topics: {', '.join(topics)}\n"
        if transcript:
            content += f"Transcript excerpt:\n{transcript[:1500]}\n"
        return await self.client.retain(content, metadata={
            "customer_id": customer_id,
            "contact_id": contact_id,
            "event_id": meeting_id,
            "event_type": "meeting",
            "event_date": date,
            "source": "meeting",
        }, db_session=db_session)

    async def retain_email(
        self,
        customer_id: str,
        contact_id: str,
        email_id: str,
        date: str,
        subject: str,
        body: str,
        direction: str,
        db_session: AsyncSession | None = None,
    ) -> bool:
        content = (
            f"Email ({direction}): {subject}\n"
            f"Date: {date}\n"
            f"Content: {body[:1500]}\n"
        )
        return await self.client.retain(content, metadata={
            "customer_id": customer_id,
            "contact_id": contact_id,
            "event_id": email_id,
            "event_type": "email",
            "event_date": date,
            "source": "email",
        }, db_session=db_session)

    async def retain_commitment(
        self,
        customer_id: str,
        contact_id: str | None,
        commitment_id: str,
        date: str,
        commitment: str,
        owner: str,
        status: str,
        due_date: str | None = None,
        db_session: AsyncSession | None = None,
    ) -> bool:
        content = (
            f"Commitment: {commitment}\n"
            f"Owner: {owner}\n"
            f"Status: {status}\n"
            f"Created: {date}\n"
        )
        if due_date:
            content += f"Due: {due_date}\n"
        return await self.client.retain(content, metadata={
            "customer_id": customer_id,
            "contact_id": contact_id or "",
            "event_id": commitment_id,
            "event_type": "commitment",
            "event_date": date,
            "source": "commitment",
            "importance": "high" if status == "open" else "normal",
        }, db_session=db_session)

    async def retain_decision(
        self,
        customer_id: str,
        contact_id: str | None,
        decision_id: str,
        date: str,
        decision: str,
        owner: str | None = None,
        status: str = "active",
        db_session: AsyncSession | None = None,
    ) -> bool:
        content = (
            f"Decision: {decision}\n"
            f"Date: {date}\n"
            f"Status: {status}\n"
        )
        if owner:
            content += f"Owner: {owner}\n"
        return await self.client.retain(content, metadata={
            "customer_id": customer_id,
            "contact_id": contact_id or "",
            "event_id": decision_id,
            "event_type": "decision",
            "event_date": date,
            "source": "decision",
        }, db_session=db_session)

    async def retain_concern(
        self,
        customer_id: str,
        contact_id: str | None,
        concern_id: str,
        date: str,
        concern: str,
        severity: str = "medium",
        db_session: AsyncSession | None = None,
    ) -> bool:
        content = (
            f"Concern: {concern}\n"
            f"Date: {date}\n"
            f"Severity: {severity}\n"
        )
        return await self.client.retain(content, metadata={
            "customer_id": customer_id,
            "contact_id": contact_id or "",
            "event_id": concern_id,
            "event_type": "concern",
            "event_date": date,
            "source": "concern",
            "importance": "high" if severity == "high" else "normal",
        }, db_session=db_session)

    async def retain_preference(
        self,
        customer_id: str,
        contact_id: str,
        preference_id: str,
        preference: str,
        pref_source: str | None = None,
        db_session: AsyncSession | None = None,
    ) -> bool:
        content = (
            f"Contact Preference: {preference}\n"
        )
        if pref_source:
            content += f"Source: {pref_source}\n"
        return await self.client.retain(content, metadata={
            "customer_id": customer_id,
            "contact_id": contact_id,
            "event_id": preference_id,
            "event_type": "preference",
            "source": "preference",
        }, db_session=db_session)

    # ── Recall helpers ────────────────────────────────────────

    async def recall_for_contact(self, query: str, customer_id: str, contact_id: str | None = None, limit: int = 20) -> list[dict]:
        metadata_filter = {"customer_id": customer_id}
        if contact_id:
            metadata_filter["contact_id"] = contact_id
        return await self.client.recall(query, limit=limit, metadata_filter=metadata_filter)

    async def recall_commitments(self, customer_id: str, limit: int = 10) -> list[dict]:
        return await self.client.recall(
            "open commitments and promises",
            limit=limit,
            metadata_filter={"customer_id": customer_id, "event_type": "commitment"},
        )

    async def recall_concerns(self, customer_id: str, limit: int = 10) -> list[dict]:
        return await self.client.recall(
            "recurring concerns and issues",
            limit=limit,
            metadata_filter={"customer_id": customer_id, "event_type": "concern"},
        )

    async def recall_decisions(self, customer_id: str, limit: int = 10) -> list[dict]:
        return await self.client.recall(
            "important decisions made",
            limit=limit,
            metadata_filter={"customer_id": customer_id, "event_type": "decision"},
        )

    async def recall_preferences(self, customer_id: str, contact_id: str | None = None, limit: int = 5) -> list[dict]:
        mf: dict = {"customer_id": customer_id, "event_type": "preference"}
        if contact_id:
            mf["contact_id"] = contact_id
        return await self.client.recall("contact preferences and communication style", limit=limit, metadata_filter=mf)

    async def recall_recent_changes(self, customer_id: str, limit: int = 10) -> list[dict]:
        return await self.client.recall(
            "what changed recently? Recent developments, new concerns, status updates",
            limit=limit,
            metadata_filter={"customer_id": customer_id},
        )

    async def reflect_on_relationship(self, customer_id: str, contact_name: str) -> str | None:
        return await self.client.reflect(
            f"Summarize the entire relationship history with {contact_name} (customer {customer_id}). "
            f"Include key milestones, recurring themes, open items, and how the relationship evolved."
        )


def get_memory_service() -> MemoryService:
    return MemoryService()
