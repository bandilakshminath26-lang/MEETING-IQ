"""AMI Meeting Corpus ingestion script.

Parses the AMI Meeting Corpus (ami_public_manual_1.6.2.zip) and
converts meeting annotations into the Meeting Intelligence Agent's
data model.

Usage:
    python scripts/ingest_ami.py [--data-dir data/raw/ami] [--limit 50]
"""

from __future__ import annotations
import argparse
import asyncio
import hashlib
import logging
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.config import get_settings  # noqa: E402
from app.db.database import init_db, async_session_factory  # noqa: E402
from app.db.models.models import Company, Contact, Meeting, Event  # noqa: E402
from app.hindsight import get_memory_service  # noqa: E402
from sqlalchemy import select  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)-30s | %(levelname)s | %(message)s")
logger = logging.getLogger("ingest_ami")


def _stable_id(text: str) -> str:
    return "AMI" + hashlib.md5(text.encode()).hexdigest()[:8].upper()


def _parse_ami_words(xml_bytes: bytes) -> str:
    """Extract words from AMI words XML file."""
    try:
        root = ET.fromstring(xml_bytes)
        words = []
        for w in root.iter("w"):
            text = w.text
            if text:
                words.append(text.strip())
        return " ".join(words)
    except Exception:
        return ""


def _parse_ami_abstractive(xml_bytes: bytes) -> str:
    """Extract abstractive summary from AMI summary XML."""
    try:
        root = ET.fromstring(xml_bytes)
        sentences = []
        for s in root.iter("sentence"):
            if s.text:
                sentences.append(s.text.strip())
        for abstract in root.iter("abstract"):
            if abstract.text:
                sentences.append(abstract.text.strip())
        return " ".join(sentences)
    except Exception:
        return ""


async def ingest_ami(data_dir: str, limit: int = 50):
    """Ingest AMI Meeting Corpus from the zip archive."""
    data_path = Path(data_dir)
    await init_db()
    memory = get_memory_service()

    zip_path = data_path / "ami_public_manual_1.6.2.zip"
    if not zip_path.exists():
        logger.error("AMI archive not found at %s", zip_path)
        logger.info("Download from: https://groups.inf.ed.ac.uk/ami/AMICorpusMirror/amicorpus/")
        return

    logger.info("Reading AMI corpus from: %s", zip_path)

    meetings_data: dict[str, dict] = {}  # meeting_id -> {transcript, summary, participants}

    with zipfile.ZipFile(zip_path, "r") as zf:
        file_list = zf.namelist()

        # Collect meeting IDs from word files
        word_files = [f for f in file_list if ("words/" in f.lower() or "words\\" in f.lower()) and f.endswith(".xml") and not f.endswith("/")]
        summary_files = [f for f in file_list if ("abstractive/" in f.lower() or "abstractive\\" in f.lower()) and f.endswith(".xml") and not f.endswith("/")]

        # Parse word files to get transcripts by meeting
        for wf in word_files[:limit * 4]:  # Multiple participants per meeting
            try:
                parts = wf.split("/")
                # AMI file naming: something like ES2002a.A.words.xml
                filename = parts[-1] if parts else wf
                meeting_prefix = filename.split(".")[0]  # e.g., ES2002a

                raw = zf.read(wf)
                transcript_chunk = _parse_ami_words(raw)

                if meeting_prefix not in meetings_data:
                    meetings_data[meeting_prefix] = {
                        "transcript_parts": [],
                        "summary": "",
                        "participants": [],
                    }

                if transcript_chunk:
                    meetings_data[meeting_prefix]["transcript_parts"].append(transcript_chunk)

                # Extract participant ID from filename
                participant = filename.split(".")[1] if "." in filename else "Unknown"
                if participant not in meetings_data[meeting_prefix]["participants"]:
                    meetings_data[meeting_prefix]["participants"].append(participant)

            except Exception as e:
                logger.debug("Error parsing %s: %s", wf, e)

        # Parse summary files
        for sf in summary_files:
            try:
                parts = sf.split("/")
                filename = parts[-1] if parts else sf
                meeting_prefix = filename.split(".")[0]

                raw = zf.read(sf)
                summary = _parse_ami_abstractive(raw)

                if meeting_prefix in meetings_data and summary:
                    meetings_data[meeting_prefix]["summary"] = summary
            except Exception:
                pass

    logger.info("Found %d AMI meetings", len(meetings_data))

    async with async_session_factory() as db:
        # Create AMI company and contacts
        existing = await db.execute(select(Company).where(Company.customer_id == "AMI"))
        if not existing.scalar_one_or_none():
            db.add(Company(
                customer_id="AMI",
                company_name="AMI Research Group",
                industry="Research & Development",
                segment="Academic",
                country="United Kingdom",
            ))
            await db.flush()

        # Create generic participants
        for i, letter in enumerate(["A", "B", "C", "D"]):
            cid = f"AMICT{letter}"
            existing = await db.execute(select(Contact).where(Contact.contact_id == cid))
            if not existing.scalar_one_or_none():
                db.add(Contact(
                    contact_id=cid,
                    customer_id="AMI",
                    name=f"Participant {letter}",
                    role="Meeting Participant",
                ))
        await db.flush()

        # Ingest meetings
        ingested = 0
        for meeting_prefix, data in list(meetings_data.items())[:limit]:
            meeting_id = f"AMI_{meeting_prefix}"

            existing = await db.execute(select(Meeting).where(Meeting.meeting_id == meeting_id))
            if existing.scalar_one_or_none():
                continue

            transcript = " ".join(data["transcript_parts"])[:5000]
            summary = data["summary"] or f"AMI meeting {meeting_prefix} with {len(data['participants'])} participants."
            participants = data["participants"]

            # Generate a pseudo-date for ordering (AMI meetings don't have real dates)
            pseudo_date = f"2004-{(ingested % 12) + 1:02d}-{(ingested % 28) + 1:02d}"

            db.add(Meeting(
                meeting_id=meeting_id,
                customer_id="AMI",
                contact_id="AMICTA",
                date=pseudo_date,
                title=f"AMI Meeting: {meeting_prefix}",
                participants=participants,
                summary=summary,
                topics=["design", "project", "discussion"],
                transcript=transcript if transcript else None,
                source="ami",
            ))

            db.add(Event(
                event_type="meeting",
                event_date=pseudo_date,
                customer_id="AMI",
                contact_id="AMICTA",
                reference_id=meeting_id,
                title=f"AMI Meeting: {meeting_prefix}",
                summary=summary[:500],
            ))

            await memory.retain_meeting(
                customer_id="AMI",
                contact_id="AMICTA",
                meeting_id=meeting_id,
                date=pseudo_date,
                title=f"AMI Meeting: {meeting_prefix}",
                summary=summary,
                topics=["design", "project", "discussion"],
                transcript=transcript[:1500] if transcript else None,
                db_session=db,
            )
            ingested += 1

        await db.commit()
        logger.info("Successfully ingested %d AMI meetings into DB + Hindsight", ingested)


def main():
    parser = argparse.ArgumentParser(description="Ingest AMI Meeting Corpus")
    parser.add_argument("--data-dir", default="data/raw/ami", help="Path to AMI data directory")
    parser.add_argument("--limit", type=int, default=50, help="Max meetings to ingest")
    args = parser.parse_args()
    asyncio.run(ingest_ami(args.data_dir, args.limit))


if __name__ == "__main__":
    main()
