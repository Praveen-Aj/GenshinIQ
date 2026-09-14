"""Permanent automated test suite for Phase 9: Best-Effort Knowledge Escalation.

Validates:
1. Local evidence sufficiency check (no escalation when local evidence is fresh and complete)
2. Escalation triggers (missing evidence, stale evidence, explicit latest request, missing entity)
3. Invariant: RETRIEVED != VALIDATED != CURRENT
4. Controlled source hierarchy (Tiers 1 to 5)
5. Timeouts, HTTP errors, rate-limiting, and error handling
6. Irrelevant content rejection (relevance threshold)
7. Stale content rejection on current-version queries
8. Conflict preservation across differing sources
9. Strict provenance preservation (source_name, source_url, source_tier, timestamps, version)
10. Fail-closed safety (Gemini cannot bypass freshness checks)
11. Historical queries allow historical evidence
12. Mandatory validation: older local KB data cannot blindly answer current version queries
13. Realistic end-to-end queries (latest version, what changed, latest characters, older patch)
"""

import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime, timezone
import urllib.error

from backend.models.chat import ChatMessage
from backend.models.knowledge_escalation import (
    EscalatedEvidenceItem,
    EscalationDecision,
    EscalationResult,
    EscalationTrigger,
    FreshnessLevel,
)
from backend.models.query_router import (
    DataSource,
    DetectedEntity,
    EvidenceBundle,
    EvidenceItem,
    EvidenceType,
    QueryIntent,
    RoutingDecision,
)
from backend.models.source_registry import SourceTier, SourceType
from backend.services.knowledge_escalation_service import (
    EscalationProvider,
    knowledge_escalation_service,
)
from backend.services.rag_service import rag_service
from backend.services.version_service import version_service


# ---------------------------------------------------------------------------
# Test Helpers & Mock Providers
# ---------------------------------------------------------------------------

class MockSuccessfulCurrentProvider:
    """Mock provider returning verified CURRENT Tier 1 official patch notes."""
    source_id = "src_hoyoverse_patch_notes"
    source_tier = SourceTier.TIER_1_OFFICIAL
    source_type = SourceType.OFFICIAL

    def fetch(self, query: str, target_version: str = "7.0"):
        return {
            "source_name": "HoYoverse Patch Notes & Maintenance Notices",
            "source_url": "https://genshin.hoyoverse.com/en/news/detail/123",
            "game_version": target_version,
            "content": f"Version {target_version} introduces Aino and new Lunar reaction balance mechanics.",
            "published_at": "2026-09-08T06:00:00Z",
            "raw_content": f"Full official notice text for Version {target_version}.",
        }


class MockStaleProvider:
    """Mock provider returning obsolete/stale evidence from an older patch."""
    source_id = "src_genshin_fandom_wiki"
    source_tier = SourceTier.TIER_4_ESTABLISHED_WIKI
    source_type = SourceType.ESTABLISHED_WIKI

    def fetch(self, query: str, target_version: str = "7.0"):
        return {
            "source_name": "Genshin Fandom Wiki",
            "source_url": "https://genshin-impact.fandom.com/wiki/Patch_5.4",
            "game_version": "5.4",
            "content": "In Version 5.4, Arlecchino remains the dominant Pyro DPS.",
            "published_at": "2025-01-01T00:00:00Z",
        }


class MockIrrelevantProvider:
    """Mock provider returning content unrelated to the query."""
    source_id = "src_hoyoverse_patch_notes"
    source_tier = SourceTier.TIER_1_OFFICIAL
    source_type = SourceType.OFFICIAL

    def fetch(self, query: str, target_version: str = "7.0"):
        return {
            "source_name": "HoYoverse Official",
            "source_url": "https://genshin.hoyoverse.com/en/news/merchandise",
            "game_version": target_version,
            "content": "Official soundtrack concert merchandise is now available in the store.",
            "published_at": "2026-09-08T00:00:00Z",
        }


