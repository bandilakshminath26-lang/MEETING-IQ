"""Kapibala Sales Conversations ingestion script.

Parses the Kapibala dataset (conversations.jsonl) which contains
sales-style conversational data. Converts dialogues into meeting
records with extracted insights.

Usage:
    python scripts/ingest_kapibala.py [--data-dir data/raw/kapibala] [--limit 100]
"""

from __future__ import annotations
import argparse
import asyncio
import hashlib
import json
import logging
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.config import get_settings  # noqa: E402
from app.db.database import init_db, async_session_factory  # noqa: E402
from app.db.models.models import Company, Contact, Meeting, Event  # noqa: E402
from app.hindsight import get_memory_service  # noqa: E402
from sqlalchemy import select  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)-30s | %(levelname)s | %(message)s")
logger = logging.getLogger("ingest_kapibala")


def _stable_id(text: str) -> str:
    return "KAP" + hashlib.md5(text.encode()).hexdigest()[:8].upper()


def _extract_conversation_text(record: dict) -> tuple[str, str, list[str]]:
    """Extract transcript text, summary, and topics from a Kapibala record.

    Kapibala records may contain different structures:
    - "messages" list with role/content pairs
    - "conversation" as plain text
    - "turns" list
    """
    transcript = ""
    summary = ""
    topics: list[str] = []

    # Try "messages" format
    if "messages" in record and isinstance(record["messages"], list):
        parts = []
        for msg in record["messages"]:
            role = msg.get("role", msg.get("speaker", "unknown"))
            content = msg.get("content", msg.get("text", ""))
            if content:
                parts.append(f"{role}: {content}")
        transcript = "\n".join(parts)

    # Try "conversation" format
    elif "conversation" in record:
        if isinstance(record["conversation"], str):
            transcript = record["conversation"]
        elif isinstance(record["conversation"], list):
            parts = []
            for turn in record["conversation"]:
                if isinstance(turn, dict):
                    speaker = turn.get("speaker", turn.get("role", ""))
                    text = turn.get("text", turn.get("content", ""))
                    parts.append(f"{speaker}: {text}")
                elif isinstance(turn, str):
                    parts.append(turn)
            transcript = "\n".join(parts)

    # Try "turns" format
    elif "turns" in record and isinstance(record["turns"], list):
        parts = []
        for turn in record["turns"]:
            if isinstance(turn, dict):
                speaker = turn.get("speaker", turn.get("role", ""))
                text = turn.get("text", turn.get("content", ""))
                parts.append(f"{speaker}: {text}")
        transcript = "\n".join(parts)

    # Try "text" or "content" as fallback
    elif "text" in record:
        transcript = record["text"]
    elif "content" in record:
        transcript = record["content"]

    # Extract summary if available
    summary = record.get("summary", record.get("abstract", ""))
    if not summary and transcript:
        # Generate a simple summary from first 200 chars
        summary = transcript[:200].replace("\n", " ") + "..."

    # Extract topics
    if "topics" in record:
        topics = record["topics"] if isinstance(record["topics"], list) else [record["topics"]]
    elif "tags" in record:
        topics = record["tags"] if isinstance(record["tags"], list) else [record["tags"]]
    elif "category" in record:
        topics = [record["category"]]
    else:
        topics = ["sales", "conversation"]

    return transcript[:5000], summary[:1000], topics


async def ingest_kapibala(data_dir: str, limit: int = 100):
    """Ingest Kapibala sales conversations from JSONL file."""
    data_path = Path(data_dir)
    await init_db()
    memory = get_memory_service()

    jsonl_path = data_path / "conversations.jsonl"
    if not jsonl_path.exists():
        logger.error("Kapibala data not found at %s", jsonl_path)
        return

    logger.info("Reading Kapibala conversations from: %s", jsonl_path)

    # Read conversations
    conversations: list[dict] = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f):
            if len(conversations) >= limit:
                break
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                conversations.append(record)
            except json.JSONDecodeError as e:
                logger.debug("Skipping malformed line %d: %s", line_num, e)

    logger.info("Loaded %d Kapibala conversations", len(conversations))

    if not conversations:
        return

    async with async_session_factory() as db:
        # Create Kapibala company
        existing = await db.execute(select(Company).where(Company.customer_id == "KAPIBALA"))
        if not existing.scalar_one_or_none():
            db.add(Company(
                customer_id="KAPIBALA",
                company_name="Kapibala Demos Inc.",
                industry="Sales Training",
                segment="Mid-Market",
                country="Global",
            ))
            await db.flush()

        # Create generic contacts for Kapibala conversations
        contacts_created = {}
        for i in range(min(10, len(conversations))):
            cid = f"KAPCT{i+1:03d}"
            existing = await db.execute(select(Contact).where(Contact.contact_id == cid))
            if not existing.scalar_one_or_none():
                db.add(Contact(
                    contact_id=cid,
                    customer_id="KAPIBALA",
                    name=f"Sales Agent {i+1}",
                    role="Sales Representative",
                ))
            contacts_created[i] = cid
        await db.flush()

        # Ingest conversations as meetings
        ingested = 0
        for idx, conv in enumerate(conversations):
            transcript, summary, topics = _extract_conversation_text(conv)
            if not transcript or len(transcript.strip()) < 50:
                continue

            meeting_id = _stable_id(f"kapibala_{idx}_{transcript[:100]}")
            existing = await db.execute(select(Meeting).where(Meeting.meeting_id == meeting_id))
            if existing.scalar_one_or_none():
                continue

            contact_id = contacts_created.get(idx % len(contacts_created), "KAPCT001")
            pseudo_date = f"2024-{(idx % 12) + 1:02d}-{(idx % 28) + 1:02d}"

            conv_id = conv.get("id", conv.get("conversation_id", str(idx)))
            title = conv.get("title", f"Sales Conversation #{conv_id}")

            db.add(Meeting(
                meeting_id=meeting_id,
                customer_id="KAPIBALA",
                contact_id=contact_id,
                date=pseudo_date,
                title=title,
                participants=["Sales Agent", "Customer"],
                summary=summary,
                topics=topics,
                transcript=transcript,
                source="kapibala",
            ))

            db.add(Event(
                event_type="meeting",
                event_date=pseudo_date,
                customer_id="KAPIBALA",
                contact_id=contact_id,
                reference_id=meeting_id,
                title=title,
                summary=summary[:500],
            ))

            await memory.retain_meeting(
                customer_id="KAPIBALA",
                contact_id=contact_id,
                meeting_id=meeting_id,
                date=pseudo_date,
                title=title,
                summary=summary,
                topics=topics,
                transcript=transcript[:1500],
                db_session=db,
            )
            ingested += 1

        await db.commit()
        logger.info("Successfully ingested %d Kapibala conversations into DB + Hindsight", ingested)


def main():
    parser = argparse.ArgumentParser(description="Ingest Kapibala sales conversations")
    parser.add_argument("--data-dir", default="data/raw/kapibala", help="Path to Kapibala data directory")
    parser.add_argument("--limit", type=int, default=100, help="Max conversations to ingest")
    args = parser.parse_args()
    asyncio.run(ingest_kapibala(args.data_dir, args.limit))


if __name__ == "__main__":
    main()
