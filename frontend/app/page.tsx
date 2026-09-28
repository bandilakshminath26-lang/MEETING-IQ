"use client";

import React, { useEffect, useState, useMemo } from "react";
import {
  api,
  Company,
  Contact,
  Commitment,
  Meeting,
  MeetingDetail,
  MeetingMemoryPreview,
  TimelineEvent,
  MeetingBriefResponse,
  ComparisonResponse,
  ChatResponse,
  ChatNextMeeting,
  MemoryItem,
  LearningCurveResponse,
  SystemStatus,
} from "@/lib/api";

// ── Icons (Inline SVG) ──────────────────────────────────────
const Icons = {
  dashboard: (
    <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
    </svg>
  ),
  users: (
    <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  ),
  brief: (
    <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
      <polyline points="10 9 9 9 8 9" />
    </svg>
  ),
  inspector: (
    <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
      <path d="M11 8v6M8 11h6" />
    </svg>
  ),
  learning: (
    <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
    </svg>
  ),
  timeline: (
    <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <line x1="12" y1="2" x2="12" y2="22" />
      <circle cx="12" cy="6" r="2" />
      <circle cx="12" cy="12" r="2" />
      <circle cx="12" cy="18" r="2" />
    </svg>
  ),
  compare: (
    <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <rect x="2" y="4" width="8" height="16" rx="1" />
      <rect x="14" y="4" width="8" height="16" rx="1" />
    </svg>
  ),
  chat: (
    <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  ),
  send: (
    <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  ),
  alert: (
    <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
      <line x1="12" y1="9" x2="12" y2="13" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  ),
  check: (
    <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  ),
  copy: (
    <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
    </svg>
  ),
  calendar: (
    <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
      <line x1="16" y1="2" x2="16" y2="6" />
      <line x1="8" y1="2" x2="8" y2="6" />
      <line x1="3" y1="10" x2="21" y2="10" />
    </svg>
  ),
};

type View =
  | "dashboard"
  | "brief"
  | "meetings"
  | "meetingDetail"
  | "inspector"
  | "learning"
  | "comparison"
  | "timeline"
  | "chat"
  | "customers";

