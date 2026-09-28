# 🏗️ Architecture Documentation

## Meeting Intelligence Agent — System Design

---

## Overview

The Meeting Intelligence Agent uses a **hybrid memory architecture** that combines
structured relational data (SQLite/PostgreSQL) with semantic long-term memory (Hindsight
by Vectorize) to produce personalized, evidence-grounded meeting preparation briefs.

---

## Core Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │
│  │Dashboard │  │ Meeting  │  │ Memory   │  │  Learning      │  │
│  │  & Stats │  │  Brief   │  │Inspector │  │  Curve Demo    │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───────┬────────┘  │
│       │              │             │                │            │
│       └──────────────┴─────────────┴────────────────┘            │
│                            │ REST API                            │
└────────────────────────────┼─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend (Python)                      │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                   MeetingAgent (Brain)                      │  │
│  │                                                            │  │
│  │  13-Step Meeting Preparation Pipeline:                     │  │
│  │                                                            │  │
│  │  1. Identify contact & company                             │  │
│  │  2. Load structured data (meetings, emails, commitments)   │  │
│  │  3. Query Hindsight for semantic memories                  │  │
│  │  4. Detect recurring concerns (cross-meeting patterns)     │  │
│  │  5. Surface open commitments / broken promises             │  │
│  │  6. Build decision history timeline                        │  │
│  │  7. Extract contact communication preferences              │  │
│  │  8. Detect priority shifts over time                       │  │
│  │  9. Compute relationship trajectory                        │  │
│  │  10. Generate evidence-grounded context for LLM            │  │
│  │  11. Produce personalized meeting brief via LLM            │  │
│  │  12. Attach evidence references                            │  │
│  │  13. Return structured response with citations             │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────┐   ┌───────────────────┐   ┌────────────────┐  │
│  │  LLM Provider│   │  MemoryService    │   │  DatasetLoader │  │
│  │  (Groq/Mock) │   │  (Retain/Recall)  │   │  (Ingestion)   │  │
│  └──────────────┘   └───────────────────┘   └────────────────┘  │
└──────┬──────────────────────┬───────────────────────┬────────────┘
       │                      │                       │
       ▼                      ▼                       ▼
┌──────────────┐    ┌────────────────────┐   ┌─────────────────┐
│  LLM API     │    │   PostgreSQL /     │   │   Hindsight     │
│  (Groq Cloud │    │   SQLite           │   │   (Vectorize)   │
│  or Mock)    │    │                    │   │                 │
│              │    │  Structured data:  │   │  Semantic memory│
│  Generates   │    │  - Companies       │   │  - Temporal     │
│  natural     │    │  - Contacts        │   │  - Relational   │
│  language    │    │  - Meetings        │   │  - Contextual   │
│  briefs      │    │  - Emails          │   │                 │
│              │    │  - Commitments     │   │  retain() →     │
│              │    │  - Decisions       │   │  recall() →     │
│              │    │  - Concerns        │   │  reflect()      │
│              │    │  - Preferences     │   │                 │
└──────────────┘    │  - Events          │   └─────────────────┘
                    │  - Snapshots       │
                    └────────────────────┘

