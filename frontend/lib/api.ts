/* ───────────────────────────────────────────────────────────
   Meeting Intelligence Agent — API Client
   ─────────────────────────────────────────────────────────── */

// Use relative paths so requests go through Next.js proxy on port 3000
const API_BASE = "http://localhost:8000";

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json();
}

// ── Types ────────────────────────────────────────────────────

export interface Company {
  customer_id: string;
  company_name: string;
  industry: string | null;
  segment: string | null;
  country: string | null;
}

export interface Contact {
  contact_id: string;
  customer_id: string;
  name: string;
  role: string | null;
  email: string | null;
  company_name: string | null;
}

export interface Meeting {
  meeting_id: string;
  customer_id: string;
  contact_id: string;
  date: string;
  title: string;
  participants: string[] | null;
  summary: string | null;
  topics: string[] | null;
  transcript: string | null;
  source: string;
  scheduled_at: string | null;
  status: string | null;
  location: string | null;
  agenda: string[] | null;
}

export interface MeetingDetail extends Meeting {
  company_name: string | null;
  contact_name: string | null;
  contact_role: string | null;
  decisions: { decision_id: string; date: string; decision: string; status: string }[];
  commitments: { commitment_id: string; commitment: string; owner: string; status: string; due_date: string | null; date_created: string }[];
  concerns: { concern_id: string; date: string; concern: string; severity: string; status: string }[];
  related_meetings: { meeting_id: string; date: string; title: string; status: string }[];
  memory_count: number;
}

export interface MeetingMemoryPreview {
  last_discussed: string | null;
  open_commitment: string | null;
  open_commitment_source: string | null;
  recurring_concern: string | null;
  recurring_concern_sources: string[];
  previous_decision: string | null;
  what_changed: string | null;
  suggested_question: string | null;
}

export interface Email {
  email_id: string;
  customer_id: string;
  contact_id: string;
  date: string;
  direction: string;
  subject: string;
  sender: string;
  recipient: string;
  body: string | null;
  related_meeting_id: string | null;
  source: string;
}

export interface Commitment {
  commitment_id: string;
  customer_id: string;
  contact_id: string | null;
  meeting_id: string | null;
  date_created: string;
  owner: string;
  commitment: string;
  due_date: string | null;
  status: string;
  evidence: string | null;
}

export interface Decision {
  decision_id: string;
  customer_id: string;
  meeting_id: string | null;
  date: string;
  decision: string;
  owner: string | null;
  status: string;
}

export interface Concern {
  concern_id: string;
  customer_id: string;
  meeting_id: string | null;
  date: string;
  concern: string;
  severity: string;
  status: string;
}

export interface Preference {
  preference_id: string;
  customer_id: string;
  contact_id: string;
  preference: string;
  source: string | null;
  confidence: number;
}

export interface TimelineEvent {
  event_type: string;
  event_date: string;
  customer_id: string;
  contact_id: string | null;
  reference_id: string | null;
  title: string | null;
  summary: string | null;
}

export interface MeetingBriefResponse {
  brief: string;
  customer_id: string;
  contact_name: string | null;
  company_name: string | null;
  evidence: string[];
  memories_used: number;
}

export interface ChatNextMeeting {
  meeting_id: string;
  title: string;
  scheduled_at: string;
  location?: string | null;
  status: string;
  contact?: {
    id: string;
    name: string;
    role?: string | null;
    email?: string | null;
  } | null;
  company?: {
    id: string;
    name: string;
  } | null;
}

export interface ChatResponse {
  response: string;
  evidence: string[];
  memories_used: number;
  next_meeting?: ChatNextMeeting | null;
  is_schedule_only?: boolean;
}

export interface ComparisonResponse {
  without_memory: string;
  with_memory: string;
  memories_used: number;
  evidence: string[];
}

export interface RelationshipSnapshot {
  customer_id: string;
  company: string;
  contact: string;
  role: string | null;
  relationship_stage: string;
  primary_concern: string | null;
  open_commitments: number;
  meeting_count: number;
  email_count: number;
}

export interface BehaviorChangeExample {
  past_memory: string;
  pattern_detected: string;
  learned_insight: string;
  changed_preparation: string[];
  evidence: string[];
}

export interface EvidenceCountItem {
  topic: string;
  count: number;
  sources: string[];
}

export interface LearningStage {
  stage_number: number;
  title: string;
  interaction_count: number;
  relationship_depth: string;
  brief_snippet: string;
  memories_available: number;
  commitments_tracked: number;
  key_signals: string[];
  risk_level: string;
  same_question?: string;
  agent_knows?: string[];
  agent_response?: string;
  what_learned?: string[];
}

export interface LearningCurveResponse {
  customer_id: string;
  company_name: string;
  contact_name: string;
  stages: LearningStage[];
  behavior_change?: BehaviorChangeExample | null;
  evidence_counts?: EvidenceCountItem[];
}

export interface MemoryItem {
  content: string;
  category: string | null;
  customer_id: string | null;
  contact_id: string | null;
  event_type: string | null;
  event_date: string | null;
  source: string | null;
  relevance_score: number | null;
}

// ── API Functions ────────────────────────────────────────────