class MockTimeoutProvider:
    """Mock provider simulating a network timeout."""
    source_id = "src_hoyoverse_patch_notes"
    source_tier = SourceTier.TIER_1_OFFICIAL
    source_type = SourceType.OFFICIAL

    def fetch(self, query: str, target_version: str = "7.0"):
        raise TimeoutError("Connection to external provider timed out after 5.0s")


class MockHttpErrorProvider:
    """Mock provider simulating an HTTP 503 error."""
    source_id = "src_hoyoverse_patch_notes"
    source_tier = SourceTier.TIER_1_OFFICIAL
    source_type = SourceType.OFFICIAL

    def fetch(self, query: str, target_version: str = "7.0"):
        raise urllib.error.HTTPError(
            url="https://genshin.hoyoverse.com/news",
            code=503,
            msg="Service Temporarily Unavailable",
            hdrs={},
            fp=None,
        )


@pytest.fixture(autouse=True)
def cleanup_mock_providers():
    """Ensure mock providers are cleared after each test."""
    yield
    knowledge_escalation_service.clear_mock_providers()


# ===========================================================================
# 1. Escalation Decision & Trigger Tests
# ===========================================================================

class TestEscalationTriggers:
    """Tests evaluating when escalation should and should not trigger."""

    def test_sufficient_local_evidence_no_escalation(self):
        """When local evidence is fresh and matches current version, do NOT escalate."""
        current_ver = version_service.get_current_version().version

        bundle = EvidenceBundle(
            items=[
                EvidenceItem(
                    source=DataSource.CANONICAL_GAME_DATA,
                    evidence_type=EvidenceType.CANONICAL_GAME_FACT,
                    content=f"Furina is a 5-star Hydro Sword character introduced in v4.2. Current patch v{current_ver}.",
                    entity_name="Furina",
                    is_stale=False,
                    game_version=current_ver,
                )
            ],
            is_sufficient=True,
        )
        routing = RoutingDecision(
            primary_intent=QueryIntent.BASIC_GAME_FACT,
            reasoning="Basic game fact for Furina",
        )

        decision = knowledge_escalation_service.evaluate_escalation(
            "What is Furina's element?",
            routing,
            bundle,
            [DetectedEntity(entity_type="character", name="Furina")],
        )

        assert decision.should_escalate is False
        assert decision.trigger is None

    def test_no_local_evidence_triggers_escalation(self):
        """When local evidence bundle is empty, trigger NO_LOCAL_EVIDENCE."""
        bundle = EvidenceBundle(items=[], is_sufficient=True)
        routing = RoutingDecision(
            primary_intent=QueryIntent.KNOWLEDGE_SEARCH,
            reasoning="Unknown query with no local items",
        )

        decision = knowledge_escalation_service.evaluate_escalation(
            "What are the stats of the new Natlan craftable weapon?",
            routing,
            bundle,
            [],
        )

        assert decision.should_escalate is True
        assert decision.trigger == EscalationTrigger.NO_LOCAL_EVIDENCE

    def test_stale_local_evidence_triggers_escalation(self):
        """When local evidence is explicitly from an older patch on a version-sensitive query, trigger STALE_LOCAL_EVIDENCE."""
        current_ver = version_service.get_current_version().version

        bundle = EvidenceBundle(
            items=[
                EvidenceItem(
                    source=DataSource.KNOWLEDGE_BASE,
                    evidence_type=EvidenceType.THEORYCRAFTING,
                    content="Version 5.4 Abyss meta revolves around Arlecchino overload.",
                    is_stale=True,
                    game_version="5.4",
                )
            ],
            is_sufficient=True,
        )
        routing = RoutingDecision(
            primary_intent=QueryIntent.VERSION_SENSITIVE,
            requires_version_check=True,
            reasoning="Abyss meta changes per patch",
        )

        decision = knowledge_escalation_service.evaluate_escalation(
            "What is the current Spiral Abyss Floor 12 meta?",
            routing,
            bundle,
            [],
        )

        assert decision.should_escalate is True
        assert decision.trigger == EscalationTrigger.STALE_LOCAL_EVIDENCE

    def test_explicit_latest_query_requires_freshness(self):
        """When user asks for 'what changed in the latest version', require current v7.0 data."""
        bundle = EvidenceBundle(
            items=[
                EvidenceItem(
                    source=DataSource.KNOWLEDGE_BASE,
                    evidence_type=EvidenceType.THEORYCRAFTING,
                    content="Kazuha swirl guide from version 5.0.",
                    is_stale=False,
                    game_version="5.0",
                )
            ],
            is_sufficient=True,
        )
        routing = RoutingDecision(
            primary_intent=QueryIntent.VERSION_SENSITIVE,
            requires_version_check=True,
            reasoning="User explicitly asks for latest version changes",
        )

        decision = knowledge_escalation_service.evaluate_escalation(
            "What changed in the latest version update?",
            routing,
            bundle,
            [],
        )

        assert decision.should_escalate is True
        assert decision.trigger == EscalationTrigger.EXPLICIT_CURRENT_REQUEST

    def test_missing_new_entity_triggers_escalation(self):
        """When a character entity is requested but has no local items, trigger MISSING_NEW_ENTITY."""
        bundle = EvidenceBundle(
            items=[
                EvidenceItem(
                    source=DataSource.CANONICAL_GAME_DATA,
                    evidence_type=EvidenceType.CANONICAL_GAME_FACT,
                    content="General game rules",
                )
            ],
            is_sufficient=True,
        )
        routing = RoutingDecision(
            primary_intent=QueryIntent.CHARACTER_BUILD,
            reasoning="Build query for Aino",
        )

        decision = knowledge_escalation_service.evaluate_escalation(
            "How should I build Aino?",
            routing,
            bundle,
            [DetectedEntity(entity_type="character", name="Aino")],
        )

        assert decision.should_escalate is True
        assert decision.trigger == EscalationTrigger.MISSING_NEW_ENTITY


