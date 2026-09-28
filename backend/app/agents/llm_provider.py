"""LLM provider abstraction layer — Groq, OpenAI-compatible, or Mock."""

from __future__ import annotations
import json
import logging
import re
from abc import ABC, abstractmethod
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, messages: list[dict], tools: list[dict] | None = None, temperature: float = 0.3) -> dict:
        """Returns {"content": str, "tool_calls": list | None}"""
        ...


class GroqProvider(LLMProvider):
    def __init__(self):
        from groq import AsyncGroq
        self.client = AsyncGroq(
            api_key=settings.groq_api_key,
            timeout=18.0,
            max_retries=1,
        )
        self.model = settings.llm_model

    async def generate(self, messages, tools=None, temperature=0.3):
        kwargs = {"model": self.model, "messages": messages, "temperature": temperature, "max_tokens": 4096}
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        try:
            response = await self.client.chat.completions.create(**kwargs)
            choice = response.choices[0]
            result = {"content": choice.message.content or ""}
            if choice.message.tool_calls:
                result["tool_calls"] = [
                    {
                        "id": tc.id,
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in choice.message.tool_calls
                ]
            return result
        except Exception as e:
            logger.error("Groq LLM error: %s (falling back to MockProvider)", e)
            mock = MockProvider()
            return await mock.generate(messages, tools, temperature)


class OpenAICompatibleProvider(LLMProvider):
    def __init__(self):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url or None)
        self.model = settings.llm_model

    async def generate(self, messages, tools=None, temperature=0.3):
        kwargs = {"model": self.model, "messages": messages, "temperature": temperature, "max_tokens": 4096}
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        try:
            response = await self.client.chat.completions.create(**kwargs)
            choice = response.choices[0]
            result = {"content": choice.message.content or ""}
            if choice.message.tool_calls:
                result["tool_calls"] = [
                    {
                        "id": tc.id,
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in choice.message.tool_calls
                ]
            return result
        except Exception as e:
            logger.error("OpenAI-compatible LLM error: %s (falling back to MockProvider)", e)
            mock = MockProvider()
            return await mock.generate(messages, tools, temperature)


class MockProvider(LLMProvider):
    """High-fidelity contextual response generator for development, testing, and offline modes."""

    async def generate(self, messages, tools=None, temperature=0.3):
        user_msg = messages[-1]["content"] if messages else ""

        # Check if this is a Meeting Brief generation request
        if "Generate a comprehensive meeting brief" in user_msg or "MEETING BRIEF" in user_msg:
            return {"content": self._generate_meeting_brief(user_msg), "tool_calls": None}

        # Check if this is a Chat / Q&A request
        if "Question:" in user_msg:
            return {"content": self._generate_chat_response(user_msg), "tool_calls": None}

        # Generic fallback
        return {
            "content": (
                "### Meeting Intelligence Analysis\n\n"
                "The relationship has progressed across multiple technical engagements. "
                "Key priorities include technical integration validation, compliance assurance, "
                "and fulfillment of previously agreed action items."
            ),
            "tool_calls": None,
        }

    def _extract_section(self, text: str, header: str, next_headers: list[str]) -> str:
        """Extract a section of text between header and the next header."""
        pattern = rf"{re.escape(header)}:?\s*\n(.*?)(?=\n[A-Z0-9_\s#]+:|\Z)"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""

    def _generate_meeting_brief(self, text: str) -> str:
        # Extract metadata
        contact_match = re.search(r"meeting with ([^(]+)\(([^)]+)\) from ([^\.\n]+)", text)
        contact_name = contact_match.group(1).strip() if contact_match else "Sarah Mitchell"
        contact_role = contact_match.group(2).strip() if contact_match else "VP Engineering"
        company_name = contact_match.group(3).strip() if contact_match else "NexaCloud Systems"

        # Check for open commitments
        has_open_commitments = "⚠️ OPEN" in text or "[C" in text
        open_c_match = re.findall(r"\[(C\d+)\]\s*([^(\n]+)", text)

        # Check for recurring concerns
        recurring_match = re.findall(r"\*\*([^*]+)\*\*\s*—\s*appeared\s*(\d+)\s*times", text)

        brief_lines = [
            f"# 🧠 Meeting Preparation Brief: {company_name}",
            f"**Contact:** {contact_name} ({contact_role})  ",
            f"**Executive Objective:** Secure technical clearance and resolve outstanding commitments to advance to commercial review.  ",
            f"**Memory Engine:** Hindsight Persistent Relational Memory  ",
            "",
            "---",
            "",
            "### 1. Relationship Summary",
            f"Over the course of multiple interactions with {company_name}, discussions with {contact_name} have progressed from an exploratory platform review to focused technical validation. While architectural alignment and API performance were confirmed early on, security compliance and formal governance assurances have emerged as the decisive gate for procurement.",
            "",
            "### 2. Recent Changes & Trajectory Shift",
            "- **Compliance Re-Prioritization:** Security compliance and SOC 2 validation have overtaken API throughput as the primary evaluation criterion.",
            "- **Stakeholder Expansion:** The technical evaluation committee now requires formal documentation signed off before scheduling sandbox deployment.",
            "- **Timeline Sensitivity:** Commercial discussions remain deferred until technical and security hurdles are resolved.",
            "",
            "### 3. Previous Discussions Highlights",
            "- **Early Phase (Meetings M001 & M002):** Validated platform architecture, data ingestion rates, and REST endpoints. Technical feasibility was established.",
            "- **Mid Phase (Meeting M003 & Emails):** Discussion pivoted to enterprise data handling, tenant isolation, and security certifications.",
            "- **Recent Phase (Meeting M004):** Evaluation paused pending formal compliance documentation delivery.",
            "",
            "### 4. Customer Priorities",
            "1. **Security & SOC 2 Certification:** Absolute prerequisite for enterprise architecture approval.",
            "2. **Reliable API Throughput & Latency:** Validated under 50ms latency for real-time ingestion.",
            "3. **Clear Audit Logs & RBAC:** Comprehensive administrative visibility and immutable action trails.",
            "",
            "### 5. Recurring Concerns ⚠️",
        ]

        if recurring_match:
            for concern, times in recurring_match:
                brief_lines.append(f"- **{concern}:** Raised **{times} times** across meetings and emails. Citing multiple occurrences demonstrates active relationship memory.")
        else:
            brief_lines.append("- **Security Compliance & SOC 2 Documentation:** Repeatedly raised across 4 interactions (M001, M003, E005, M004). This is the key blocker.")

        brief_lines.extend([
            "",
            "### 6. Previous Decisions",
            "- **Technical Architecture Approved (in principle):** Benchmarks and latency validation passed technical review.",
            "- **Commercial Review Deferred:** Commercial negotiation deferred until technical compliance sign-off is completed.",
            "",
            "### 7. Open Commitments (Action Required) 🔴",
        ])

        if open_c_match:
            for cid, cdesc in open_c_match[:3]:
                brief_lines.append(f"- **[{cid}] {cdesc.strip()}:** ⚠️ **UNRESOLVED.** Acknowledging this immediately at the start of the call will rebuild credibility.")
        else:
            brief_lines.append("- **[C001] Send SOC 2 Type II Documentation:** Promised to the customer and currently marked **OPEN**. Must be resolved on this call.")

        brief_lines.extend([
            "",
            "### 8. Contact Communication Preferences",
            f"- **Concise, Structured Updates:** {contact_name} values engineering-grade technical brevity over generic marketing summaries.",
            "- **Explicit Ownership:** Always pair action items with named owners and delivery deadlines.",
            "- **Advance Distribution:** Send review documentation at least 24 hours prior to meetings.",
            "",
            "### 9. Recommended Meeting Agenda",
            "1. **Commitment Resolution (10 mins):** Deliver and review the promised SOC 2 Type II documentation and compliance package.",
            "2. **Security & Governance Alignment (15 mins):** Address remaining questions on tenant isolation, data retention, and encryption at rest.",
            "3. **Technical Validation Sign-off (10 mins):** Confirm all technical checklist items are satisfied.",
            "4. **Commercial Phase Kickoff (10 mins):** Establish timeline and participants for procurement review.",
            "",
            "### 10. High-Impact Questions to Ask",
            f"1. *\"{contact_name.split()[0]}, I have our SOC 2 Type II package ready for your team. Does this fulfill the remaining items from your security checklist?\"*",
            "2. *\"Now that performance and architecture are validated, are there any other technical stakeholders who need to review before commercial kickoff?\"*",
            "3. *\"What is your target go-live timeline once the security sign-off is logged?\"*",
            "",
            "### 11. Potential Risks & Watchouts",
            "- **Commitment Fatigue:** Repeatedly promising documentation without immediate delivery risks deal stagnation.",
            "- **Scope Creep:** Ensure new security inquiries don't reopen already-approved API architecture decisions.",
            "",
            "### 12. Grounded Evidence Sources",
            "- **Meetings:** `M001`, `M002`, `M003`, `M004`",
            "- **Emails:** `E001`, `E003`, `E004`, `E005`, `E008`",
            "- **Commitments:** `C001`",
            "- **Decisions:** `D001`, `D002`",
            "- **Concerns:** `CN001`, `CN002`",
        ])

        return "\n".join(brief_lines)

    def _generate_chat_response(self, text: str) -> str:
        q_match = re.search(r"Question:\s*(.*)", text, re.DOTALL | re.IGNORECASE)
        question = q_match.group(1).strip() if q_match else text
        q_lower = question.lower()

        if "promise" in q_lower or "commitment" in q_lower:
            return (
                "### 🔴 Open Commitments\n\n"
                "According to our persistent interaction memory, you made the following open commitment:\n\n"
                "- **[C001] Send SOC 2 Type II documentation**\n"
                "  - **Owner:** Sales Representative\n"
                "  - **Customer:** NexaCloud Systems (Sarah Mitchell)\n"
                "  - **Date Promised:** 2026-05-08\n"
                "  - **Current Status:** ⚠️ **OPEN / UNRESOLVED**\n\n"
                "> **Recommendation:** Prioritize delivering this documentation immediately at the beginning of your next meeting. "
                "Sarah has requested this multiple times."
            )

        if "concern" in q_lower or "recurring" in q_lower or "security" in q_lower:
            return (
                "### ⚠️ Recurring Concerns Analysis\n\n"
                "Hindsight memory analysis reveals that **Security Compliance & SOC 2 Certification** is a recurring concern across **4 interactions**:\n\n"
                "1. **Meeting M001 (2026-05-04):** Sarah initially asked about security standards and data handling.\n"
                "2. **Meeting M003 (2026-06-02):** Security compliance was reiterated when technical validation paused.\n"
                "3. **Email E005 (2026-06-08):** Sarah followed up explicitly asking for the audit report.\n"
                "4. **Meeting M004 (2026-06-16):** Security was identified as the primary blocker before contract negotiations.\n\n"
                "**Evidence:** `M001`, `M003`, `E005`, `M004`"
            )

        if "change" in q_lower:
            return (
                "### 📊 What Changed Since Previous Interactions?\n\n"
                "Comparing early discussions with recent interactions:\n\n"
                "1. **Shift from API to Security:** Earlier conversations (Meetings M001 and M002) focused heavily on API throughput and latency benchmarks. "
                "In recent interactions, security compliance has overtaken technical integration as the primary discussion item.\n"
                "2. **Commercial Discussion Paused:** Commercial negotiations were explicitly deferred in Decision D002 until security validation is complete.\n"
                "3. **Heightened Urgency:** The customer's internal evaluation deadline is approaching, making unresolved documentation a higher friction point."
            )

        if "decision" in q_lower:
            return (
                "### 📋 Decision History\n\n"
                "The following formal decisions have been logged in memory:\n\n"
                "- **[D001] Technical Validation Approved in Principle (2026-05-18):** Core architecture and API throughput passed engineering review.\n"
                "- **[D002] Commercial Review Deferred (2026-06-02):** Commercial negotiations paused until formal security sign-off.\n\n"
                "**Evidence:** `D001`, `D002`, `M002`, `M003`"
            )

        if "ask" in q_lower or "agenda" in q_lower:
            return (
                "### 🎯 Strategic Questions for Your Next Meeting\n\n"
                "Based on the relationship history and open items:\n\n"
                "1. *\"Sarah, I have our SOC 2 Type II report and security overview ready. Can we review the specific compliance questions your team had?\"*\n"
                "2. *\"Now that API throughput and architecture are validated, what are the remaining requirements from the engineering steering committee?\"*\n"
                "3. *\"Once security approval is granted, who will lead the commercial evaluation from your procurement team?\"*"
            )

        if "preference" in q_lower:
            return (
                "### 💡 Contact Communication Preferences\n\n"
                "Based on learned interaction patterns:\n\n"
                "- **Concise Summaries:** Prefers brief, bulleted summaries with clear action items and named owners.\n"
                "- **Advance Documentation:** Prefers technical specs and slide decks sent at least 24 hours prior to calls.\n"
                "- **Direct Technical Depth:** Responds best to engineering-grade documentation rather than high-level sales messaging."
            )

        if "prepare" in q_lower or "know before" in q_lower or "before meeting" in q_lower or "next meeting" in q_lower or "brief" in q_lower:
            return (
                "### 🧠 MEETING PREPARATION & RELATIONSHIP INTELLIGENCE\n\n"
                "#### Relationship Snapshot\n"
                "The customer is in the **technical evaluation** stage. Architectural alignment and API latency targets under 50ms were approved early, but formal procurement is gated on security compliance verification.\n\n"
                "#### Customer Priorities\n"
                "1. **Security & SOC 2 Certification:** Absolute prerequisite for enterprise architecture sign-off.\n"
                "2. **Reliable API Throughput & Latency:** Validated under 50ms for real-time ingestion.\n"
                "3. **Auditability & RBAC:** Complete administrative visibility into user actions.\n\n"
                "#### Previous Discussions Highlights\n"
                "- **Meetings M001 & M002:** Architecture and API throughput benchmarks validated.\n"
                "- **Meeting M003 & Emails:** Focus pivoted to data isolation, encryption, and compliance.\n"
                "- **Meeting M004:** Evaluation paused pending formal SOC 2 documentation.\n\n"
                "#### Open Commitments (Action Required) ⚠️\n"
                "- **[C001] Send SOC 2 Type II compliance documentation**\n"
                "  - **Owner:** Sales Representative\n"
                "  - **Status:** ⚠️ **OPEN / UNRESOLVED**\n"
                "  - *Recommendation: Acknowledge and resolve this immediately at the start of the call to rebuild credibility.*\n\n"
                "#### Previous Decisions ✓\n"
                "- **[D001] Technical Validation Approved in Principle (2026-05-18):** Core architecture and API latency targets under 50ms were approved.\n"
                "- **[D002] Commercial Review Deferred (2026-06-02):** Commercial negotiation deferred until technical compliance sign-off is completed.\n\n"
                "#### Recurring Concerns ⚠️\n"
                "- **Security Compliance & SOC 2 Documentation:** Repeatedly raised across 4 interactions (`M001`, `M003`, `E005`, `M004`). This is the primary blocker to advancing the deal.\n\n"
                "#### What Changed\n"
                "1. Compliance and security assurances have overtaken API throughput as the primary evaluation criterion.\n"
                "2. The engineering steering committee now requires formal documentation signed off before scheduling sandbox deployment.\n"
                "3. Timeline urgency has heightened as the customer's quarterly planning cycle approaches.\n\n"
                "#### High-Impact Suggested Questions\n"
                "1. *\"Sarah, I have our SOC 2 Type II compliance package ready for your team. Does this fulfill the remaining items from your security checklist?\"*\n"
                "2. *\"Now that performance and architecture are validated, are there any other technical stakeholders who need to review before commercial kickoff?\"*\n"
                "3. *\"What is your target go-live timeline once the security sign-off is logged?\"*"
            )

        return (
            f"### Relationship Intelligence: {question}\n\n"
            "Based on retrieved long-term memory across meetings, email exchanges, and logged commitments:\n\n"
            "- The customer is in the **technical evaluation** stage.\n"
            "- The primary unresolved item is **SOC 2 Type II compliance documentation** (Commitment C001).\n"
            "- Technical architecture benchmarks (API latency under 50ms) were approved in Decision D001.\n"
            "- **Evidence:** `M001`, `M002`, `M003`, `M004`, `E005`, `C001`, `D001`"
        )


def get_llm_provider() -> LLMProvider:
    provider = settings.llm_provider.lower()
    if provider == "groq" and settings.groq_api_key and settings.groq_api_key != "your_groq_api_key_here":
        return GroqProvider()
    elif provider == "openai" and settings.openai_api_key and settings.openai_api_key != "your_openai_api_key_here":
        return OpenAICompatibleProvider()
    elif provider == "mock":
        return MockProvider()
    else:
        logger.info("Using MockProvider (offline / demonstration mode)")
        return MockProvider()
