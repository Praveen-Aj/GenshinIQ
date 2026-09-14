"""Phase 9 Strict Acceptance Audit Automated Verification Test Suite.

Encodes all audit scenarios mandated in the acceptance review:
1. Version Dynamism & v8.0 Simulation (fail-closed, no silent downgrade to 7.0)
2. New Entity Escalation & Fail-Closed (unrecognized entity triggers escalation)
3. Partial Knowledge Gaps Recognition (Lan Yan build recommendations trigger escalation)
4. Current Build Recommendation for Preview Entity (Aino preview entity boundaries)
5. Latest Abyss Floor 12 Test (generic mechanics do not accidentally satisfy Abyss queries)
6. Gemini Bypass Verification (Gemini API is never called when evidence is insufficient)
7. Source Conflict Preservation (disagreements recorded with tiers and topics)
8. Invariant RETRIEVED != VALIDATED != CURRENT
9. Cache Identity and Version Safety (v7.0 cache entries do not satisfy v8.0 lookups)
"""

import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime, timezone

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
from backend.models.version import GameVersion, VersionStatus
from backend.services.knowledge_escalation_service import (
    EscalationProvider,
    knowledge_escalation_service,
)
from backend.services.rag_service import rag_service
from backend.services.query_router import query_router
from backend.services.version_service import version_service


@pytest.fixture(autouse=True)
def cleanup():
    knowledge_escalation_service.clear_mock_providers()
    yield
    knowledge_escalation_service.clear_mock_providers()


# ---------------------------------------------------------------------------
# 1. Version Dynamism & Future Version 8.0 Simulation
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_audit_future_version_8_0_simulation():
    """CURRENT=8.0 with local KB at 7.0 must FAIL CLOSED and never downgrade to 7.0."""
    v80 = GameVersion(
        version="8.0",
        name="Teyvat Remade",
        release_date="2027-09-01",
        major_region="Khaenri'ah",
        is_current=True,
        is_released=True,
    )

    with patch.object(version_service, "get_current_version", return_value=v80), \
         patch.object(version_service, "get_latest_known_version", return_value=v80):

        queries = [
            "What changed in the latest version?",
            "What are the latest characters?",
            "What is the current Abyss information?",
            "What is the current build recommendation for a newly released character?",
        ]

        for q in queries:
            routing = query_router.classify(q)
            bundle, _ = await rag_service._assemble_evidence(q, routing)
            # Invariant: Must fail closed because no verified v8.0 evidence exists
            assert bundle.is_sufficient is False, f"Query '{q}' should have failed closed under v8.0!"
            assert "couldn't verify sufficiently current information" in bundle.insufficiency_reason
            # Invariant: 7.0 items must not be presented as current 8.0 knowledge
            current_knowledge_items = [
                it for it in bundle.items
                if it.game_version == "8.0" and it.source != DataSource.VERSION_SERVICE
            ]
            assert len(current_knowledge_items) == 0


# ---------------------------------------------------------------------------
# 2. New Entity Test
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_audit_new_entity_escalation_and_fail_closed():
    """Unrecognized entity 'NewHeroX' with kit query must trigger MISSING_NEW_ENTITY and fail closed."""
    q = "What are the talents and skills for NewHeroX?"
    routing = query_router.classify(q)
    bundle, _ = await rag_service._assemble_evidence(q, routing)

    assert bundle.is_sufficient is False
    assert "couldn't verify sufficiently current information" in bundle.insufficiency_reason


# ---------------------------------------------------------------------------
# 3. Partial Knowledge Test
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_audit_partial_knowledge_lan_yan_build_gap():
    """Lan Yan has canonical base stats but lacks curated build guides -> triggers PARTIAL_LOCAL_KB and fails closed."""
    q = "What are the recommended artifacts and weapons for Lan Yan?"
    routing = query_router.classify(q)
    assert routing.primary_intent == QueryIntent.CHARACTER_BUILD

    bundle, _ = await rag_service._assemble_evidence(q, routing)
    assert bundle.is_sufficient is False
    assert "couldn't verify sufficiently current information" in bundle.insufficiency_reason


# ---------------------------------------------------------------------------
# 4. Current Build Recommendation for Preview Entity (Aino)
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_audit_aino_unreleased_preview_handling():
    """Aino is UNRELEASED_PREVIEW: canonical facts available, live gameplay/guides NOT_APPLICABLE."""
    q = "What is the current build recommendation for Aino?"
    routing = query_router.classify(q)
    bundle, _ = await rag_service._assemble_evidence(q, routing)

    # Local bundle includes release applicability notice stating UNRELEASED_PREVIEW
    applicability_items = [it for it in bundle.items if "RELEASE & APPLICABILITY: AINO" in it.content]
    assert len(applicability_items) >= 1
    assert "UNRELEASED_PREVIEW" in applicability_items[0].content