# ===========================================================================
# 2. Validation Gate: RETRIEVED != VALIDATED != CURRENT
# ===========================================================================

class TestValidationGate:
    """Tests validating external content before accepting as usable evidence."""

    @pytest.mark.anyio
    async def test_current_version_evidence_accepted(self):
        """When external source returns verified current version evidence, accept as CURRENT."""
        current_ver = version_service.get_current_version().version
        knowledge_escalation_service.register_mock_provider(
            "src_hoyoverse_patch_notes",
            MockSuccessfulCurrentProvider(),
        )

        decision = EscalationDecision(
            should_escalate=True,
            trigger=EscalationTrigger.EXPLICIT_CURRENT_REQUEST,
            target_query="What changed in the latest patch?",
            target_version=current_ver,
            reason="User query requires current version patch details",
        )

        result = await knowledge_escalation_service.escalate("What changed in the latest patch?", decision)

        assert result.success is True
        assert result.is_current_verified is True
        assert len(result.items) == 1
        assert result.items[0].freshness == FreshnessLevel.CURRENT
        assert result.items[0].retrieval_status == "VALIDATED"
        assert result.items[0].game_version == current_ver
        assert result.items[0].source_tier == SourceTier.TIER_1_OFFICIAL

    @pytest.mark.anyio
    async def test_current_version_evidence_unavailable_fails_closed(self):
        """When external source only has stale v5.4 data for a v7.0 query, fail closed."""
        current_ver = version_service.get_current_version().version
        knowledge_escalation_service.register_mock_provider(
            "src_genshin_fandom_wiki",
            MockStaleProvider(),
        )

        decision = EscalationDecision(
            should_escalate=True,
            trigger=EscalationTrigger.EXPLICIT_CURRENT_REQUEST,
            target_query="What changed in the latest patch?",
            target_version=current_ver,
            reason="User query requires current version patch details",
        )

        result = await knowledge_escalation_service.escalate("What changed in the latest patch?", decision)

        # Invariant: RETRIEVED != VALIDATED != CURRENT
        assert result.success is False
        assert result.is_current_verified is False
        assert "I couldn't verify sufficiently current information" in result.failure_reason
        # Item was marked STALE
        assert any(it.freshness == FreshnessLevel.STALE for it in result.items)

    @pytest.mark.anyio
    async def test_external_source_timeout_controlled_failure(self):
        """When external provider times out, safely record failure and fail closed."""
        knowledge_escalation_service.register_mock_provider(
            "src_hoyoverse_patch_notes",
            MockTimeoutProvider(),
        )

        decision = EscalationDecision(
            should_escalate=True,
            trigger=EscalationTrigger.NO_LOCAL_EVIDENCE,
            target_query="Check latest patch status",
            target_version="7.0",
            reason="Network timeout check",
        )

        result = await knowledge_escalation_service.escalate("Check latest patch status", decision)

        assert result.success is False
        assert any("timeout" in f.lower() for f in result.sources_failed)
        assert "couldn't verify sufficiently current information" in result.failure_reason

    @pytest.mark.anyio
    async def test_external_source_http_error_controlled_failure(self):
        """When external provider returns HTTP 503, safely record failure and fail closed."""
        knowledge_escalation_service.register_mock_provider(
            "src_hoyoverse_patch_notes",
            MockHttpErrorProvider(),
        )

        decision = EscalationDecision(
            should_escalate=True,
            trigger=EscalationTrigger.NO_LOCAL_EVIDENCE,
            target_query="Check latest patch status",
            target_version="7.0",
            reason="HTTP error check",
        )

        result = await knowledge_escalation_service.escalate("Check latest patch status", decision)

        assert result.success is False
        assert any("http 503" in f.lower() for f in result.sources_failed)
        assert "couldn't verify sufficiently current information" in result.failure_reason

    @pytest.mark.anyio
    async def test_external_source_irrelevant_content_rejected(self):
        """When external content has no relevance to query, reject it."""
        knowledge_escalation_service.register_mock_provider(
            "src_hoyoverse_patch_notes",
            MockIrrelevantProvider(),
        )

        decision = EscalationDecision(
            should_escalate=True,
            trigger=EscalationTrigger.NO_LOCAL_EVIDENCE,
            target_query="How does Furina's elemental burst scale with HP?",
            target_version="7.0",
            reason="Query about Furina burst scaling",
        )

        result = await knowledge_escalation_service.escalate(
            "How does Furina's elemental burst scale with HP?",
            decision,
        )

        assert result.success is False
        assert any(it.retrieval_status == "IRRELEVANT_REJECTED" for it in result.items)


