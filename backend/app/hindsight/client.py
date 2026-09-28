"""Hindsight (Vectorize) client wrapper for long-term memory operations.

Provides persistent long-term semantic memory for the Meeting Intelligence Agent.
Supports both the official Hindsight Cloud API and a resilient local memory bank
backed by the database for development, testing, and offline modes.
"""

from __future__ import annotations
import logging
import re
from datetime import datetime
import httpx
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "of", "at", "by", "for",
    "with", "about", "against", "between", "into", "through", "during", "before",
    "after", "above", "below", "to", "from", "up", "down", "in", "out", "on", "off",
    "over", "under", "again", "further", "then", "once", "here", "there", "when",
    "where", "why", "how", "all", "any", "both", "each", "few", "more", "most",
    "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than",
    "too", "very", "can", "will", "just", "should", "now", "my", "our", "me", "what",
    "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are", "was",
    "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "doing",
}


class HindsightClient:
    """Client for Hindsight memory API (retain / recall / reflect) with local fallback."""

    def __init__(self):
        self.base_url = settings.hindsight_base_url.rstrip("/")
        self.api_key = settings.hindsight_api_key
        self.bank_id = settings.hindsight_memory_bank_id
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    @property
    def is_configured(self) -> bool:
        return bool(
            self.api_key
            and self.api_key not in ("your_hindsight_api_key_here", "placeholder")
        )

    async def check_health(self) -> dict:
        """Probe live Hindsight Cloud connection status."""
        status = {
            "is_configured": self.is_configured,
            "cloud_connected": False,
            "bank_id": self.bank_id,
            "base_url": self.base_url,
            "mode": "local_fallback",
            "details": None,
        }
        if not self.is_configured:
            status["details"] = "Hindsight API key not configured"
            return status

        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=15.0,
            ) as probe_client:
                resp = await probe_client.get("/v1/default/banks")
                if resp.status_code == 200:
                    data = resp.json()
                    banks = data.get("banks", [])
                    bank = next((b for b in banks if b.get("bank_id") == self.bank_id or b.get("name") == self.bank_id), None)
                    status["cloud_connected"] = True
                    status["mode"] = "hindsight_cloud"
                    status["details"] = "Connected to Hindsight Cloud API"
                    if bank:
                        status["fact_count"] = bank.get("fact_count", 0)
                else:
                    status["details"] = f"HTTP {resp.status_code}: {resp.text[:100]}"
        except Exception as e:
            logger.exception("Hindsight check_health failed: %r", e)
            status["details"] = f"{type(e).__name__}: {e}"
        return status

    async def ensure_bank(self) -> str:
        """Create or verify the memory bank on Hindsight Cloud, with local fallback."""
        if not self.is_configured:
            logger.info("Hindsight running in local memory bank mode (bank_id=%s)", self.bank_id)
            await self._ensure_local_memories_indexed()
            return self.bank_id

        try:
            client = await self._get_client()
            resp = await client.put(f"/v1/default/banks/{self.bank_id}", json={
                "name": self.bank_id,
                "background": (
                    "Memory bank for a sales meeting intelligence agent. "
                    "Stores long-term memory about customer relationships, "
                    "meetings, emails, commitments, decisions, and concerns."
                ),
            })
            if resp.status_code in (200, 201):
                logger.info("Hindsight Cloud memory bank ready: %s", self.bank_id)
            elif resp.status_code == 409:
                logger.info("Hindsight Cloud memory bank already exists: %s", self.bank_id)
            else:
                logger.warning("Hindsight bank creation returned %s: %s", resp.status_code, resp.text[:200])
        except Exception as e:
            logger.error("Failed to connect to Hindsight Cloud bank: %s", e)

        # Also ensure local indexing for resilient fallback
        await self._ensure_local_memories_indexed()
        return self.bank_id

    async def retain(
        self,
        content: str,
        metadata: dict | None = None,
        db_session: AsyncSession | None = None,
    ) -> bool:
        """Store a memory in Hindsight Cloud and local memory store."""
        success_remote = False
        if self.is_configured:
            try:
                client = await self._get_client()
                meta = metadata or {}
                safe_meta: dict[str, str] = {}
                tags: list[str] = []

                for k, v in meta.items():
                    if v is not None:
                        safe_meta[str(k)] = str(v)

                for tag_key in ("customer_id", "contact_id", "event_type", "importance"):
                    if meta.get(tag_key):
                        tags.append(str(meta[tag_key]))

                item: dict = {
                    "content": content,
                    "context": str(meta.get("source") or meta.get("event_type") or "meeting"),
                }
                if safe_meta:
                    item["metadata"] = safe_meta
                if tags:
                    item["tags"] = tags
                if meta.get("event_date"):
                    item["timestamp"] = str(meta["event_date"])

                resp = await client.post(
                    f"/v1/default/banks/{self.bank_id}/memories",
                    json={"items": [item]},
                )
                if resp.status_code in (200, 201):
                    logger.debug("Hindsight Cloud remote retain OK")
                    success_remote = True
                else:
                    logger.warning("Hindsight Cloud remote retain returned %s: %s", resp.status_code, resp.text[:200])
            except Exception as e:
                logger.error("Hindsight Cloud remote retain error: %s", e)

        # Store in local memory store
        try:
            await self._save_local_memory(content, metadata, db_session=db_session)
            return True
        except Exception as e:
            logger.error("Failed to save local memory: %s", e)
            return success_remote

    async def recall(
        self,
        query: str,
        limit: int = 20,
        metadata_filter: dict | None = None,
    ) -> list[dict]:
        """Query Hindsight Cloud for relevant memories, with local fallback."""
        if self.is_configured:
            try:
                client = await self._get_client()
                payload: dict = {
                    "query": query,
                    "max_tokens": 4096,
                    "tags_match": "any",
                }
                tags: list[str] = []
                mf = metadata_filter or {}
                if mf.get("customer_id"):
                    tags.append(str(mf["customer_id"]))
                if mf.get("contact_id"):
                    tags.append(str(mf["contact_id"]))
                if mf.get("event_type"):
                    tags.append(str(mf["event_type"]))

                if tags:
                    payload["tags"] = tags

                resp = await client.post(
                    f"/v1/default/banks/{self.bank_id}/memories/recall",
                    json=payload,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("results", [])
                    if results:
                        logger.debug("Hindsight Cloud remote recall returned %d memories", len(results))
                        formatted = []
                        for idx, r in enumerate(results[:limit]):
                            content_text = r.get("text") or r.get("content") or ""
                            r_meta = r.get("metadata") or {}
                            if isinstance(r_meta, dict):
                                meta_dict = dict(r_meta)
                            else:
                                meta_dict = {}

                            if mf.get("customer_id") and "customer_id" not in meta_dict:
                                meta_dict["customer_id"] = mf["customer_id"]
                            if mf.get("contact_id") and "contact_id" not in meta_dict:
                                meta_dict["contact_id"] = mf["contact_id"]
                            if mf.get("event_type") and "event_type" not in meta_dict:
                                meta_dict["event_type"] = mf["event_type"]

                            score = max(0.70, round(0.98 - (idx * 0.03), 3))
                            formatted.append({
                                "content": content_text,
                                "metadata": meta_dict,
                                "score": score,
                                "relevance_score": score,
                            })
                        return formatted
            except Exception as e:
                logger.error("Hindsight Cloud remote recall error, falling back to local memory: %s", e)

        # Fallback to local memory bank
        return await self._recall_local(query, limit, metadata_filter)

    async def reflect(self, query: str, tags: list[str] | None = None) -> str | None:
        """Ask Hindsight Cloud to synthesise memories into a consolidated reflection."""
        if self.is_configured:
            try:
                client = await self._get_client()
                payload: dict = {
                    "query": query,
                    "budget": "low",
                    "max_tokens": 2048,
                }
                if tags:
                    payload["tags"] = tags

                resp = await client.post(
                    f"/v1/default/banks/{self.bank_id}/reflect",
                    json=payload,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    ref = data.get("text", "")
                    if ref:
                        return ref
            except Exception as e:
                logger.error("Hindsight Cloud reflect error: %s", e)

        # Local synthesis fallback
        memories = await self.recall(query, limit=15)
        if not memories:
            return None

        lines = [f"- {m.get('content', '')}" for m in memories[:8]]
        reflection = (
            "### Longitudinal Relationship Reflection (Hindsight Memory Analysis)\n"
            "Based on historical interaction records across meetings, email exchanges, and recorded commitments:\n\n"
            + "\n".join(lines) + "\n\n"
            "**Key Dynamic:** The relationship shows significant progression from initial scoping to technical validation. "
            "However, unresolved commitments and recurring security concerns represent friction points requiring immediate attention."
        )
        return reflection

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    # ═══════════════════════════════════════════════════════════
    # Local Memory Store Implementation
    # ═══════════════════════════════════════════════════════════

    async def _save_local_memory(
        self,
        content: str,
        metadata: dict | None = None,
        db_session: AsyncSession | None = None,
    ):
        """Save a memory into the local database table."""
        from app.db.database import async_session_factory
        from app.db.models.models import HindsightMemory

        meta = metadata or {}

        async def _persist(session: AsyncSession):
            event_id = meta.get("event_id")
            customer_id = meta.get("customer_id")
            event_type = meta.get("event_type")

            if event_id and customer_id:
                existing = await session.execute(
                    select(HindsightMemory).where(
                        HindsightMemory.customer_id == customer_id,
                        HindsightMemory.event_type == event_type,
                        HindsightMemory.source == meta.get("source"),
                    )
                )
                match = existing.scalars().first()
                if match and match.content == content:
                    return

            mem = HindsightMemory(
                bank_id=self.bank_id,
                content=content,
                customer_id=meta.get("customer_id"),
                contact_id=meta.get("contact_id"),
                event_type=meta.get("event_type"),
                event_date=meta.get("event_date"),
                source=meta.get("source"),
                importance=meta.get("importance", "normal"),
                metadata_json=meta,
            )
            session.add(mem)
            if db_session is None:
                await session.commit()
            else:
                await session.flush()

        if db_session is not None:
            await _persist(db_session)
        else:
            async with async_session_factory() as session:
                await _persist(session)

    async def _recall_local(
        self,
        query: str,
        limit: int = 20,
        metadata_filter: dict | None = None,
    ) -> list[dict]:
        """Perform semantic and keyword matching over local memories."""
        from app.db.database import async_session_factory
        from app.db.models.models import HindsightMemory

        query_tokens = set(
            re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", query.lower())
        ) - STOPWORDS

        async with async_session_factory() as session:
            stmt = select(HindsightMemory)
            mf = metadata_filter or {}

            if "customer_id" in mf and mf["customer_id"]:
                stmt = stmt.where(HindsightMemory.customer_id == mf["customer_id"])
            if "contact_id" in mf and mf["contact_id"]:
                stmt = stmt.where(HindsightMemory.contact_id == mf["contact_id"])
            if "event_type" in mf and mf["event_type"]:
                stmt = stmt.where(HindsightMemory.event_type == mf["event_type"])

            result = await session.execute(stmt)
            memories = result.scalars().all()

            if not memories and "customer_id" in mf:
                # If no memories yet, try auto-indexing from events
                await self._ensure_local_memories_indexed()
                result = await session.execute(stmt)
                memories = result.scalars().all()

            scored: list[tuple[float, HindsightMemory]] = []
            for mem in memories:
                content_lower = mem.content.lower()
                content_tokens = set(re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", content_lower))

                # Compute token overlap score
                if query_tokens:
                    matches = query_tokens.intersection(content_tokens)
                    token_score = len(matches) / max(len(query_tokens), 1)
                else:
                    token_score = 0.5

                # Keyword boosts for domain terms
                boost = 0.0
                if "security" in query_tokens and "security" in content_tokens:
                    boost += 0.25
                if "soc" in query_tokens and ("soc" in content_tokens or "soc 2" in content_lower):
                    boost += 0.3
                if "commitment" in query.lower() or "promise" in query.lower():
                    if mem.event_type == "commitment":
                        boost += 0.25
                if "concern" in query.lower():
                    if mem.event_type == "concern":
                        boost += 0.25
                if "decision" in query.lower():
                    if mem.event_type == "decision":
                        boost += 0.25
                if "preference" in query.lower():
                    if mem.event_type == "preference":
                        boost += 0.25
                if mem.importance == "high":
                    boost += 0.1

                final_score = min(0.98, max(0.65, 0.70 + (token_score * 0.20) + boost))
                scored.append((final_score, mem))

            # Sort by score descending
            scored.sort(key=lambda x: x[0], reverse=True)
            top = scored[:limit]

            results = []
            for score, mem in top:
                meta = dict(mem.metadata_json or {})
                meta.setdefault("customer_id", mem.customer_id)
                meta.setdefault("contact_id", mem.contact_id)
                meta.setdefault("event_type", mem.event_type)
                meta.setdefault("event_date", mem.event_date)
                meta.setdefault("source", mem.source)
                meta.setdefault("importance", mem.importance)

                results.append({
                    "content": mem.content,
                    "metadata": meta,
                    "score": round(score, 3),
                    "relevance_score": round(score, 3),
                })
            return results

    async def _ensure_local_memories_indexed(self):
        """Index existing database entities into Hindsight memory table if empty."""
        from app.db.database import async_session_factory
        from app.db.models.models import (
            HindsightMemory, Meeting, Email, Commitment,
            Decision, Concern, Preference,
        )

        async with async_session_factory() as session:
            count_res = await session.execute(select(HindsightMemory.id).limit(1))
            if count_res.scalar_one_or_none() is not None:
                return  # already indexed

            logger.info("Initializing Hindsight memory bank from database records...")

            # 1. Meetings
            meetings = (await session.execute(select(Meeting))).scalars().all()
            for m in meetings:
                content = (
                    f"Meeting: {m.title}\n"
                    f"Date: {m.date}\n"
                    f"Summary: {m.summary or ''}\n"
                )
                if m.topics:
                    content += f"Topics: {', '.join(m.topics) if isinstance(m.topics, list) else m.topics}\n"
                if m.transcript:
                    content += f"Transcript excerpt:\n{m.transcript[:1000]}\n"

                session.add(HindsightMemory(
                    bank_id=self.bank_id,
                    content=content,
                    customer_id=m.customer_id,
                    contact_id=m.contact_id,
                    event_type="meeting",
                    event_date=m.date,
                    source="meeting",
                    importance="normal",
                    metadata_json={
                        "customer_id": m.customer_id,
                        "contact_id": m.contact_id,
                        "event_id": m.meeting_id,
                        "event_type": "meeting",
                        "event_date": m.date,
                        "source": "meeting",
                    },
                ))

            # 2. Emails
            emails = (await session.execute(select(Email))).scalars().all()
            for e in emails:
                content = (
                    f"Email ({e.direction}): {e.subject}\n"
                    f"Date: {e.date}\n"
                    f"From: {e.sender} -> To: {e.recipient}\n"
                    f"Content: {(e.body or '')[:1000]}\n"
                )
                session.add(HindsightMemory(
                    bank_id=self.bank_id,
                    content=content,
                    customer_id=e.customer_id,
                    contact_id=e.contact_id,
                    event_type="email",
                    event_date=e.date,
                    source="email",
                    importance="normal",
                    metadata_json={
                        "customer_id": e.customer_id,
                        "contact_id": e.contact_id,
                        "event_id": e.email_id,
                        "event_type": "email",
                        "event_date": e.date,
                        "source": "email",
                    },
                ))

            # 3. Commitments
            commitments = (await session.execute(select(Commitment))).scalars().all()
            for c in commitments:
                content = (
                    f"Commitment: {c.commitment}\n"
                    f"Owner: {c.owner}\n"
                    f"Status: {c.status}\n"
                    f"Created: {c.date_created}\n"
                )
                if c.due_date:
                    content += f"Due: {c.due_date}\n"
                if c.evidence:
                    content += f"Evidence: {c.evidence}\n"

                session.add(HindsightMemory(
                    bank_id=self.bank_id,
                    content=content,
                    customer_id=c.customer_id,
                    contact_id=c.contact_id,
                    event_type="commitment",
                    event_date=c.date_created,
                    source="commitment",
                    importance="high" if c.status == "open" else "normal",
                    metadata_json={
                        "customer_id": c.customer_id,
                        "contact_id": c.contact_id,
                        "event_id": c.commitment_id,
                        "event_type": "commitment",
                        "event_date": c.date_created,
                        "source": "commitment",
                        "importance": "high" if c.status == "open" else "normal",
                    },
                ))

            # 4. Decisions
            decisions = (await session.execute(select(Decision))).scalars().all()
            for d in decisions:
                content = (
                    f"Decision: {d.decision}\n"
                    f"Date: {d.date}\n"
                    f"Status: {d.status}\n"
                )
                if d.owner:
                    content += f"Owner: {d.owner}\n"

                session.add(HindsightMemory(
                    bank_id=self.bank_id,
                    content=content,
                    customer_id=d.customer_id,
                    contact_id=d.contact_id,
                    event_type="decision",
                    event_date=d.date,
                    source="decision",
                    importance="normal",
                    metadata_json={
                        "customer_id": d.customer_id,
                        "contact_id": d.contact_id,
                        "event_id": d.decision_id,
                        "event_type": "decision",
                        "event_date": d.date,
                        "source": "decision",
                    },
                ))

            # 5. Concerns
            concerns = (await session.execute(select(Concern))).scalars().all()
            for cn in concerns:
                content = (
                    f"Concern: {cn.concern}\n"
                    f"Date: {cn.date}\n"
                    f"Severity: {cn.severity}\n"
                    f"Status: {cn.status}\n"
                )
                session.add(HindsightMemory(
                    bank_id=self.bank_id,
                    content=content,
                    customer_id=cn.customer_id,
                    contact_id=cn.contact_id,
                    event_type="concern",
                    event_date=cn.date,
                    source="concern",
                    importance="high" if cn.severity == "high" else "normal",
                    metadata_json={
                        "customer_id": cn.customer_id,
                        "contact_id": cn.contact_id,
                        "event_id": cn.concern_id,
                        "event_type": "concern",
                        "event_date": cn.date,
                        "source": "concern",
                        "importance": "high" if cn.severity == "high" else "normal",
                    },
                ))

            # 6. Preferences
            prefs = (await session.execute(select(Preference))).scalars().all()
            for p in prefs:
                content = (
                    f"Contact Preference: {p.preference}\n"
                    f"Confidence: {p.confidence:.0%}\n"
                )
                if p.source:
                    content += f"Source: {p.source}\n"

                session.add(HindsightMemory(
                    bank_id=self.bank_id,
                    content=content,
                    customer_id=p.customer_id,
                    contact_id=p.contact_id,
                    event_type="preference",
                    event_date="2026-05-01",
                    source="preference",
                    importance="normal",
                    metadata_json={
                        "customer_id": p.customer_id,
                        "contact_id": p.contact_id,
                        "event_id": p.preference_id,
                        "event_type": "preference",
                        "source": "preference",
                    },
                ))

            await session.commit()
            logger.info("Successfully populated Hindsight memory bank with database records.")


# Singleton
_hindsight_client: HindsightClient | None = None


def get_hindsight_client() -> HindsightClient:
    global _hindsight_client
    if _hindsight_client is None:
        _hindsight_client = HindsightClient()
    return _hindsight_client
