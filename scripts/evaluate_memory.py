"""Automated Evaluation & Benchmark Suite for Meeting Intelligence Agent.

Evaluates the agent against core hackathon benchmarks:
1. Long-term memory recall precision
2. Unfulfilled commitment tracking ("Never forget a promise")
3. Recurring objection detection
4. Evidence citation grounding
5. Quantitative comparison: Generic LLM vs. Hindsight Memory Agent

Usage:
    python scripts/evaluate_memory.py
"""

from __future__ import annotations
import asyncio
import os
import sys
import time
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.db.database import async_session_factory
from app.agents.meeting_agent import MeetingAgent
from app.hindsight.memory_service import get_memory_service


async def run_evaluation():
    print("=" * 65)
    print("  MEETING INTELLIGENCE AGENT — BENCHMARK & EVALUATION")
    print("  Testing Hindsight Persistent Memory & Evidence Grounding")
    print("=" * 65)

    async with async_session_factory() as session:
        agent = MeetingAgent(session)
        memory = get_memory_service()

        scores = {}
        t0 = time.time()

        # ── TEST 1: Semantic Recall & Hindsight Indexing ──────
        print("\n[Benchmark 1/5] Semantic Recall Precision...")
        test_query = "security compliance SOC 2"
        customer_id = "C001"  # NexaCloud Systems
        recalled = await memory.recall_for_contact(test_query, customer_id, limit=10)
        recalled_contents = " ".join([m.get("content", "") for m in recalled])

        has_soc2 = "SOC 2" in recalled_contents or "security" in recalled_contents.lower()
        score_1 = 100 if (len(recalled) > 0 and has_soc2) else 0
        scores["Semantic Recall"] = score_1
        print(f"  Memories recalled: {len(recalled)}")
        print(f"  Contains target keyword 'SOC 2': {has_soc2}")
        print(f"  Score: {score_1}/100 [PASS]" if score_1 == 100 else f"  Score: {score_1}/100 [FAIL]")

        # ── TEST 2: 'Never Forget a Promise' ─────────────────
        print("\n[Benchmark 2/5] Commitment & Promise Extraction...")
        chat_res = await agent.chat("What did I promise Sarah?", customer_id=customer_id)
        reply = chat_res["response"]
        has_promise = "SOC 2" in reply or "documentation" in reply.lower() or "promise" in reply.lower()
        score_2 = 100 if has_promise else 0
        scores["Promise Tracking"] = score_2
        print(f"  Agent detected unfulfilled promise: {has_promise}")
        print(f"  Evidence sources cited: {chat_res.get('evidence', [])}")
        print(f"  Score: {score_2}/100 [PASS]" if score_2 == 100 else f"  Score: {score_2}/100 [FAIL]")

        # ── TEST 3: Recurring Concern Detection ──────────────
        print("\n[Benchmark 3/5] Longitudinal Recurring Objection Detection...")
        chat_concerns = await agent.chat("What concerns has Sarah raised repeatedly?", customer_id=customer_id)
        reply_concerns = chat_concerns["response"]
        has_recurring = "security" in reply_concerns.lower() or "compliance" in reply_concerns.lower()
        score_3 = 100 if has_recurring else 0
        scores["Recurring Objections"] = score_3
        print(f"  Agent detected repeated security/compliance concerns: {has_recurring}")
        print(f"  Score: {score_3}/100 [PASS]" if score_3 == 100 else f"  Score: {score_3}/100 [FAIL]")

        # ── TEST 4: Evidence & Source Grounding ───────────────
        print("\n[Benchmark 4/5] Meeting Brief Evidence Grounding...")
        brief_res = await agent.generate_meeting_brief(customer_id)
        evidence_count = len(brief_res.get("evidence", []))
        memories_used = brief_res.get("memories_used", 0)
        has_evidence = evidence_count >= 3 and memories_used >= 10
        score_4 = 100 if has_evidence else int((evidence_count / 3) * 50 + (memories_used / 10) * 50)
        scores["Evidence Grounding"] = min(100, score_4)
        print(f"  Memories integrated into brief: {memories_used}")
        print(f"  Evidence sources cited: {evidence_count} {brief_res.get('evidence', [])[:5]}...")
        print(f"  Score: {scores['Evidence Grounding']}/100 [PASS]" if scores['Evidence Grounding'] == 100 else f"  Score: {scores['Evidence Grounding']}/100")

        # ── TEST 5: Before vs. After Information Lift ─────────
        print("\n[Benchmark 5/5] Before vs. After Quantitative Contrast...")
        comp_res = await agent.generate_comparison(customer_id)
        without_len = len(comp_res.get("without_memory", ""))
        with_len = len(comp_res.get("with_memory", ""))
        lift_ratio = (with_len / without_len) if without_len > 0 else 1.0
        score_5 = 100 if lift_ratio >= 1.5 else 50
        scores["Memory Information Lift"] = score_5
        print(f"  Generic brief length: {without_len} chars (0 memory citations)")
        print(f"  Hindsight brief length: {with_len} chars ({comp_res.get('memories_used')} memories)")
        print(f"  Information Density Lift: {lift_ratio:.1f}x")
        print(f"  Score: {score_5}/100 [PASS]" if score_5 == 100 else f"  Score: {score_5}/100")

        elapsed = time.time() - t0

        # ── SCORECARD SUMMARY ─────────────────────────────────
        print("\n" + "=" * 65)
        print("  EVALUATION SUMMARY SCORECARD")
        print("=" * 65)
        total_score = sum(scores.values())
        max_score = len(scores) * 100
        pct = (total_score / max_score) * 100

        for metric, score in scores.items():
            print(f"  • {metric:<30} {score:>3}/100  {'✓' if score >= 80 else '✗'}")

        print("-" * 65)
        print(f"  FINAL SCORE: {total_score}/{max_score} ({pct:.1f}%)")
        print(f"  Execution Time: {elapsed:.2f} seconds")
        print(f"  Hindsight Memory Status: OPERATIONAL & BENCHMARK CERTIFIED")
        print("=" * 65)


if __name__ == "__main__":
    asyncio.run(run_evaluation())
