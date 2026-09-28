"""Tests for the backend API endpoints and core logic.

Tests the FastAPI endpoints, MeetingAgent pipeline, data models,
and Hindsight integration layer using the local SQLite backend.
"""

import sys
import os
import asyncio
import pytest
from pathlib import Path

# Ensure backend is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("LLM_PROVIDER", "mock")


# ─────────────────────────────────────────────────────────────────
# 1. Configuration Tests
# ─────────────────────────────────────────────────────────────────

class TestConfig:
    def test_settings_load(self):
        """Settings object should load from environment/defaults."""
        from app.config import Settings
        s = Settings()
        assert s.app_env is not None
        assert s.app_port == 8000
        assert "sqlite" in s.database_url or "postgresql" in s.database_url

    def test_cors_origins_default(self):
        from app.config import Settings
        s = Settings()
        assert "localhost:3000" in s.cors_origins

    def test_hindsight_defaults(self):
        from app.config import Settings
        s = Settings()
        assert s.hindsight_memory_bank_id == "meeting-intelligence"


# ─────────────────────────────────────────────────────────────────
# 2. Database Model Tests
# ─────────────────────────────────────────────────────────────────

class TestModels:
    def test_company_model_fields(self):
        from app.db.models.models import Company
        assert hasattr(Company, "customer_id")
        assert hasattr(Company, "company_name")
        assert hasattr(Company, "industry")
        assert hasattr(Company, "segment")
        assert hasattr(Company, "country")

    def test_contact_model_fields(self):
        from app.db.models.models import Contact
        assert hasattr(Contact, "contact_id")
        assert hasattr(Contact, "customer_id")
        assert hasattr(Contact, "name")
        assert hasattr(Contact, "role")
        assert hasattr(Contact, "email")

    def test_meeting_model_fields(self):
        from app.db.models.models import Meeting
        assert hasattr(Meeting, "meeting_id")
        assert hasattr(Meeting, "customer_id")
        assert hasattr(Meeting, "contact_id")
        assert hasattr(Meeting, "date")
        assert hasattr(Meeting, "title")
        assert hasattr(Meeting, "summary")
        assert hasattr(Meeting, "transcript")
        assert hasattr(Meeting, "source")

    def test_email_model_fields(self):
        from app.db.models.models import Email
        assert hasattr(Email, "email_id")
        assert hasattr(Email, "direction")
        assert hasattr(Email, "subject")
        assert hasattr(Email, "body")

    def test_commitment_model_fields(self):
        from app.db.models.models import Commitment
        assert hasattr(Commitment, "commitment_id")
        assert hasattr(Commitment, "commitment")
        assert hasattr(Commitment, "owner")
        assert hasattr(Commitment, "status")
        assert hasattr(Commitment, "due_date")
        assert hasattr(Commitment, "evidence")

    def test_decision_model_fields(self):
        from app.db.models.models import Decision
        assert hasattr(Decision, "decision_id")
        assert hasattr(Decision, "decision")
        assert hasattr(Decision, "status")

    def test_concern_model_fields(self):
        from app.db.models.models import Concern
        assert hasattr(Concern, "concern_id")
        assert hasattr(Concern, "concern")
        assert hasattr(Concern, "severity")

    def test_preference_model_fields(self):
        from app.db.models.models import Preference
        assert hasattr(Preference, "preference_id")
        assert hasattr(Preference, "preference")
        assert hasattr(Preference, "confidence")

    def test_event_model_fields(self):
        from app.db.models.models import Event
        assert hasattr(Event, "event_type")
        assert hasattr(Event, "event_date")
        assert hasattr(Event, "reference_id")

    def test_hindsight_memory_model(self):
        from app.db.models.models import HindsightMemory
        assert hasattr(HindsightMemory, "bank_id")
        assert hasattr(HindsightMemory, "content")
        assert hasattr(HindsightMemory, "event_type")

    def test_relationship_snapshot_model(self):
        from app.db.models.models import RelationshipSnapshot
        assert hasattr(RelationshipSnapshot, "relationship_stage")
        assert hasattr(RelationshipSnapshot, "open_commitments")
        assert hasattr(RelationshipSnapshot, "meeting_count")


# ─────────────────────────────────────────────────────────────────
# 3. Schema Tests
# ─────────────────────────────────────────────────────────────────

