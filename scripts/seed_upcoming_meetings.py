"""Seed upcoming (future) meetings into the database using existing customers/contacts.

Run once after the schema migration to populate demo upcoming meetings.
Usage: python -m scripts.seed_upcoming_meetings
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Ensure backend is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.db.database import async_session_factory, init_db
from app.db.models.models import Meeting


# Generate future dates relative to "now"
def future_dt(days: int, hour: int = 10, minute: int = 30) -> datetime:
    return datetime.utcnow() + timedelta(days=days, hours=hour - datetime.utcnow().hour, minutes=minute - datetime.utcnow().minute)


UPCOMING_MEETINGS = [
    {
        "meeting_id": "MU001",
        "customer_id": "C003",
        "contact_id": "P003",
        "title": "Quarterly Account Review",
        "participants": ["Daniel Wong", "Lakshminath"],
        "location": "Online — Microsoft Teams",
        "agenda": [
            "Integration progress update",
            "Security compliance review",
            "Implementation timeline discussion",
            "Q4 planning and next steps",
        ],
        "days_ahead": 1,
        "hour": 10,
        "minute": 30,
    },
    {
        "meeting_id": "MU002",
        "customer_id": "C001",
        "contact_id": "P001",
        "title": "SOC 2 Compliance Follow-up",
        "participants": ["Sarah Mitchell", "Lakshminath", "Security Team"],
        "location": "Online — Zoom",
        "agenda": [
            "SOC 2 audit documentation status",
            "Outstanding security requirements",
            "Vendor assessment completion",
            "Contract security addendum",
        ],
        "days_ahead": 3,
        "hour": 14,
        "minute": 0,
    },
    {
        "meeting_id": "MU003",
        "customer_id": "C005",
        "contact_id": "P005",
        "title": "FinEdge Technical Architecture Review",
        "participants": ["Michael Tan", "Lakshminath", "Engineering Lead"],
        "location": "Online — Google Meet",
        "agenda": [
            "API integration architecture",
            "Data encryption requirements",
            "Performance benchmarks review",
            "Regulatory compliance mapping",
        ],
        "days_ahead": 5,
        "hour": 11,
        "minute": 0,
    },
    {
        "meeting_id": "MU004",
        "customer_id": "C004",
        "contact_id": "P004",
        "title": "Orion HealthTech Implementation Kickoff",
        "participants": ["Priya Menon", "Lakshminath"],
        "location": "In-Person — Orion HealthTech, Bangalore Office",
        "agenda": [
            "Implementation roadmap walkthrough",
            "HIPAA compliance requirements",
            "Data migration planning",
            "Success metrics definition",
        ],
        "days_ahead": 7,
        "hour": 15,
        "minute": 0,
    },
    {
        "meeting_id": "MU005",
        "customer_id": "C002",
        "contact_id": "P002",
        "title": "Vertex Retail Digital Transformation Check-in",
        "participants": ["Arjun Rao", "Lakshminath"],
        "location": "Online — Microsoft Teams",
        "agenda": [
            "POS integration progress",
            "Inventory sync requirements",
            "Omnichannel strategy alignment",
        ],
        "days_ahead": 10,
        "hour": 10,
        "minute": 0,
    },
]


async def seed():
    await init_db()

    async with async_session_factory() as session:
        for m in UPCOMING_MEETINGS:
            dt = future_dt(m["days_ahead"], m["hour"], m["minute"])
            date_str = dt.strftime("%Y-%m-%d")

            # Check if this upcoming meeting already exists
            from sqlalchemy import select
            existing = await session.execute(
                select(Meeting).where(
                    Meeting.meeting_id == m["meeting_id"],
                    Meeting.customer_id == m["customer_id"],
                    Meeting.status == "upcoming",
                )
            )
            if existing.scalar_one_or_none():
                print(f"  ⏭ {m['meeting_id']} already exists, skipping.")
                continue

            meeting = Meeting(
                meeting_id=m["meeting_id"],
                customer_id=m["customer_id"],
                contact_id=m["contact_id"],
                date=date_str,
                title=m["title"],
                participants=m["participants"],
                summary=None,  # No summary yet — meeting hasn't happened
                topics=m.get("agenda"),
                transcript=None,
                source="demo",
                scheduled_at=dt,
                status="upcoming",
                location=m.get("location"),
                agenda=m.get("agenda"),
            )
            session.add(meeting)
            print(f"  ✅ {m['meeting_id']}: {m['title']} — {date_str} {dt.strftime('%H:%M')}")

        await session.commit()
        print("\n✅ Upcoming meetings seeded successfully.")


if __name__ == "__main__":
    asyncio.run(seed())
