"""Enron Email Corpus ingestion script.

Parses the Enron maildir archive and converts emails into the Meeting
Intelligence Agent's data model — storing them in PostgreSQL/SQLite and
retaining them in the Hindsight memory bank.

Usage:
    python scripts/ingest_enron.py [--data-dir data/raw/enron] [--limit 500]
"""

from __future__ import annotations
import argparse
import asyncio
import hashlib
import logging
import os
import re
import sys
import tarfile
from email import policy
from email.parser import BytesParser
from pathlib import Path

# Ensure the backend is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.config import get_settings  # noqa: E402
from app.db.database import init_db, async_session_factory  # noqa: E402
from app.db.models.models import Company, Contact, Email, Event  # noqa: E402
from app.hindsight import get_memory_service  # noqa: E402
from sqlalchemy import select  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)-30s | %(levelname)s | %(message)s")
logger = logging.getLogger("ingest_enron")


# ── Parsing helpers ──────────────────────────────────────────────

def _stable_id(text: str) -> str:
    """Generate a short deterministic ID from text."""
    return "EN" + hashlib.md5(text.encode()).hexdigest()[:8].upper()


def _extract_name(addr: str) -> str:
    """Extract a human-readable name from an email address."""
    match = re.match(r"^(.*?)\s*<", addr)
    if match and match.group(1).strip():
        return match.group(1).strip().strip('"')
    local = addr.split("@")[0] if "@" in addr else addr
    return local.replace(".", " ").replace("_", " ").title()


def _parse_email_bytes(raw: bytes) -> dict | None:
    """Parse raw email bytes into a structured dict."""
    try:
        parser = BytesParser(policy=policy.default)
        msg = parser.parsebytes(raw)

        from_addr = msg.get("From", "")
        to_addr = msg.get("To", "")
        subject = msg.get("Subject", "(no subject)")
        date_str = msg.get("Date", "")

        # Extract plain text body
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        body = part.get_content()
                    except Exception:
                        body = str(part.get_payload(decode=True) or b"", errors="replace")
                    break
        else:
            try:
                body = msg.get_content()
            except Exception:
                body = str(msg.get_payload(decode=True) or b"", errors="replace")

        # Parse date to YYYY-MM-DD
        from email.utils import parsedate_to_datetime
        try:
            dt = parsedate_to_datetime(date_str)
            date_normalized = dt.strftime("%Y-%m-%d")
        except Exception:
            date_normalized = "2002-01-01"

        if not from_addr or not body or len(body.strip()) < 20:
            return None

        return {
            "from": from_addr.strip(),
            "to": to_addr.strip(),
            "subject": subject.strip(),
            "date": date_normalized,
            "body": body.strip()[:3000],  # Truncate very long emails
            "from_name": _extract_name(from_addr),
            "to_name": _extract_name(to_addr),
        }
    except Exception as e:
        logger.debug("Failed to parse email: %s", e)
        return None


# ── Main ingestion ───────────────────────────────────────────────