# ===========================================================================
# 3. Provenance & Conflict Preservation Tests
# ===========================================================================

class TestProvenanceAndConflict:
    """Tests confirming strict metadata provenance and conflict tracking."""

    @pytest.mark.anyio
    async def test_provenance_metadata_preserved(self):
        """Verify that every escalated item retains full provenance fields."""
        current_ver = version_service.get_current_version().version
        knowledge_escalation_service.register_mock_provider(
            "src_hoyoverse_patch_notes",
            MockSuccessfulCurrentProvider(),
        )

        decision = EscalationDecision(
            should_escalate=True,
            trigger=EscalationTrigger.EXPLICIT_CURRENT_REQUEST,
            target_query="What is the latest version?",
            target_version=current_ver,
            reason="Version query",
        )

        result = await knowledge_escalation_service.escalate("What is the latest version?", decision)

        assert len(result.items) > 0
        item = result.items[0]
        assert item.source_name == "HoYoverse Patch Notes & Maintenance Notices"
        assert item.source_url.startswith("https://")
        assert item.source_tier == SourceTier.TIER_1_OFFICIAL
        assert item.source_type == SourceType.OFFICIAL
        assert item.retrieved_at is not None
        assert item.published_at is not None
        assert item.game_version == current_ver
        assert item.freshness == FreshnessLevel.CURRENT
        assert item.relevance >= 0.25

    @pytest.mark.anyio
    async def test_multiple_source_conflict_preserved(self):
        """When two sources return conflicting recommendations, preserve the conflict."""
        class MockProviderA:
            source_id = "src_kqm_guides"
            source_tier = SourceTier.TIER_2_THEORYCRAFTING
            source_type = SourceType.KQM
            def fetch(self, q, target_version="7.0"):
                return {
                    "source_name": "KQM Theorycrafting Guide",
                    "source_url": "https://keqingmains.com/ayaka",
                    "game_version": target_version,
                    "content": "Ayaka weapon ranking: BIS: Mistsplitter Reforged is undisputed #1.",
                    "published_at": "2026-09-08T00:00:00Z",
                }

        class MockProviderB:
            source_id = "src_genshin_fandom_wiki"
            source_tier = SourceTier.TIER_4_ESTABLISHED_WIKI
            source_type = SourceType.ESTABLISHED_WIKI
            def fetch(self, q, target_version="7.0"):
                return {
                    "source_name": "Wiki Guide",
                    "source_url": "https://genshin-impact.fandom.com/ayaka",
                    "game_version": target_version,
                    "content": "Ayaka weapon ranking: BIS: Haran Geppaku Futsu recommended.",
                    "published_at": "2026-09-08T00:00:00Z",
                }

        knowledge_escalation_service.register_mock_provider("src_kqm_guides", MockProviderA())
        knowledge_escalation_service.register_mock_provider("src_genshin_fandom_wiki", MockProviderB())

        decision = EscalationDecision(
            should_escalate=True,
            trigger=EscalationTrigger.SOURCE_CONFLICT,
            target_query="Best weapon for Ayaka",
            target_version="7.0",
            reason="Conflict verification",
        )

        result = await knowledge_escalation_service.escalate("Best weapon for Ayaka", decision)

        assert result.success is True
        assert len(result.conflicts_detected) > 0
        conflict = result.conflicts_detected[0]
        assert conflict["source_a"] == "KQM Theorycrafting Guide"
        assert conflict["source_b"] == "Wiki Guide"


