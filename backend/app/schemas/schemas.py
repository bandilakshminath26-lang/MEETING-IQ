"""Pydantic schemas for API request/response serialisation."""

from __future__ import annotations
from pydantic import BaseModel, Field


# ── Company ──────────────────────────────────────────────────
class CompanyOut(BaseModel):
    customer_id: str
    company_name: str
    industry: str | None = None
    segment: str | None = None
    country: str | None = None

    model_config = {"from_attributes": True}


# ── Contact ──────────────────────────────────────────────────
class ContactOut(BaseModel):
    contact_id: str
    customer_id: str
    name: str
    role: str | None = None
    email: str | None = None
    company_name: str | None = None

    model_config = {"from_attributes": True}


# ── Meeting ──────────────────────────────────────────────────
class MeetingOut(BaseModel):
    meeting_id: str
    customer_id: str
    contact_id: str
    date: str
    title: str
    participants: list | None = None
    summary: str | None = None
    topics: list | None = None
    transcript: str | None = None
    source: str = "synthetic"
    scheduled_at: str | None = None
    status: str | None = "completed"
    location: str | None = None
    agenda: list | None = None

    model_config = {"from_attributes": True}


class MeetingDetailOut(BaseModel):
    meeting_id: str
    customer_id: str
    contact_id: str
    date: str
    title: str
    participants: list | None = None
    summary: str | None = None
    topics: list | None = None
    transcript: str | None = None
    source: str = "synthetic"
    scheduled_at: str | None = None
    status: str | None = "completed"
    location: str | None = None
    agenda: list | None = None
    # Enriched fields populated by the API
    company_name: str | None = None
    contact_name: str | None = None
    contact_role: str | None = None
    decisions: list = Field(default_factory=list)
    commitments: list = Field(default_factory=list)
    concerns: list = Field(default_factory=list)
    related_meetings: list = Field(default_factory=list)
    memory_count: int = 0

    model_config = {"from_attributes": True}


class MeetingMemoryPreview(BaseModel):
    last_discussed: str | None = None
    open_commitment: str | None = None
    open_commitment_source: str | None = None
    recurring_concern: str | None = None
    recurring_concern_sources: list[str] = Field(default_factory=list)
    previous_decision: str | None = None
    what_changed: str | None = None
    suggested_question: str | None = None


class MeetingPrepareRequest(BaseModel):
    customer_id: str
    contact_id: str | None = None


# ── Email ────────────────────────────────────────────────────
class EmailOut(BaseModel):
    email_id: str
    customer_id: str
    contact_id: str
    date: str
    direction: str
    subject: str
    sender: str
    recipient: str
    body: str | None = None
    related_meeting_id: str | None = None
    source: str = "synthetic"

    model_config = {"from_attributes": True}


# ── Commitment ───────────────────────────────────────────────
class CommitmentOut(BaseModel):
    commitment_id: str
    customer_id: str
    contact_id: str | None = None
    meeting_id: str | None = None
    date_created: str
    owner: str
    commitment: str
    due_date: str | None = None
    status: str
    evidence: str | None = None

    model_config = {"from_attributes": True}


class CommitmentUpdate(BaseModel):
    status: str | None = None
    evidence: str | None = None


# ── Decision ─────────────────────────────────────────────────
class DecisionOut(BaseModel):
    decision_id: str
    customer_id: str
    meeting_id: str | None = None
    date: str
    decision: str
    owner: str | None = None
    status: str

    model_config = {"from_attributes": True}


# ── Concern ──────────────────────────────────────────────────
class ConcernOut(BaseModel):
    concern_id: str
    customer_id: str
    meeting_id: str | None = None
    date: str
    concern: str
    severity: str
    status: str

    model_config = {"from_attributes": True}


# ── Preference ───────────────────────────────────────────────
class PreferenceOut(BaseModel):
    preference_id: str
    customer_id: str
    contact_id: str
    preference: str
    source: str | None = None
    confidence: float

    model_config = {"from_attributes": True}


# ── Event / Timeline ────────────────────────────────────────
class TimelineEvent(BaseModel):
    event_type: str
    event_date: str
    customer_id: str
    contact_id: str | None = None
    reference_id: str | None = None
    title: str | None = None
    summary: str | None = None

    model_config = {"from_attributes": True}


# ── Relationship Snapshot ────────────────────────────────────
class RelationshipSnapshotOut(BaseModel):
    customer_id: str
    company: str
    contact: str
    role: str | None = None
    relationship_stage: str
    primary_concern: str | None = None
    open_commitments: int
    meeting_count: int
    email_count: int

    model_config = {"from_attributes": True}


# ── Agent / Chat ─────────────────────────────────────────────
class ContactBrief(BaseModel):
    id: str
    name: str
    role: str | None = None
    email: str | None = None


class CompanyBrief(BaseModel):
    id: str
    name: str


class NextMeetingOut(BaseModel):
    meeting_id: str
    title: str
    scheduled_at: str
    location: str | None = None
    status: str = "upcoming"
    contact: ContactBrief | None = None
    company: CompanyBrief | None = None


class ChatRequest(BaseModel):
    message: str
    customer_id: str | None = None
    contact_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    evidence: list[str] = Field(default_factory=list)
    memories_used: int = 0
    next_meeting: NextMeetingOut | None = None
    is_schedule_only: bool = False


class MeetingBriefRequest(BaseModel):
    customer_id: str
    contact_id: str | None = None


class MeetingBriefResponse(BaseModel):
    brief: str
    customer_id: str
    contact_name: str | None = None
    company_name: str | None = None
    evidence: list[str] = Field(default_factory=list)
    memories_used: int = 0


# ── Memory ───────────────────────────────────────────────────
class MemoryItem(BaseModel):
    content: str
    category: str | None = None
    customer_id: str | None = None
    contact_id: str | None = None
    event_type: str | None = None
    event_date: str | None = None
    source: str | None = None
    relevance_score: float | None = None


class MemoryRecallRequest(BaseModel):
    query: str
    customer_id: str | None = None
    contact_id: str | None = None
    limit: int = 20


class MemoryRecallResponse(BaseModel):
    memories: list[MemoryItem]
    total: int


# ── Demo ─────────────────────────────────────────────────────
class DemoComparisonRequest(BaseModel):
    customer_id: str
    contact_id: str | None = None


class DemoComparisonResponse(BaseModel):
    without_memory: str
    with_memory: str
    memories_used: int = 0
    evidence: list[str] = Field(default_factory=list)


class BehaviorChangeExample(BaseModel):
    past_memory: str
    pattern_detected: str
    learned_insight: str
    changed_preparation: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class EvidenceCountItem(BaseModel):
    topic: str
    count: int
    sources: list[str] = Field(default_factory=list)


class LearningStage(BaseModel):
    stage_number: int
    title: str
    interaction_count: int
    relationship_depth: str
    brief_snippet: str
    memories_available: int
    commitments_tracked: int
    key_signals: list[str]
    risk_level: str
    same_question: str = "Prepare me for my meeting with Sarah."
    agent_knows: list[str] = Field(default_factory=list)
    agent_response: str = ""
    what_learned: list[str] = Field(default_factory=list)


class LearningCurveRequest(BaseModel):
    customer_id: str
    contact_id: str | None = None


class LearningCurveResponse(BaseModel):
    customer_id: str
    company_name: str
    contact_name: str
    stages: list[LearningStage]
    behavior_change: BehaviorChangeExample | None = None
    evidence_counts: list[EvidenceCountItem] = Field(default_factory=list)

