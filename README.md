# 🧠 Meeting Intelligence Agent

> **Memory-Powered Meeting Preparation for Sales Professionals**

An AI agent that **remembers the history of professional relationships** and uses persistent long-term memory to prepare you for future meetings. Built for the **Hindsight Hackathon** by Vectorize.

---

## 🎯 The Problem

Sales representatives have 5th, 10th, or 20th meetings with customers — but their tools have **zero memory** of what happened before. They manually search notes, emails, and CRM records before every meeting, often missing:

- **Promises they made** that are still unfulfilled
- **Concerns the customer raised** repeatedly
- **Decisions that were made** in previous discussions
- **How the relationship evolved** over time

## 💡 The Solution

An AI meeting preparation agent with **persistent long-term memory** powered by **Hindsight (Vectorize)**.

The core loop:

```
Meeting → Remember → Recall → Reason → Prepare → Meeting → Learn again
```

The agent becomes **increasingly intelligent** as more interactions accumulate:

| Interaction | Agent Understanding |
|---|---|
| 1st | Generic customer context |
| 5th | Remembers concerns, promises, and decisions |
| 20th | Deep relationship understanding with evidence |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│                  Frontend                    │
│           Next.js + TypeScript               │
│         (Dashboard, Timeline, Chat)          │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│              FastAPI Backend                 │
│      Agent Tools + Meeting Prep Pipeline     │
└───────┬─────────────────────────┬───────────┘
        │                         │
        ▼                         ▼
┌───────────────┐     ┌────────────────────┐
│  PostgreSQL   │     │    Hindsight       │
│  Structured   │     │  (Vectorize)       │
│   Records     │     │  Semantic Memory   │
│  IDs, Dates   │     │  Temporal Context  │
│  Statuses     │     │  Relationship      │
│               │     │  Intelligence      │
└───────────────┘     └────────────────────┘
```

**PostgreSQL** stores structured business records (entities, IDs, dates, statuses).

**Hindsight** provides long-term semantic and relational memory (intelligence layer).

---

## ✨ Core Features

1. **Customer/Contact Memory** — Remembers every interaction, concern, commitment, and preference
2. **Meeting Preparation** — Generates personalized meeting briefs with evidence
3. **Never Forget a Promise** — Tracks commitments and surfaces unfulfilled ones
4. **What Changed?** — Detects shifts in customer priorities over time
5. **Recurring Concerns** — Identifies patterns across multiple interactions
6. **Decision History** — Tracks decision sequences and current status
7. **Contact Preferences** — Learns communication preferences
8. **Memory Inspector** — Visual UI to inspect what the agent remembers and why
9. **Before/After Demo** — Side-by-side comparison of generic vs memory-enhanced preparation
10. **Visual Timeline** — Chronological view of all interactions

---

## 🗄️ Data Sources

| Dataset | Purpose | Type | Ingestion Script |
|---|---|---|---|
| Synthetic Longitudinal | Controlled customer relationship chains | 10 companies, 40 meetings, 80 emails | `seed_demo.py` |
| AMI Meeting Corpus | Meeting/transcript structure | Public research dataset | `ingest_ami.py` |
| Kapibala Sales Conversations | Sales dialogue patterns | Public dataset | `ingest_kapibala.py` |
| Enron Email Corpus | Real-world email scale testing | 500K+ enterprise emails | `ingest_enron.py` |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker (for PostgreSQL)

### 1. Clone & Setup

```bash
cd meeting-intelligence-agent
cp .env.example .env
# Edit .env with your API keys
```

### 2. Start PostgreSQL

```bash
docker compose up -d
```

### 3. Backend

```bash
cd backend
pip install -e ".[dev]"
python ../scripts/seed_demo.py
uvicorn app.main:app --reload
```

> **Note:** The backend automatically defaults to local SQLite development mode with embedded Hindsight persistent relational memory. No Docker or external PostgreSQL setup is strictly required to run the demo locally!

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

### 5. Ingest Additional Datasets (Optional)

```bash
# AMI Meeting Corpus (requires data/raw/ami/ami_public_manual_1.6.2.zip)
python scripts/ingest_ami.py --limit 50

# Kapibala Sales Conversations (requires data/raw/kapibala/conversations.jsonl)
python scripts/ingest_kapibala.py --limit 100

