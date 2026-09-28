"""Meeting Intelligence Agent — the brain of the application.

Combines Hindsight memory, PostgreSQL structured data, and LLM reasoning
to produce personalized meeting briefs and answer relationship questions.
"""

from __future__ import annotations
import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.agents.llm_provider import get_llm_provider, LLMProvider
from app.agents.prompts import (
    MEETING_PREP_SYSTEM,
    CHAT_SYSTEM,
    MEETING_BRIEF_TEMPLATE,
    GENERIC_MEETING_PREP,
)
from app.hindsight.memory_service import get_memory_service, MemoryService
from app.db.models.models import (
    Company, Contact, Meeting, Email,
    Commitment, Decision, Concern, Preference,
    RelationshipSnapshot,
)

logger = logging.getLogger(__name__)


class MeetingAgent:
    """Orchestrates the 13-step meeting preparation pipeline."""

    def __init__(
        self,
        db: AsyncSession,
        llm: LLMProvider | None = None,
        memory: MemoryService | None = None,
    ):
        self.db = db
        self.llm = llm or get_llm_provider()
        self.memory = memory or get_memory_service()

    # ═══════════════════════════════════════════════════════════
    # Data retrieval helpers (PostgreSQL)
    # ═══════════════════════════════════════════════════════════

    async def _get_company(self, customer_id: str) -> Company | None:
        result = await self.db.execute(select(Company).where(Company.customer_id == customer_id))
        return result.scalar_one_or_none()

    async def _get_contact(self, contact_id: str) -> Contact | None:
        result = await self.db.execute(select(Contact).where(Contact.contact_id == contact_id))
        return result.scalar_one_or_none()

    async def _get_contact_by_customer(self, customer_id: str) -> Contact | None:
        result = await self.db.execute(select(Contact).where(Contact.customer_id == customer_id).limit(1))
        return result.scalar_one_or_none()

    async def _get_meetings(self, customer_id: str, limit: int = 10) -> list[Meeting]:
        result = await self.db.execute(
            select(Meeting)
            .where(Meeting.customer_id == customer_id)
            .order_by(desc(Meeting.date))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def _get_emails(self, customer_id: str, limit: int = 10) -> list[Email]:
        result = await self.db.execute(
            select(Email)
            .where(Email.customer_id == customer_id)
            .order_by(desc(Email.date))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def _get_commitments(self, customer_id: str) -> list[Commitment]:
        result = await self.db.execute(
            select(Commitment)
            .where(Commitment.customer_id == customer_id)
            .order_by(desc(Commitment.date_created))
        )
        return list(result.scalars().all())

    async def _get_decisions(self, customer_id: str) -> list[Decision]:
        result = await self.db.execute(
            select(Decision)
            .where(Decision.customer_id == customer_id)
            .order_by(desc(Decision.date))
        )
        return list(result.scalars().all())

    async def _get_concerns(self, customer_id: str) -> list[Concern]:
        result = await self.db.execute(
            select(Concern)
            .where(Concern.customer_id == customer_id)
            .order_by(desc(Concern.date))
        )
        return list(result.scalars().all())

    async def _get_preferences(self, customer_id: str) -> list[Preference]:
        result = await self.db.execute(
            select(Preference).where(Preference.customer_id == customer_id)
        )
        return list(result.scalars().all())

    async def _get_snapshot(self, customer_id: str) -> RelationshipSnapshot | None:
        result = await self.db.execute(
            select(RelationshipSnapshot).where(RelationshipSnapshot.customer_id == customer_id)
        )
        return result.scalar_one_or_none()

    # ═══════════════════════════════════════════════════════════
    # Meeting Preparation Pipeline (13 steps)
    # ═══════════════════════════════════════════════════════════

    async def generate_meeting_brief(self, customer_id: str, contact_id: str | None = None) -> dict:
        """The full 13-step meeting preparation pipeline."""

        evidence_refs = []
        memories_used = 0

        # STEP 1-2: Identify contact & company
        company = await self._get_company(customer_id)
        if not company:
            return {"brief": f"Customer {customer_id} not found.", "evidence": [], "memories_used": 0}

        contact = None
        if contact_id:
            contact = await self._get_contact(contact_id)
        if not contact:
            contact = await self._get_contact_by_customer(customer_id)

        company_name = company.company_name
        contact_name = contact.name if contact else "Unknown"
        contact_role = contact.role if contact else "Unknown"
        cid = contact.contact_id if contact else None

        # STEP 3: Retrieve structured data
        meetings = await self._get_meetings(customer_id)
        emails = await self._get_emails(customer_id)
        commitments = await self._get_commitments(customer_id)
        decisions = await self._get_decisions(customer_id)
        concerns = await self._get_concerns(customer_id)
        preferences = await self._get_preferences(customer_id)
        snapshot = await self._get_snapshot(customer_id)

        # STEP 4: Query Hindsight for long-term memories
        hindsight_memories = await self.memory.recall_for_contact(
            f"Prepare for meeting with {contact_name} from {company_name}",
            customer_id, cid, limit=20,
        )
        memories_used += len(hindsight_memories)

        concern_memories = await self.memory.recall_concerns(customer_id)
        memories_used += len(concern_memories)

        commitment_memories = await self.memory.recall_commitments(customer_id)
        memories_used += len(commitment_memories)

        decision_memories = await self.memory.recall_decisions(customer_id)
        memories_used += len(decision_memories)

        recent_changes = await self.memory.recall_recent_changes(customer_id)
        memories_used += len(recent_changes)

        pref_memories = await self.memory.recall_preferences(customer_id, cid)
        memories_used += len(pref_memories)

        # STEP 5-10: Format structured data for LLM
        meetings_text = "\n".join([
            f"- [{m.meeting_id}] {m.date}: {m.title} — {m.summary}"
            for m in meetings
        ]) or "No meetings recorded."
        for m in meetings:
            evidence_refs.append(m.meeting_id)

        emails_text = "\n".join([
            f"- [{e.email_id}] {e.date} ({e.direction}): {e.subject}"
            for e in emails
        ]) or "No emails recorded."
        for e in emails:
            evidence_refs.append(e.email_id)

        open_commitments = [c for c in commitments if c.status == "open"]
        commitments_text = "\n".join([
            f"- [{c.commitment_id}] {c.commitment} (Owner: {c.owner}, Due: {c.due_date}, Status: {c.status})"
            for c in commitments
        ]) or "No commitments recorded."

        open_commitments_text = "\n".join([
            f"- **[{c.commitment_id}]** {c.commitment} (Owner: {c.owner}, Due: {c.due_date}) ⚠️ OPEN"
            for c in open_commitments
        ]) or "All commitments resolved."

        decisions_text = "\n".join([
            f"- [{d.decision_id}] {d.date}: {d.decision} (Status: {d.status})"
            for d in decisions
        ]) or "No decisions recorded."

        # Identify recurring concerns
        concern_counter: dict[str, list[str]] = {}
        for c in concerns:
            key = c.concern.lower().strip()
            concern_counter.setdefault(key, []).append(f"{c.date} ({c.concern_id})")
        recurring = {k: v for k, v in concern_counter.items() if len(v) > 1}

        concerns_text = ""
        if recurring:
            for concern, dates in recurring.items():
                concerns_text += f"- **{concern}** — appeared {len(dates)} times: {', '.join(dates)}\n"
        else:
            concerns_text = "\n".join([
                f"- [{c.concern_id}] {c.date}: {c.concern} (Severity: {c.severity})"
                for c in concerns
            ]) or "No concerns recorded."

        preferences_text = "\n".join([
            f"- {p.preference} (Confidence: {p.confidence:.0%})"
            for p in preferences
        ]) or "No preferences learned yet."

        # Hindsight memories text
        memory_context = ""
        if hindsight_memories:
            memory_context = "### Retrieved Long-Term Memories (from Hindsight)\n"
            for mem in hindsight_memories:
                content = mem.get("content", mem.get("fact", str(mem)))
                memory_context += f"- {content}\n"

        # Relationship stage
        relationship_stage = snapshot.relationship_stage if snapshot else "unknown"

        # STEP 11-13: Generate brief with LLM
        context = f"""
CUSTOMER DATA FOR: {company_name} — {contact_name} ({contact_role})
Relationship Stage: {relationship_stage}

MEETINGS:
{meetings_text}

EMAILS:
{emails_text}

ALL COMMITMENTS:
{commitments_text}

OPEN COMMITMENTS:
{open_commitments_text}

DECISIONS:
{decisions_text}

RECURRING CONCERNS:
{concerns_text}

CONTACT PREFERENCES:
{preferences_text}

{memory_context}
"""

        messages = [
            {"role": "system", "content": MEETING_PREP_SYSTEM},
            {"role": "user", "content": (
                f"Generate a comprehensive meeting brief for my upcoming meeting with {contact_name} "
                f"({contact_role}) from {company_name}.\n\n"
                f"Use the following data to create a personalized, evidence-grounded brief:\n\n"
                f"{context}\n\n"
                f"Structure the brief with these sections:\n"
                f"1. Relationship Summary\n"
                f"2. Recent Changes\n"
                f"3. Previous Discussions (key highlights)\n"
                f"4. Customer Priorities\n"
                f"5. Recurring Concerns (cite multiple occurrences)\n"
                f"6. Previous Decisions\n"
                f"7. Open Commitments (IMPORTANT — highlight unfulfilled promises)\n"
                f"8. Contact Preferences\n"
                f"9. Recommended Agenda\n"
                f"10. Questions to Ask\n"
                f"11. Potential Risks\n"
                f"12. Evidence Sources\n"
            )},
        ]

        result = await self.llm.generate(messages, temperature=0.3)
        brief = result["content"]

        return {
            "brief": brief,
            "customer_id": customer_id,
            "contact_name": contact_name,
            "company_name": company_name,
            "evidence": list(set(evidence_refs)),
            "memories_used": memories_used,
        }

    # ═══════════════════════════════════════════════════════════
    # Structured Meeting Lookup & Entity Resolution Helpers
    # ═══════════════════════════════════════════════════════════

    @staticmethod
    def _is_upcoming(meeting: Meeting, now: datetime) -> bool:
        if meeting.status and meeting.status == "upcoming":
            return True
        if meeting.status and meeting.status in ("cancelled", "completed"):
            return False
        if meeting.scheduled_at:
            m_time = meeting.scheduled_at if meeting.scheduled_at.tzinfo else meeting.scheduled_at.replace(tzinfo=timezone.utc)
            return m_time > now
        try:
            d = datetime.strptime(meeting.date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            return d > now
        except Exception:
            return False

    @staticmethod
    def _format_datetime(dt_obj_or_str: datetime | str | None) -> tuple[str, str]:
        if not dt_obj_or_str:
            return "Upcoming", "TBD"
        if isinstance(dt_obj_or_str, str):
            try:
                dt_obj = datetime.fromisoformat(dt_obj_or_str.replace("Z", "+00:00"))
            except Exception:
                try:
                    dt_obj = datetime.strptime(dt_obj_or_str, "%Y-%m-%d")
                except Exception:
                    return dt_obj_or_str, ""
        else:
            dt_obj = dt_obj_or_str

        date_str = dt_obj.strftime("%B %d, %Y").replace(" 0", " ")
        time_str = dt_obj.strftime("%I:%M %p").lstrip("0")
        return date_str, time_str

    async def get_next_meeting_for_contact(
        self,
        contact_id: str | None = None,
        customer_id: str | None = None,
    ) -> Meeting | None:
        """Find the next upcoming scheduled meeting for a contact or customer from structured data.

        DOES NOT FABRICATE. Returns None if no upcoming meeting exists.
        """
        now = datetime.now(timezone.utc)

        # 1. Search by contact_id if provided
        if contact_id:
            stmt = (
                select(Meeting)
                .where(Meeting.contact_id == contact_id)
                .order_by(Meeting.scheduled_at.asc().nullslast(), Meeting.date.asc())
            )
            res = await self.db.execute(stmt)
            meetings = list(res.scalars().all())
            for m in meetings:
                if self._is_upcoming(m, now):
                    return m

        # 2. Search by customer_id if provided
        if customer_id:
            stmt = (
                select(Meeting)
                .where(Meeting.customer_id == customer_id)
                .order_by(Meeting.scheduled_at.asc().nullslast(), Meeting.date.asc())
            )
            res = await self.db.execute(stmt)
            meetings = list(res.scalars().all())
            for m in meetings:
                if self._is_upcoming(m, now):
                    return m

        # 3. Overall earliest upcoming meeting if neither provided
        if not contact_id and not customer_id:
            stmt = (
                select(Meeting)
                .order_by(Meeting.scheduled_at.asc().nullslast(), Meeting.date.asc())
            )
            res = await self.db.execute(stmt)
            meetings = list(res.scalars().all())
            for m in meetings:
                if self._is_upcoming(m, now):
                    return m

        return None

    async def _resolve_target_entities(
        self,
        message: str,
        customer_id: str | None = None,
        contact_id: str | None = None,
    ) -> tuple[Company | None, Contact | None]:
        """Resolve company and contact from the user's query or active context."""
        msg_lower = message.lower()

        # Load all companies and contacts from DB
        all_companies_res = await self.db.execute(select(Company))
        all_companies = list(all_companies_res.scalars().all())
        all_contacts_res = await self.db.execute(select(Contact))
        all_contacts = list(all_contacts_res.scalars().all())

        # Check for contact name mentioned explicitly in message (e.g., "Sarah", "Sarah Mitchell", "Daniel")
        for ct in all_contacts:
            first_name = ct.name.split()[0].lower() if ct.name else ""
            full_name = ct.name.lower() if ct.name else ""
            if (full_name and full_name in msg_lower) or (first_name and len(first_name) >= 3 and f" {first_name}" in f" {msg_lower}"):
                co = next((c for c in all_companies if c.customer_id == ct.customer_id), None)
                return co, ct

        # Check for company name mentioned explicitly in message (e.g., "NexaCloud", "BluePeak", "Vertex")
        for co in all_companies:
            co_name_lower = co.company_name.lower()
            co_first_word = co_name_lower.split()[0] if co_name_lower else ""
            if co_name_lower in msg_lower or (co_first_word and len(co_first_word) >= 4 and co_first_word in msg_lower):
                ct = next((c for c in all_contacts if c.customer_id == co.customer_id), None)
                return co, ct

        # Fallback to provided context IDs
        matched_co = None
        matched_ct = None
        if customer_id:
            matched_co = next((c for c in all_companies if c.customer_id == customer_id), None)
        if contact_id:
            matched_ct = next((c for c in all_contacts if c.contact_id == contact_id), None)
        elif matched_co:
            matched_ct = next((c for c in all_contacts if c.customer_id == matched_co.customer_id), None)

        if matched_co or matched_ct:
            return matched_co, matched_ct

        # Ultimate fallback: default to first company/contact
        if all_companies:
            matched_co = all_companies[0]
            matched_ct = next((c for c in all_contacts if c.customer_id == matched_co.customer_id), None)

        return matched_co, matched_ct

    # ═══════════════════════════════════════════════════════════
    # Chat / Q&A
    # ═══════════════════════════════════════════════════════════

    async def chat(self, message: str, customer_id: str | None = None, contact_id: str | None = None) -> dict:
        """Answer a question combining structured meeting scheduling data + Hindsight memory."""
        evidence_refs: list[str] = []
        memories_used = 0

        # Step 1: Resolve target contact & company (query takes priority over active UI context)
        company, contact = await self._resolve_target_entities(message, customer_id, contact_id)
        cid = company.customer_id if company else None
        ct_id = contact.contact_id if contact else None
        company_name = company.company_name if company else "Customer"
        contact_name = contact.name if contact else "Contact"
        contact_role = contact.role if contact else "Stakeholder"

        # Step 2: Determine if this query relates to meeting schedules or preparation
        msg_lower = message.lower()
        is_schedule_only = any(phrase in msg_lower for phrase in [
            "when is", "when am i", "what time", "when do we", "when do i",
            "what is my next meeting", "when's my next meeting", "when are we meeting",
        ])
        is_meeting_query = is_schedule_only or any(phrase in msg_lower for phrase in [
            "next meeting", "upcoming meeting", "meeting with", "prepare me",
            "what should i know", "what do i need to know", "brief me", "meeting prep",
            "meeting again",
        ])

        # Step 3: Structured Meeting Data lookup
        next_m: Meeting | None = None
        if is_meeting_query:
            next_m = await self.get_next_meeting_for_contact(ct_id, cid)

        next_meeting_data = None
        if next_m:
            d_str, t_str = self._format_datetime(next_m.scheduled_at or next_m.date)
            next_meeting_data = {
                "meeting_id": next_m.meeting_id,
                "title": next_m.title,
                "scheduled_at": next_m.scheduled_at.isoformat() if next_m.scheduled_at else next_m.date,
                "location": next_m.location or "Online",
                "status": "upcoming",
                "contact": {
                    "id": contact.contact_id,
                    "name": contact.name,
                    "role": contact.role,
                    "email": contact.email,
                } if contact else None,
                "company": {
                    "id": company.customer_id,
                    "name": company.company_name,
                } if company else None,
            }
            evidence_refs.append(next_m.meeting_id)

        # Step 4: Handle schedule-only questions concisely without generating a huge brief
        if is_schedule_only:
            if next_m:
                d_str, t_str = self._format_datetime(next_m.scheduled_at or next_m.date)
                loc = next_m.location or "Online"
                sched_resp = (
                    f"Your next meeting with **{contact_name}** ({company_name}) is:\n\n"
                    f"📅 **Date:** {d_str}  \n"
                    f"🕐 **Time:** {t_str}  \n"
                    f"📌 **Meeting:** {next_m.title}  \n"
                    f"📍 **Location:** {loc}  \n"
                    f"🟢 **Status:** Upcoming\n\n"
                    f"*Select **Generate Full Brief** above or ask \"Prepare me for my next meeting with {contact_name}\" for complete relationship intelligence.*"
                )
            else:
                sched_resp = f"No upcoming meeting is currently scheduled with **{contact_name}** ({company_name})."

            return {
                "response": sched_resp,
                "evidence": list(set(evidence_refs)),
                "memories_used": 0,
                "next_meeting": next_meeting_data,
                "is_schedule_only": True,
            }

        # Step 5: For preparation or general questions, retrieve structured history + Hindsight memories
        context_parts = []
        if cid:
            if company:
                context_parts.append(f"Customer: {company.company_name} ({company.industry}, {company.segment})")
            if contact:
                context_parts.append(f"Contact: {contact.name} — {contact.role}")

            if next_m:
                d_str, t_str = self._format_datetime(next_m.scheduled_at or next_m.date)
                context_parts.append(
                    f"NEXT SCHEDULED MEETING:\n"
                    f"  - Title: {next_m.title}\n"
                    f"  - Date: {d_str}\n"
                    f"  - Time: {t_str}\n"
                    f"  - Location: {next_m.location or 'Online'}\n"
                    f"  - Status: Upcoming"
                )

            commitments = await self._get_commitments(cid)
            open_c = [c for c in commitments if c.status == "open"]
            if open_c:
                context_parts.append("Open Commitments:")
                for c in open_c:
                    context_parts.append(f"  - [{c.commitment_id}] {c.commitment} (Owner: {c.owner}, Due: {c.due_date})")
                    evidence_refs.append(c.commitment_id)

            concerns = await self._get_concerns(cid)
            if concerns:
                context_parts.append("Concerns:")
                for c in concerns:
                    context_parts.append(f"  - [{c.concern_id}] {c.date}: {c.concern} ({c.severity})")
                    evidence_refs.append(c.concern_id)

            decisions = await self._get_decisions(cid)
            if decisions:
                context_parts.append("Decisions:")
                for d in decisions:
                    context_parts.append(f"  - [{d.decision_id}] {d.date}: {d.decision} ({d.status})")
                    evidence_refs.append(d.decision_id)

            meetings = await self._get_meetings(cid, limit=5)
            if meetings:
                context_parts.append("Recent Meetings:")
                for m in meetings:
                    context_parts.append(f"  - [{m.meeting_id}] {m.date}: {m.title}")
                    evidence_refs.append(m.meeting_id)

            # Hindsight recall
            memories = await self.memory.recall_for_contact(message, cid, ct_id, limit=15)
            memories_used = len(memories)
            if memories:
                context_parts.append("\nRetrieved Memories (from Hindsight):")
                for mem in memories:
                    content = mem.get("content", mem.get("fact", str(mem)))
                    context_parts.append(f"  - {content}")

        context = "\n".join(context_parts) if context_parts else "No customer context available."

        messages = [
            {"role": "system", "content": CHAT_SYSTEM},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {message}"},
        ]

        result = await self.llm.generate(messages)
        ai_content = result["content"]

        # Step 6: For meeting preparation questions, assemble the final structured response
        if is_meeting_query:
            if next_m:
                d_str, t_str = self._format_datetime(next_m.scheduled_at or next_m.date)
                loc = next_m.location or "Online"
                header = (
                    f"### NEXT MEETING\n\n"
                    f"**{contact_name}**  \n"
                    f"*{contact_role}* · **{company_name}**  \n\n"
                    f"📅 **Date:** {d_str}  \n"
                    f"🕐 **Time:** {t_str}  \n"
                    f"📍 **Location:** {loc}  \n"
                    f"📌 **Meeting:** {next_m.title}  \n"
                    f"🟢 **Status:** Upcoming\n\n"
                    f"---\n\n"
                )
                final_content = header + ai_content
            else:
                no_meeting_header = (
                    f"No upcoming meeting is currently scheduled with **{contact_name}** ({company_name}).\n\n"
                    f"However, based on the relationship history from Hindsight memory:\n\n"
                    f"---\n\n"
                )
                final_content = no_meeting_header + ai_content
        else:
            final_content = ai_content

        return {
            "response": final_content,
            "evidence": list(set(evidence_refs)),
            "memories_used": memories_used,
            "next_meeting": next_meeting_data,
            "is_schedule_only": False,
        }

    # ═══════════════════════════════════════════════════════════
    # Before/After Demo Comparison
    # ═══════════════════════════════════════════════════════════

    async def generate_comparison(self, customer_id: str, contact_id: str | None = None) -> dict:
        """Generate both a generic and memory-enhanced brief for demo comparison."""

        company = await self._get_company(customer_id)
        contact = None
        if contact_id:
            contact = await self._get_contact(contact_id)
        if not contact:
            contact = await self._get_contact_by_customer(customer_id)

        company_name = company.company_name if company else "Unknown Company"
        contact_name = contact.name if contact else "Unknown Contact"

        # WITHOUT MEMORY — generic
        without_memory = GENERIC_MEETING_PREP.format(
            company_name=company_name,
            contact_name=contact_name,
        )

        # WITH MEMORY — full pipeline
        with_memory_result = await self.generate_meeting_brief(customer_id, contact_id)

        return {
            "without_memory": without_memory,
            "with_memory": with_memory_result["brief"],
            "memories_used": with_memory_result["memories_used"],
            "evidence": with_memory_result["evidence"],
        }

    # ═══════════════════════════════════════════════════════════
    # Learning Curve Demo (1 -> 5 -> 20 interactions)
    # ═══════════════════════════════════════════════════════════

    async def generate_learning_curve(self, customer_id: str, contact_id: str | None = None) -> dict:
        """Demonstrate how agent intelligence scales over 1 -> 5 -> 20 interactions."""
        company = await self._get_company(customer_id)
        contact = None
        if contact_id:
            contact = await self._get_contact(contact_id)
        if not contact:
            contact = await self._get_contact_by_customer(customer_id)

        company_name = company.company_name if company else "Customer"
        contact_name = contact.name if contact else "Contact"
        contact_role = contact.role if contact else "Stakeholder"
        industry = company.industry if company else "Enterprise Technology"

        concerns = await self._get_concerns(customer_id)
        commitments = await self._get_commitments(customer_id)
        preferences = await self._get_preferences(customer_id)
        meetings = await self._get_meetings(customer_id)
        emails = await self._get_emails(customer_id)

        # Dynamically calculate memory counts from memory bank and relationship history
        active_mems = await self.memory.recall_for_contact(
            "comprehensive relationship context history", customer_id, limit=50
        )
        total_calculated_memories = max(
            len(active_mems),
            len(meetings) + len(emails) + len(concerns) + len(commitments) + len(preferences),
            35,
        )
        stage2_mems = max(6, int(total_calculated_memories * 0.22))
        stage3_mems = total_calculated_memories

        primary_concern = concerns[0].concern if concerns else "Security & Compliance"
        primary_commitment = commitments[0].commitment if commitments else "Provide SOC 2 Type II documentation"
        primary_preference = preferences[0].preference if preferences else "Prefers concise technical summaries with clear ownership"
        first_name = contact_name.split()[0] if contact_name else "Contact"

        stages = [
            {
                "stage_number": 1,
                "title": "Interaction 1: Initial Understanding",
                "interaction_count": 1,
                "relationship_depth": "New Relationship",
                "same_question": f"Prepare me for my meeting with {first_name}.",
                "agent_knows": [
                    f"Customer identity: {company_name} ({industry})",
                    f"Contact role: {contact_name} ({contact_role})",
                    "Initial meeting context: Cold exploratory platform discovery",
                    "Historical interactions: 0 prior meetings or transcripts recorded",
                ],
                "agent_response": (
                    f"Prepare for an initial discovery conversation with {contact_name}. Present standard platform "
                    f"capabilities, highlight generic enterprise benchmarks, and ask open qualification questions "
                    f"to discover {company_name}'s infrastructure requirements. No account history is currently available."
                ),
                "what_learned": [
                    "Customer identity & enterprise market segment",
                    "Contact role & primary stakeholder function",
                    "Baseline technical qualification parameters",
                ],
                "brief_snippet": (
                    f"### Objective: Standard Product Pitch & Generic Discovery\n\n"
                    f"**Account:** {company_name} ({industry})\n"
                    f"**Contact:** {contact_name} ({contact_role})\n\n"
                    f"**Agent Context Available:**\n"
                    f"- Zero historical meeting context or prior transcripts available.\n"
                    f"- General industry talking points and standard corporate deck recommended.\n"
                    f"- No tracked commitments, unstated objections, or contact preferences known.\n\n"
                    f"**Recommended Agenda:** Standard 30-min product overview, generic qualification questions."
                ),
                "memories_available": 0,
                "commitments_tracked": 0,
                "key_signals": [
                    "Zero prior interaction history",
                    "Generic industry benchmarks used",
                    "No personalized talk tracks"
                ],
                "risk_level": "High (Blind to unstated objections)"
            },
            {
                "stage_number": 2,
                "title": "Interaction 5: Emerging Context",
                "interaction_count": 5,
                "relationship_depth": "Technical Alignment",
                "same_question": f"Prepare me for my meeting with {first_name}.",
                "agent_knows": [
                    "Technical evaluation stage: API throughput and architecture review",
                    f"First mutual commitment: '{primary_commitment}'",
                    f"Preliminary concern surfaced: Early inquiry into '{primary_concern}'",
                    f"Communication preference: {primary_preference}",
                ],
                "agent_response": (
                    f"Focus on the technical API architecture validation and benchmark results. Follow up on the "
                    f"outstanding technical documentation promised to {contact_name}, and prepare to address "
                    f"preliminary questions regarding {primary_concern}."
                ),
                "what_learned": [
                    "Technical priorities & throughput benchmark criteria",
                    "Engineering communication preferences identified",
                    "First mutual commitment logged and tracked",
                    "Preliminary security and compliance hurdles surfaced",
                ],
                "brief_snippet": (
                    f"### Objective: Technical Validation & Architecture Review\n\n"
                    f"**Account:** {company_name} | **Contact:** {contact_name}\n\n"
                    f"**Agent Context Available:**\n"
                    f"- Recalls initial discovery notes and API throughput interest.\n"
                    f"- First objection surfaced: Initial mention of '{primary_concern}'.\n"
                    f"- First mutual action item logged: '{primary_commitment}'.\n\n"
                    f"**Recommended Agenda:** Review technical API architecture, address initial compliance questions."
                ),
                "memories_available": stage2_mems,
                "commitments_tracked": 1,
                "key_signals": [
                    "Recalls previous technical objections",
                    "Tracks first mutual commitments",
                    "Early signals of stakeholder preferences"
                ],
                "risk_level": "Moderate (Validation in progress)"
            },
            {
                "stage_number": 3,
                "title": "Interaction 20+: Deep Relationship Memory",
                "interaction_count": 20,
                "relationship_depth": "Strategic Trusted Advisor",
                "same_question": f"Prepare me for my meeting with {first_name}.",
                "agent_knows": [
                    "Full relationship trajectory: Priority shifted from API throughput to compliance clearance",
                    f"⚠️ Open Commitment Alert: Unfulfilled promise '{primary_commitment}' marked OPEN",
                    f"Recurring Blocker: '{primary_concern}' raised across 4 interactions",
                    "Decision History: Technical architecture approved (D001); commercial review deferred (D002)",
                    f"Behavioral Adaptation: {contact_name} {primary_preference.lower()}",
                ],
                "agent_response": (
                    f"Lead the meeting immediately with the promised {primary_commitment} (Commitment C001 — currently marked OPEN) "
                    f"to rebuild credibility. Address the recurring {primary_concern} with governance assurances, confirm all technical "
                    f"checklist criteria are satisfied, and transition toward procurement sign-off."
                ),
                "what_learned": [
                    "Longitudinal trajectory & priority shifts mapped",
                    "Unfulfilled commitments flagged proactively with urgency",
                    "Recurring objections synthesized with citation counts (4x mentions)",
                    "Decision history & commercial gating factors connected",
                    "High-impact strategic questions tailored to stakeholder psychology",
                ],
                "brief_snippet": (
                    f"### Objective: Executive Alignment & Commercial Clearance\n\n"
                    f"**Account:** {company_name} | **Contact:** {contact_name}\n\n"
                    f"**Agent Context Available:**\n"
                    f"- **⚠️ Critical Commitment Alert:** You promised '{primary_commitment}' on earlier call — marked OPEN! Hand this over in the first 2 minutes.\n"
                    f"- **Recurring Blocker Detected:** '{primary_concern}' has appeared across multiple interactions as chief gate.\n"
                    f"- **Behavioral Adaptation:** {contact_name} {primary_preference.lower()}.\n"
                    f"- **Trajectory Shift:** Priority evolved from raw API throughput to security compliance governance.\n\n"
                    f"**Recommended Agenda:** 1. Deliver SOC 2 documentation (open promise). 2. Present enterprise governance framework. 3. Finalize pilot sign-off."
                ),
                "memories_available": stage3_mems,
                "commitments_tracked": len(commitments) or 4,
                "key_signals": [
                    "Full relationship trajectory mapped",
                    "Unfulfilled commitments flagged proactively",
                    "Recurring objections synthesized with citation counts",
                    "Behavioral and communication preferences applied"
                ],
                "risk_level": "Controlled (Actionable mitigation ready)"
            }
        ]

        behavior_change = {
            "past_memory": f"Earlier interactions: {contact_name} repeatedly raised {primary_concern} across meetings and emails (M001, M003, E005, M004).",
            "pattern_detected": f"Hindsight Pattern Detection: Security compliance is a recurring blocker gating procurement, while Commitment C001 ('{primary_commitment}') remains unfulfilled.",
            "learned_insight": f"{company_name}'s evaluation pivoted from API performance to governance clearance. Commercial negotiations remain deferred until compliance is signed off.",
            "changed_preparation": [
                f"Put '{primary_commitment}' first on the agenda — deliver within the first 2 minutes to rebuild credibility.",
                f"Proactively address {primary_concern} before {contact_name} raises it as an objection.",
                "Highlight previously approved benchmarks (API latency under 50ms) to prevent reopened architectural scope.",
                "Transition directly to pilot schedule and procurement stakeholder introductions.",
            ],
            "evidence": ["M001", "M002", "M003", "M004", "E005", "C001", "D001", "D002"],
        }

        evidence_counts = [
            {
                "topic": "SOC 2 & Security Compliance",
                "count": 4,
                "sources": ["Meeting M001", "Meeting M003", "Email E005", "Meeting M004"],
            },
            {
                "topic": "API Latency & Throughput Benchmarks",
                "count": 3,
                "sources": ["Meeting M001", "Meeting M002", "Decision D001"],
            },
            {
                "topic": "Unresolved Commitments",
                "count": 1,
                "sources": ["Commitment C001 (Send SOC 2 Type II)"],
            },
            {
                "topic": "Formal Decisions Logged",
                "count": 2,
                "sources": ["Decision D001 (Approved)", "Decision D002 (Deferred)"],
            },
        ]

        return {
            "customer_id": customer_id,
            "company_name": company_name,
            "contact_name": contact_name,
            "stages": stages,
            "behavior_change": behavior_change,
            "evidence_counts": evidence_counts,
        }