# ===========================================================================
# 4. Mandatory Old Data Validation (Core Phase 9 Invariant)
# ===========================================================================

class TestMandatoryOldDataValidation:
    """CRITICAL TEST: Verify that when local KB only contains old data (v5.4),
    a version-sensitive query does NOT blindly answer from that old data."""

    @pytest.mark.anyio
    async def test_old_local_data_does_not_blindly_answer_current_query(self):
        """Simulate local KB having only v5.4 Abyss patch notes when live version is v7.0.
        Without valid external v7.0 data, system MUST fail closed."""
        current_ver = version_service.get_current_version().version

        # External escalation returns only stale/unverified data
        knowledge_escalation_service.register_mock_provider(
            "src_genshin_fandom_wiki",
            MockStaleProvider(),
        )

        messages = [
            ChatMessage(role="user", content="What changed in the latest Abyss blessing for this patch?")
        ]

        response = await rag_service.generate_response(messages=messages)

        # Invariant: Must fail closed with controlled explanation
        assert "couldn't verify sufficiently current information" in response.content.lower()
        # Must NOT pretend old data was current
        assert "5.4" not in response.content or "stale" in response.content.lower() or "safety measure" in response.content.lower()

    @pytest.mark.anyio
    @patch("backend.services.gemini_service.gemini_service.generate_content", new_callable=AsyncMock)
    async def test_historical_query_allows_historical_evidence(self, mock_gemini):
        """Historical query (e.g. 'in patch 2.4') is allowed to use historical evidence without failing closed."""
        mock_gemini.return_value = "In patch 2.4, Shenhe and Yun Jin were introduced alongside Enkanomiya."

        messages = [
            ChatMessage(role="user", content="What characters were introduced back in patch 2.4 historically?")
        ]

        response = await rag_service.generate_response(messages=messages)

        # For historical queries, older evidence is legitimate context
        assert "Shenhe" in response.content or "2.4" in response.content
        assert "couldn't verify sufficiently current" not in response.content.lower()


