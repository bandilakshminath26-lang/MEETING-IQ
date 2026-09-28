# Data Pipeline Documentation

## Overview

The Meeting Intelligence Agent ingests data from multiple sources through
specialized ingestion scripts. Each dataset feeds both the **structured
database** (SQLite/PostgreSQL) and the **Hindsight memory bank**.

---

## Data Sources

### 1. Synthetic Longitudinal Dataset (Primary)

**Path:** `data/synthetic/*.jsonl`

The controlled, curated dataset specifically designed to demonstrate the
agent's longitudinal memory capabilities. Contains realistic customer
relationship chains with deliberate patterns.

| File | Entity Type | Count | Purpose |
|---|---|---|---|
| `companies.jsonl` | Company | 10 | Companies with industry/segment |
| `contacts.jsonl` | Contact | 10+ | Named contacts with roles |
| `meetings.jsonl` | Meeting | 40+ | Meeting summaries & transcripts |
| `emails.jsonl` | Email | 80+ | Bidirectional email threads |
| `commitments.jsonl` | Commitment | 20+ | Promises with status tracking |
| `decisions.jsonl` | Decision | 15+ | Decision records with owners |
| `concerns.jsonl` | Concern | 15+ | Customer concerns with severity |
| `preferences.jsonl` | Preference | 10+ | Communication preferences |
| `events.jsonl` | Event | 100+ | Unified timeline events |
| `relationship_snapshots.jsonl` | Snapshot | 10 | Relationship stage summaries |

**Ingestion:** `POST /datasets/ingest-synthetic` or `python scripts/seed_demo.py`

### 2. AMI Meeting Corpus

**Path:** `data/raw/ami/ami_public_manual_1.6.2.zip`

The AMI Corpus is a multi-modal dataset of meeting recordings with
annotations. We extract meeting transcripts and abstractive summaries.

- **Source:** University of Edinburgh
- **Content:** ~100 meetings with multiple participants
- **Format:** XML word-level transcripts + summary annotations

**Ingestion:** `python scripts/ingest_ami.py --limit 50`

### 3. Kapibala Sales Conversations

**Path:** `data/raw/kapibala/conversations.jsonl`

Sales conversation dataset containing dialogue exchanges that demonstrate
sales interaction patterns.

- **Content:** Sales dialogue transcripts
- **Format:** JSONL with conversation turns

**Ingestion:** `python scripts/ingest_kapibala.py --limit 100`

### 4. Enron Email Corpus

**Path:** `data/raw/enron/` (tar.gz or extracted maildir)

The Enron Email Dataset provides real-world email communication patterns
from a large organization. Used for scale testing and realistic email
thread analysis.

- **Source:** Carnegie Mellon University / FERC
- **Content:** ~500,000 emails from 150 users
- **Format:** Standard email files in maildir structure

**Ingestion:** `python scripts/ingest_enron.py --limit 500`

---

## Ingestion Architecture

```
                    ┌─────────────────────┐
                    │   Raw Data Source    │
                    │  (.jsonl, .tar.gz,  │
                    │   .zip, maildir)     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Parser / Loader   │
                    │                     │
                    │  - Read raw format  │
                    │  - Normalize fields │
                    │  - Deduplicate      │
                    │  - Validate schema  │
                    └───────┬─────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
                ▼                       ▼
    ┌───────────────────┐   ┌───────────────────┐
    │  PostgreSQL/SQLite│   │     Hindsight     │
    │                   │   │                   │
    │  - Company        │   │  retain_meeting() │
    │  - Contact        │   │  retain_email()   │
    │  - Meeting        │   │  retain_commit()  │
    │  - Email          │   │  retain_decision()│
    │  - Commitment     │   │  retain_concern() │
    │  - Decision       │   │  retain_pref()    │
    │  - Concern        │   │                   │
    │  - Preference     │   │  Metadata:        │
    │  - Event          │   │  - customer_id    │
    │  - Snapshot       │   │  - contact_id     │
    │                   │   │  - event_type     │
    └───────────────────┘   │  - event_date     │
                            └───────────────────┘
```

---

## Running All Ingestion Scripts

```bash
# 1. Seed the synthetic dataset (fastest, always run first)
python scripts/seed_demo.py

# 2. Ingest AMI meetings (requires data/raw/ami/ami_public_manual_1.6.2.zip)
python scripts/ingest_ami.py --limit 50

# 3. Ingest Kapibala conversations (requires data/raw/kapibala/conversations.jsonl)
python scripts/ingest_kapibala.py --limit 100

# 4. Ingest Enron emails (requires data/raw/enron/enron_mail_20150507.tar.gz)
python scripts/ingest_enron.py --limit 500
```

---

## Data Quality & Deduplication

Every ingestion script implements:

1. **ID-based deduplication** — Checks for existing records before insert
2. **Schema validation** — Required fields verified before storage
3. **Content truncation** — Long transcripts/bodies capped to prevent DB bloat
4. **Null safety** — Optional fields default gracefully
5. **Source tagging** — Every record is tagged with its source dataset