```

---

## Hybrid Memory Design: Why Two Systems?

### PostgreSQL / SQLite — Structured Storage

| Responsibility | Examples |
|---|---|
| Entity identity & relationships | Company → Contact → Meeting chain |
| Temporal ordering | Meeting dates, email timestamps |
| Status tracking | Commitment open/resolved, concern severity |
| Exact-match queries | "All open commitments for customer C001" |
| Referential integrity | Foreign keys ensure data consistency |

### Hindsight (Vectorize) — Semantic Memory

| Responsibility | Examples |
|---|---|
| Semantic similarity recall | "What concerns has Sarah raised?" |
| Cross-event pattern detection | Recurring themes across meetings |
| Temporal + relational context | "How did the relationship evolve?" |
| Contextual briefing support | Rich context for LLM reasoning |
| Long-term memory persistence | Survives beyond session boundaries |

### Why Both?

Neither system alone is sufficient:

- **SQL alone** can't answer "What's the customer's primary concern?" without
  encoding every possible semantic query as a SQL WHERE clause.
- **Semantic memory alone** can't guarantee "show me all open commitments" with
  100% recall — structured status fields require exact-match queries.

The agent queries **both** systems in parallel and merges results before passing
unified context to the LLM for brief generation.

---

## Data Flow

### 1. Ingestion Pipeline

```
Raw Data Sources
  ├── data/synthetic/*.jsonl      ← Controlled longitudinal dataset
  ├── data/raw/ami/               ← AMI Meeting Corpus
  ├── data/raw/kapibala/          ← Kapibala Sales Conversations
  └── data/raw/enron/             ← Enron Email Corpus
        │
        ▼
  DatasetLoader / Ingestion Scripts
        │
        ├──→ PostgreSQL/SQLite (structured records)
        └──→ Hindsight Memory Bank (semantic embeddings)
```

### 2. Meeting Brief Generation

```
User Request: "Prepare for meeting with Sarah Mitchell"
        │
        ▼
  MeetingAgent.generate_meeting_brief()
        │
        ├──→ PostgreSQL: Load company, contact, meetings, emails,
        │    commitments, decisions, concerns, preferences
        │
        ├──→ Hindsight: recall_for_contact(), recall_concerns(),
        │    recall_commitments(), recall_decisions(),
        │    recall_recent_changes(), recall_preferences()
        │
        ▼
  Merge & Format Context
        │
        ▼
  LLM.generate() → Personalized Meeting Brief
        │
        ▼
  Response with: brief, evidence[], memories_used
```

---

## Entity Relationship Diagram

```
Company (1) ──→ (N) Contact
Contact (1) ──→ (N) Meeting
Contact (1) ──→ (N) Email
Contact (1) ──→ (N) Commitment
Contact (1) ──→ (N) Decision
Contact (1) ──→ (N) Concern
Contact (1) ──→ (N) Preference
Company (1) ──→ (N) Event (timeline)
Company (1) ──→ (1) RelationshipSnapshot
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Service info + Hindsight status |
| `GET` | `/health` | Health check |
| `GET` | `/api/customers/` | List all companies |
| `GET` | `/api/contacts/` | List all contacts |
| `GET` | `/api/contacts/{customer_id}` | Contact details + stats |
| `GET` | `/api/contacts/{customer_id}/timeline` | Interaction timeline |
| `GET` | `/api/commitments/` | Commitments by customer |
| `PATCH` | `/api/commitments/{id}` | Update commitment status |
| `POST` | `/api/agent/chat` | Q&A with memory context |
| `POST` | `/api/agent/meeting-brief` | Generate preparation brief |
| `POST` | `/api/agent/comparison` | Before/after demo |
| `POST` | `/api/agent/learning-curve` | 1→5→20 demo stages |
| `GET` | `/api/memory/contact/{cid}` | Inspect memory bank |
| `POST` | `/api/memory/recall` | Semantic memory recall |
| `POST` | `/datasets/ingest-synthetic` | Seed synthetic dataset |

---

## LLM Provider Strategy

The system supports three LLM backends:

1. **Groq** (default production) — Meta Llama 4 Scout via Groq Cloud
2. **OpenAI-compatible** — Any OpenAI API-compatible endpoint
3. **Mock** (development) — Rich, structured mock responses that simulate
   real LLM output for development and demo without API keys

The mock provider generates realistic briefs with:
- Customer-specific data woven into responses
- Proper markdown formatting
- Evidence citations
- Commitment alerts

---

## Frontend Components

| Component | Purpose |
|---|---|
| **Dashboard** | Company selector, stats cards, commitment tracker |
| **Meeting Brief** | Full 12-section personalized brief with evidence |
| **Memory Inspector** | Browse Hindsight memories by category |
| **Timeline** | Chronological interaction visualization |
| **Before/After** | Side-by-side generic vs memory-enhanced comparison |
| **Learning Curve** | 1→5→20 interaction intelligence progression |
| **Chat** | Free-form Q&A with memory-augmented responses |

---

## Evaluation Framework

The `scripts/evaluate_memory.py` benchmark tests five dimensions:

| Metric | Weight | What It Tests |
|---|---|---|
| Semantic Recall | 100 | Can the system recall relevant memories? |
| Promise Tracking | 100 | Are open commitments detected and surfaced? |
| Recurring Objections | 100 | Are cross-meeting concern patterns identified? |
| Evidence Grounding | 100 | Is every claim linked to source events? |
| Memory Information Lift | 100 | Does memory measurably improve output quality? |
| **Total** | **500** | |

---

## Security & Configuration

- All secrets externalized to `.env` (never in code)
- CORS restricted to `http://localhost:3000` by default
- Database credentials via environment variables
- Hindsight API key optional (falls back to local SQLite memory bank)
- LLM API key optional (falls back to mock provider)