export default function Home() {
  const [view, setView] = useState<View>("dashboard");
  const [companies, setCompanies] = useState<Company[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState<string>("C001");
  const [selectedContact, setSelectedContact] = useState<Contact | null>(null);
  const [commitments, setCommitments] = useState<Commitment[]>([]);
  const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>([]);
  const [timelineFilter, setTimelineFilter] = useState<string>("all");

  // Brief state
  const [brief, setBrief] = useState<MeetingBriefResponse | null>(null);
  const [briefLoading, setBriefLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  // Comparison state
  const [comparison, setComparison] = useState<ComparisonResponse | null>(null);
  const [compLoading, setCompLoading] = useState(false);

  // Learning curve state
  const [learningCurve, setLearningCurve] = useState<LearningCurveResponse | null>(null);
  const [selectedStage, setSelectedStage] = useState<number>(3);
  const [learningLoading, setLearningLoading] = useState(false);

  // Memory Inspector state
  const [inspectorQuery, setInspectorQuery] = useState("security compliance SOC 2");
  const [inspectorMemories, setInspectorMemories] = useState<MemoryItem[]>([]);
  const [inspectorFilter, setInspectorFilter] = useState("all");
  const [inspectorLoading, setInspectorLoading] = useState(false);
  const [inspectedMemory, setInspectedMemory] = useState<MemoryItem | null>(null);

  // Chat state
  const [chatMessages, setChatMessages] = useState<
    {
      role: string;
      content: string;
      evidence?: string[];
      memoriesUsed?: number;
      nextMeeting?: ChatNextMeeting | null;
      isScheduleOnly?: boolean;
    }[]
  >([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);

  // General error banner
  const [error, setError] = useState<string | null>(null);

  // Live System Status (Hindsight Cloud, LLM, Database)
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);

  // Why This Matters interactive state
  const [activeWhyThisMatters, setActiveWhyThisMatters] = useState<string | null>(null);

  // Meetings state
  const [upcomingMeetings, setUpcomingMeetings] = useState<Meeting[]>([]);
  const [pastMeetings, setPastMeetings] = useState<Meeting[]>([]);
  const [selectedMeeting, setSelectedMeeting] = useState<MeetingDetail | null>(null);
  const [meetingMemoryPreview, setMeetingMemoryPreview] = useState<MeetingMemoryPreview | null>(null);
  const [dashboardMemoryPreview, setDashboardMemoryPreview] = useState<MeetingMemoryPreview | null>(null);
  const [activeDashboardMeetingId, setActiveDashboardMeetingId] = useState<string | null>(null);
  const [meetingsLoading, setMeetingsLoading] = useState(false);
  const [meetingDetailLoading, setMeetingDetailLoading] = useState(false);
  const [memoryPreviewLoading, setMemoryPreviewLoading] = useState(false);
  const [meetingsFilterCustomer, setMeetingsFilterCustomer] = useState<string>("all");
  const [meetingsTab, setMeetingsTab] = useState<"upcoming" | "past" | "all">("upcoming");
  const [meetingsSearch, setMeetingsSearch] = useState<string>("");

  function formatMeetingTime(dateStr?: string | null, scheduledAt?: string | null) {
    if (scheduledAt) {
      try {
        const dt = new Date(scheduledAt);
        const now = new Date();
        const diffMs = dt.getTime() - now.getTime();
        const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24));
        let rel = "";
        if (diffDays === 0) rel = "Today · ";
        else if (diffDays === 1) rel = "Tomorrow · ";
        else if (diffDays > 1 && diffDays <= 7) rel = `In ${diffDays} days · `;
        return `${rel}${dt.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })} at ${dt.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })}`;
      } catch {
        // fallback
      }
    }
    return dateStr || "Date scheduled";
  }

  function formatDateOnly(scheduledAt?: string | null) {
    if (!scheduledAt) return "Upcoming";
    try {
      const dt = new Date(scheduledAt);
      return dt.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
    } catch {
      return scheduledAt;
    }
  }

  function formatTimeOnly(scheduledAt?: string | null) {
    if (!scheduledAt) return "";
    try {
      const dt = new Date(scheduledAt);
      return dt.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
    } catch {
      return "";
    }
  }

  async function loadDashboardPreviewForMeeting(m: Meeting) {
    setActiveDashboardMeetingId(m.meeting_id);
    try {
      const preview = await api.getMeetingMemoryPreview(m.meeting_id, m.date);
      setDashboardMemoryPreview(preview);
    } catch (err) {
      console.error("Dashboard preview fetch failed:", err);
    }
  }

  // ── Evidence Resolution & Navigation ────────────────────────
  function resolveEvidence(id: string) {
    const cleanId = id.trim();
    const matchedEvent = timelineEvents.find(
      (e) => e.reference_id?.toLowerCase() === cleanId.toLowerCase() || e.summary?.includes(cleanId)
    );
    const matchedCommitment = commitments.find(
      (c) => c.commitment_id?.toLowerCase() === cleanId.toLowerCase()
    );
    const matchedMeeting = [...upcomingMeetings, ...pastMeetings].find(
      (m) => m.meeting_id?.toLowerCase() === cleanId.toLowerCase()
    );

    if (cleanId.startsWith("M")) {
      const date = matchedMeeting?.date || matchedEvent?.event_date || "";
      const formattedDate = date ? new Date(date).toLocaleDateString("en-US", { month: "short", day: "numeric" }) : "";
      return {
        type: "meeting" as const,
        label: `${cleanId} · Meeting${formattedDate ? ` · ${formattedDate}` : ""}`,
        title: matchedMeeting?.title || matchedEvent?.title || "Meeting Interaction",
        date,
      };
    }
    if (cleanId.startsWith("E")) {
      const date = matchedEvent?.event_date || "";
      const formattedDate = date ? new Date(date).toLocaleDateString("en-US", { month: "short", day: "numeric" }) : "";
      return {
        type: "email" as const,
        label: `${cleanId} · Email${formattedDate ? ` · ${formattedDate}` : ""}`,
        title: matchedEvent?.title || "Email Correspondence",
        date,
      };
    }
    if (cleanId.startsWith("D")) {
      return {
        type: "decision" as const,
        label: `${cleanId} · Decision`,
        title: matchedEvent?.title || "Agreed Decision Milestone",
        date: matchedEvent?.event_date || "",
      };
    }
    if (cleanId.startsWith("C") && !cleanId.startsWith("CN")) {
      const status = matchedCommitment?.status ? ` · ${matchedCommitment.status.toUpperCase()}` : "";
      return {
        type: "commitment" as const,
        label: `${cleanId} · Commitment${status}`,
        title: matchedCommitment?.commitment || "Tracked Commitment",
        date: matchedCommitment?.date_created || "",
      };
    }
    if (cleanId.startsWith("CN")) {
      return {
        type: "concern" as const,
        label: `${cleanId} · Concern`,
        title: matchedEvent?.title || "Logged Stakeholder Concern",
        date: matchedEvent?.event_date || "",
      };
    }
    return {
      type: "memory" as const,
      label: `${cleanId} · Hindsight Recall`,
      title: "Semantic Memory Retrieval",
      date: "",
    };
  }

  function handleEvidenceClick(id: string) {
    const res = resolveEvidence(id);
    if (res.type === "meeting") {
      setView("meetings");
      loadMeetingsPage();
    } else if (res.type === "commitment") {
      setView("timeline");
      setTimelineFilter("commitment");
    } else if (res.type === "decision") {
      setView("timeline");
      setTimelineFilter("decision");
    } else if (res.type === "email") {
      setView("timeline");
      setTimelineFilter("email");
    } else if (res.type === "concern") {
      setView("timeline");
      setTimelineFilter("concern");
    } else {
      setView("inspector");
      setInspectorQuery(id);
      searchMemory(id);
    }
  }

  // ── Why This Matters Dynamic Grounding ──────────────────────
  function getWhyThisMatters(topicKey: string) {
    const lowerKey = topicKey.toLowerCase();
    let title = "Security & Compliance Requirements";
    let terms = ["security", "soc 2", "compliance", "cert", "audit"];

    if (lowerKey.includes("pricing") || lowerKey.includes("commercial")) {
      title = "Enterprise Pricing & Commercial Flexibility";
      terms = ["pricing", "commercial", "discount", "contract", "enterprise", "flexibility"];
    } else if (lowerKey.includes("api") || lowerKey.includes("salesforce") || lowerKey.includes("integrat")) {
      title = "Salesforce & API Architecture Integration";
      terms = ["api", "integration", "salesforce", "technical", "connector"];
    }

    const matchingEvents = timelineEvents.filter((e) => {
      const text = `${e.title || ""} ${e.summary || ""}`.toLowerCase();
      return terms.some((t) => text.includes(t));
    });

    const matchingCommitments = commitments.filter((c) => {
      const text = `${c.commitment} ${c.evidence || ""}`.toLowerCase();
      return terms.some((t) => text.includes(t));
    });

    const dates = Array.from(
      new Set([
        ...matchingEvents.map((e) => e.event_date),
        ...matchingCommitments.map((c) => c.date_created),
      ])
    ).sort();

    const formattedDates = dates.map((d) => {
      try {
        return new Date(d).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
      } catch {
        return d;
      }
    });

    const sources = Array.from(
      new Set([
        ...matchingEvents.map((e) => e.reference_id).filter(Boolean),
        ...matchingCommitments.map((c) => c.commitment_id).filter(Boolean),
      ])
    ) as string[];

    const quote =
      matchingCommitments[0]?.commitment ||
      matchingEvents[0]?.summary ||
      "Recurring strategic requirement actively tracked across executive meetings.";

    return {
      title,
      occurrences: matchingEvents.length + matchingCommitments.length,
      dates: formattedDates,
      sources,
      quote,
      searchQuery: terms.slice(0, 3).join(" "),
    };
  }

  function renderWhyThisMatters(topic: string, label: string) {
    const isExpanded = activeWhyThisMatters === topic;
    const data = getWhyThisMatters(topic);

    return (
      <div key={topic} style={{ margin: "10px 0" }}>
        <button
          className="why-this-matters-toggle"
          onClick={() => setActiveWhyThisMatters(isExpanded ? null : topic)}
        >
          <span>🔍</span>
          <span>{isExpanded ? `Hide Context: ${label}` : `Why is ${label} highlighted?`}</span>
          <span style={{ fontSize: "0.65rem" }}>{isExpanded ? "▲" : "▼"}</span>
        </button>

        {isExpanded && (
          <div className="why-this-matters-box fade-in">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
              <div>
                <p style={{ fontSize: "0.68rem", fontWeight: 800, color: "var(--primary-blue)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                  WHY THIS MATTERS · GROUNDED MEMORY TRAIL
                </p>
                <h4 style={{ fontSize: "0.98rem", fontWeight: 800, marginTop: 2 }}>{data.title}</h4>
              </div>
              <span className="badge badge-active" style={{ fontSize: "0.68rem" }}>
                {data.occurrences} Historical Signals
              </span>
            </div>

            <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)", marginBottom: 12 }}>
              Mentioned across multiple historical interactions with {selectedCompany?.company_name || "the account"}.
            </p>

            {data.dates.length > 0 && (
              <div style={{ marginBottom: 12 }}>
                <p style={{ fontSize: "0.7rem", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: 6 }}>
                  Relevant Timeline History:
                </p>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                  {data.dates.map((d, i) => (
                    <span key={i} className="stat-pill" style={{ fontSize: "0.72rem" }}>
                      📅 {d}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div style={{ padding: 12, background: "var(--very-light-blue)", borderRadius: "var(--radius-sm)", marginBottom: 12, borderLeft: "3px solid var(--primary-blue)" }}>
              <p style={{ fontSize: "0.7rem", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: 4 }}>
                Supporting Memory Grounding:
              </p>
              <p style={{ fontSize: "0.82rem", color: "var(--text-primary)", fontStyle: "italic", margin: 0 }}>
                &quot;{data.quote}&quot;
              </p>
            </div>

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 8 }}>
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                {data.sources.map((s) => (
                  <button
                    key={s}
                    className="evidence-chip"
                    style={{ fontSize: "0.68rem", padding: "2px 8px" }}
                    onClick={() => handleEvidenceClick(s)}
                  >
                    Source: {s}
                  </button>
                ))}
              </div>
              <button
                className="btn-secondary"
                style={{ fontSize: "0.75rem", padding: "4px 10px" }}
                onClick={() => {
                  setView("inspector");
                  setInspectorQuery(data.searchQuery);
                  searchMemory(data.searchQuery);
                }}
              >
                Open in Memory Inspector →
              </button>
            </div>
          </div>
        )}
      </div>
    );
  }

  // ── Memory Evidence Card Component ──────────────────────────
  function renderMemoryEvidenceCard(evidence: string[], memoriesUsed: number, contextLabel?: string) {
    const safeEvidence = Array.from(new Set(evidence || [])).filter(Boolean);
    const interactionCount = safeEvidence.filter((e) => e.startsWith("M") || e.startsWith("E")).length;
    const decisionCount = safeEvidence.filter((e) => e.startsWith("D")).length;
    const commitmentCount = safeEvidence.filter((e) => e.startsWith("C") && !e.startsWith("CN")).length;
    const concernCount = safeEvidence.filter((e) => e.startsWith("CN") || e.startsWith("R")).length;

    return (
      <div className="memory-evidence-card">
        <div className="memory-evidence-header">
          <div className="memory-evidence-title">
            <span style={{ fontSize: "1.1rem" }}>🧠</span>
            <span>Memory Evidence Trail</span>
          </div>
          <span className="hindsight-grounded-tag">
            {contextLabel || "Hindsight Cloud Grounded"}
          </span>
        </div>

        <div className="memory-evidence-stats">
          <div className="stat-pill primary">
            <strong>{memoriesUsed || safeEvidence.length}</strong> memories recalled
          </div>
          {interactionCount > 0 && (
            <div className="stat-pill">
              <strong>{interactionCount}</strong> historical interactions
            </div>
          )}
          {decisionCount > 0 && (
            <div className="stat-pill">
              <strong>{decisionCount}</strong> decisions
            </div>
          )}
          {commitmentCount > 0 && (
            <div className="stat-pill">
              <strong>{commitmentCount}</strong> commitments
            </div>
          )}
          {concernCount > 0 && (
            <div className="stat-pill">
              <strong>{concernCount}</strong> recurring concerns
            </div>
          )}
        </div>

        <div className="evidence-chips-container">
          {safeEvidence.map((refId) => {
            const res = resolveEvidence(refId);
            return (
              <button
                key={refId}
                className="evidence-chip"
                title={`${res.title}${res.date ? ` (${res.date})` : ""}`}
                onClick={() => handleEvidenceClick(refId)}
              >
                <span className={`chip-type ${res.type}`}>{res.type}</span>
                <span>{res.label}</span>
              </button>
            );
          })}
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingTop: 8, borderTop: "1px dashed #BFDBFE", flexWrap: "wrap", gap: 8 }}>
          <span style={{ fontSize: "0.72rem", color: "var(--text-secondary)" }}>
            Click any evidence pill to trace the original historical interaction.
          </span>
          <button
            onClick={() => {
              setView("inspector");
              if (safeEvidence.length > 0) {
                setInspectorQuery(safeEvidence[0]);
                searchMemory(safeEvidence[0]);
              }
            }}
            style={{
              background: "none",
              border: "none",
              color: "var(--primary-blue)",
              fontSize: "0.76rem",
              fontWeight: 700,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: 4,
            }}
          >
            View Memory Trail in Inspector →
          </button>
        </div>
      </div>
    );
  }

  // Load initial data on mount
  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const [companiesData, contactsData, upcomingData, statusData] = await Promise.all([
        api.getCustomers(),
        api.getContacts(),
        api.getUpcomingMeetings(),
        api.getSystemStatus().catch(() => null),
      ]);
      setCompanies(companiesData);
      setContacts(contactsData);
      setUpcomingMeetings(upcomingData);
      if (statusData) setSystemStatus(statusData);

      // Default to NexaCloud Systems (C001) if available, or first company
      const defaultCust = companiesData.find((c) => c.customer_id === "C001") || companiesData[0];
      if (defaultCust) {
        setSelectedCustomer(defaultCust.customer_id);
        await loadCustomerData(defaultCust.customer_id, contactsData);
      }

      // Load preview for the initial upcoming meeting
      if (upcomingData.length > 0) {
        const initialMeeting =
          upcomingData.find((m) => m.customer_id === (defaultCust?.customer_id || "C001")) ||
          upcomingData[0];
        loadDashboardPreviewForMeeting(initialMeeting);
      }
    } catch (e: any) {
      setError(`Failed to load data: ${e.message}. Is the backend running on port 8000?`);
    }
  }

  async function loadCustomerData(customerId: string, customContacts?: Contact[]) {
    setSelectedCustomer(customerId);
    const contactList = customContacts || contacts;
    const contact = contactList.find((c) => c.customer_id === customerId);
    setSelectedContact(contact || null);

    // Reset briefs & comparisons when customer changes
    setBrief(null);
    setComparison(null);
    setLearningCurve(null);

    try {
      const [commitmentsData, timelineData] = await Promise.all([
        api.getCommitments(customerId),
        api.getCustomerTimeline(customerId),
      ]);
      setCommitments(commitmentsData);
      setTimelineEvents(timelineData);

      // If customer has an upcoming meeting, sync preview
      const custUpcoming = upcomingMeetings.find((m) => m.customer_id === customerId);
      if (custUpcoming) {
        loadDashboardPreviewForMeeting(custUpcoming);
      }
    } catch (e: any) {
      console.error("Error loading customer data:", e);
    }
  }

  async function loadMeetingsPage() {
    setMeetingsLoading(true);
    try {
      const [upcoming, past] = await Promise.all([
        api.getUpcomingMeetings(),
        api.getPastMeetings(),
      ]);
      setUpcomingMeetings(upcoming);
      setPastMeetings(past);
    } catch (e: any) {
      setError(`Failed to load meetings: ${e.message}`);
    }
    setMeetingsLoading(false);
  }

  async function openMeetingDetail(meetingId: string, date?: string) {
    setMeetingDetailLoading(true);
    setSelectedMeeting(null);
    setMeetingMemoryPreview(null);
    try {
      const detail = await api.getMeetingDetail(meetingId, date);
      setSelectedMeeting(detail);
      setView("meetingDetail");
      // Load memory preview in parallel
      loadMemoryPreview(meetingId, date);
    } catch (e: any) {
      setError(`Failed to load meeting detail: ${e.message}`);
    }
    setMeetingDetailLoading(false);
  }

  async function loadMemoryPreview(meetingId: string, date?: string) {
    setMemoryPreviewLoading(true);
    try {
      const preview = await api.getMeetingMemoryPreview(meetingId, date);
      setMeetingMemoryPreview(preview);
    } catch (e: any) {
      console.error("Memory preview load failed:", e);
    }
    setMemoryPreviewLoading(false);
  }

  function prepareUpcomingBrief(customerId: string, contactId?: string) {
    loadCustomerData(customerId);
    setView("brief");
    // Trigger brief generation for this customer
    setTimeout(async () => {
      setBriefLoading(true);
      setBrief(null);
      try {
        const result = await api.getMeetingBrief(customerId, contactId);
        setBrief(result);
      } catch (e: any) {
        setError(`Brief generation failed: ${e.message}`);
      }
      setBriefLoading(false);
    }, 100);
  }

  async function generateBrief() {
    if (!selectedCustomer) return;
    setBriefLoading(true);
    setBrief(null);
    try {
      const result = await api.getMeetingBrief(selectedCustomer, selectedContact?.contact_id);
      setBrief(result);
    } catch (e: any) {
      setError(`Brief generation failed: ${e.message}`);
    }
    setBriefLoading(false);
  }

  async function generateComparison() {
    if (!selectedCustomer) return;
    setCompLoading(true);
    setComparison(null);
    try {
      const result = await api.getComparison(selectedCustomer, selectedContact?.contact_id);
      setComparison(result);
    } catch (e: any) {
      setError(`Comparison failed: ${e.message}`);
    }
    setCompLoading(false);
  }

  async function loadLearningCurve() {
    if (!selectedCustomer) return;
    setLearningLoading(true);
    try {
      const result = await api.getLearningCurve(selectedCustomer, selectedContact?.contact_id);
      setLearningCurve(result);
    } catch (e: any) {
      setError(`Learning curve failed: ${e.message}`);
    }
    setLearningLoading(false);
  }

  async function searchMemory(queryText?: string) {
    const q = queryText !== undefined ? queryText : inspectorQuery;
    if (!q.trim()) return;
    setInspectorLoading(true);
    try {
      const result = await api.recallMemory(q, selectedCustomer, selectedContact?.contact_id);
      setInspectorMemories(result.memories);
    } catch (e: any) {
      setError(`Memory recall failed: ${e.message}`);
    }
    setInspectorLoading(false);
  }

  async function toggleCommitmentStatus(commitmentId: string, currentStatus: string) {
    const newStatus = currentStatus === "open" ? "completed" : "open";
    try {
      // Optimistic update
      setCommitments((prev) =>
        prev.map((c) => (c.commitment_id === commitmentId ? { ...c, status: newStatus } : c))
      );
      await api.updateCommitment(commitmentId, { status: newStatus });
    } catch (e: any) {
      setError(`Failed to update commitment: ${e.message}`);
      // Revert on error
      const refreshed = await api.getCommitments(selectedCustomer);
      setCommitments(refreshed);
    }
  }

  async function sendChat() {
    if (!chatInput.trim() || chatLoading) return;
    const msg = chatInput;
    setChatInput("");
    setChatLoading(true);
    setChatMessages((prev) => [...prev, { role: "user", content: msg }]);

    try {
      const result = await api.chat(msg, selectedCustomer || undefined, selectedContact?.contact_id || undefined);
      setChatMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: result.response,
          evidence: result.evidence,
          memoriesUsed: result.memories_used,
          nextMeeting: result.next_meeting,
          isScheduleOnly: result.is_schedule_only,
        },
      ]);
    } catch (e: any) {
      setChatMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Error communicating with agent: ${e.message}` },
      ]);
    }
    setChatLoading(false);
  }

  function copyBriefText() {
    if (!brief) return;
    navigator.clipboard.writeText(brief.brief);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  const selectedCompany = companies.find((c) => c.customer_id === selectedCustomer);
  const openCommitments = commitments.filter((c) => c.status === "open");

  const filteredTimeline = useMemo(() => {
    if (timelineFilter === "all") return timelineEvents;
    return timelineEvents.filter((ev) => ev.event_type === timelineFilter);
  }, [timelineEvents, timelineFilter]);

  const filteredInspectorMemories = useMemo(() => {
    if (inspectorFilter === "all") return inspectorMemories;
    return inspectorMemories.filter((m) => (m.event_type || m.category) === inspectorFilter);
  }, [inspectorMemories, inspectorFilter]);

  const filteredUpcomingMeetings = useMemo(() => {
    if (meetingsFilterCustomer === "all") return upcomingMeetings;
    return upcomingMeetings.filter((m) => m.customer_id === meetingsFilterCustomer);
  }, [upcomingMeetings, meetingsFilterCustomer]);

  const filteredPastMeetings = useMemo(() => {
    let list = pastMeetings;
    if (meetingsFilterCustomer !== "all") {
      list = list.filter((m) => m.customer_id === meetingsFilterCustomer);
    }
    if (meetingsSearch.trim()) {
      const q = meetingsSearch.toLowerCase();
      list = list.filter(
        (m) =>
          m.title.toLowerCase().includes(q) ||
          (m.summary && m.summary.toLowerCase().includes(q)) ||
          m.customer_id.toLowerCase().includes(q) ||
          m.participants?.some((p) => p.toLowerCase().includes(q))
      );
    }
    return list;
  }, [pastMeetings, meetingsFilterCustomer, meetingsSearch]);

  const activeUpcomingMeeting = useMemo(() => {
    if (activeDashboardMeetingId) {
      const found = upcomingMeetings.find((m) => m.meeting_id === activeDashboardMeetingId);
      if (found) return found;
    }
    return (
      upcomingMeetings.find((m) => m.customer_id === selectedCustomer) ||
      upcomingMeetings[0] ||
      null
    );
  }, [upcomingMeetings, activeDashboardMeetingId, selectedCustomer]);

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      {/* ── SIDEBAR ────────────────────────────────────────── */}
      <aside
        style={{
          width: 270,
          background: "rgba(255, 255, 255, 0.95)",
          backdropFilter: "blur(12px)",
          WebkitBackdropFilter: "blur(12px)",
          borderRight: "1px solid var(--border-color)",
          padding: "24px 16px",
          display: "flex",
          flexDirection: "column",
          gap: 6,
          position: "fixed",
          top: 0,
          left: 0,
          bottom: 0,
          zIndex: 20,
          overflowY: "auto",
        }}
      >
        <div style={{ marginBottom: 20, padding: "0 8px" }}>
          <img
            src="/images/meetingiq-logo.png"
            alt="MeetingIQ — Hindsight Memory Agent"
            style={{
              width: "100%",
              maxWidth: 200,
              height: "auto",
              objectFit: "contain",
            }}
          />
        </div>

        {/* Navigation Items */}
        {(
          [
            ["dashboard", "Dashboard", Icons.dashboard],
            ["brief", "Meeting Brief", Icons.brief],
            ["meetings", "Meetings", Icons.calendar],
            ["inspector", "Memory Inspector", Icons.inspector],
            ["learning", "Learning Curve", Icons.learning],
            ["comparison", "Before vs After", Icons.compare],
            ["timeline", "Timeline", Icons.timeline],
            ["chat", "Ask Agent", Icons.chat],
            ["customers", "Customer Directory", Icons.users],
          ] as [View, string, React.ReactNode][]
        ).map(([v, label, icon]) => (
          <button
            key={v}
            className={`sidebar-link ${view === v ? "active" : ""}`}
            onClick={() => {
              setView(v);
              if (v === "meetings") loadMeetingsPage();
              if (v === "comparison" && !comparison && selectedCustomer) generateComparison();
              if (v === "learning" && !learningCurve && selectedCustomer) loadLearningCurve();
              if (v === "inspector" && inspectorMemories.length === 0 && selectedCustomer) searchMemory();
            }}
            style={{
              border: "none",
              background: "none",
              textAlign: "left",
              cursor: "pointer",
              width: "100%",
              display: "flex",
              alignItems: "center",
              gap: 12,
            }}
          >
            {icon}
            <span style={{ fontSize: "0.88rem" }}>{label}</span>
            {v === "meetings" && upcomingMeetings.length > 0 && (
              <span
                style={{
                  marginLeft: "auto",
                  fontSize: "0.65rem",
                  padding: "2px 6px",
                  borderRadius: 6,
                  background: "var(--light-blue)",
                  color: "var(--primary-blue)",
                  border: "1px solid #BFDBFE",
                  fontWeight: 700,
                }}
              >
                {upcomingMeetings.length} NEXT
              </span>
            )}
            {v === "inspector" && (
              <span
                style={{
                  marginLeft: "auto",
                  fontSize: "0.65rem",
                  padding: "2px 6px",
                  borderRadius: 6,
                  background: "var(--very-light-blue)",
                  color: "var(--deep-blue)",
                  border: "1px solid var(--border-color)",
                  fontWeight: 700,
                }}
              >
                LIVE
              </span>
            )}
          </button>
        ))}

        {/* Customer Selector in Sidebar */}
        <div
          style={{
            marginTop: "auto",
            borderTop: "1px solid var(--border-color)",
            paddingTop: 16,
            background: "var(--very-light-blue)",
            borderRadius: "var(--radius-sm)",
            padding: 12,
            border: "1px solid var(--border-color)",
          }}
        >
          <label
            style={{
              fontSize: "0.68rem",
              color: "var(--text-muted)",
              fontWeight: 700,
              textTransform: "uppercase",
              letterSpacing: "0.06em",
              marginBottom: 6,
              display: "block",
            }}
          >
            Active Account Context
          </label>
          <select
            value={selectedCustomer}
            onChange={(e) => loadCustomerData(e.target.value)}
            style={{
              width: "100%",
              padding: "9px 12px",
              background: "var(--bg-card)",
              border: "1px solid var(--border-color)",
              borderRadius: "var(--radius-sm)",
              color: "var(--text-primary)",
              fontSize: "0.85rem",
              fontWeight: 600,
              outline: "none",
              cursor: "pointer",
            }}
          >
            {companies.map((c) => (
              <option key={c.customer_id} value={c.customer_id}>
                {c.company_name} ({c.customer_id})
              </option>
            ))}
          </select>
          {selectedContact && (
            <p style={{ fontSize: "0.72rem", color: "var(--text-secondary)", marginTop: 6 }}>
              👤 {selectedContact.name} ({selectedContact.role || "Lead"})
            </p>
          )}
        </div>

        {/* Live Engine & Hindsight Status */}
        <div
          style={{
            marginTop: 10,
            padding: "10px 12px",
            background: "var(--very-light-blue)",
            borderRadius: "var(--radius-sm)",
            border: "1px solid var(--border-color)",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginBottom: 8,
            }}
          >
            <span
              style={{
                fontSize: "0.66rem",
                fontWeight: 800,
                letterSpacing: "0.06em",
                textTransform: "uppercase",
                color: "var(--text-muted)",
              }}
            >
              ENGINE STATUS
            </span>
            <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
              <span
                style={{
                  width: 7,
                  height: 7,
                  borderRadius: "50%",
                  background: systemStatus?.hindsight.connected ? "#10B981" : "#F59E0B",
                  boxShadow: systemStatus?.hindsight.connected ? "0 0 6px #10B981" : "none",
                  display: "inline-block",
                }}
              />
              <span
                style={{
                  fontSize: "0.68rem",
                  fontWeight: 800,
                  color: systemStatus?.hindsight.connected ? "#065F46" : "#92400E",
                }}
              >
                {systemStatus?.hindsight.connected ? "LIVE CLOUD" : "LOCAL FALLBACK"}
              </span>
            </div>
          </div>

          <div
            style={{
              fontSize: "0.72rem",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: "3px 0",
              borderBottom: "1px dashed var(--border-color)",
            }}
          >
            <span style={{ color: "var(--text-secondary)" }}>● Hindsight Cloud</span>
            <span
              style={{
                fontWeight: 700,
                color: systemStatus?.hindsight.connected ? "#2563A8" : "#64748B",
              }}
            >
              {systemStatus?.hindsight.fact_count ?? 105} Cloud Facts
            </span>
          </div>

          <div
            style={{
              fontSize: "0.72rem",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: "3px 0",
              borderBottom: "1px dashed var(--border-color)",
            }}
          >
            <span style={{ color: "var(--text-secondary)" }}>● Groq LLM</span>
            <span style={{ fontWeight: 700, color: "var(--text-primary)" }}>
              {systemStatus?.llm.model ? systemStatus.llm.model.replace("qwen/", "") : "qwen3.8-27b"}
            </span>
          </div>

          <div
            style={{
              fontSize: "0.72rem",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: "3px 0",
              borderBottom: "1px dashed var(--border-color)",
            }}
          >
            <span style={{ color: "var(--text-secondary)" }}>● Relational Database</span>
            <span style={{ fontWeight: 700, color: "var(--text-primary)" }}>
              {systemStatus?.database.counts.memories ?? 311} Records
            </span>
          </div>

          <div
            style={{
              fontSize: "0.72rem",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: "3px 0",
            }}
          >
            <span style={{ color: "var(--text-secondary)" }}>🧠 Bank ID</span>
            <span style={{ fontWeight: 700, color: "var(--accent-emerald)" }}>
              {systemStatus?.hindsight.bank_id || "meeting-intelligence"}
            </span>
          </div>
        </div>
      </aside>

      {/* ── MAIN CONTENT AREA ──────────────────────────────── */}
      <main style={{ marginLeft: 270, flex: 1, padding: "32px 40px", maxWidth: 1400 }}>
        {error && (
          <div
            style={{
              padding: 16,
              background: "var(--danger-light)",
              border: "1px solid var(--danger-border)",
              borderRadius: "var(--radius-sm)",
              marginBottom: 24,
              color: "var(--danger)",
              display: "flex",
              alignItems: "center",
              gap: 10,
              fontSize: "0.9rem",
            }}
          >
            {Icons.alert}
            <span>{error}</span>
            <button
              onClick={() => setError(null)}
              style={{
                marginLeft: "auto",
                background: "none",
                border: "none",
                color: "var(--danger)",
                cursor: "pointer",
                fontSize: "1rem",
              }}
            >
              ✕
            </button>
          </div>
        )}

        {/* ═════════════════════════════════════════════════════ */}
        {/* VIEW: DASHBOARD                                       */}
        {/* ═════════════════════════════════════════════════════ */}
        {view === "dashboard" && (
          <div className="fade-in">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 28 }}>
              <div>
                <h2 className="page-header-title" style={{ fontSize: "1.9rem", fontWeight: 800, letterSpacing: "-0.03em" }}>
                  Sales Account Intelligence: <span className="gradient-text">{selectedCompany?.company_name}</span>
                </h2>
                <p className="page-header-subtitle" style={{ fontSize: "0.92rem", marginTop: 4 }}>
                  Persistent relational memory across 40 meetings, 80 emails, and longitudinal commitments.
                </p>
              </div>
              <button
                className="btn-primary"
                onClick={() => {
                  setView("brief");
                  generateBrief();
                }}
              >
                {Icons.brief} Generate Meeting Brief
              </button>
            </div>

            {/* Metrics Row */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 16, marginBottom: 28 }}>
              {[
                {
                  label: "Enterprise Accounts",
                  value: companies.length,
                  color: "var(--accent-indigo)",
                  sub: "Synthetic & Public ground truth",
                },
                {
                  label: "Key Stakeholders",
                  value: contacts.length,
                  color: "var(--accent-violet)",
                  sub: "Roles & Preferences mapped",
                },
                {
                  label: "Upcoming Meetings",
                  value: upcomingMeetings.length,
                  color: "var(--accent-emerald)",
                  sub: "Scheduled with Hindsight prep",
                  onClick: () => {
                    setView("meetings");
                    loadMeetingsPage();
                  },
                },
                {
                  label: "Open Commitments",
                  value: openCommitments.length,
                  color: openCommitments.length > 0 ? "var(--accent-rose)" : "var(--accent-emerald)",
                  sub: openCommitments.length > 0 ? "⚠️ Requires follow-up" : "All promises cleared",
                },
                {
                  label: "Timeline Interactions",
                  value: timelineEvents.length,
                  color: "var(--accent-cyan)",
                  sub: "Meetings, emails & decisions",
                },
              ].map((stat, i) => (
                <div
                  key={i}
                  className="glass-card"
                  style={{
                    padding: 20,
                    cursor: stat.onClick ? "pointer" : "default",
                    transition: "all 0.2s",
                  }}
                  onClick={stat.onClick}
                >
                  <p
                    style={{
                      fontSize: "0.72rem",
                      color: "var(--text-muted)",
                      fontWeight: 700,
                      textTransform: "uppercase",
                      letterSpacing: "0.06em",
                    }}
                  >
                    {stat.label}
                  </p>
                  <p style={{ fontSize: "2.1rem", fontWeight: 800, color: stat.color, marginTop: 4, lineHeight: 1.1 }}>
                    {stat.value}
                  </p>
                  <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: 6 }}>{stat.sub}</p>
                </div>
              ))}
            </div>

            {/* Spotlight Card */}
            {selectedCompany && (
              <div
                className="glass-card"
                style={{
                  padding: 28,
                  marginBottom: 28,
                  borderLeft: "4px solid var(--accent-indigo)",
                  background: "linear-gradient(135deg, #FFFFFF 0%, var(--very-light-blue) 100%)",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                      <h3 style={{ fontSize: "1.45rem", fontWeight: 800 }}>{selectedCompany.company_name}</h3>
                      <span className="badge badge-active">{selectedCompany.segment}</span>
                      <span className="badge badge-medium">{selectedCompany.industry}</span>
                    </div>
                    <p style={{ color: "var(--text-secondary)", fontSize: "0.86rem", marginTop: 4 }}>
                      Primary Location: {selectedCompany.country} • Account ID: {selectedCompany.customer_id}
                    </p>
                  </div>
                  <div style={{ display: "flex", gap: 10 }}>
                    <button
                      className="btn-secondary"
                      onClick={() => {
                        setView("learning");
                        loadLearningCurve();
                      }}
                      style={{ fontSize: "0.82rem", padding: "8px 16px" }}
                    >
                      {Icons.learning} Learning Curve
                    </button>
                    <button
                      className="btn-secondary"
                      onClick={() => {
                        setView("comparison");
                        generateComparison();
                      }}
                      style={{ fontSize: "0.82rem", padding: "8px 16px" }}
                    >
                      {Icons.compare} Before vs After
                    </button>
                  </div>
                </div>

                {/* Primary Contact Banner */}
                {selectedContact && (
                  <div
                    style={{
                      display: "flex",
                      gap: 24,
                      marginTop: 20,
                      paddingTop: 18,
                      borderTop: "1px solid var(--border-color)",
                    }}
                  >
                    <div style={{ flex: 1.2 }}>
                      <p style={{ fontSize: "0.7rem", color: "var(--text-muted)", fontWeight: 700, textTransform: "uppercase" }}>
                        Lead Stakeholder
                      </p>
                      <p style={{ fontWeight: 700, fontSize: "1.05rem", marginTop: 2 }}>{selectedContact.name}</p>
                      <p style={{ color: "var(--accent-violet)", fontSize: "0.84rem" }}>{selectedContact.role}</p>
                      <p style={{ color: "var(--text-muted)", fontSize: "0.78rem" }}>{selectedContact.email}</p>
                    </div>
                    <div style={{ flex: 1 }}>
                      <p style={{ fontSize: "0.7rem", color: "var(--text-muted)", fontWeight: 700, textTransform: "uppercase" }}>
                        Commitments Status
                      </p>
                      <p
                        style={{
                          fontWeight: 700,
                          fontSize: "1.05rem",
                          marginTop: 2,
                          color: openCommitments.length > 0 ? "var(--accent-rose)" : "var(--accent-emerald)",
                        }}
                      >
                        {openCommitments.length} Open / {commitments.length} Total
                      </p>
                      <p style={{ color: "var(--text-muted)", fontSize: "0.78rem" }}>
                        Never forget unfulfilled promises
                      </p>
                    </div>
                    <div style={{ flex: 1 }}>
                      <p style={{ fontSize: "0.7rem", color: "var(--text-muted)", fontWeight: 700, textTransform: "uppercase" }}>
                        Memory Footprint
                      </p>
                      <p style={{ fontWeight: 700, fontSize: "1.05rem", marginTop: 2, color: "var(--accent-cyan)" }}>
                        {timelineEvents.length} Events Ingested
                      </p>
                      <p style={{ color: "var(--text-muted)", fontSize: "0.78rem" }}>
                        Semantic graph in Hindsight
                      </p>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* ── PROMINENT UPCOMING MEETING SECTION (Step 5) ── */}
            {activeUpcomingMeeting && (
              <div
                className="glass-card"
                style={{
                  padding: 28,
                  marginBottom: 28,
                  borderLeft: "4px solid var(--accent-emerald)",
                  background: "#FFFFFF",
                  boxShadow: "0 4px 18px rgba(15, 39, 66, 0.06)",
                }}
              >
                {/* Header bar with badge & switcher */}
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    flexWrap: "wrap",
                    gap: 12,
                    marginBottom: 16,
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <span
                      style={{
                        padding: "5px 12px",
                        borderRadius: 100,
                        background: "var(--success-light)",
                        border: "1px solid var(--success-border)",
                        color: "var(--success)",
                        fontSize: "0.74rem",
                        fontWeight: 700,
                        letterSpacing: "0.05em",
                        textTransform: "uppercase",
                        display: "inline-flex",
                        alignItems: "center",
                        gap: 6,
                      }}
                    >
                      <span
                        style={{ width: 8, height: 8, borderRadius: "50%", background: "var(--success)" }}
                        className="pulse-glow"
                      />
                      Upcoming Meeting
                    </span>
                    <span style={{ color: "var(--text-primary)", fontWeight: 700, fontSize: "0.95rem" }}>
                      {formatMeetingTime(activeUpcomingMeeting.date, activeUpcomingMeeting.scheduled_at)}
                    </span>
                    {activeUpcomingMeeting.location && (
                      <span style={{ color: "var(--text-muted)", fontSize: "0.82rem" }}>
                        📍 {activeUpcomingMeeting.location}
                      </span>
                    )}
                  </div>

                  {/* Switch between upcoming meetings */}
                  {upcomingMeetings.length > 1 && (
                    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                      <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginRight: 4 }}>
                        Next sessions:
                      </span>
                      {upcomingMeetings.map((m, idx) => {
                        const comp = companies.find((c) => c.customer_id === m.customer_id);
                        const isCur = m.meeting_id === activeUpcomingMeeting.meeting_id;
                        return (
                          <button
                            key={`${m.meeting_id}-${idx}`}
                            onClick={() => loadDashboardPreviewForMeeting(m)}
                            style={{
                              padding: "4px 10px",
                              fontSize: "0.75rem",
                              borderRadius: "var(--radius-sm)",
                              border: isCur ? "1px solid var(--accent-emerald)" : "1px solid var(--border-color)",
                              background: isCur ? "var(--success-light)" : "#FFFFFF",
                              color: isCur ? "var(--success)" : "var(--text-secondary)",
                              cursor: "pointer",
                              fontWeight: isCur ? 700 : 500,
                            }}
                          >
                            {comp?.company_name.split(" ")[0] || m.meeting_id}
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>

                {/* Meeting Title & Customer Info */}
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "flex-start",
                    flexWrap: "wrap",
                    gap: 16,
                  }}
                >
                  <div>
                    <h3 style={{ fontSize: "1.45rem", fontWeight: 800, color: "var(--text-primary)" }}>
                      {activeUpcomingMeeting.title}
                    </h3>
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 12,
                        marginTop: 4,
                        flexWrap: "wrap",
                      }}
                    >
                      <span style={{ fontSize: "0.92rem", fontWeight: 600, color: "var(--accent-violet)" }}>
                        👤{" "}
                        {contacts.find((c) => c.customer_id === activeUpcomingMeeting.customer_id)?.name ||
                          activeUpcomingMeeting.participants?.[0] ||
                          "Key Stakeholder"}
                      </span>
                      <span style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
                        (
                        {contacts.find((c) => c.customer_id === activeUpcomingMeeting.customer_id)?.role ||
                          "Lead"}
                        )
                      </span>
                      <span style={{ color: "var(--text-muted)" }}>•</span>
                      <span style={{ fontSize: "0.92rem", fontWeight: 700, color: "var(--text-primary)" }}>
                        🏢{" "}
                        {companies.find((c) => c.customer_id === activeUpcomingMeeting.customer_id)
                          ?.company_name || activeUpcomingMeeting.customer_id}
                      </span>
                    </div>

                    {activeUpcomingMeeting.agenda && activeUpcomingMeeting.agenda.length > 0 && (
                      <div
                        style={{
                          display: "flex",
                          gap: 8,
                          marginTop: 10,
                          flexWrap: "wrap",
                          alignItems: "center",
                        }}
                      >
                        <span
                          style={{
                            fontSize: "0.72rem",
                            color: "var(--text-muted)",
                            textTransform: "uppercase",
                            fontWeight: 700,
                          }}
                        >
                          Agenda:
                        </span>
                        {activeUpcomingMeeting.agenda.map((ag, i) => (
                          <span
                            key={i}
                            style={{
                              fontSize: "0.75rem",
                              padding: "3px 8px",
                              borderRadius: 4,
                              background: "var(--light-blue)",
                              border: "1px solid #BFDBFE",
                              color: "var(--text-primary)",
                            }}
                          >
                            • {ag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div style={{ display: "flex", gap: 10, marginTop: 4 }}>
                    <button
                      className="btn-primary"
                      onClick={() =>
                        prepareUpcomingBrief(
                          activeUpcomingMeeting.customer_id,
                          activeUpcomingMeeting.contact_id
                        )
                      }
                      style={{ fontSize: "0.85rem", padding: "8px 18px" }}
                    >
                      {Icons.brief} Prepare Meeting Brief
                    </button>
                    <button
                      className="btn-secondary"
                      onClick={() =>
                        openMeetingDetail(activeUpcomingMeeting.meeting_id, activeUpcomingMeeting.date)
                      }
                      style={{ fontSize: "0.85rem", padding: "8px 18px" }}
                    >
                      {Icons.inspector} View Meeting Details
                    </button>
                  </div>
                </div>

                {/* ── MEMORY PREVIEW (Step 6) ── */}
                <div
                  style={{
                    marginTop: 20,
                    padding: "16px 20px",
                    borderRadius: "var(--radius-md)",
                    background: "var(--very-light-blue)",
                    border: "1px solid #BFDBFE",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      marginBottom: 12,
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span style={{ fontSize: "1rem" }}>🧠</span>
                      <span
                        style={{
                          fontSize: "0.78rem",
                          fontWeight: 800,
                          textTransform: "uppercase",
                          letterSpacing: "0.06em",
                          color: "var(--accent-indigo)",
                        }}
                      >
                        Hindsight Relational Memory Preview
                      </span>
                      <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>
                        — Retained across historical meetings, emails &amp; decisions
                      </span>
                    </div>
                    <span className="badge badge-active" style={{ fontSize: "0.68rem" }}>
                      HINDSIGHT ACTIVE
                    </span>
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14 }}>
                    {/* Last discussed */}
                    <div
                      style={{
                        padding: 12,
                        borderRadius: "var(--radius-sm)",
                        background: "#FFFFFF",
                        border: "1px solid var(--border-color)",
                      }}
                    >
                      <p
                        style={{
                          fontSize: "0.7rem",
                          color: "var(--text-muted)",
                          fontWeight: 700,
                          textTransform: "uppercase",
                        }}
                      >
                        🧠 Last Discussed
                      </p>
                      <p
                        style={{
                          fontSize: "0.82rem",
                          color: "var(--text-primary)",
                          marginTop: 4,
                          lineHeight: 1.4,
                        }}
                      >
                        {dashboardMemoryPreview?.last_discussed ||
                          "Reviewing previous discussions and requirements."}
                      </p>
                    </div>

                    {/* Open Commitment */}
                    <div
                      style={{
                        padding: 12,
                        borderRadius: "var(--radius-sm)",
                        background: "var(--danger-light)",
                        border: "1px solid var(--danger-border)",
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <p
                          style={{
                            fontSize: "0.7rem",
                            color: "var(--danger)",
                            fontWeight: 700,
                            textTransform: "uppercase",
                          }}
                        >
                          ⚠️ Open Commitment
                        </p>
                        {dashboardMemoryPreview?.open_commitment_source && (
                          <span style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>
                            {dashboardMemoryPreview.open_commitment_source}
                          </span>
                        )}
                      </div>
                      <p
                        style={{
                          fontSize: "0.82rem",
                          color: "var(--text-primary)",
                          marginTop: 4,
                          lineHeight: 1.4,
                          fontWeight: 600,
                        }}
                      >
                        {dashboardMemoryPreview?.open_commitment || "No unfulfilled promises pending."}
                      </p>
                    </div>

                    {/* Recurring Concern */}
                    <div
                      style={{
                        padding: 12,
                        borderRadius: "var(--radius-sm)",
                        background: "var(--warning-light)",
                        border: "1px solid var(--warning-border)",
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <p
                          style={{
                            fontSize: "0.7rem",
                            color: "var(--warning)",
                            fontWeight: 700,
                            textTransform: "uppercase",
                          }}
                        >
                          🔁 Recurring Concern
                        </p>
                        {dashboardMemoryPreview?.recurring_concern_sources &&
                          dashboardMemoryPreview.recurring_concern_sources.length > 0 && (
                            <span style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>
                              {dashboardMemoryPreview.recurring_concern_sources.length} sources
                            </span>
                          )}
                      </div>
                      <p
                        style={{
                          fontSize: "0.82rem",
                          color: "var(--text-primary)",
                          marginTop: 4,
                          lineHeight: 1.4,
                          fontWeight: 600,
                        }}
                      >
                        {dashboardMemoryPreview?.recurring_concern ||
                          "Timeline and integration security review."}
                      </p>
                    </div>
                  </div>

                  {/* Second row: Previous Decision, What Changed, Suggested Question */}
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "1fr 1fr 1.2fr",
                      gap: 14,
                      marginTop: 12,
                    }}
                  >
                    <div
                      style={{
                        padding: 12,
                        borderRadius: "var(--radius-sm)",
                        background: "var(--success-light)",
                        border: "1px solid var(--success-border)",
                      }}
                    >
                      <p
                        style={{
                          fontSize: "0.7rem",
                          color: "var(--success)",
                          fontWeight: 700,
                          textTransform: "uppercase",
                        }}
                      >
                        ✓ Previous Decision
                      </p>
                      <p
                        style={{
                          fontSize: "0.82rem",
                          color: "var(--text-primary)",
                          marginTop: 4,
                          lineHeight: 1.4,
                        }}
                      >
                        {dashboardMemoryPreview?.previous_decision ||
                          "Technical validation phase approved."}
                      </p>
                    </div>

                    <div
                      style={{
                        padding: 12,
                        borderRadius: "var(--radius-sm)",
                        background: "#F0F9FF",
                        border: "1px solid #BAE6FD",
                      }}
                    >
                      <p
                        style={{
                          fontSize: "0.7rem",
                          color: "var(--accent-cyan)",
                          fontWeight: 700,
                          textTransform: "uppercase",
                        }}
                      >
                        📈 What Changed
                      </p>
                      <p
                        style={{
                          fontSize: "0.82rem",
                          color: "var(--text-primary)",
                          marginTop: 4,
                          lineHeight: 1.4,
                        }}
                      >
                        {dashboardMemoryPreview?.what_changed ||
                          "Customer moved from evaluation to enterprise rollout requirements."}
                      </p>
                    </div>

                    <div
                      style={{
                        padding: 12,
                        borderRadius: "var(--radius-sm)",
                        background: "var(--light-blue)",
                        border: "1px solid #BFDBFE",
                      }}
                    >
                      <p
                        style={{
                          fontSize: "0.7rem",
                          color: "var(--accent-indigo)",
                          fontWeight: 700,
                          textTransform: "uppercase",
                        }}
                      >
                        💡 Suggested Preparation Question
                      </p>
                      <p
                        style={{
                          fontSize: "0.82rem",
                          color: "var(--text-primary)",
                          marginTop: 4,
                          lineHeight: 1.4,
                          fontStyle: "italic",
                        }}
                      >
                        &ldquo;
                        {dashboardMemoryPreview?.suggested_question ||
                          "Has your team finalized the deployment timeline since our last review?"}
                        &rdquo;
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Commitments & Promises Tracker */}
            <div className="glass-card" style={{ padding: 24, marginBottom: 28 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                <div>
                  <h3 style={{ fontSize: "1.15rem", fontWeight: 700 }}>
                    🤝 Commitments &amp; Promises Tracker
                  </h3>
                  <p style={{ color: "var(--text-secondary)", fontSize: "0.82rem" }}>
                    Feature 3: &quot;Never forget a promise&quot; — track commitments extracted across meetings &amp; emails
                  </p>
                </div>
                <span className="badge badge-open">
                  {openCommitments.length} UNRESOLVED
                </span>
              </div>

              {commitments.length > 0 ? (
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  {commitments.map((c) => {
                    const isOpen = c.status === "open";
                    return (
                      <div
                        key={c.commitment_id}
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          padding: "14px 18px",
                          background: isOpen ? "var(--danger-light)" : "var(--success-light)",
                          border: `1px solid ${isOpen ? "var(--danger-border)" : "var(--success-border)"}`,
                          borderRadius: "var(--radius-sm)",
                        }}
                      >
                        <div style={{ flex: 1 }}>
                          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                            <span style={{ fontWeight: 600, fontSize: "0.92rem" }}>{c.commitment}</span>
                            <span className={isOpen ? "badge badge-open" : "badge badge-completed"}>
                              {c.status.toUpperCase()}
                            </span>
                          </div>
                          <p style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: 4 }}>
                            Owner: <strong style={{ color: "var(--text-primary)" }}>{c.owner}</strong> • Due: {c.due_date || "Not set"} • Created: {c.date_created} • Ref: [{c.commitment_id}]
                          </p>
                        </div>
                        <button
                          onClick={() => toggleCommitmentStatus(c.commitment_id, c.status)}
                          className={isOpen ? "btn-secondary" : "btn-primary"}
                          style={{ fontSize: "0.75rem", padding: "6px 14px", marginLeft: 16 }}
                        >
                          {isOpen ? "✓ Mark Resolved" : "↩ Re-open"}
                        </button>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>No commitments logged for this account.</p>
              )}
            </div>

            {/* Quick Directory Table */}
            <div className="glass-card" style={{ padding: 24 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                <div>
                  <h3 style={{ fontSize: "1.15rem", fontWeight: 700 }}>Active Accounts</h3>
                  <p style={{ color: "var(--text-secondary)", fontSize: "0.82rem" }}>Select any account to inspect memory</p>
                </div>
                <button className="btn-secondary" onClick={() => setView("customers")} style={{ fontSize: "0.8rem", padding: "6px 14px" }}>
                  View All Directory →
                </button>
              </div>

              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                  <thead>
                    <tr>
                      {["Company", "Lead Contact", "Industry", "Segment", "Actions"].map((h) => (
                        <th
                          key={h}
                          style={{
                            textAlign: "left",
                            padding: "10px 14px",
                            borderBottom: "1px solid var(--border-color)",
                            fontSize: "0.72rem",
                            color: "var(--text-muted)",
                            fontWeight: 700,
                            textTransform: "uppercase",
                          }}
                        >
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {companies.map((c) => {
                      const contact = contacts.find((ct) => ct.customer_id === c.customer_id);
                      const isSelected = c.customer_id === selectedCustomer;
                      return (
                        <tr
                          key={c.customer_id}
                          style={{
                            cursor: "pointer",
                            background: isSelected ? "var(--light-blue)" : "transparent",
                          }}
                          onClick={() => loadCustomerData(c.customer_id)}
                        >
                          <td style={{ padding: "14px", borderBottom: "1px solid #F1F5F9", fontWeight: 700 }}>
                            {c.company_name} {isSelected && <span style={{ color: "var(--accent-indigo)", fontSize: "0.8rem" }}>★ Active</span>}
                          </td>
                          <td style={{ padding: "14px", borderBottom: "1px solid #F1F5F9", color: "var(--text-secondary)" }}>
                            {contact?.name || "—"} ({contact?.role || "Stakeholder"})
                          </td>
                          <td style={{ padding: "14px", borderBottom: "1px solid #F1F5F9", color: "var(--text-secondary)" }}>
                            {c.industry}
                          </td>
                          <td style={{ padding: "14px", borderBottom: "1px solid #F1F5F9" }}>
                            <span className="badge badge-active">{c.segment}</span>
                          </td>
                          <td style={{ padding: "14px", borderBottom: "1px solid #F1F5F9" }}>
                            <button
                              className="btn-primary"
                              style={{ padding: "5px 12px", fontSize: "0.72rem" }}
                              onClick={(e) => {
                                e.stopPropagation();
                                loadCustomerData(c.customer_id);
                                setView("brief");
                                generateBrief();
                              }}
                            >
                              Prep Brief
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ═════════════════════════════════════════════════════ */}
        {/* VIEW: MEETING BRIEF                                   */}
        {/* ═════════════════════════════════════════════════════ */}
        {view === "brief" && (
          <div className="fade-in">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
              <div>
                <h2 className="page-header-title" style={{ fontSize: "1.75rem", fontWeight: 800 }}>
                  📄 Meeting Preparation Brief
                </h2>
                <p className="page-header-subtitle" style={{ fontSize: "0.88rem" }}>
                  13-Step Memory Pipeline for {selectedCompany?.company_name} — {selectedContact?.name} ({selectedContact?.role})
                </p>
              </div>
              <div style={{ display: "flex", gap: 10 }}>
                {brief && (
                  <button className="btn-secondary" onClick={copyBriefText}>
                    {Icons.copy} {copied ? "Copied!" : "Copy Brief"}
                  </button>
                )}
                <button className="btn-primary" onClick={generateBrief} disabled={briefLoading}>
                  {briefLoading ? <span className="spinner" /> : Icons.brief}
                  {briefLoading ? "Generating Brief..." : "Regenerate Brief"}
                </button>
              </div>
            </div>

            {brief ? (
              <div className="glass-card fade-in" style={{ padding: 36 }}>
                {/* Brief Meta Header */}
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    paddingBottom: 20,
                    marginBottom: 24,
                    borderBottom: "1px solid var(--border-color)",
                  }}
                >
                  <div>
                    <p style={{ fontSize: "0.72rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 700 }}>
                      Executive Prepared Brief
                    </p>
                    <h3 style={{ fontSize: "1.3rem", fontWeight: 800, marginTop: 2 }}>
                      {brief.company_name} — {brief.contact_name}
                    </h3>
                  </div>
                  <div style={{ textAlign: "right", display: "flex", gap: 12 }}>
                    <div
                      style={{
                        padding: "8px 16px",
                        background: "var(--light-blue)",
                        border: "1px solid #BFDBFE",
                        borderRadius: "var(--radius-sm)",
                      }}
                    >
                      <p style={{ fontSize: "0.68rem", color: "var(--accent-indigo)", fontWeight: 700 }}>HINDSIGHT MEMORY</p>
                      <p style={{ fontSize: "1.1rem", fontWeight: 800, color: "var(--text-primary)" }}>
                        {brief.memories_used} Memories Recalled
                      </p>
                    </div>
                    <div
                      style={{
                        padding: "8px 16px",
                        background: "var(--success-light)",
                        border: "1px solid var(--success-border)",
                        borderRadius: "var(--radius-sm)",
                      }}
                    >
                      <p style={{ fontSize: "0.68rem", color: "var(--accent-emerald)", fontWeight: 700 }}>EVIDENCE CITATIONS</p>
                      <p style={{ fontSize: "1.1rem", fontWeight: 800, color: "var(--text-primary)" }}>
                        {brief.evidence.length} Primary Sources
                      </p>
                    </div>
                  </div>
                </div>

                {/* Executive Fast-Look Strip (First Viewport Summary) */}
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                    gap: 12,
                    marginBottom: 26,
                    padding: 18,
                    background: "linear-gradient(135deg, rgba(239, 246, 255, 0.7) 0%, rgba(248, 250, 252, 0.95) 100%)",
                    border: "1px solid #BFDBFE",
                    borderRadius: "var(--radius-sm)",
                    boxShadow: "0 2px 8px rgba(37, 99, 168, 0.04)",
                  }}
                >
                  <div style={{ padding: "6px 8px", borderRight: "1px solid var(--border-color)" }}>
                    <span style={{ fontSize: "0.65rem", fontWeight: 800, color: "var(--primary-blue)", textTransform: "uppercase", letterSpacing: "0.06em", display: "block" }}>
                      📅 NEXT MEETING
                    </span>
                    <p style={{ fontSize: "0.84rem", fontWeight: 700, marginTop: 4, color: "var(--text-primary)", lineHeight: 1.3 }}>
                      {activeUpcomingMeeting?.title || "Upcoming Account Meeting"}
                    </p>
                    <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
                      {activeUpcomingMeeting ? formatMeetingTime(activeUpcomingMeeting.date, activeUpcomingMeeting.scheduled_at) : "Scheduled Soon"}
                    </span>
                  </div>

                  <div style={{ padding: "6px 8px", borderRight: "1px solid var(--border-color)" }}>
                    <span style={{ fontSize: "0.65rem", fontWeight: 800, color: "var(--danger)", textTransform: "uppercase", letterSpacing: "0.06em", display: "block" }}>
                      ⚠️ TOP PRIORITY
                    </span>
                    <p style={{ fontSize: "0.84rem", fontWeight: 700, marginTop: 4, color: "var(--text-primary)", lineHeight: 1.3 }}>
                      SOC 2 Type II Sign-off
                    </p>
                    <span style={{ fontSize: "0.7rem", color: "var(--danger)", fontWeight: 600 }}>
                      Chief Deal Blocker (4x raised)
                    </span>
                  </div>

                  <div style={{ padding: "6px 8px", borderRight: "1px solid var(--border-color)" }}>
                    <span style={{ fontSize: "0.65rem", fontWeight: 800, color: "var(--accent-amber)", textTransform: "uppercase", letterSpacing: "0.06em", display: "block" }}>
                      ⚡ OPEN COMMITMENT
                    </span>
                    <p style={{ fontSize: "0.84rem", fontWeight: 700, marginTop: 4, color: "var(--text-primary)", lineHeight: 1.3 }}>
                      {commitments.find((c) => c.status === "open")?.commitment
                        ? commitments.find((c) => c.status === "open")!.commitment.slice(0, 36) + "..."
                        : "Deliver SOC 2 Audit Report"}
                    </p>
                    <span style={{ fontSize: "0.7rem", color: "var(--accent-amber)", fontWeight: 600 }}>
                      {commitments.find((c) => c.status === "open")?.commitment_id || "C001"} · OPEN
                    </span>
                  </div>

                  <div style={{ padding: "6px 8px", borderRight: "1px solid var(--border-color)" }}>
                    <span style={{ fontSize: "0.65rem", fontWeight: 800, color: "var(--accent-indigo)", textTransform: "uppercase", letterSpacing: "0.06em", display: "block" }}>
                      🔄 RECENT CHANGE
                    </span>
                    <p style={{ fontSize: "0.84rem", fontWeight: 700, marginTop: 4, color: "var(--text-primary)", lineHeight: 1.3 }}>
                      Evaluation Paused for Compliance
                    </p>
                    <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
                      Decision D002 Connected
                    </span>
                  </div>

                  <div style={{ padding: "6px 8px" }}>
                    <span style={{ fontSize: "0.65rem", fontWeight: 800, color: "var(--accent-emerald)", textTransform: "uppercase", letterSpacing: "0.06em", display: "block" }}>
                      🎯 PREFERENCE
                    </span>
                    <p style={{ fontSize: "0.84rem", fontWeight: 700, marginTop: 4, color: "var(--text-primary)", lineHeight: 1.3 }}>
                      Direct &amp; Technical Detail
                    </p>
                    <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
                      {brief.contact_name} · Lead with proof
                    </span>
                  </div>
                </div>

                {/* Formatted Content */}
                <div
                  className="brief-content"
                  style={{ lineHeight: 1.7 }}
                  dangerouslySetInnerHTML={{ __html: formatMarkdown(brief.brief) }}
                />

                {/* Why This Matters Interactive Deep-Dives */}
                <div style={{ marginTop: 24 }}>
                  <p style={{ fontSize: "0.75rem", fontWeight: 800, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8 }}>
                    Interactive Memory Deep-Dives:
                  </p>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                    {renderWhyThisMatters("soc2", "SOC 2 Compliance Blocker")}
                    {renderWhyThisMatters("pricing", "Commercial Pricing & Terms")}
                    {renderWhyThisMatters("api", "Salesforce API Integration")}
                  </div>
                </div>

                {/* Polished Memory Evidence Card */}
                {renderMemoryEvidenceCard(brief.evidence, brief.memories_used, "Meeting Brief Evidence Trail")}
              </div>
            ) : briefLoading ? (
              <div className="glass-card" style={{ padding: 60, textAlign: "center" }}>
                <div className="spinner" style={{ margin: "0 auto 20px", width: 36, height: 36 }} />
                <h3 style={{ fontSize: "1.2rem", fontWeight: 700 }}>Synthesizing Meeting Brief via Hindsight...</h3>
                <p style={{ color: "var(--text-secondary)", marginTop: 8, fontSize: "0.9rem" }}>
                  Querying semantic memory bank for {selectedCompany?.company_name}...
                </p>
                <div style={{ display: "flex", justifyContent: "center", gap: 16, marginTop: 20, color: "var(--text-muted)", fontSize: "0.8rem" }}>
                  <span>✓ Loading meetings &amp; emails</span>
                  <span>✓ Identifying recurring concerns</span>
                  <span>✓ Checking open promises</span>
                </div>
              </div>
            ) : (
              <div className="glass-card" style={{ padding: 60, textAlign: "center" }}>
                <span style={{ fontSize: "3rem" }}>📄</span>
                <h3 style={{ fontSize: "1.25rem", fontWeight: 700, marginTop: 12 }}>
                  Generate an Evidence-Grounded Brief
                </h3>
                <p style={{ color: "var(--text-secondary)", maxWidth: 520, margin: "8px auto 24px", fontSize: "0.9rem" }}>
                  Our agent analyzes past meetings, extracted commitments, recurring objections, and contact preferences to prepare you in seconds.
                </p>
                <button className="btn-primary" onClick={generateBrief}>
                  {Icons.brief} Generate Brief for {selectedCompany?.company_name}
                </button>
              </div>
            )}
          </div>
        )}

        {/* ═════════════════════════════════════════════════════ */}
        {/* VIEW: MEETINGS (Steps 2 & 3)                           */}
        {/* ═════════════════════════════════════════════════════ */}
        {view === "meetings" && (
          <div className="fade-in">
            {/* Header */}
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "flex-start",
                marginBottom: 24,
                flexWrap: "wrap",
                gap: 16,
              }}
            >
              <div>
                <h2 className="page-header-title" style={{ fontSize: "1.75rem", fontWeight: 800 }}>
                  📅 Meetings &amp; Longitudinal Relationship Intelligence
                </h2>
                <p className="page-header-subtitle" style={{ fontSize: "0.88rem", marginTop: 4 }}>
                  Persistent meeting intelligence across {upcomingMeetings.length} upcoming scheduled sessions
                  and {pastMeetings.length} historical meetings.
                </p>
              </div>

              {/* Account Filter & Refresh */}
              <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                <select
                  value={meetingsFilterCustomer}
                  onChange={(e) => setMeetingsFilterCustomer(e.target.value)}
                  style={{
                    padding: "8px 14px",
                    background: "var(--bg-card)",
                    border: "1px solid var(--border-color)",
                    borderRadius: "var(--radius-sm)",
                    color: "var(--text-primary)",
                    fontSize: "0.85rem",
                    cursor: "pointer",
                  }}
                >
                  <option value="all">All Accounts ({companies.length})</option>
                  {companies.map((c) => (
                    <option key={c.customer_id} value={c.customer_id}>
                      {c.company_name} ({c.customer_id})
                    </option>
                  ))}
                </select>

                <button
                  className="btn-secondary"
                  onClick={loadMeetingsPage}
                  disabled={meetingsLoading}
                  style={{ fontSize: "0.85rem", padding: "8px 16px" }}
                >
                  {meetingsLoading ? <span className="spinner" /> : "↻ Refresh"}
                </button>
              </div>
            </div>

            {/* Status Tabs */}
            <div
              style={{
                display: "flex",
                gap: 10,
                marginBottom: 24,
                borderBottom: "1px solid var(--border-color)",
                paddingBottom: 12,
              }}
            >
              {[
                {
                  id: "upcoming",
                  label: `Upcoming Meetings (${filteredUpcomingMeetings.length})`,
                  count: filteredUpcomingMeetings.length,
                },
                {
                  id: "past",
                  label: `Meeting History (${filteredPastMeetings.length})`,
                  count: filteredPastMeetings.length,
                },
                {
                  id: "all",
                  label: `All Meetings (${filteredUpcomingMeetings.length + filteredPastMeetings.length})`,
                  count: filteredUpcomingMeetings.length + filteredPastMeetings.length,
                },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setMeetingsTab(tab.id as any)}
                  style={{
                    padding: "8px 18px",
                    borderRadius: "var(--radius-sm)",
                    border: "none",
                    background: meetingsTab === tab.id ? "var(--light-blue)" : "transparent",
                    color: meetingsTab === tab.id ? "var(--primary-blue)" : "var(--text-secondary)",
                    fontWeight: meetingsTab === tab.id ? 700 : 500,
                    fontSize: "0.88rem",
                    cursor: "pointer",
                    transition: "all 0.2s",
                    borderBottom: meetingsTab === tab.id ? "2px solid var(--primary-blue)" : "none",
                  }}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* ── UPCOMING MEETINGS SECTION ── */}
            {(meetingsTab === "upcoming" || meetingsTab === "all") && (
              <div style={{ marginBottom: 36 }}>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                    marginBottom: 16,
                  }}
                >
                  <h3 style={{ fontSize: "1.2rem", fontWeight: 700 }}>
                    ⚡ Scheduled Upcoming Sessions ({filteredUpcomingMeetings.length})
                  </h3>
                  <span
                    style={{
                      fontSize: "0.72rem",
                      color: "var(--accent-emerald)",
                      background: "var(--success-light)",
                      padding: "2px 8px",
                      borderRadius: 10,
                      fontWeight: 700,
                    }}
                  >
                    READY FOR HINDSIGHT PREP
                  </span>
                </div>

                {filteredUpcomingMeetings.length > 0 ? (
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "repeat(auto-fill, minmax(540px, 1fr))",
                      gap: 20,
                    }}
                  >
                    {filteredUpcomingMeetings.map((m, idx) => {
                      const comp = companies.find((c) => c.customer_id === m.customer_id);
                      const cont = contacts.find(
                        (ct) => ct.contact_id === m.contact_id || ct.customer_id === m.customer_id
                      );
                      return (
                        <div
                          key={`${m.meeting_id}-${idx}`}
                          className="glass-card"
                          style={{
                            padding: 24,
                            borderLeft: "4px solid var(--accent-emerald)",
                            display: "flex",
                            flexDirection: "column",
                            justifyContent: "space-between",
                          }}
                        >
                          <div>
                            {/* Card Top: Timing & Location */}
                            <div
                              style={{
                                display: "flex",
                                justifyContent: "space-between",
                                alignItems: "center",
                                marginBottom: 12,
                              }}
                            >
                              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                <span
                                  style={{
                                    fontSize: "0.72rem",
                                    padding: "3px 8px",
                                    borderRadius: 100,
                                    background: "var(--success-light)",
                                    color: "var(--success)",
                                    fontWeight: 700,
                                    textTransform: "uppercase",
                                  }}
                                >
                                  Upcoming
                                </span>
                                <span
                                  style={{
                                    fontSize: "0.88rem",
                                    fontWeight: 700,
                                    color: "var(--text-primary)",
                                  }}
                                >
                                  {formatMeetingTime(m.date, m.scheduled_at)}
                                </span>
                              </div>
                              {m.location && (
                                <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                                  📍 {m.location}
                                </span>
                              )}
                            </div>

                            {/* Meeting Title */}
                            <h4
                              style={{
                                fontSize: "1.2rem",
                                fontWeight: 800,
                                color: "var(--text-primary)",
                                marginBottom: 8,
                              }}
                            >
                              {m.title}
                            </h4>

                            {/* Stakeholder & Company */}
                            <div
                              style={{
                                display: "flex",
                                alignItems: "center",
                                gap: 10,
                                flexWrap: "wrap",
                                marginBottom: 12,
                              }}
                            >
                              <span
                                style={{
                                  fontSize: "0.85rem",
                                  fontWeight: 600,
                                  color: "var(--accent-violet)",
                                }}
                              >
                                👤 {cont?.name || m.participants?.[0] || "Key Stakeholder"}
                              </span>
                              <span style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
                                ({cont?.role || "Lead"})
                              </span>
                              <span style={{ color: "var(--text-muted)" }}>•</span>
                              <span
                                style={{
                                  fontSize: "0.85rem",
                                  fontWeight: 700,
                                  color: "var(--text-primary)",
                                }}
                              >
                                🏢 {comp?.company_name || m.customer_id}
                              </span>
                            </div>

                            {/* Participants */}
                            {m.participants && m.participants.length > 0 && (
                              <p
                                style={{
                                  fontSize: "0.75rem",
                                  color: "var(--text-muted)",
                                  marginBottom: 10,
                                }}
                              >
                                👥 Participants: {m.participants.join(", ")}
                              </p>
                            )}

                            {/* Agenda Items */}
                            {m.agenda && m.agenda.length > 0 && (
                              <div
                                style={{
                                  display: "flex",
                                  gap: 6,
                                  flexWrap: "wrap",
                                  marginBottom: 16,
                                }}
                              >
                                {m.agenda.map((ag, i) => (
                                  <span
                                    key={i}
                                    style={{
                                      fontSize: "0.72rem",
                                      padding: "2px 8px",
                                      borderRadius: 4,
                                      background: "var(--light-blue)",
                                      border: "1px solid #BFDBFE",
                                      color: "var(--text-secondary)",
                                    }}
                                  >
                                    • {ag}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>

                          {/* Action Buttons */}
                          <div
                            style={{
                              display: "flex",
                              gap: 10,
                              paddingTop: 16,
                              borderTop: "1px solid var(--border-color)",
                              marginTop: 8,
                            }}
                          >
                            <button
                              className="btn-primary"
                              onClick={() => prepareUpcomingBrief(m.customer_id, m.contact_id)}
                              style={{ fontSize: "0.82rem", padding: "8px 16px", flex: 1 }}
                            >
                              {Icons.brief} Prepare Meeting Brief
                            </button>
                            <button
                              className="btn-secondary"
                              onClick={() => openMeetingDetail(m.meeting_id, m.date)}
                              style={{ fontSize: "0.82rem", padding: "8px 16px" }}
                            >
                              {Icons.inspector} View Meeting
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="glass-card" style={{ padding: 32, textAlign: "center" }}>
                    <p style={{ color: "var(--text-muted)", fontSize: "0.88rem" }}>
                      No upcoming meetings scheduled for this account filter.
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* ── PAST MEETINGS / MEETING HISTORY SECTION ── */}
            {(meetingsTab === "past" || meetingsTab === "all") && (
              <div>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: 16,
                    flexWrap: "wrap",
                    gap: 12,
                  }}
                >
                  <h3 style={{ fontSize: "1.2rem", fontWeight: 700 }}>
                    📜 Completed Meeting History &amp; Longitudinal Record ({filteredPastMeetings.length})
                  </h3>

                  {/* Search box */}
                  <input
                    type="text"
                    placeholder="Search past meetings by title, participant, summary..."
                    value={meetingsSearch}
                    onChange={(e) => setMeetingsSearch(e.target.value)}
                    style={{
                      padding: "8px 14px",
                      background: "var(--bg-card)",
                      border: "1px solid var(--border-color)",
                      borderRadius: "var(--radius-sm)",
                      color: "var(--text-primary)",
                      fontSize: "0.85rem",
                      width: 320,
                      outline: "none",
                    }}
                  />
                </div>

                <div className="glass-card" style={{ padding: 20 }}>
                  <div style={{ overflowX: "auto" }}>
                    <table style={{ width: "100%", borderCollapse: "collapse" }}>
                      <thead>
                        <tr>
                          {["Date", "Meeting Title", "Company", "Stakeholder", "Status", "Summary Snippet", "Actions"].map(
                            (h) => (
                              <th
                                key={h}
                                style={{
                                  textAlign: "left",
                                  padding: "10px 14px",
                                  borderBottom: "1px solid var(--border-color)",
                                  fontSize: "0.72rem",
                                  color: "var(--text-muted)",
                                  fontWeight: 700,
                                  textTransform: "uppercase",
                                }}
                              >
                                {h}
                              </th>
                            )
                          )}
                        </tr>
                      </thead>
                      <tbody>
                        {filteredPastMeetings.slice(0, 35).map((m, idx) => {
                          const comp = companies.find((c) => c.customer_id === m.customer_id);
                          const cont = contacts.find(
                            (ct) => ct.contact_id === m.contact_id || ct.customer_id === m.customer_id
                          );
                          return (
                            <tr
                              key={`${m.meeting_id}-${m.date}-${idx}`}
                              onClick={() => openMeetingDetail(m.meeting_id, m.date)}
                              style={{
                                cursor: "pointer",
                                transition: "background 0.2s",
                                borderBottom: "1px solid #F1F5F9",
                              }}
                              className="meeting-row-hover"
                            >
                              <td
                                style={{
                                  padding: "14px",
                                  fontSize: "0.82rem",
                                  color: "var(--text-secondary)",
                                  whiteSpace: "nowrap",
                                }}
                              >
                                {m.date}
                              </td>
                              <td
                                style={{
                                  padding: "14px",
                                  fontWeight: 700,
                                  fontSize: "0.9rem",
                                  color: "var(--text-primary)",
                                }}
                              >
                                {m.title}
                              </td>
                              <td
                                style={{
                                  padding: "14px",
                                  fontSize: "0.85rem",
                                  color: "var(--text-secondary)",
                                }}
                              >
                                {comp?.company_name || m.customer_id}
                              </td>
                              <td
                                style={{
                                  padding: "14px",
                                  fontSize: "0.82rem",
                                  color: "var(--accent-violet)",
                                }}
                              >
                                {cont?.name || m.participants?.[0] || "Stakeholder"}
                              </td>
                              <td style={{ padding: "14px" }}>
                                <span className="badge badge-completed" style={{ fontSize: "0.68rem" }}>
                                  COMPLETED
                                </span>
                              </td>
                              <td
                                style={{
                                  padding: "14px",
                                  fontSize: "0.8rem",
                                  color: "var(--text-muted)",
                                  maxWidth: 320,
                                  overflow: "hidden",
                                  textOverflow: "ellipsis",
                                  whiteSpace: "nowrap",
                                }}
                              >
                                {m.summary || "Transcript & interaction recorded."}
                              </td>
                              <td style={{ padding: "14px" }}>
                                <button
                                  className="btn-secondary"
                                  style={{ padding: "4px 10px", fontSize: "0.75rem" }}
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    openMeetingDetail(m.meeting_id, m.date);
                                  }}
                                >
                                  View →
                                </button>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                  {filteredPastMeetings.length > 35 && (
                    <p
                      style={{
                        textAlign: "center",
                        fontSize: "0.78rem",
                        color: "var(--text-muted)",
                        marginTop: 16,
                      }}
                    >
                      Showing first 35 of {filteredPastMeetings.length} historical meetings. Use search to refine.
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ═════════════════════════════════════════════════════ */}
        {/* VIEW: MEETING DETAIL (Step 7)                          */}
        {/* ═════════════════════════════════════════════════════ */}
        {view === "meetingDetail" && (
          <div className="fade-in">
            {meetingDetailLoading && (
              <div style={{ textAlign: "center", padding: 60 }}>
                <div className="spinner" style={{ margin: "0 auto 16px" }} />
                <p style={{ color: "var(--text-secondary)" }}>
                  Loading meeting details &amp; Hindsight memory...
                </p>
              </div>
            )}

            {!meetingDetailLoading && selectedMeeting && (
              <div>
                {/* Page Header */}
                <div style={{ marginBottom: 20 }}>
                  <h2 className="page-header-title" style={{ fontSize: "1.75rem", fontWeight: 800 }}>
                    📅 Meeting Intelligence &amp; Record Details
                  </h2>
                  <p className="page-header-subtitle" style={{ fontSize: "0.88rem", marginTop: 4 }}>
                    Longitudinal interaction audit, commitments, and Hindsight memory grounding for {selectedCompany?.company_name}.
                  </p>
                </div>

                {/* Navigation Bar */}
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: 24,
                  }}
                >
                  <div style={{ display: "flex", gap: 10 }}>
                    <button
                      className="btn-secondary"
                      onClick={() => setView("meetings")}
                      style={{ fontSize: "0.85rem" }}
                    >
                      ← Back to Meetings
                    </button>
                    <button
                      className="btn-secondary"
                      onClick={() => setView("dashboard")}
                      style={{ fontSize: "0.85rem" }}
                    >
                      ← Dashboard
                    </button>
                  </div>

                  <button
                    className="btn-primary"
                    onClick={() =>
                      prepareUpcomingBrief(selectedMeeting.customer_id, selectedMeeting.contact_id)
                    }
                  >
                    {Icons.brief} Prepare Meeting Brief
                  </button>
                </div>

                {/* Meeting Header Banner */}
                <div
                  className="glass-card"
                  style={{
                    padding: 28,
                    marginBottom: 24,
                    borderLeft: `4px solid ${
                      selectedMeeting.status === "upcoming"
                        ? "var(--accent-emerald)"
                        : "var(--accent-indigo)"
                    }`,
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "flex-start",
                      flexWrap: "wrap",
                      gap: 16,
                    }}
                  >
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                        <h2 style={{ fontSize: "1.75rem", fontWeight: 800 }}>
                          {selectedMeeting.title}
                        </h2>
                        <span
                          className={
                            selectedMeeting.status === "upcoming"
                              ? "badge badge-active"
                              : "badge badge-completed"
                          }
                        >
                          {selectedMeeting.status?.toUpperCase() || "COMPLETED"}
                        </span>
                      </div>
                      <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", marginTop: 6 }}>
                        📅 {formatMeetingTime(selectedMeeting.date, selectedMeeting.scheduled_at)}
                        {selectedMeeting.location && ` • 📍 ${selectedMeeting.location}`}
                        {` • Ref: [${selectedMeeting.meeting_id}]`}
                      </p>
                    </div>

                    <div style={{ textAlign: "right" }}>
                      <p style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--text-primary)" }}>
                        🏢 {selectedMeeting.company_name}
                      </p>
                      <p style={{ fontSize: "0.88rem", color: "var(--accent-violet)", marginTop: 2 }}>
                        👤 {selectedMeeting.contact_name} (
                        {selectedMeeting.contact_role || "Stakeholder"})
                      </p>
                    </div>
                  </div>

                  {/* Participants & Agenda */}
                  <div
                    style={{
                      display: "flex",
                      gap: 24,
                      marginTop: 20,
                      paddingTop: 18,
                      borderTop: "1px solid var(--border-color)",
                      flexWrap: "wrap",
                    }}
                  >
                    <div style={{ flex: 1, minWidth: 200 }}>
                      <p
                        style={{
                          fontSize: "0.7rem",
                          color: "var(--text-muted)",
                          fontWeight: 700,
                          textTransform: "uppercase",
                        }}
                      >
                        Participants
                      </p>
                      <p style={{ fontSize: "0.88rem", color: "var(--text-primary)", marginTop: 4 }}>
                        {selectedMeeting.participants && selectedMeeting.participants.length > 0
                          ? selectedMeeting.participants.join(", ")
                          : selectedMeeting.contact_name || "Primary Stakeholder"}
                      </p>
                    </div>

                    {selectedMeeting.agenda && selectedMeeting.agenda.length > 0 && (
                      <div style={{ flex: 2, minWidth: 280 }}>
                        <p
                          style={{
                            fontSize: "0.7rem",
                            color: "var(--text-muted)",
                            fontWeight: 700,
                            textTransform: "uppercase",
                          }}
                        >
                          Agenda
                        </p>
                        <div style={{ display: "flex", gap: 8, marginTop: 4, flexWrap: "wrap" }}>
                          {selectedMeeting.agenda.map((ag, i) => (
                            <span
                              key={i}
                              style={{
                                fontSize: "0.78rem",
                                padding: "3px 10px",
                                borderRadius: 6,
                                background: "var(--light-blue)",
                                border: "1px solid #BFDBFE",
                              }}
                            >
                              • {ag}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Hindsight Memory Preview (for upcoming or rich context) */}
                {selectedMeeting.status === "upcoming" && (
                  <div
                    className="glass-card"
                    style={{
                      padding: 24,
                      marginBottom: 24,
                      border: "1px solid #BFDBFE",
                      background: "linear-gradient(135deg, #FFFFFF 0%, var(--very-light-blue) 100%)",
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        marginBottom: 16,
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <span style={{ fontSize: "1.2rem" }}>🧠</span>
                        <div>
                          <h3
                            style={{
                              fontSize: "1.05rem",
                              fontWeight: 700,
                              color: "var(--text-primary)",
                            }}
                          >
                            Hindsight-Powered Memory Preview
                          </h3>
                          <p style={{ fontSize: "0.78rem", color: "var(--text-secondary)" }}>
                            Historical context recalled from earlier meetings, emails, and commitments with{" "}
                            {selectedMeeting.company_name}
                          </p>
                        </div>
                      </div>
                      <span className="badge badge-active">HINDSIGHT RECALL</span>
                    </div>

                    {memoryPreviewLoading ? (
                      <div style={{ textAlign: "center", padding: 20 }}>
                        <div className="spinner" style={{ margin: "0 auto 8px" }} />
                        <p style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                          Recalling relational memory graph...
                        </p>
                      </div>
                    ) : (
                      <div
                        style={{
                          display: "grid",
                          gridTemplateColumns: "repeat(3, 1fr)",
                          gap: 14,
                        }}
                      >
                        <div
                          style={{
                            padding: 14,
                            borderRadius: "var(--radius-sm)",
                            background: "#FFFFFF",
                            border: "1px solid var(--border-color)",
                          }}
                        >
                          <p
                            style={{
                              fontSize: "0.7rem",
                              color: "var(--text-muted)",
                              fontWeight: 700,
                              textTransform: "uppercase",
                            }}
                          >
                            🧠 Last Discussed
                          </p>
                          <p
                            style={{
                              fontSize: "0.84rem",
                              color: "var(--text-primary)",
                              marginTop: 6,
                              lineHeight: 1.4,
                            }}
                          >
                            {meetingMemoryPreview?.last_discussed ||
                              "Previous discussions focused on architecture and requirements."}
                          </p>
                        </div>

                        <div
                          style={{
                            padding: 14,
                            borderRadius: "var(--radius-sm)",
                            background: "var(--danger-light)",
                            border: "1px solid var(--danger-border)",
                          }}
                        >
                          <p
                            style={{
                              fontSize: "0.7rem",
                              color: "var(--danger)",
                              fontWeight: 700,
                              textTransform: "uppercase",
                            }}
                          >
                            ⚠️ Open Commitment
                          </p>
                          <p
                            style={{
                              fontSize: "0.84rem",
                              color: "var(--text-primary)",
                              marginTop: 6,
                              lineHeight: 1.4,
                              fontWeight: 600,
                            }}
                          >
                            {meetingMemoryPreview?.open_commitment || "No open commitments pending."}
                          </p>
                          {meetingMemoryPreview?.open_commitment_source && (
                            <p style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginTop: 4 }}>
                              Source: {meetingMemoryPreview.open_commitment_source}
                            </p>
                          )}
                        </div>

                        <div
                          style={{
                            padding: 14,
                            borderRadius: "var(--radius-sm)",
                            background: "var(--warning-light)",
                            border: "1px solid var(--warning-border)",
                          }}
                        >
                          <p
                            style={{
                              fontSize: "0.7rem",
                              color: "var(--warning)",
                              fontWeight: 700,
                              textTransform: "uppercase",
                            }}
                          >
                            🔁 Recurring Concern
                          </p>
                          <p
                            style={{
                              fontSize: "0.84rem",
                              color: "var(--text-primary)",
                              marginTop: 6,
                              lineHeight: 1.4,
                              fontWeight: 600,
                            }}
                          >
                            {meetingMemoryPreview?.recurring_concern || "Timeline and integration security."}
                          </p>
                          {meetingMemoryPreview?.recurring_concern_sources &&
                            meetingMemoryPreview.recurring_concern_sources.length > 0 && (
                              <p
                                style={{
                                  fontSize: "0.7rem",
                                  color: "var(--text-muted)",
                                  marginTop: 4,
                                }}
                              >
                                Sources: {meetingMemoryPreview.recurring_concern_sources.join(", ")}
                              </p>
                            )}
                        </div>

                        <div
                          style={{
                            padding: 14,
                            borderRadius: "var(--radius-sm)",
                            background: "var(--success-light)",
                            border: "1px solid var(--success-border)",
                          }}
                        >
                          <p
                            style={{
                              fontSize: "0.7rem",
                              color: "var(--success)",
                              fontWeight: 700,
                              textTransform: "uppercase",
                            }}
                          >
                            ✓ Previous Decision
                          </p>
                          <p
                            style={{
                              fontSize: "0.84rem",
                              color: "var(--text-primary)",
                              marginTop: 6,
                              lineHeight: 1.4,
                            }}
                          >
                            {meetingMemoryPreview?.previous_decision || "Technical validation approved."}
                          </p>
                        </div>

                        <div
                          style={{
                            padding: 14,
                            borderRadius: "var(--radius-sm)",
                            background: "#F0F9FF",
                            border: "1px solid #BAE6FD",
                          }}
                        >
                          <p
                            style={{
                              fontSize: "0.7rem",
                              color: "var(--accent-cyan)",
                              fontWeight: 700,
                              textTransform: "uppercase",
                            }}
                          >
                            📈 What Changed
                          </p>
                          <p
                            style={{
                              fontSize: "0.84rem",
                              color: "var(--text-primary)",
                              marginTop: 6,
                              lineHeight: 1.4,
                            }}
                          >
                            {meetingMemoryPreview?.what_changed ||
                              "Customer transitioned to deployment review."}
                          </p>
                        </div>

                        <div
                          style={{
                            padding: 14,
                            borderRadius: "var(--radius-sm)",
                            background: "var(--light-blue)",
                            border: "1px solid #BFDBFE",
                          }}
                        >
                          <p
                            style={{
                              fontSize: "0.7rem",
                              color: "var(--accent-indigo)",
                              fontWeight: 700,
                              textTransform: "uppercase",
                            }}
                          >
                            💡 Suggested Question
                          </p>
                          <p
                            style={{
                              fontSize: "0.84rem",
                              color: "var(--text-primary)",
                              marginTop: 6,
                              lineHeight: 1.4,
                              fontStyle: "italic",
                            }}
                          >
                            &ldquo;
                            {meetingMemoryPreview?.suggested_question ||
                              "Has your implementation timeline changed since our last discussion?"}
                            &rdquo;
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Two-Column Details Grid */}
                <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 24 }}>
                  {/* Left Column: Summary & Decisions */}
                  <div>
                    {/* Summary / Discussion */}
                    <div className="glass-card" style={{ padding: 24, marginBottom: 24 }}>
                      <h3 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: 12 }}>
                        📝 Discussion &amp; Summary
                      </h3>
                      <p style={{ color: "var(--text-secondary)", fontSize: "0.92rem", lineHeight: 1.6 }}>
                        {selectedMeeting.summary || "No transcript summary recorded."}
                      </p>
                    </div>

                    {/* Transcript if available */}
                    {selectedMeeting.transcript && (
                      <div className="glass-card" style={{ padding: 24, marginBottom: 24 }}>
                        <h3 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: 12 }}>
                          🎙️ Conversation Transcript Excerpt
                        </h3>
                        <div
                          style={{
                            padding: 16,
                            borderRadius: "var(--radius-sm)",
                            background: "var(--very-light-blue)",
                            border: "1px solid var(--border-color)",
                            maxHeight: 260,
                            overflowY: "auto",
                            fontSize: "0.82rem",
                            fontFamily: "monospace",
                            lineHeight: 1.6,
                            color: "var(--text-secondary)",
                          }}
                        >
                          {selectedMeeting.transcript}
                        </div>
                      </div>
                    )}

                    {/* Decisions */}
                    <div className="glass-card" style={{ padding: 24, marginBottom: 24 }}>
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          marginBottom: 14,
                        }}
                      >
                        <h3 style={{ fontSize: "1.1rem", fontWeight: 700 }}>
                          ✓ Decisions Logged ({selectedMeeting.decisions.length})
                        </h3>
                        <span className="badge badge-completed">EXTRACTED</span>
                      </div>
                      {selectedMeeting.decisions.length > 0 ? (
                        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                          {selectedMeeting.decisions.map((d) => (
                            <div
                              key={d.decision_id}
                              style={{
                                padding: "10px 14px",
                                borderRadius: "var(--radius-sm)",
                                background: "var(--success-light)",
                                border: "1px solid var(--success-border)",
                                display: "flex",
                                justifyContent: "space-between",
                                alignItems: "center",
                              }}
                            >
                              <span style={{ fontSize: "0.88rem", fontWeight: 600 }}>{d.decision}</span>
                              <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>
                                {d.date}
                              </span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                          No decisions recorded for this account.
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Right Column: Commitments, Concerns, Memory Footprint, Related Meetings */}
                  <div>
                    {/* Commitments */}
                    <div className="glass-card" style={{ padding: 24, marginBottom: 24 }}>
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          marginBottom: 14,
                        }}
                      >
                        <h3 style={{ fontSize: "1.1rem", fontWeight: 700 }}>
                          🤝 Commitments ({selectedMeeting.commitments.length})
                        </h3>
                        <span className="badge badge-open">
                          {selectedMeeting.commitments.filter((c) => c.status === "open").length} OPEN
                        </span>
                      </div>
                      {selectedMeeting.commitments.length > 0 ? (
                        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                          {selectedMeeting.commitments.map((c) => {
                            const isOpen = c.status === "open";
                            return (
                              <div
                                key={c.commitment_id}
                                style={{
                                  padding: "10px 14px",
                                  borderRadius: "var(--radius-sm)",
                                  background: isOpen
                                    ? "rgba(244, 63, 94, 0.05)"
                                    : "rgba(16, 185, 129, 0.05)",
                                  border: `1px solid ${
                                    isOpen ? "var(--danger-border)" : "var(--success-border)"
                                  }`,
                                }}
                              >
                                <div
                                  style={{
                                    display: "flex",
                                    justifyContent: "space-between",
                                    alignItems: "center",
                                  }}
                                >
                                  <span style={{ fontSize: "0.86rem", fontWeight: 600 }}>
                                    {c.commitment}
                                  </span>
                                  <span
                                    className={isOpen ? "badge badge-open" : "badge badge-completed"}
                                    style={{ fontSize: "0.65rem" }}
                                  >
                                    {c.status}
                                  </span>
                                </div>
                                <div
                                  style={{
                                    display: "flex",
                                    justifyContent: "space-between",
                                    alignItems: "center",
                                    marginTop: 6,
                                  }}
                                >
                                  <p style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>
                                    Owner: {c.owner} • Due: {c.due_date || "N/A"}
                                  </p>
                                  <button
                                    onClick={() => toggleCommitmentStatus(c.commitment_id, c.status)}
                                    className={isOpen ? "btn-secondary" : "btn-primary"}
                                    style={{ fontSize: "0.7rem", padding: "3px 8px" }}
                                  >
                                    {isOpen ? "✓ Mark Done" : "↩ Re-open"}
                                  </button>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      ) : (
                        <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                          No commitments recorded for this account.
                        </p>
                      )}
                    </div>

                    {/* Concerns */}
                    <div className="glass-card" style={{ padding: 24, marginBottom: 24 }}>
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          marginBottom: 14,
                        }}
                      >
                        <h3 style={{ fontSize: "1.1rem", fontWeight: 700 }}>
                          ⚠️ Identified Concerns ({selectedMeeting.concerns.length})
                        </h3>
                      </div>
                      {selectedMeeting.concerns.length > 0 ? (
                        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                          {selectedMeeting.concerns.map((cn) => (
                            <div
                              key={cn.concern_id}
                              style={{
                                padding: "10px 14px",
                                borderRadius: "var(--radius-sm)",
                                background: "var(--warning-light)",
                                border: "1px solid var(--warning-border)",
                                display: "flex",
                                justifyContent: "space-between",
                                alignItems: "center",
                              }}
                            >
                              <span style={{ fontSize: "0.86rem", fontWeight: 500 }}>
                                {cn.concern}
                              </span>
                              <span
                                className={
                                  cn.severity === "high"
                                    ? "badge badge-high"
                                    : cn.severity === "medium"
                                    ? "badge badge-medium"
                                    : "badge badge-low"
                                }
                                style={{ fontSize: "0.65rem" }}
                              >
                                {cn.severity}
                              </span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                          No concerns recorded.
                        </p>
                      )}
                    </div>

                    {/* Hindsight Memory Footprint */}
                    <div
                      className="glass-card"
                      style={{
                        padding: 20,
                        marginBottom: 24,
                        borderLeft: "3px solid var(--accent-indigo)",
                      }}
                    >
                      <p
                        style={{
                          fontSize: "0.7rem",
                          color: "var(--text-muted)",
                          fontWeight: 700,
                          textTransform: "uppercase",
                        }}
                      >
                        🧠 Relational Memory Footprint
                      </p>
                      <p
                        style={{
                          fontSize: "1.2rem",
                          fontWeight: 800,
                          color: "var(--accent-indigo)",
                          marginTop: 4,
                        }}
                      >
                        {selectedMeeting.memory_count} Events Retained
                      </p>
                      <p
                        style={{
                          fontSize: "0.78rem",
                          color: "var(--text-secondary)",
                          marginTop: 4,
                        }}
                      >
                        Stored in persistent semantic graph for {selectedMeeting.company_name}.
                      </p>
                      <button
                        className="btn-secondary"
                        onClick={() => {
                          setSelectedCustomer(selectedMeeting.customer_id);
                          setView("inspector");
                          searchMemory();
                        }}
                        style={{
                          marginTop: 12,
                          fontSize: "0.78rem",
                          padding: "6px 14px",
                          width: "100%",
                          justifyContent: "center",
                        }}
                      >
                        🔍 Open Memory Inspector →
                      </button>
                    </div>

                    {/* Related Meetings */}
                    {selectedMeeting.related_meetings.length > 0 && (
                      <div className="glass-card" style={{ padding: 24 }}>
                        <h3 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: 12 }}>
                          🔄 Related Account Meetings ({selectedMeeting.related_meetings.length})
                        </h3>
                        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                          {selectedMeeting.related_meetings.map((rm, idx) => (
                            <div
                              key={`${rm.meeting_id}-${idx}`}
                              onClick={() => openMeetingDetail(rm.meeting_id, rm.date)}
                              style={{
                                padding: "10px 14px",
                                borderRadius: "var(--radius-sm)",
                                background: "#FFFFFF",
                                border: "1px solid var(--border-color)",
                                display: "flex",
                                justifyContent: "space-between",
                                alignItems: "center",
                                cursor: "pointer",
                                transition: "all 0.2s",
                              }}
                            >
                              <div>
                                <p
                                  style={{
                                    fontSize: "0.85rem",
                                    fontWeight: 600,
                                    color: "var(--text-primary)",
                                  }}
                                >
                                  {rm.title}
                                </p>
                                <p style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>
                                  {rm.date}
                                </p>
                              </div>
                              <span
                                style={{
                                  fontSize: "0.75rem",
                                  color: "var(--accent-indigo)",
                                }}
                              >
                                View →
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ═════════════════════════════════════════════════════ */}
        {/* VIEW: MEMORY INSPECTOR                                */}
        {/* ═════════════════════════════════════════════════════ */}
        {view === "inspector" && (
          <div className="fade-in">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 24 }}>
              <div>
                <h2 className="page-header-title" style={{ fontSize: "1.75rem", fontWeight: 800 }}>
                  🔍 Hindsight Memory Inspector
                </h2>
                <p className="page-header-subtitle" style={{ fontSize: "0.88rem" }}>
                  Feature 8: Inspect what the agent remembers, why it believes it, and query the Hindsight semantic bank.
                </p>
              </div>
              <span className="badge badge-active" style={{ fontSize: "0.8rem", padding: "6px 14px" }}>
                Bank ID: meeting-intelligence
              </span>
            </div>

            {/* Semantic Query Search Bar */}
            <div className="glass-card" style={{ padding: 20, marginBottom: 24 }}>
              <div style={{ display: "flex", gap: 10 }}>
                <input
                  value={inspectorQuery}
                  onChange={(e) => setInspectorQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && searchMemory()}
                  placeholder="Semantic query in Hindsight memory (e.g., 'security compliance', 'pricing pushback', 'API requirements')..."
                  style={{
                    flex: 1,
                    padding: "12px 16px",
                    background: "var(--bg-card)",
                    border: "1px solid var(--border-color)",
                    borderRadius: "var(--radius-sm)",
                    color: "var(--text-primary)",
                    fontSize: "0.9rem",
                    outline: "none",
                  }}
                />
                <button className="btn-primary" onClick={() => searchMemory()} disabled={inspectorLoading}>
                  {inspectorLoading ? <span className="spinner" /> : Icons.inspector}
                  {inspectorLoading ? "Searching..." : "Semantic Recall"}
                </button>
              </div>

              {/* Category Filter Pills */}
              <div style={{ display: "flex", gap: 8, marginTop: 16, alignItems: "center", flexWrap: "wrap" }}>
                <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", fontWeight: 700, textTransform: "uppercase" }}>
                  Category:
                </span>
                {[
                  ["all", "All Memories"],
                  ["meeting", "Meetings"],
                  ["email", "Emails"],
                  ["commitment", "Commitments"],
                  ["concern", "Concerns"],
                  ["decision", "Decisions"],
                  ["preference", "Preferences"],
                ].map(([val, label]) => (
                  <button
                    key={val}
                    onClick={() => setInspectorFilter(val)}
                    style={{
                      background: inspectorFilter === val ? "var(--primary-blue)" : "#FFFFFF",
                      color: inspectorFilter === val ? "#fff" : "var(--text-secondary)",
                      border: "1px solid var(--border-color)",
                      padding: "4px 12px",
                      borderRadius: 100,
                      fontSize: "0.75rem",
                      cursor: "pointer",
                      fontWeight: 600,
                    }}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {/* Results Grid */}
            <div style={{ display: "grid", gridTemplateColumns: inspectedMemory ? "1fr 400px" : "1fr", gap: 20 }}>
              <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                {filteredInspectorMemories.length > 0 ? (
                  filteredInspectorMemories.map((mem, idx) => (
                    <div
                      key={idx}
                      className="glass-card"
                      style={{
                        padding: 18,
                        cursor: "pointer",
                        borderLeft: `4px solid ${
                          mem.event_type === "concern"
                            ? "var(--accent-rose)"
                            : mem.event_type === "commitment"
                            ? "var(--accent-amber)"
                            : "var(--accent-indigo)"
                        }`,
                      }}
                      onClick={() => setInspectedMemory(mem)}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                          <span
                            className={
                              mem.event_type === "concern"
                                ? "badge badge-high"
                                : mem.event_type === "commitment"
                                ? "badge badge-open"
                                : "badge badge-active"
                            }
                          >
                            {mem.event_type || mem.category || "Memory"}
                          </span>
                          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{mem.event_date}</span>
                        </div>
                        {mem.relevance_score && (
                          <span style={{ fontSize: "0.75rem", color: "var(--accent-cyan)", fontWeight: 700 }}>
                            {(mem.relevance_score * 100).toFixed(0)}% Match
                          </span>
                        )}
                      </div>
                      <p style={{ fontSize: "0.88rem", lineHeight: 1.5, color: "var(--text-primary)" }}>
                        {mem.content}
                      </p>
                      <div style={{ marginTop: 8, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
                          Source: {mem.source || "hindsight"} • Account: {mem.customer_id}
                        </span>
                        <span style={{ fontSize: "0.75rem", color: "var(--accent-indigo)", fontWeight: 600 }}>
                          Explain Grounding →
                        </span>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="glass-card" style={{ padding: 48, textAlign: "center" }}>
                    <p style={{ color: "var(--text-muted)" }}>No memories found matching the query. Try a different term or click below.</p>
                    <button
                      className="btn-secondary"
                      onClick={() => searchMemory("security compliance SOC 2")}
                      style={{ marginTop: 12, fontSize: "0.8rem" }}
                    >
                      Search &quot;security compliance SOC 2&quot;
                    </button>
                  </div>
                )}
              </div>

              {/* &quot;Why does the agent believe this?&quot; Grounding Drawer */}
              {inspectedMemory && (
                <div
                  className="glass-card fade-in"
                  style={{
                    padding: 24,
                    alignSelf: "flex-start",
                    position: "sticky",
                    top: 24,
                    border: "1px solid var(--accent-indigo)",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                    <h4 style={{ fontSize: "1rem", fontWeight: 700, color: "var(--accent-indigo)" }}>
                      🧠 Why does the agent believe this?
                    </h4>
                    <button
                      onClick={() => setInspectedMemory(null)}
                      style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer" }}
                    >
                      ✕
                    </button>
                  </div>

                  <div style={{ display: "flex", flexDirection: "column", gap: 12, fontSize: "0.84rem" }}>
                    <div>
                      <p style={{ fontSize: "0.68rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 700 }}>
                        Memory Fact
                      </p>
                      <p style={{ marginTop: 4, color: "var(--text-primary)" }}>{inspectedMemory.content}</p>
                    </div>

                    <div>
                      <p style={{ fontSize: "0.68rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 700 }}>
                        Grounding Evidence &amp; Event
                      </p>
                      <p style={{ marginTop: 4, color: "var(--text-secondary)" }}>
                        Recorded from <strong>{inspectedMemory.source}</strong> on <strong>{inspectedMemory.event_date}</strong>.
                      </p>
                    </div>

                    <div>
                      <p style={{ fontSize: "0.68rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 700 }}>
                        Relational Context
                      </p>
                      <p style={{ marginTop: 4, color: "var(--text-secondary)" }}>
                        Mapped to Customer ID: <strong>{inspectedMemory.customer_id}</strong>
                        {inspectedMemory.contact_id && <> • Stakeholder ID: <strong>{inspectedMemory.contact_id}</strong></>}
                      </p>
                    </div>

                    <div>
                      <p style={{ fontSize: "0.68rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 700 }}>
                        Semantic Relevance Score
                      </p>
                      <p style={{ marginTop: 4, color: "var(--accent-cyan)", fontWeight: 700 }}>
                        {inspectedMemory.relevance_score ? `${(inspectedMemory.relevance_score * 100).toFixed(1)}% semantic match` : "Direct relational lookup"}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ═════════════════════════════════════════════════════ */}
        {/* VIEW: LEARNING CURVE DEMO                             */}
        {/* ═════════════════════════════════════════════════════ */}
        {/* ═════════════════════════════════════════════════════ */}
        {/* VIEW: AGENT LEARNING CURVE DEMO                       */}
        {/* ═════════════════════════════════════════════════════ */}
        {view === "learning" && (
          <div className="fade-in">
            {/* Header */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 }}>
              <div>
                <h2 className="page-header-title" style={{ fontSize: "1.75rem", fontWeight: 800 }}>
                  📈 Agent Learning Curve: Memory ➔ Learning ➔ Behavior Change
                </h2>
                <p className="page-header-subtitle" style={{ fontSize: "0.88rem", marginTop: 4 }}>
                  Demonstrating how persistent relational memory in Hindsight transforms cold discovery into strategic executive advisory over time.
                </p>
              </div>
              <button className="btn-primary" onClick={loadLearningCurve} disabled={learningLoading}>
                {learningLoading ? <span className="spinner" /> : Icons.learning}
                {learningLoading ? "Calculating Curve..." : "Refresh Learning Curve"}
              </button>
            </div>

            {/* High-Level Causal Chain & Progression Ribbon */}
            <div
              className="glass-card"
              style={{
                padding: "16px 22px",
                marginBottom: 24,
                background: "linear-gradient(135deg, #EAF3FB 0%, #F5F9FD 100%)",
                border: "1px solid #BFDBFE",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 14 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <span style={{ fontSize: "0.72rem", fontWeight: 800, letterSpacing: "0.08em", color: "var(--accent-indigo)", textTransform: "uppercase" }}>
                    CORE CAUSAL STORY
                  </span>
                  <span style={{ fontSize: "0.84rem", color: "var(--text-primary)", fontWeight: 500 }}>
                    Interactions ➔ Memory ➔ Learning ➔ Relationship Understanding ➔ Behavior Change ➔ Better Next Meeting
                  </span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 12, fontSize: "0.78rem" }}>
                  <span style={{ color: "var(--text-muted)", fontWeight: 600 }}>Accumulated Relationship Knowledge:</span>
                  <span style={{ color: "var(--accent-rose)", fontWeight: 700 }}>
                    {learningCurve?.stages[0]?.memories_available ?? 0} memories (Cold)
                  </span>
                  <span style={{ color: "var(--text-muted)" }}>➔</span>
                  <span style={{ color: "var(--accent-amber)", fontWeight: 700 }}>
                    {learningCurve?.stages[1]?.memories_available ?? 8} memories (Emerging)
                  </span>
                  <span style={{ color: "var(--text-muted)" }}>➔</span>
                  <span style={{ color: "var(--accent-emerald)", fontWeight: 700 }}>
                    {learningCurve?.stages[2]?.memories_available ?? 43} memories (Strategic Advisory)
                  </span>
                </div>
              </div>
            </div>

            {learningCurve ? (
              <div>
                {/* 3 Stages Stepper Selector */}
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16, marginBottom: 24 }}>
                  {learningCurve.stages.map((stage) => {
                    const isSelected = selectedStage === stage.stage_number;
                    return (
                      <div
                        key={stage.stage_number}
                        className="glass-card"
                        style={{
                          padding: 20,
                          cursor: "pointer",
                          border: isSelected ? "2px solid var(--accent-indigo)" : "1px solid var(--border-color)",
                          background: isSelected ? "var(--light-blue)" : "var(--bg-card)",
                          boxShadow: isSelected ? "0 4px 18px rgba(37, 99, 168, 0.15)" : "none",
                          transition: "all 0.2s ease",
                        }}
                        onClick={() => setSelectedStage(stage.stage_number)}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <span className="badge badge-active" style={{ fontSize: "0.7rem", fontWeight: 700 }}>
                            STAGE {stage.stage_number}
                          </span>
                          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                            {stage.interaction_count === 1 ? "1 Interaction" : `${stage.interaction_count} Interactions`}
                          </span>
                        </div>
                        <h4 style={{ fontSize: "1.05rem", fontWeight: 700, marginTop: 10 }}>{stage.title}</h4>
                        <p style={{ fontSize: "0.8rem", color: "var(--accent-violet)", marginTop: 2, fontWeight: 600 }}>
                          {stage.relationship_depth}
                        </p>
                        <div style={{ marginTop: 12, display: "flex", gap: 12, fontSize: "0.74rem", color: "var(--text-muted)" }}>
                          <span>🧠 <strong>{stage.memories_available}</strong> accumulated memories</span>
                          <span>🤝 <strong>{stage.commitments_tracked}</strong> promises</span>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Selected Stage Detail */}
                {(() => {
                  const currentStage =
                    learningCurve.stages.find((s) => s.stage_number === selectedStage) || learningCurve.stages[2];
                  return (
                    <div className="glass-card fade-in" style={{ padding: 30, marginBottom: 28 }}>
                      {/* Stage Header */}
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          paddingBottom: 18,
                          marginBottom: 20,
                          borderBottom: "1px solid var(--border-color)",
                        }}
                      >
                        <div>
                          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
                            <span className="badge badge-active">STAGE {currentStage.stage_number} OF 3</span>
                            <span style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>
                              ({currentStage.interaction_count === 1 ? "1 Interaction" : `${currentStage.interaction_count} Interactions Completed`})
                            </span>
                          </div>
                          <h3 style={{ fontSize: "1.45rem", fontWeight: 800 }}>{currentStage.title}</h3>
                          <p style={{ color: "var(--text-secondary)", fontSize: "0.86rem", marginTop: 2 }}>
                            Relationship Depth: <strong style={{ color: "var(--accent-violet)" }}>{currentStage.relationship_depth}</strong>
                          </p>
                        </div>
                        <div style={{ textAlign: "right" }}>
                          <p style={{ fontSize: "0.72rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 700 }}>
                            Risk Profile
                          </p>
                          <p style={{ fontWeight: 700, fontSize: "0.95rem", color: currentStage.stage_number === 1 ? "var(--accent-rose)" : currentStage.stage_number === 2 ? "var(--accent-amber)" : "var(--accent-emerald)" }}>
                            {currentStage.risk_level}
                          </p>
                        </div>
                      </div>

                      {/* SECTION 1: THE SAME QUESTION TEST ACROSS ALL 3 STAGES */}
                      <div
                        style={{
                          marginBottom: 24,
                          padding: 18,
                          background: "var(--light-blue)",
                          border: "1px solid #BFDBFE",
                          borderRadius: "var(--radius-sm)",
                        }}
                      >
                        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
                          <span style={{ fontSize: "0.7rem", fontWeight: 800, letterSpacing: "0.08em", color: "var(--accent-indigo)", textTransform: "uppercase" }}>
                            IDENTICAL USER QUESTION AT ALL 3 STAGES
                          </span>
                          <span style={{ fontSize: "0.88rem", fontWeight: 700, color: "var(--dark-navy)" }}>
                            &quot;{currentStage.same_question || `Prepare me for my meeting with ${learningCurve.contact_name.split(" ")[0]}.`}&quot;
                          </span>
                        </div>

                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1.2fr", gap: 16 }}>
                          {/* What Agent Knows */}
                          <div
                            style={{
                              background: "#FFFFFF",
                              padding: 14,
                              borderRadius: "var(--radius-sm)",
                              border: "1px solid var(--border-color)",
                            }}
                          >
                            <p style={{ fontSize: "0.72rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 700, marginBottom: 8 }}>
                              {currentStage.stage_number === 1 ? "📋 What the Agent Knows:" : "🧠 What the Agent Now Remembers:"}
                            </p>
                            <ul style={{ paddingLeft: 18, margin: 0, fontSize: "0.82rem", color: "var(--text-secondary)", lineHeight: 1.6 }}>
                              {(currentStage.agent_knows && currentStage.agent_knows.length > 0
                                ? currentStage.agent_knows
                                : currentStage.key_signals
                              ).map((item, idx) => (
                                <li key={idx} style={{ marginBottom: 4 }}>
                                  {item}
                                </li>
                              ))}
                            </ul>
                          </div>

                          {/* Agent Understanding Response */}
                          <div
                            style={{
                              background: "#FFFFFF",
                              padding: 14,
                              borderRadius: "var(--radius-sm)",
                              border: "1px solid var(--border-color)",
                            }}
                          >
                            <p style={{ fontSize: "0.72rem", color: "var(--accent-indigo)", textTransform: "uppercase", fontWeight: 700, marginBottom: 8 }}>
                              🤖 Agent Response at Stage {currentStage.stage_number}:
                            </p>
                            <p style={{ fontSize: "0.84rem", color: "var(--text-primary)", lineHeight: 1.6, margin: 0 }}>
                              {currentStage.agent_response ||
                                (currentStage.stage_number === 1
                                  ? "Prepare for an initial discovery conversation. Present standard platform capabilities and high-level architectural overview."
                                  : currentStage.stage_number === 2
                                  ? "Focus on the technical API architecture validation and benchmark results. Follow up on the outstanding technical specifications."
                                  : "Lead the meeting immediately with the promised SOC 2 documentation (Commitment C001 — OPEN) to rebuild credibility. Address the recurring security concern.")}
                            </p>
                          </div>
                        </div>
                      </div>

                      {/* SECTION 2: WHAT THE AGENT LEARNED */}
                      <div style={{ marginBottom: 24 }}>
                        <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontWeight: 700, textTransform: "uppercase", marginBottom: 8 }}>
                          {currentStage.stage_number === 1 ? "💡 What Was Learned at Initial Discovery:" : "✨ What the Agent Learned in This Transition:"}
                        </p>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                          {(currentStage.what_learned && currentStage.what_learned.length > 0
                            ? currentStage.what_learned
                            : currentStage.key_signals
                          ).map((item, idx) => (
                            <span
                              key={idx}
                              style={{
                                padding: "6px 14px",
                                background: currentStage.stage_number === 3 ? "var(--light-blue)" : "#FFFFFF",
                                border: currentStage.stage_number === 3 ? "1px solid #BFDBFE" : "1px solid var(--border-color)",
                                borderRadius: 100,
                                fontSize: "0.78rem",
                                fontWeight: 500,
                                color: currentStage.stage_number === 3 ? "var(--primary-blue)" : "var(--text-primary)",
                              }}
                            >
                              {currentStage.stage_number === 1 ? "•" : "+"} {item}
                            </span>
                          ))}
                        </div>
                      </div>

                      {/* SECTION 3: KEY SIGNALS ACTIVE */}
                      <div style={{ marginBottom: 24 }}>
                        <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontWeight: 700, textTransform: "uppercase", marginBottom: 8 }}>
                          Active Intelligence Signals:
                        </p>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                          {currentStage.key_signals.map((sig, i) => (
                            <span
                              key={i}
                              style={{
                                padding: "5px 12px",
                                background: "var(--very-light-blue)",
                                border: "1px solid var(--border-color)",
                                borderRadius: 100,
                                fontSize: "0.75rem",
                                fontWeight: 500,
                                color: "var(--text-secondary)",
                              }}
                            >
                              ✓ {sig}
                            </span>
                          ))}
                        </div>
                      </div>

                      {/* SECTION 4: GENERATED BRIEF SNIPPET */}
                      <div
                        style={{
                          padding: 22,
                          background: "var(--very-light-blue)",
                          borderRadius: "var(--radius-sm)",
                          border: "1px solid var(--border-color)",
                        }}
                      >
                        <p style={{ fontSize: "0.72rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 700, marginBottom: 12 }}>
                          Generated Meeting Brief Snippet for Stage {currentStage.stage_number}
                        </p>
                        <div
                          className="brief-content"
                          dangerouslySetInnerHTML={{ __html: formatMarkdown(currentStage.brief_snippet) }}
                        />
                      </div>
                    </div>
                  );
                })()}

                {/* SECTION 5: "MEMORY THAT CHANGED THE NEXT MEETING" */}
                <div
                  className="glass-card"
                  style={{
                    padding: 28,
                    marginBottom: 28,
                    border: "1px solid #BFDBFE",
                    background: "linear-gradient(135deg, #FFFFFF 0%, var(--very-light-blue) 100%)",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
                    <span style={{ fontSize: "1.2rem" }}>⚡</span>
                    <h3 style={{ fontSize: "1.25rem", fontWeight: 800 }}>
                      MEMORY THAT CHANGED THE NEXT MEETING
                    </h3>
                  </div>
                  <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginBottom: 20 }}>
                    How persistent pattern detection across 4 previous interactions directly altered the upcoming meeting agenda.
                  </p>

                  <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14 }}>
                    {/* Step 1: Past Interaction */}
                    <div
                      style={{
                        padding: 16,
                        background: "#FFFFFF",
                        border: "1px solid var(--border-color)",
                        borderRadius: "var(--radius-sm)",
                      }}
                    >
                      <span className="badge badge-active" style={{ fontSize: "0.68rem", marginBottom: 8 }}>
                        1. PAST INTERACTIONS
                      </span>
                      <p style={{ fontSize: "0.82rem", color: "var(--text-primary)", lineHeight: 1.5, marginTop: 6 }}>
                        Sarah repeatedly raised <strong>SOC 2 Type II compliance</strong> across 4 interactions (M001, M003, E005, M004).
                      </p>
                      <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
                        Sources: M001, M003, E005, M004
                      </span>
                    </div>

                    {/* Step 2: Hindsight Pattern Detection */}
                    <div
                      style={{
                        padding: 16,
                        background: "var(--light-blue)",
                        border: "1px solid #BFDBFE",
                        borderRadius: "var(--radius-sm)",
                      }}
                    >
                      <span className="badge badge-active" style={{ fontSize: "0.68rem", marginBottom: 8, background: "var(--light-blue)" }}>
                        2. PATTERN DETECTED
                      </span>
                      <p style={{ fontSize: "0.82rem", color: "var(--text-primary)", lineHeight: 1.5, marginTop: 6 }}>
                        Hindsight flagged security compliance as the <strong>chief deal blocker</strong> + Commitment <strong>C001</strong> remains unfulfilled (OPEN).
                      </p>
                      <span style={{ fontSize: "0.7rem", color: "var(--accent-indigo)" }}>
                        Graph Relationship Linked
                      </span>
                    </div>

                    {/* Step 3: Learned Insight */}
                    <div
                      style={{
                        padding: 16,
                        background: "#FFFFFF",
                        border: "1px solid var(--border-color)",
                        borderRadius: "var(--radius-sm)",
                      }}
                    >
                      <span className="badge badge-active" style={{ fontSize: "0.68rem", marginBottom: 8 }}>
                        3. LEARNED INSIGHT
                      </span>
                      <p style={{ fontSize: "0.82rem", color: "var(--text-primary)", lineHeight: 1.5, marginTop: 6 }}>
                        Account evaluation pivoted from raw API speed to <strong>governance clearance</strong>. Commercial review is paused until compliance sign-off.
                      </p>
                      <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
                        Decision D002 Connected
                      </span>
                    </div>

                    {/* Step 4: Changed Next Meeting */}
                    <div
                      style={{
                        padding: 16,
                        background: "var(--success-light)",
                        border: "1px solid var(--success-border)",
                        borderRadius: "var(--radius-sm)",
                      }}
                    >
                      <span className="badge badge-active" style={{ fontSize: "0.68rem", marginBottom: 8, background: "var(--success-light)", color: "var(--success)" }}>
                        4. CHANGED PREPARATION
                      </span>
                      <ul style={{ paddingLeft: 16, margin: "6px 0 0 0", fontSize: "0.78rem", color: "var(--text-primary)", lineHeight: 1.5 }}>
                        <li>Deliver SOC 2 package in <strong>first 2 minutes</strong>.</li>
                        <li>Address security proactively before objections rise.</li>
                        <li>Advance directly to commercial procurement review.</li>
                      </ul>
                    </div>
                  </div>
                </div>

                {/* SECTION 6: EVIDENCE & CITATION COUNTS */}
                <div style={{ marginBottom: 28 }}>
                  <p style={{ fontSize: "0.78rem", color: "var(--text-muted)", fontWeight: 700, textTransform: "uppercase", marginBottom: 12 }}>
                    Evidence &amp; Citation Synthesized by Hindsight:
                  </p>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14 }}>
                    {(learningCurve.evidence_counts && learningCurve.evidence_counts.length > 0
                      ? learningCurve.evidence_counts
                      : [
                          { topic: "SOC 2 & Security Compliance", count: 4, sources: ["M001", "M003", "E005", "M004"] },
                          { topic: "API Latency & Throughput", count: 3, sources: ["M001", "M002", "D001"] },
                          { topic: "Unresolved Commitments", count: 1, sources: ["C001 (Send SOC 2 Type II)"] },
                          { topic: "Formal Decisions Logged", count: 2, sources: ["D001 Approved", "D002 Deferred"] },
                        ]
                    ).map((ec, idx) => (
                      <div
                        key={idx}
                        className="glass-card"
                        style={{
                          padding: 16,
                          background: "var(--bg-card)",
                          border: "1px solid var(--border-color)",
                        }}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <span style={{ fontSize: "0.8rem", fontWeight: 700 }}>{ec.topic}</span>
                          <span className="badge badge-active" style={{ fontSize: "0.7rem", fontWeight: 800 }}>
                            {ec.count}x
                          </span>
                        </div>
                        <div style={{ marginTop: 8, display: "flex", flexWrap: "wrap", gap: 4 }}>
                          {ec.sources.map((s, si) => (
                            <span key={si} style={{ fontSize: "0.68rem", color: "var(--text-muted)", fontFamily: "monospace" }}>
                              {s}{si < ec.sources.length - 1 ? " • " : ""}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* SECTION 7: BEFORE VS AFTER SUMMARY */}
                <div
                  className="glass-card"
                  style={{
                    padding: 24,
                    border: "1px solid var(--border-color)",
                    background: "var(--very-light-blue)",
                  }}
                >
                  <h4 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: 14 }}>
                    Before Memory vs After 20+ Interactions Summary
                  </h4>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
                    {/* Before */}
                    <div
                      style={{
                        padding: 16,
                        background: "var(--danger-light)",
                        border: "1px solid var(--danger-border)",
                        borderRadius: "var(--radius-sm)",
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
                        <span className="badge" style={{ background: "var(--danger-light)", color: "var(--danger)", fontSize: "0.7rem", fontWeight: 700 }}>
                          BEFORE MEMORY (INTERACTION 1)
                        </span>
                      </div>
                      <ul style={{ paddingLeft: 18, margin: 0, fontSize: "0.82rem", color: "var(--text-secondary)", lineHeight: 1.6 }}>
                        <li>Generic, one-size-fits-all meeting brief from public web info only.</li>
                        <li>Blind to previous promises and unfulfilled commitments.</li>
                        <li>No detection of recurring objections, concerns, or deal risks.</li>
                        <li>Treats recurring stakeholder as a cold lead on every single call.</li>
                        <li>High risk of commitment failure and repeating answered questions.</li>
                      </ul>
                    </div>

                    {/* After */}
                    <div
                      style={{
                        padding: 16,
                        background: "var(--success-light)",
                        border: "1px solid var(--success-border)",
                        borderRadius: "var(--radius-sm)",
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
                        <span className="badge" style={{ background: "var(--success-light)", color: "var(--success)", fontSize: "0.7rem", fontWeight: 700 }}>
                          AFTER 20+ INTERACTIONS (HINDSIGHT ACTIVE)
                        </span>
                      </div>
                      <ul style={{ paddingLeft: 18, margin: 0, fontSize: "0.82rem", color: "var(--text-primary)", lineHeight: 1.6 }}>
                        <li>Hyper-personalized meeting brief grounded in persistent interaction memory.</li>
                        <li>Proactive alerts on unfulfilled commitments (C001) before walking into the call.</li>
                        <li>Recurring concerns synthesized with citation counts (4x mentions).</li>
                        <li>Communication preferences and previous decisions applied automatically.</li>
                        <li>Continuous learning loop: each interaction compounds intelligence.</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            ) : learningLoading ? (
              <div className="glass-card" style={{ padding: 60, textAlign: "center" }}>
                <div className="spinner" style={{ margin: "0 auto 20px", width: 36, height: 36 }} />
                <p style={{ color: "var(--text-secondary)" }}>Modeling longitudinal intelligence curve...</p>
              </div>
            ) : null}
          </div>
        )}

        {/* ═════════════════════════════════════════════════════ */}
        {/* VIEW: BEFORE VS AFTER COMPARISON                      */}
        {/* ═════════════════════════════════════════════════════ */}
        {view === "comparison" && (
          <div className="fade-in">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 24 }}>
              <div>
                <h2 className="page-header-title" style={{ fontSize: "1.75rem", fontWeight: 800 }}>
                  ⚖️ Before vs After — Memory Demo
                </h2>
                <p className="page-header-subtitle" style={{ fontSize: "0.88rem" }}>
                  The 60-second judge test: A side-by-side comparison proving why persistent memory changes everything.
                </p>
              </div>
              <button className="btn-primary" onClick={generateComparison} disabled={compLoading}>
                {compLoading ? <span className="spinner" /> : Icons.compare}
                {compLoading ? "Generating Comparison..." : "Regenerate Comparison"}
              </button>
            </div>

            {comparison ? (
              <div className="comparison-grid">
                {/* WITHOUT Memory */}
                <div
                  className="glass-card fade-in"
                  style={{
                    padding: 28,
                    borderColor: "#E2E8F0",
                    background: "#F8FAFC",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 12,
                      marginBottom: 20,
                      paddingBottom: 16,
                      borderBottom: "1px solid var(--border-color)",
                    }}
                  >
                    <span style={{ fontSize: "1.8rem" }}>❌</span>
                    <div>
                      <h3 style={{ color: "var(--danger)", fontSize: "1.15rem", fontWeight: 800 }}>
                        WITHOUT Memory (Generic LLM)
                      </h3>
                      <p style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
                        0 memories used • 0 commitments tracked • Generic cold questions
                      </p>
                    </div>
                  </div>
                  <div className="brief-content" dangerouslySetInnerHTML={{ __html: formatMarkdown(comparison.without_memory) }} />
                </div>

                {/* WITH Hindsight Memory */}
                <div
                  className="glass-card fade-in fade-in-delay-1"
                  style={{
                    padding: 28,
                    borderColor: "#BFDBFE",
                    background: "linear-gradient(135deg, #FFFFFF 0%, #F5F9FD 100%)",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 12,
                      marginBottom: 20,
                      paddingBottom: 16,
                      borderBottom: "1px solid #BFDBFE",
                    }}
                  >
                    <span style={{ fontSize: "1.8rem" }}>🧠</span>
                    <div>
                      <h3 style={{ color: "var(--success)", fontSize: "1.15rem", fontWeight: 800 }}>
                        WITH Hindsight Memory
                      </h3>
                      <p style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
                        {comparison.memories_used} memories recalled • {comparison.evidence.length} evidence sources
                      </p>
                    </div>
                  </div>
                  <div className="brief-content" dangerouslySetInnerHTML={{ __html: formatMarkdown(comparison.with_memory) }} />
                  {renderMemoryEvidenceCard(comparison.evidence, comparison.memories_used, "With Memory Pipeline Trail")}
                </div>
              </div>
            ) : compLoading ? (
              <div className="glass-card" style={{ padding: 60, textAlign: "center" }}>
                <div className="spinner" style={{ margin: "0 auto 20px", width: 36, height: 36 }} />
                <p style={{ color: "var(--text-secondary)" }}>Running dual pipelines (generic vs Hindsight memory)...</p>
              </div>
            ) : null}
          </div>
        )}

        {/* ═════════════════════════════════════════════════════ */}
        {/* VIEW: RELATIONSHIP TIMELINE                           */}
        {/* ═════════════════════════════════════════════════════ */}
        {view === "timeline" && (
          <div className="fade-in">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 24 }}>
              <div>
                <h2 className="page-header-title" style={{ fontSize: "1.75rem", fontWeight: 800 }}>
                  📅 Relationship Timeline
                </h2>
                <p className="page-header-subtitle" style={{ fontSize: "0.88rem" }}>
                  Chronological interaction stream for {selectedCompany?.company_name} ({timelineEvents.length} total events)
                </p>
              </div>

              {/* Filter Buttons */}
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                {["all", "meeting", "email", "commitment", "concern", "decision"].map((f) => (
                  <button
                    key={f}
                    onClick={() => setTimelineFilter(f)}
                    style={{
                      background: timelineFilter === f ? "var(--primary-blue)" : "#FFFFFF",
                      color: timelineFilter === f ? "#fff" : "var(--text-secondary)",
                      border: "1px solid var(--border-color)",
                      padding: "5px 12px",
                      borderRadius: 100,
                      fontSize: "0.72rem",
                      cursor: "pointer",
                      fontWeight: 600,
                      textTransform: "capitalize",
                    }}
                  >
                    {f}
                  </button>
                ))}
              </div>
            </div>

            {filteredTimeline.length > 0 ? (
              <div className="timeline-line">
                {filteredTimeline.map((ev, i) => (
                  <div
                    key={i}
                    className="fade-in"
                    style={{ position: "relative", marginBottom: 20, animationDelay: `${i * 0.03}s` }}
                  >
                    <div className={`timeline-dot timeline-dot-${ev.event_type}`} style={{ top: 6 }} />
                    <div className="glass-card" style={{ padding: 18 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                        <span
                          className={`badge badge-${
                            ev.event_type === "concern"
                              ? "high"
                              : ev.event_type === "commitment"
                              ? "open"
                              : ev.event_type === "decision"
                              ? "completed"
                              : "active"
                          }`}
                        >
                          {ev.event_type}
                        </span>
                        <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{ev.event_date}</span>
                      </div>
                      <p style={{ fontWeight: 700, fontSize: "0.95rem" }}>{ev.title}</p>
                      {ev.summary && (
                        <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)", marginTop: 4, lineHeight: 1.5 }}>
                          {ev.summary}
                        </p>
                      )}
                      {ev.reference_id && (
                        <p style={{ fontSize: "0.72rem", color: "var(--accent-indigo)", marginTop: 6, fontWeight: 600 }}>
                          Ref ID: {ev.reference_id}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="glass-card" style={{ padding: 48, textAlign: "center" }}>
                <p style={{ color: "var(--text-muted)" }}>No events matching the selected filter.</p>
              </div>
            )}
          </div>
        )}

        {/* ═════════════════════════════════════════════════════ */}
        {/* VIEW: ASK THE AGENT (CHAT)                            */}
        {/* ═════════════════════════════════════════════════════ */}
        {view === "chat" && (
          <div className="fade-in" style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 80px)" }}>
            <div style={{ marginBottom: 16 }}>
              <h2 className="page-header-title" style={{ fontSize: "1.75rem", fontWeight: 800 }}>
                💬 Ask the Meeting Intelligence Agent
              </h2>
              <p className="page-header-subtitle" style={{ fontSize: "0.88rem" }}>
                Grounding answers directly in {selectedCompany?.company_name}&apos;s Hindsight memory bank.
              </p>
            </div>

            {/* Suggested Prompt Chips */}
            {chatMessages.length === 0 && (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10, marginBottom: 20 }}>
                {[
                  "Prepare me for my next meeting with Sarah.",
                  "When is my next meeting with Sarah?",
                  "What should I know before meeting Sarah?",
                  "Prepare me for my next meeting with NexaCloud.",
                  "What did I promise Sarah?",
                  "What concerns has Sarah raised repeatedly?",
                ].map((q) => (
                  <button
                    key={q}
                    className="btn-secondary"
                    style={{ fontSize: "0.8rem", textAlign: "left", padding: "10px 14px", lineHeight: 1.4 }}
                    onClick={() => {
                      setChatInput(q);
                    }}
                  >
                    💡 {q}
                  </button>
                ))}
              </div>
            )}

            {/* Chat Messages Stream */}
            <div style={{ flex: 1, overflowY: "auto", marginBottom: 16, paddingRight: 8 }}>
              {chatMessages.map((msg, i) => (
                <div
                  key={i}
                  style={{
                    marginBottom: 16,
                    display: "flex",
                    justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
                  }}
                >
                  <div
                    className={msg.role === "user" ? "user-chat-bubble" : "agent-chat-bubble"}
                    style={{
                      maxWidth: "85%",
                      padding: 18,
                      borderRadius: "var(--radius-md)",
                      background: msg.role === "user" ? "var(--primary-blue)" : "#FFFFFF",
                      color: msg.role === "user" ? "#FFFFFF" : "var(--text-primary)",
                      border: msg.role === "user" ? "1px solid var(--primary-blue)" : "1px solid var(--border-color)",
                      boxShadow: msg.role === "user" ? "0 4px 14px rgba(37, 99, 168, 0.25)" : "var(--shadow-card)",
                    }}
                  >
                    {/* Dedicated Next Meeting UI Card */}
                    {msg.nextMeeting && (
                      <div
                        style={{
                          background: "var(--very-light-blue)",
                          border: "1px solid #BFDBFE",
                          borderRadius: "var(--radius-md)",
                          padding: "16px 18px",
                          marginBottom: 16,
                          boxShadow: "0 4px 14px rgba(15, 39, 66, 0.06)",
                        }}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                            <span
                              style={{
                                fontSize: "0.72rem",
                                fontWeight: 800,
                                letterSpacing: "0.08em",
                                color: "var(--primary-blue)",
                                textTransform: "uppercase",
                              }}
                            >
                              NEXT MEETING
                            </span>
                            <span className="badge badge-active" style={{ fontSize: "0.68rem" }}>
                              🟢 {msg.nextMeeting.status ? msg.nextMeeting.status.toUpperCase() : "UPCOMING"}
                            </span>
                          </div>
                          <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", fontFamily: "monospace" }}>
                            {msg.nextMeeting.meeting_id}
                          </span>
                        </div>

                        <div style={{ fontSize: "1.18rem", fontWeight: 700, color: "var(--dark-navy)", marginBottom: 6 }}>
                          {msg.nextMeeting.title}
                        </div>

                        <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.86rem", color: "var(--text-secondary)", marginBottom: 12 }}>
                          <span>
                            👤 <strong style={{ color: "var(--dark-navy)" }}>{msg.nextMeeting.contact?.name || "Lead Stakeholder"}</strong>
                            {msg.nextMeeting.contact?.role ? ` · ${msg.nextMeeting.contact.role}` : ""}
                          </span>
                          <span>•</span>
                          <span>🏢 {msg.nextMeeting.company?.name || "Account"}</span>
                        </div>

                        <div
                          style={{
                            display: "flex",
                            flexWrap: "wrap",
                            gap: 16,
                            fontSize: "0.84rem",
                            color: "var(--text-primary)",
                            padding: "9px 13px",
                            background: "#FFFFFF",
                            borderRadius: "var(--radius-sm)",
                            marginBottom: 14,
                            border: "1px solid var(--border-color)",
                          }}
                        >
                          <div>📅 <strong>{formatDateOnly(msg.nextMeeting.scheduled_at)}</strong></div>
                          {formatTimeOnly(msg.nextMeeting.scheduled_at) && (
                            <div>🕐 <strong>{formatTimeOnly(msg.nextMeeting.scheduled_at)}</strong></div>
                          )}
                          <div>📍 {msg.nextMeeting.location || "Online"}</div>
                        </div>

                        <div style={{ display: "flex", gap: 10 }}>
                          <button
                            className="btn-primary"
                            style={{ fontSize: "0.8rem", padding: "7px 13px", display: "inline-flex", alignItems: "center", gap: 6 }}
                            onClick={() => openMeetingDetail(msg.nextMeeting!.meeting_id)}
                          >
                            🔍 Open Meeting
                          </button>
                          <button
                            className="btn-secondary"
                            style={{ fontSize: "0.8rem", padding: "7px 13px", display: "inline-flex", alignItems: "center", gap: 6 }}
                            onClick={() => {
                              if (msg.nextMeeting?.company?.id) {
                                prepareUpcomingBrief(msg.nextMeeting.company.id, msg.nextMeeting.contact?.id);
                              }
                            }}
                          >
                            ⚡ Generate Full Brief
                          </button>
                        </div>
                      </div>
                    )}

                    {msg.role === "user" ? (
                      <p
                        style={{
                          color: "#FFFFFF",
                          fontWeight: 500,
                          fontSize: "0.95rem",
                          lineHeight: 1.55,
                          margin: 0,
                        }}
                      >
                        {msg.content}
                      </p>
                    ) : (
                      <div
                        className="brief-content"
                        dangerouslySetInnerHTML={{ __html: formatMarkdown(msg.content) }}
                      />
                    )}
                    {msg.evidence && msg.evidence.length > 0 && (
                      <div style={{ marginTop: 14 }}>
                        {renderMemoryEvidenceCard(msg.evidence, msg.memoriesUsed || 0, "Grounding for this Answer")}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {chatLoading && (
                <div style={{ display: "flex", alignItems: "center", gap: 10, color: "var(--text-secondary)", padding: 12 }}>
                  <div className="spinner" />
                  <span style={{ fontSize: "0.85rem" }}>Searching Hindsight memory &amp; reasoning...</span>
                </div>
              )}
            </div>

            {/* Chat Input Bar */}
            <div style={{ display: "flex", gap: 10 }}>
              <input
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && sendChat()}
                placeholder="Ask anything about promises, previous discussions, or concerns..."
                style={{
                  flex: 1,
                  padding: "14px 18px",
                  background: "var(--bg-card)",
                  border: "1px solid var(--border-color)",
                  borderRadius: "var(--radius-sm)",
                  color: "var(--text-primary)",
                  fontSize: "0.92rem",
                  outline: "none",
                }}
              />
              <button className="btn-primary" onClick={sendChat} disabled={chatLoading}>
                {Icons.send} Ask Agent
              </button>
            </div>
          </div>
        )}

        {/* ═════════════════════════════════════════════════════ */}
        {/* VIEW: CUSTOMERS DIRECTORY                             */}
        {/* ═════════════════════════════════════════════════════ */}
        {view === "customers" && (
          <div className="fade-in">
            <h2 className="page-header-title" style={{ fontSize: "1.75rem", fontWeight: 800, marginBottom: 8 }}>
              👥 Customer &amp; Stakeholder Directory
            </h2>
            <p className="page-header-subtitle" style={{ marginBottom: 24, fontSize: "0.88rem" }}>
              10 Enterprise accounts mapped into PostgreSQL relational schema &amp; Hindsight semantic memory
            </p>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))", gap: 18 }}>
              {contacts.map((c) => {
                const company = companies.find((co) => co.customer_id === c.customer_id);
                const isSelected = c.customer_id === selectedCustomer;
                return (
                  <div
                    key={c.contact_id}
                    className="glass-card"
                    style={{
                      padding: 22,
                      cursor: "pointer",
                      border: isSelected ? "2px solid var(--accent-indigo)" : "1px solid var(--border-color)",
                      background: isSelected ? "var(--light-blue)" : "var(--bg-card)",
                    }}
                    onClick={() => {
                      loadCustomerData(c.customer_id);
                      setView("dashboard");
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                      <div>
                        <h4 style={{ fontWeight: 800, fontSize: "1.1rem" }}>{c.name}</h4>
                        <p style={{ color: "var(--accent-violet)", fontSize: "0.86rem", fontWeight: 600 }}>{c.role}</p>
                      </div>
                      <span className="badge badge-active">{company?.segment}</span>
                    </div>

                    <div style={{ marginTop: 14, paddingTop: 12, borderTop: "1px solid var(--border-color)" }}>
                      <p style={{ fontWeight: 600, fontSize: "0.9rem", color: "var(--text-primary)" }}>
                        {company?.company_name}
                      </p>
                      <p style={{ color: "var(--text-muted)", fontSize: "0.78rem" }}>
                        {company?.industry} • {company?.country}
                      </p>
                      <p style={{ color: "var(--text-secondary)", fontSize: "0.78rem", marginTop: 4 }}>
                        ✉️ {c.email}
                      </p>
                    </div>

                    <div style={{ marginTop: 16, display: "flex", gap: 8 }}>
                      <button
                        className="btn-primary"
                        style={{ flex: 1, fontSize: "0.75rem", padding: "6px 12px", justifyContent: "center" }}
                        onClick={(e) => {
                          e.stopPropagation();
                          loadCustomerData(c.customer_id);
                          setView("brief");
                          generateBrief();
                        }}
                      >
                        Prepare Brief
                      </button>
                      <button
                        className="btn-secondary"
                        style={{ fontSize: "0.75rem", padding: "6px 12px" }}
                        onClick={(e) => {
                          e.stopPropagation();
                          loadCustomerData(c.customer_id);
                          setView("timeline");
                        }}
                      >
                        Timeline
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

// ── Markdown Formatter ────────────────────────────────────────
function formatMarkdown(text: string): string {
  if (!text) return "";
  let formatted = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // Facts vs Recommendations section header annotations
  formatted = formatted
    .replace(
      /^### (.*(relationship|summary|changes|discussions|priorities|concerns|decisions|commitments|preferences|contact|main contact|top commitments).*)$/gim,
      '<div class="fact-section-header"><span class="fact-pill">🧠 REMEMBERED FACT · HINDSIGHT GROUNDED</span></div><h3>$1</h3>'
    )
    .replace(
      /^### (.*(agenda|questions|preparation|risks|takeaways|advisory|recommendation|steps).*)$/gim,
      '<div class="rec-section-header"><span class="rec-pill">⚡ AI RECOMMENDATION · STRATEGIC SYNTHESIS</span></div><h3>$1</h3>'
    )
    .replace(/^### (.+)$/gm, "<h3>$1</h3>")
    .replace(/^## (.+)$/gm, "<h2>$1</h2>")
    .replace(/^# (.+)$/gm, "<h1>$1</h1>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/^- (.+)$/gm, "<li>$1</li>")
    .replace(/^(\d+)\. (.+)$/gm, "<li>$2</li>")
    .replace(/(<li>[\s\S]*<\/li>)/, "<ul>$1</ul>")
    .replace(/---/g, "<hr/>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\[([A-Z]{1,3}\d{3,4})\]/g, '<span class="evidence-chip" style="padding:2px 8px;font-size:0.72rem;margin:0 2px;display:inline-flex;">🔍 $1</span>')
    .replace(/\[([^\]]+)\]/g, "<strong>[$1]</strong>")
    .replace(/\n\n/g, "</p><p>")
    .replace(/\n/g, "<br/>")
    .replace(/^(.+)$/, "<p>$&</p>");

  return formatted;
}