async def ingest_enron(data_dir: str, limit: int = 500):
    """Ingest Enron emails from either extracted maildir or tar.gz archive."""
    data_path = Path(data_dir)
    await init_db()
    memory = get_memory_service()

    emails_parsed: list[dict] = []

    # Check for tar.gz first
    tar_path = data_path / "enron_mail_20150507.tar.gz"
    if not tar_path.exists():
        # Try parent directories
        for candidate in [
            data_path.parent / "enron_mail_20150507.tar.gz",
            data_path.parent.parent / "enron_mail_20150507.tar.gz",
        ]:
            if candidate.exists():
                tar_path = candidate
                break

    if tar_path.exists():
        logger.info("Reading from tar.gz archive: %s", tar_path)
        with tarfile.open(tar_path, "r:gz") as tar:
            for member in tar:
                if len(emails_parsed) >= limit:
                    break
                if not member.isfile() or member.name.endswith("/"):
                    continue
                # Only process email files (skip directories, dots files)
                if "/." in member.name or member.size > 500_000:
                    continue
                try:
                    f = tar.extractfile(member)
                    if f is None:
                        continue
                    raw = f.read()
                    parsed = _parse_email_bytes(raw)
                    if parsed:
                        emails_parsed.append(parsed)
                except Exception:
                    continue
    else:
        # Fall back to extracted maildir
        maildir = data_path / "maildir"
        if not maildir.exists():
            maildir = data_path
        logger.info("Reading from extracted maildir: %s", maildir)
        for root, dirs, files in os.walk(maildir):
            if len(emails_parsed) >= limit:
                break
            for fname in files:
                if len(emails_parsed) >= limit:
                    break
                fpath = Path(root) / fname
                if fpath.stat().st_size > 500_000:
                    continue
                try:
                    raw = fpath.read_bytes()
                    parsed = _parse_email_bytes(raw)
                    if parsed:
                        emails_parsed.append(parsed)
                except Exception:
                    continue

    logger.info("Parsed %d emails from Enron corpus", len(emails_parsed))

    if not emails_parsed:
        logger.warning("No emails found. Ensure data is at %s", data_dir)
        return

    # Create a synthetic company/contact for Enron
    async with async_session_factory() as db:
        # Upsert Enron company
        existing = await db.execute(select(Company).where(Company.customer_id == "ENRON"))
        if not existing.scalar_one_or_none():
            db.add(Company(
                customer_id="ENRON",
                company_name="Enron Corporation",
                industry="Energy & Trading",
                segment="Enterprise",
                country="United States",
            ))
            await db.flush()

        # Collect unique senders/recipients as contacts
        people: dict[str, str] = {}  # email_addr -> name
        for em in emails_parsed:
            addr = em["from"].split("<")[-1].strip(">").strip().lower()
            if "@enron.com" in addr:
                people[addr] = em["from_name"]

        # Create contacts (up to 50 most active)
        contact_map: dict[str, str] = {}  # email_addr -> contact_id
        for idx, (addr, name) in enumerate(list(people.items())[:50]):
            cid = f"ENCT{idx+1:03d}"
            existing = await db.execute(select(Contact).where(Contact.contact_id == cid))
            if not existing.scalar_one_or_none():
                db.add(Contact(
                    contact_id=cid,
                    customer_id="ENRON",
                    name=name,
                    role="Employee",
                    email=addr,
                ))
            contact_map[addr] = cid
        await db.flush()

        # Ingest emails
        ingested = 0
        for em in emails_parsed:
            email_id = _stable_id(f"{em['date']}_{em['subject']}_{em['from']}")
            existing = await db.execute(select(Email).where(Email.email_id == email_id))
            if existing.scalar_one_or_none():
                continue

            sender_addr = em["from"].split("<")[-1].strip(">").strip().lower()
            contact_id = contact_map.get(sender_addr, "ENCT001")

            direction = "outbound" if "@enron.com" in sender_addr else "inbound"

            db.add(Email(
                email_id=email_id,
                customer_id="ENRON",
                contact_id=contact_id,
                date=em["date"],
                direction=direction,
                subject=em["subject"],
                sender=em["from"],
                recipient=em["to"][:300],
                body=em["body"],
                source="enron",
            ))

            # Add to timeline
            db.add(Event(
                event_type="email",
                event_date=em["date"],
                customer_id="ENRON",
                contact_id=contact_id,
                reference_id=email_id,
                title=em["subject"],
                summary=em["body"][:500],
            ))

            # Retain in Hindsight
            await memory.retain_email(
                customer_id="ENRON",
                contact_id=contact_id,
                email_id=email_id,
                date=em["date"],
                subject=em["subject"],
                body=em["body"],
                direction=direction,
                db_session=db,
            )
            ingested += 1

        await db.commit()
        logger.info("Successfully ingested %d Enron emails into DB + Hindsight", ingested)


# ── CLI ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Ingest Enron email corpus")
    parser.add_argument("--data-dir", default="data/raw/enron", help="Path to Enron data directory")
    parser.add_argument("--limit", type=int, default=500, help="Max emails to ingest")
    args = parser.parse_args()
    asyncio.run(ingest_enron(args.data_dir, args.limit))


if __name__ == "__main__":
    main()