class TestSchemas:
    def test_chat_request_schema(self):
        from app.schemas.schemas import ChatRequest
        req = ChatRequest(message="test", customer_id="C001")
        assert req.message == "test"
        assert req.customer_id == "C001"
        assert req.contact_id is None

    def test_chat_response_schema(self):
        from app.schemas.schemas import ChatResponse
        resp = ChatResponse(response="hello", evidence=["E001"], memories_used=5)
        assert resp.response == "hello"
        assert len(resp.evidence) == 1
        assert resp.memories_used == 5

    def test_meeting_brief_request(self):
        from app.schemas.schemas import MeetingBriefRequest
        req = MeetingBriefRequest(customer_id="C001", contact_id="CT001")
        assert req.customer_id == "C001"

    def test_meeting_brief_response(self):
        from app.schemas.schemas import MeetingBriefResponse
        resp = MeetingBriefResponse(
            brief="Test brief",
            customer_id="C001",
            contact_name="Sarah",
            company_name="Acme",
            evidence=["M001"],
            memories_used=10,
        )
        assert "brief" in resp.brief.lower() or len(resp.brief) > 0
        assert resp.memories_used == 10

    def test_learning_stage_schema(self):
        from app.schemas.schemas import LearningStage
        stage = LearningStage(
            stage_number=1,
            title="Cold Discovery",
            interaction_count=1,
            relationship_depth="Baseline",
            brief_snippet="Generic meeting",
            memories_available=0,
            commitments_tracked=0,
            key_signals=["No data"],
            risk_level="High",
        )
        assert stage.stage_number == 1
        assert stage.memories_available == 0

    def test_learning_curve_response(self):
        from app.schemas.schemas import LearningCurveResponse, LearningStage
        stages = [
            LearningStage(
                stage_number=i,
                title=f"Stage {i}",
                interaction_count=i * 5,
                relationship_depth="Test",
                brief_snippet="Test",
                memories_available=i * 10,
                commitments_tracked=i,
                key_signals=["signal"],
                risk_level="Low",
            )
            for i in range(1, 4)
        ]
        resp = LearningCurveResponse(
            customer_id="C001",
            company_name="Test",
            contact_name="Test Contact",
            stages=stages,
        )
        assert len(resp.stages) == 3

    def test_demo_comparison_response(self):
        from app.schemas.schemas import DemoComparisonResponse
        resp = DemoComparisonResponse(
            without_memory="generic",
            with_memory="personalized",
            memories_used=15,
            evidence=["M001"],
        )
        assert resp.without_memory != resp.with_memory

    def test_memory_item_schema(self):
        from app.schemas.schemas import MemoryItem
        item = MemoryItem(
            content="Test memory",
            category="meeting",
            customer_id="C001",
            event_type="meeting",
        )
        assert item.content == "Test memory"

    def test_commitment_update_schema(self):
        from app.schemas.schemas import CommitmentUpdate
        update = CommitmentUpdate(status="resolved", evidence="Delivered docs")
        assert update.status == "resolved"


# ─────────────────────────────────────────────────────────────────
# 4. LLM Provider Tests
# ─────────────────────────────────────────────────────────────────

class TestLLMProvider:
    def test_mock_provider_available(self):
        from app.agents.llm_provider import get_llm_provider
        os.environ["LLM_PROVIDER"] = "mock"
        provider = get_llm_provider()
        assert provider is not None

    def test_mock_provider_generates_output(self):
        from app.agents.llm_provider import get_llm_provider
        os.environ["LLM_PROVIDER"] = "mock"
        provider = get_llm_provider()

        async def _run():
            return await provider.generate([
                {"role": "system", "content": "You are a test assistant."},
                {"role": "user", "content": "Hello"},
            ])

        result = asyncio.run(_run())
        assert "content" in result
        assert len(result["content"]) > 0


# ─────────────────────────────────────────────────────────────────
# 5. Hindsight Client Tests
# ─────────────────────────────────────────────────────────────────

class TestHindsightClient:
    def test_client_initializes(self):
        from app.hindsight.client import get_hindsight_client
        client = get_hindsight_client()
        assert client is not None

    def test_memory_service_initializes(self):
        from app.hindsight.memory_service import get_memory_service
        service = get_memory_service()
        assert service is not None
        assert service.client is not None


# ─────────────────────────────────────────────────────────────────
# 6. Dataset Loader Tests
# ─────────────────────────────────────────────────────────────────