# Enron Email Corpus (requires data/raw/enron/enron_mail_20150507.tar.gz)
python scripts/ingest_enron.py --limit 500
```

### 6. Run Tests

```bash
python -m pytest tests/ -v
```

### 7. Automated Benchmark & Evaluation

Run the automated evaluation benchmark suite to verify recall precision, commitment extraction, and information lift:

```bash
python scripts/evaluate_memory.py
```

Expected scorecard output:
```text
=================================================================
  EVALUATION SUMMARY SCORECARD
=================================================================
  • Semantic Recall                100/100  ✓
  • Promise Tracking               100/100  ✓
  • Recurring Objections           100/100  ✓
  • Evidence Grounding             100/100  ✓
  • Memory Information Lift        100/100  ✓
-----------------------------------------------------------------
  FINAL SCORE: 500/500 (100.0%)
  Hindsight Memory Status: OPERATIONAL & BENCHMARK CERTIFIED
=================================================================
```

### 8. Open Web Application

Navigate to `http://localhost:3000`

---

## 🔑 Environment Variables

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | SQLite / PostgreSQL connection string | `sqlite+aiosqlite:///./meeting_intelligence.db` |
| `HINDSIGHT_API_KEY` | Vectorize Hindsight API key | Optional (uses local bank when omitted) |
| `HINDSIGHT_BASE_URL` | Hindsight API endpoint | `https://memory.hindsight.ai` |
| `HINDSIGHT_MEMORY_BANK_ID` | Memory bank namespace | `meeting-intelligence` |
| `GROQ_API_KEY` | Groq LLM API key | Optional (rich mock provider included) |
| `LLM_MODEL` | Model name | `meta-llama/llama-4-scout-17b-16e-instruct` |
| `LLM_PROVIDER` | `groq` / `openai` / `mock` | `mock` |

---

## 📁 Project Structure

```
meeting-intelligence-agent/
├── frontend/              # Next.js + TypeScript (Port 3000)
│   ├── app/               # App router, Dashboard, Memory Inspector, Learning Curve
│   └── lib/               # Typed API client
├── backend/               # FastAPI + SQLAlchemy + Hindsight (Port 8000)
│   └── app/
│       ├── agents/        # LLM provider, MeetingAgent pipeline, prompts
│       ├── api/           # REST routes (/customers, /contacts, /agent, /memory)
│       ├── db/            # SQLAlchemy ORM models & async engine
│       ├── hindsight/     # Hindsight API client & MemoryService layer
│       ├── ingestion/     # Longitudinal dataset loaders
│       └── schemas/       # Pydantic v2 schemas
├── data/
│   ├── synthetic/         # Controlled longitudinal ground truth (10 companies)
│   └── raw/               # AMI Meeting Corpus, Kapibala, Enron
├── scripts/
│   ├── seed_demo.py           # Seeds DB & Hindsight memory bank
│   ├── evaluate_memory.py     # Automated benchmark suite (500/500)
│   ├── ingest_ami.py          # AMI Meeting Corpus ingestion
│   ├── ingest_kapibala.py     # Kapibala Sales Conversations ingestion
│   └── ingest_enron.py        # Enron Email Corpus ingestion
├── tests/
│   └── test_backend.py        # Comprehensive backend test suite
├── docs/
│   ├── architecture.md        # System architecture documentation
│   ├── hindsight_integration.md # Hindsight API integration guide
│   └── data_pipeline.md       # Data ingestion pipeline docs
├── docker-compose.yml     # PostgreSQL container setup
├── .env.example           # Environment variable template
└── README.md              # This file
```

---

## 🎬 Demo Scenario

**Customer:** NexaCloud Systems  
**Contact:** Sarah Mitchell — VP Engineering

1. **Meeting 1:** Sarah raises security concerns → Sales rep promises SOC 2 docs
2. **Meeting 2:** API integration discussion
3. **Meeting 3:** Security concern reappears
4. **Email:** Sarah requests documentation again
5. **Meeting 4:** Security becomes a blocker

**"Prepare Meeting"** → The agent produces a personalized brief with:

- ⚠️ **Recurring Concern:** Security compliance appeared 4 times
- 🔴 **Open Commitment:** SOC 2 docs promised but unresolved
- 📊 **What Changed:** Security overtook API integration as primary concern
- ✅ **Previous Decision:** Technical validation pending security resolution
- 💡 **Preference:** Sarah prefers concise summaries with action items

---

## 📝 License

MIT