# ===========================================================================
# 5. Realistic End-to-End Query Tests
# ===========================================================================

class TestRealisticEndToEndQueries:
    """End-to-end tests for representative user queries across Phase 8 router + Phase 9 escalation."""

    @pytest.mark.anyio
    @patch("backend.services.gemini_service.gemini_service.generate_content", new_callable=AsyncMock)
    async def test_e2e_query_a_latest_genshin_version(self, mock_gemini):
        """Query A: 'What is the latest Genshin version?'"""
        current_ver = version_service.get_current_version()
        mock_gemini.return_value = f"The current live version is Version {current_ver.version} ('{current_ver.name}')."

        knowledge_escalation_service.register_mock_provider(
            "src_hoyoverse_patch_notes",
            MockSuccessfulCurrentProvider(),
        )

        messages = [ChatMessage(role="user", content="What is the latest Genshin version?")]
        response = await rag_service.generate_response(messages=messages)

        assert current_ver.version in response.content
        assert len(response.citations) > 0

    @pytest.mark.anyio
    @patch("backend.services.gemini_service.gemini_service.generate_content", new_callable=AsyncMock)
    async def test_e2e_query_b_what_changed_in_latest_version(self, mock_gemini):
        """Query B: 'What changed in the latest version?'"""
        mock_gemini.return_value = "Version 7.0 introduced Nod-Khadar, the Lunar reaction system, and new characters."

        knowledge_escalation_service.register_mock_provider(
            "src_hoyoverse_patch_notes",
            MockSuccessfulCurrentProvider(),
        )

        messages = [ChatMessage(role="user", content="What changed in the latest version?")]
        response = await rag_service.generate_response(messages=messages)

        assert "Version 7.0" in response.content or "changed" in response.content.lower()
        assert "VERSION_SENSITIVE" in response.query_intents

    @pytest.mark.anyio
    @patch("backend.services.gemini_service.gemini_service.generate_content", new_callable=AsyncMock)
    async def test_e2e_query_c_what_are_the_latest_characters(self, mock_gemini):
        """Query C: 'What are the latest characters?'"""
        mock_gemini.return_value = "The latest confirmed playable characters include Xilonen, Chasca, and Ororon."

        messages = [ChatMessage(role="user", content="What are the latest characters?")]
        response = await rag_service.generate_response(messages=messages)

        assert len(response.content) > 10
        assert len(response.query_intents) > 0

    @pytest.mark.anyio
    @patch("backend.services.gemini_service.gemini_service.generate_content", new_callable=AsyncMock)
    async def test_e2e_query_d_current_build_for_aino(self, mock_gemini):
        """Query D: 'What is the current build recommendation for Aino?'
        Aino is an unreleased/preview character. Must state preview status and qualify build recommendations."""
        mock_gemini.return_value = (
            "Aino is currently in UNRELEASED_PREVIEW status for Version 7.0. "
            "Canonical kit attributes (Hydro, Claymore) are verified, but live gameplay guides are NOT_APPLICABLE until official release."
        )

        messages = [ChatMessage(role="user", content="What is the current build recommendation for Aino?")]
        response = await rag_service.generate_response(messages=messages)

        assert "Aino" in response.content
        assert "UNRELEASED_PREVIEW" in response.content or "NOT_APPLICABLE" in response.content or "preview" in response.content.lower()

    @pytest.mark.anyio
    @patch("backend.services.gemini_service.gemini_service.generate_content", new_callable=AsyncMock)
    async def test_e2e_query_e_older_historical_patch(self, mock_gemini):
        """Query E: 'Tell me about an older historical patch.'"""
        mock_gemini.return_value = "Version 1.1 'A New Star Approaches' introduced Tartaglia (Childe), Zhongli, and the Unreconciled Stars event."

        messages = [ChatMessage(role="user", content="Tell me about version 1.1 historically.")]
        response = await rag_service.generate_response(messages=messages)

        assert "1.1" in response.content
        assert "couldn't verify sufficiently current" not in response.content.lower()