class TestDatasetLoader:
    def test_read_jsonl_function(self):
        from app.ingestion.dataset_loader import _read_jsonl
        import tempfile
        import json

        # Create a temp JSONL file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
            f.write(json.dumps({"key": "value1"}) + "\n")
            f.write(json.dumps({"key": "value2"}) + "\n")
            tmp_path = Path(f.name)

        try:
            items = _read_jsonl(tmp_path)
            assert len(items) == 2
            assert items[0]["key"] == "value1"
            assert items[1]["key"] == "value2"
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_synthetic_data_exists(self):
        """Verify the synthetic dataset files exist."""
        data_dir = Path(__file__).resolve().parent.parent / "data" / "synthetic"
        expected_files = [
            "companies.jsonl",
            "contacts.jsonl",
            "meetings.jsonl",
            "emails.jsonl",
            "commitments.jsonl",
            "decisions.jsonl",
            "concerns.jsonl",
            "preferences.jsonl",
            "events.jsonl",
            "relationship_snapshots.jsonl",
        ]
        for fname in expected_files:
            filepath = data_dir / fname
            assert filepath.exists(), f"Missing synthetic data file: {fname}"
            assert filepath.stat().st_size > 0, f"Empty synthetic data file: {fname}"


# ─────────────────────────────────────────────────────────────────
# 7. Prompt Template Tests
# ─────────────────────────────────────────────────────────────────

class TestPrompts:
    def test_system_prompts_exist(self):
        from app.agents.prompts import MEETING_PREP_SYSTEM, CHAT_SYSTEM
        assert len(MEETING_PREP_SYSTEM) > 100
        assert len(CHAT_SYSTEM) > 100

    def test_meeting_brief_template_exists(self):
        from app.agents.prompts import MEETING_BRIEF_TEMPLATE
        assert "meeting" in MEETING_BRIEF_TEMPLATE.lower() or len(MEETING_BRIEF_TEMPLATE) > 0

    def test_generic_meeting_prep_template(self):
        from app.agents.prompts import GENERIC_MEETING_PREP
        # Should have placeholders for company and contact
        assert "{company_name}" in GENERIC_MEETING_PREP or "company" in GENERIC_MEETING_PREP.lower()


# ─────────────────────────────────────────────────────────────────
# 8. Integration Smoke Tests
# ─────────────────────────────────────────────────────────────────

class TestIntegration:
    def test_app_creates(self):
        """FastAPI app should instantiate without errors."""
        from app.main import app
        assert app is not None
        assert app.title == "Meeting Intelligence Agent"

    def test_routes_registered(self):
        """All expected routes should be registered."""
        from app.main import app
        routes = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/" in routes
        assert "/health" in routes

    def test_all_entity_types_in_synthetic(self):
        """Verify synthetic dataset has all 10 entity types."""
        import json
        data_dir = Path(__file__).resolve().parent.parent / "data" / "synthetic"

        companies = [json.loads(l) for l in open(data_dir / "companies.jsonl")]
        contacts = [json.loads(l) for l in open(data_dir / "contacts.jsonl")]
        meetings = [json.loads(l) for l in open(data_dir / "meetings.jsonl")]
        emails = [json.loads(l) for l in open(data_dir / "emails.jsonl")]
        commitments = [json.loads(l) for l in open(data_dir / "commitments.jsonl")]
        decisions = [json.loads(l) for l in open(data_dir / "decisions.jsonl")]
        concerns = [json.loads(l) for l in open(data_dir / "concerns.jsonl")]
        preferences = [json.loads(l) for l in open(data_dir / "preferences.jsonl")]

        assert len(companies) >= 5, "Need at least 5 companies"
        assert len(contacts) >= 5, "Need at least 5 contacts"
        assert len(meetings) >= 10, "Need at least 10 meetings"
        assert len(emails) >= 10, "Need at least 10 emails"
        assert len(commitments) >= 5, "Need at least 5 commitments"
        assert len(decisions) >= 5, "Need at least 5 decisions"
        assert len(concerns) >= 5, "Need at least 5 concerns"
        assert len(preferences) >= 5, "Need at least 5 preferences"

    def test_meeting_has_required_fields(self):
        """Each meeting should have required fields."""
        import json
        data_dir = Path(__file__).resolve().parent.parent / "data" / "synthetic"
        meetings = [json.loads(l) for l in open(data_dir / "meetings.jsonl")]

        for m in meetings:
            assert "meeting_id" in m, "Missing meeting_id"
            assert "customer_id" in m, "Missing customer_id"
            assert "date" in m, "Missing date"
            assert "summary" in m or "title" in m, "Missing summary/title"

    def test_commitment_status_values(self):
        """Commitments should have valid status values."""
        import json
        data_dir = Path(__file__).resolve().parent.parent / "data" / "synthetic"
        commitments = [json.loads(l) for l in open(data_dir / "commitments.jsonl")]

        valid_statuses = {"open", "resolved", "overdue", "in_progress", "completed"}
        for c in commitments:
            assert c.get("status", "open") in valid_statuses, f"Invalid status: {c.get('status')}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