export const api = {
  // Customers
  getCustomers: () => fetchAPI<Company[]>("/api/customers/"),
  getCustomer: (id: string) => fetchAPI<Company>(`/api/customers/${id}`),

  // Contacts
  getContacts: (customerId?: string) =>
    fetchAPI<Contact[]>(`/api/contacts/${customerId ? `?customer_id=${customerId}` : ""}`),
  getContact: (id: string) => fetchAPI<Contact>(`/api/contacts/${id}`),
  getContactMeetings: (id: string) => fetchAPI<Meeting[]>(`/api/contacts/${id}/meetings`),
  getContactEmails: (id: string) => fetchAPI<Email[]>(`/api/contacts/${id}/emails`),
  getContactCommitments: (id: string) => fetchAPI<Commitment[]>(`/api/contacts/${id}/commitments`),
  getContactDecisions: (id: string) => fetchAPI<Decision[]>(`/api/contacts/${id}/decisions`),
  getContactConcerns: (id: string) => fetchAPI<Concern[]>(`/api/contacts/${id}/concerns`),
  getContactTimeline: (id: string) => fetchAPI<TimelineEvent[]>(`/api/contacts/${id}/timeline`),

  // Commitments
  getCommitments: (customerId?: string, status?: string) => {
    const params = new URLSearchParams();
    if (customerId) params.set("customer_id", customerId);
    if (status) params.set("status", status);
    return fetchAPI<Commitment[]>(`/api/commitments/?${params}`);
  },
  updateCommitment: (id: string, update: { status?: string; evidence?: string }) =>
    fetchAPI<Commitment>(`/api/commitments/${id}`, {
      method: "PATCH",
      body: JSON.stringify(update),
    }),

  // Agent
  chat: (message: string, customerId?: string, contactId?: string) =>
    fetchAPI<ChatResponse>("/api/agent/chat", {
      method: "POST",
      body: JSON.stringify({ message, customer_id: customerId, contact_id: contactId }),
    }),
  getMeetingBrief: (customerId: string, contactId?: string) =>
    fetchAPI<MeetingBriefResponse>("/api/agent/meeting-brief", {
      method: "POST",
      body: JSON.stringify({ customer_id: customerId, contact_id: contactId }),
    }),
  getComparison: (customerId: string, contactId?: string) =>
    fetchAPI<ComparisonResponse>("/api/agent/comparison", {
      method: "POST",
      body: JSON.stringify({ customer_id: customerId, contact_id: contactId }),
    }),
  getLearningCurve: (customerId: string, contactId?: string) =>
    fetchAPI<LearningCurveResponse>("/api/agent/learning-curve", {
      method: "POST",
      body: JSON.stringify({ customer_id: customerId, contact_id: contactId }),
    }),

  // Memory
  recallMemory: (query: string, customerId?: string, contactId?: string) =>
    fetchAPI<{ memories: MemoryItem[]; total: number }>("/api/memory/recall", {
      method: "POST",
      body: JSON.stringify({ query, customer_id: customerId, contact_id: contactId }),
    }),
  getCustomerTimeline: (customerId: string) =>
    fetchAPI<TimelineEvent[]>(`/api/memory/contact/${customerId}`),

  // Meetings
  getMeetings: (customerId?: string) => {
    const params = customerId ? `?customer_id=${customerId}` : "";
    return fetchAPI<Meeting[]>(`/api/meetings/${params}`);
  },
  getUpcomingMeetings: (customerId?: string) => {
    const params = customerId ? `?customer_id=${customerId}` : "";
    return fetchAPI<Meeting[]>(`/api/meetings/upcoming${params}`);
  },
  getPastMeetings: (customerId?: string) => {
    const params = customerId ? `?customer_id=${customerId}` : "";
    return fetchAPI<Meeting[]>(`/api/meetings/past${params}`);
  },
  getMeetingDetail: (meetingId: string, date?: string) => {
    const params = date ? `?date=${date}` : "";
    return fetchAPI<MeetingDetail>(`/api/meetings/${meetingId}${params}`);
  },
  getMeetingMemoryPreview: (meetingId: string, date?: string) => {
    const params = date ? `?date=${date}` : "";
    return fetchAPI<MeetingMemoryPreview>(`/api/meetings/${meetingId}/memory-preview${params}`);
  },

  // Ingestion
  ingestSynthetic: () =>
    fetchAPI<{ status: string; counts?: Record<string, number> }>("/api/datasets/ingest-synthetic", {
      method: "POST",
    }),

  // Health
  getHealth: () => fetchAPI<{ status: string }>("/api/health"),

  // System Status
  getSystemStatus: () => fetchAPI<SystemStatus>("/api/system/status"),
};

// ── System Status ──────────────────────────────────────────
export interface SystemStatus {
  status: string;
  timestamp: string;
  hindsight: {
    configured: boolean;
    connected: boolean;
    mode: string;
    bank_id: string;
    base_url: string;
    details: string | null;
    fact_count?: number;
  };
  llm: {
    provider: string;
    model: string;
    configured: boolean;
    status: string;
  };
  database: {
    status: string;
    type: string;
    counts: {
      companies: number;
      meetings: number;
      commitments: number;
      memories: number;
    };
  };
}
