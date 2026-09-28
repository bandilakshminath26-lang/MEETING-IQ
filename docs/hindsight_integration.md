# Hindsight Integration Guide

## Overview

This document describes how the Meeting Intelligence Agent integrates with
**Hindsight by Vectorize** — the core memory system that provides persistent,
semantic, temporal, and relational intelligence.

---

## Architecture: Local vs Cloud

The system supports two modes:

### 1. Local Memory Bank (Default — Development)

When `HINDSIGHT_API_KEY` is not set, the system uses a **local SQLite-backed
memory bank** (`hindsight_memories` table) that provides:

- Full `retain()` / `recall()` / `reflect()` API surface
- Keyword-based search with metadata filtering
- Persistence across server restarts
- Zero external dependencies

### 2. Cloud Memory (Production)

When `HINDSIGHT_API_KEY` is configured:

- Memories are retained via the Hindsight REST API
- Semantic vector search with embedding similarity
- Temporal awareness and relationship graphs
- Scale-out memory across multiple agents

---

## Core Operations

### retain(content, metadata)

Stores a memory in the Hindsight bank. Called during data ingestion.

```python
await memory.retain_meeting(
    customer_id="C001",
    contact_id="CT001",
    meeting_id="M001",
    date="2024-01-15",
    title="Initial Discovery Call",
    summary="Discussed API throughput requirements...",
    topics=["API", "integration", "pricing"],
)
```

**Metadata fields:**
- `customer_id` — Links memory to a company
- `contact_id` — Links memory to a specific person
- `event_id` — Unique identifier for the source event
- `event_type` — One of: `meeting`, `email`, `commitment`, `decision`, `concern`, `preference`
- `event_date` — When the event occurred
- `importance` — `high` or `normal`

### recall(query, limit, metadata_filter)

Retrieves semantically relevant memories.

```python
memories = await memory.recall_for_contact(
    query="What concerns has Sarah raised?",
    customer_id="C001",
    contact_id="CT001",
    limit=20,
)
```

### reflect(prompt)

Asks Hindsight to synthesize a summary from stored memories.

```python
summary = await memory.reflect_on_relationship(
    customer_id="C001",
    contact_name="Sarah Mitchell",
)
```

---

## Memory Categories

| Category | Stored When | Used For |
|---|---|---|
| `meeting` | Meeting ingested | Historical context |
| `email` | Email ingested | Communication patterns |
| `commitment` | Promise extracted | Unfulfilled promise alerts |
| `decision` | Decision logged | Decision history |
| `concern` | Concern raised | Recurring concern detection |
| `preference` | Preference learned | Communication personalization |

---

## Memory Service Layer

The `MemoryService` class (`backend/app/hindsight/memory_service.py`) provides
domain-specific convenience methods:

| Method | Purpose |
|---|---|
| `retain_meeting()` | Store meeting with structured metadata |
| `retain_email()` | Store email with direction tracking |
| `retain_commitment()` | Store promise with status and due date |
| `retain_decision()` | Store decision with owner |
| `retain_concern()` | Store concern with severity |
| `retain_preference()` | Store contact preference |
| `recall_for_contact()` | Retrieve all memories for a contact |
| `recall_commitments()` | Retrieve promise/commitment memories |
| `recall_concerns()` | Retrieve concern/objection memories |
| `recall_decisions()` | Retrieve decision memories |
| `recall_preferences()` | Retrieve preference memories |
| `recall_recent_changes()` | Retrieve recent developments |
| `reflect_on_relationship()` | Generate relationship summary |

---

## Evidence Grounding

Every fact in the meeting brief can be traced back to a source event:

```
Brief: "Sarah raised security compliance concerns 4 times"
  └── Evidence: [CONC001, CONC002, CONC005, CONC008]
       └── Each links to a specific meeting and date
```

This is a core differentiator — the agent never fabricates. Every claim has
a provenance chain back to the original meeting transcript, email, or event.