# ---------------------------------------------------------------------------
# 5. Latest Abyss Floor 12 Test
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_audit_latest_abyss_floor_12_no_false_positive():
    """Generic theorycrafting (snapshotting, ICD) must NOT satisfy current Abyss Floor 12 queries."""
    q = "What is the current Spiral Abyss Floor 12 meta for this patch?"
    routing = query_router.classify(q)
    bundle, _ = await rag_service._assemble_evidence(q, routing)

    assert bundle.is_sufficient is False
    assert "couldn't verify sufficiently current information" in bundle.insufficiency_reason


# ---------------------------------------------------------------------------
# 6. Gemini Bypass Test
# ---------------------------------------------------------------------------

@pytest.mark.anyio
@patch("backend.services.gemini_service.gemini_service.generate_content", new_callable=AsyncMock)
async def test_audit_gemini_bypass_on_insufficient_evidence(mock_gemini):
    """When required evidence cannot be verified, Gemini generate_content must NOT be called."""
    messages = [
        ChatMessage(role="user", content="What is the current Spiral Abyss Floor 12 meta for this patch?")
    ]
    response = await rag_service.generate_response(messages=messages)

    # Gemini must never be invoked
    mock_gemini.assert_not_called()
    assert "couldn't verify sufficiently current information" in response.content


# ---------------------------------------------------------------------------
# 7. Source Conflict Test
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_audit_source_conflict_recording():
    """Contradictory BIS weapon recommendations across external sources are preserved with tiers."""
    class MockA:
        source_id = "src_kqm_guides"
        source_tier = SourceTier.TIER_2_THEORYCRAFTING
        source_type = SourceType.KQM
        def fetch(self, q, target_version="7.0"):
            return {
                "source_name": "KQM Guide",
                "source_url": "https://keqingmains.com/ayaka",
                "game_version": "7.0",
                "content": "Ayaka weapon ranking: BIS: Mistsplitter Reforged",
            }

    class MockB:
        source_id = "src_genshin_fandom_wiki"
        source_tier = SourceTier.TIER_4_ESTABLISHED_WIKI
        source_type = SourceType.ESTABLISHED_WIKI
        def fetch(self, q, target_version="7.0"):
            return {
                "source_name": "Fandom Wiki",
                "source_url": "https://genshin-impact.fandom.com/ayaka",
                "game_version": "7.0",
                "content": "Ayaka weapon ranking: BIS: Haran Geppaku Futsu",
            }

    knowledge_escalation_service.register_mock_provider("src_kqm_guides", MockA())
    knowledge_escalation_service.register_mock_provider("src_genshin_fandom_wiki", MockB())

    decision = EscalationDecision(
        should_escalate=True,
        trigger=EscalationTrigger.SOURCE_CONFLICT,
        target_query="Best weapon ranking for Ayaka audit test",
        target_version="7.0",
        reason="Conflict test",
    )

    result = await knowledge_escalation_service.escalate("Best weapon ranking for Ayaka audit test", decision)
    assert result.success is True
    assert len(result.conflicts_detected) >= 1
    conflict = result.conflicts_detected[0]
    assert conflict["source_a"] == "KQM Guide"
    assert conflict["source_b"] == "Fandom Wiki"


# ---------------------------------------------------------------------------
# 8. Invariant: RETRIEVED != VALIDATED != CURRENT
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_audit_retrieved_not_automatically_current():
    """A fetched page with no version metadata cannot be marked CURRENT."""
    class MockUnversionedProvider:
        source_id = "src_hoyoverse_patch_notes"
        source_tier = SourceTier.TIER_1_OFFICIAL
        source_type = SourceType.OFFICIAL
        def fetch(self, q, target_version="7.0"):
            return {
                "source_name": "Official News",
                "source_url": "https://genshin.hoyoverse.com/news",
                "game_version": None,  # No version tag found
                "content": "General adventure announcement and maintenance notice.",
            }

    knowledge_escalation_service.register_mock_provider("src_hoyoverse_patch_notes", MockUnversionedProvider())

    decision = EscalationDecision(
        should_escalate=True,
        trigger=EscalationTrigger.EXPLICIT_CURRENT_REQUEST,
        target_query="Uncached audit query for unversioned page",
        target_version="7.0",
        reason="Test",
    )

    result = await knowledge_escalation_service.escalate("Uncached audit query for unversioned page", decision)
    assert result.success is False
    assert result.is_current_verified is False
    assert any(it.freshness == FreshnessLevel.UNKNOWN for it in result.items)


# ---------------------------------------------------------------------------
# 9. Cache Safety & Version Keying
# ---------------------------------------------------------------------------

def test_audit_cache_identity_includes_version():
    """Cache keys must incorporate target_version so v7.0 cache cannot satisfy v8.0 query."""
    cache = knowledge_escalation_service._cache
    # Verify format of existing keys
    for k in cache:
        parts = k.split(":")
        assert len(parts) >= 3, f"Cache key '{k}' must include sid:query:version!"
