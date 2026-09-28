"""Migrate existing SQLite database to add new Meeting columns and seed upcoming meetings."""

import sqlite3
from datetime import datetime, timedelta

DB_PATH = r"c:\Users\Lakshminath Bandi\OneDrive\Desktop\Microsoft hackthon prototype\meeting-intelligence-agent\backend\meeting_intelligence.db"


def migrate_schema():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(meetings)")
    cols = [row[1] for row in cur.fetchall()]
    print("Existing columns:", cols)

    new_cols = [
        ("scheduled_at", "DATETIME", None),
        ("status", "VARCHAR(20)", "'completed'"),
        ("location", "VARCHAR(300)", None),
        ("agenda", "TEXT", None),
    ]

    for col_name, col_type, default_val in new_cols:
        if col_name not in cols:
            sql = f"ALTER TABLE meetings ADD COLUMN {col_name} {col_type}"
            if default_val:
                sql += f" DEFAULT {default_val}"
            cur.execute(sql)
            print(f"  Added column: {col_name}")
        else:
            print(f"  Column {col_name} already exists")

    conn.commit()

    cur.execute("PRAGMA table_info(meetings)")
    cols = [row[1] for row in cur.fetchall()]
    print("Updated columns:", cols)
    conn.close()


def seed_upcoming_meetings():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    now = datetime.utcnow()

    meetings = [
        {
            "meeting_id": "MU001",
            "customer_id": "C003",
            "contact_id": "P003",
            "title": "Quarterly Account Review",
            "participants": '["Daniel Wong", "Lakshminath"]',
            "location": "Online \u2014 Microsoft Teams",
            "agenda": '["Integration progress update", "Security compliance review", "Implementation timeline discussion", "Q4 planning and next steps"]',
            "days_ahead": 1,
            "hour": 10,
            "minute": 30,
        },
        {
            "meeting_id": "MU002",
            "customer_id": "C001",
            "contact_id": "P001",
            "title": "SOC 2 Compliance Follow-up",
            "participants": '["Sarah Mitchell", "Lakshminath", "Security Team"]',
            "location": "Online \u2014 Zoom",
            "agenda": '["SOC 2 audit documentation status", "Outstanding security requirements", "Vendor assessment completion", "Contract security addendum"]',
            "days_ahead": 3,
            "hour": 14,
            "minute": 0,
        },
        {
            "meeting_id": "MU003",
            "customer_id": "C005",
            "contact_id": "P005",
            "title": "FinEdge Technical Architecture Review",
            "participants": '["Michael Tan", "Lakshminath", "Engineering Lead"]',
            "location": "Online \u2014 Google Meet",
            "agenda": '["API integration architecture", "Data encryption requirements", "Performance benchmarks review", "Regulatory compliance mapping"]',
            "days_ahead": 5,
            "hour": 11,
            "minute": 0,
        },
        {
            "meeting_id": "MU004",
            "customer_id": "C004",
            "contact_id": "P004",
            "title": "Orion HealthTech Implementation Kickoff",
            "participants": '["Priya Menon", "Lakshminath"]',
            "location": "In-Person \u2014 Orion HealthTech, Bangalore Office",
            "agenda": '["Implementation roadmap walkthrough", "HIPAA compliance requirements", "Data migration planning", "Success metrics definition"]',
            "days_ahead": 7,
            "hour": 15,
            "minute": 0,
        },
        {
            "meeting_id": "MU005",
            "customer_id": "C002",
            "contact_id": "P002",
            "title": "Vertex Retail Digital Transformation Check-in",
            "participants": '["Arjun Rao", "Lakshminath"]',
            "location": "Online \u2014 Microsoft Teams",
            "agenda": '["POS integration progress", "Inventory sync requirements", "Omnichannel strategy alignment"]',
            "days_ahead": 10,
            "hour": 10,
            "minute": 0,
        },
    ]

    for m in meetings:
        dt = now + timedelta(days=m["days_ahead"])
        dt = dt.replace(hour=m["hour"], minute=m["minute"], second=0, microsecond=0)
        date_str = dt.strftime("%Y-%m-%d")
        scheduled_at_str = dt.isoformat()

        # Check if exists
        cur.execute(
            "SELECT id FROM meetings WHERE meeting_id = ? AND customer_id = ? AND status = 'upcoming'",
            (m["meeting_id"], m["customer_id"]),
        )
        if cur.fetchone():
            print(f"  Skip {m['meeting_id']}: already exists")
            continue

        cur.execute(
            """INSERT INTO meetings
            (meeting_id, customer_id, contact_id, date, title, participants, summary, topics, transcript, source, scheduled_at, status, location, agenda)
            VALUES (?, ?, ?, ?, ?, ?, NULL, ?, NULL, 'demo', ?, 'upcoming', ?, ?)""",
            (
                m["meeting_id"],
                m["customer_id"],
                m["contact_id"],
                date_str,
                m["title"],
                m["participants"],
                m["agenda"],
                scheduled_at_str,
                m["location"],
                m["agenda"],
            ),
        )
        print(f"  Seeded {m['meeting_id']}: {m['title']} on {date_str} {dt.strftime('%H:%M')}")

    conn.commit()
    conn.close()
    print("\nDone seeding upcoming meetings.")


if __name__ == "__main__":
    print("=== Step 1: Migrate schema ===")
    migrate_schema()
    print("\n=== Step 2: Seed upcoming meetings ===")
    seed_upcoming_meetings()
