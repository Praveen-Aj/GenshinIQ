"""Phase 10: Citation and Grounding System Tests.

Tests:
1. Four-level citation assembly (DATASET, SOURCE, CALCULATION, ACCOUNT).
2. Automated claim-evidence extraction and verification.
3. Grounding scoring and status classification (FULLY_GROUNDED, PARTIALLY_GROUNDED, UNGROUNDED).
4. Non-decorative citation relevance filtering.
5. Integration with RAG pipeline and ChatResponse models.
"""

import pytest
from unittest.mock import AsyncMock, patch

from backend.models.chat import ChatMessage, ChatResponse, Citation
from types import SimpleNamespace

from backend.models.grounding import (
    CitationType,
    ConfidenceLevel,
    GroundingStatus,
    GroundingVerificationResult,
    SupportedClaim,
)
from backend.models.query_router import (
    DataSource,
    EvidenceBundle,
    EvidenceItem,
    EvidenceType,
    QueryIntent,
    RoutingDecision,
)
from backend.services.grounding_service import GroundingService, grounding_service
from backend.services.rag_service import rag_service


# ===================================================================
# 1. Four-Level Citation Assembly Tests
# ===================================================================

def test_build_dataset_citation():
    """Verify CitationType.DATASET citation structure for canonical entities."""
    citation = grounding_service.build_dataset_citation(
        entity_name="Kaedehara Kazuha",
        entity_type="character",
        attributes_summary="5★ Anemo Sword | Base ATK Lv90: 297",
        game_version="7.0",
    )
    assert citation.citation_type == CitationType.DATASET.value
    assert citation.source_name == "Canonical Game Database"
    assert citation.confidence == ConfidenceLevel.HIGH.value
    assert citation.authority_tier == 1
    assert citation.character == "Kaedehara Kazuha"
    assert "/api/characters/kaedehara_kazuha" in citation.source_url
    assert citation.claim_supported is not None


def test_build_account_citation():
    """Verify CitationType.ACCOUNT citation structure for user showcase."""
    citation = grounding_service.build_account_citation(
        uid="817739968",
        character_name="Kaedehara Kazuha",
        build_summary="Kaedehara Kazuha Lv.90 C2",
    )
    assert citation.citation_type == CitationType.ACCOUNT.value
    assert "Enka.Network" in citation.source_name
    assert "817739968" in citation.source_url
    assert citation.character == "Kaedehara Kazuha"
    assert citation.confidence == ConfidenceLevel.HIGH.value
    assert citation.authority_tier == 1


def test_build_calculation_citation():
    """Verify CitationType.CALCULATION citation structure for stat engine."""
    citation = grounding_service.build_calculation_citation(
        character_name="Hu Tao",
        calculation_summary="Total HP: 31450, Total ATK: 1250, CR: 71.4%, CD: 210.5%, CV: 215.3",
        formula_reference="Additive Combat Stat Scaling",
    )
    assert citation.citation_type == CitationType.CALCULATION.value
    assert "Stat Engine" in citation.source_name
    assert citation.character == "Hu Tao"
    assert "Formula: Additive Combat Stat Scaling" in citation.snippet
    assert citation.confidence == ConfidenceLevel.HIGH.value


def test_build_source_citation_fresh_and_stale():
    """Verify CitationType.SOURCE citation structure for knowledge docs."""
    fresh_doc = SimpleNamespace(
        id="guide_kazuha_v70",
        title="Kazuha Complete Guide",
        summary="Comprehensive guide for Kazuha.",
        metadata=SimpleNamespace(
            source="KeqingMains",
            source_url="https://keqingmains.com/kazuha",
            canonical_url="https://keqingmains.com/kazuha",
            character="Kaedehara Kazuha",
            topic="Character Guide",
            game_version="7.0",
            source_id="src_kqm_guides",
            source_type="theorycrafting",
            authority_tier=2,
            content_hash="mock_hash_1",
            is_stale=False,
        ),
    )
    fresh_citation = grounding_service.build_source_citation(fresh_doc)
    assert fresh_citation.citation_type == CitationType.SOURCE.value
    assert fresh_citation.confidence == ConfidenceLevel.HIGH.value
    assert fresh_citation.source_name == "KeqingMains"
    assert fresh_citation.authority_tier == 2

    # Stale document drops confidence to MEDIUM
    stale_doc = SimpleNamespace(
        id="guide_bennett_v50",
        title="Bennett Guide",
        summary="Older guide.",
        metadata=SimpleNamespace(
            source="KeqingMains",
            source_url="https://keqingmains.com/bennett",
            canonical_url="https://keqingmains.com/bennett",
            character="Bennett",
            topic="Character Guide",
            game_version="5.0",
            source_id="src_kqm_guides",
            source_type="theorycrafting",
            authority_tier=2,
            content_hash="mock_hash_2",
            is_stale=True,
        ),
    )
    stale_citation = grounding_service.build_source_citation(stale_doc)
    assert stale_citation.citation_type == CitationType.SOURCE.value
    assert stale_citation.confidence == ConfidenceLevel.MEDIUM.value


# ===================================================================
# 2. Automated Claim Extraction & Verification Tests
# ===================================================================

def test_claim_extraction_numeric_and_attributes():
    """Verify extraction of percentages, base stats, CV, and constellations."""
    service = GroundingService()
    text = (
        "Hu Tao is a Pyro character. At Lv. 90, she has Base ATK: 106 and Base HP: 15552. "
        "With Staff of Homa, her Total ATK: 1250 and she achieves 71.4% CRIT Rate, "
        "+180.2% CRIT DMG, and a Crit Value: 215.4 at C1."
    )
    claims = service._extract_claims_from_text(text)
    assert any("71.4%" in c for c in claims)
    assert any("Base ATK" in c for c in claims)
    assert any("Base HP" in c for c in claims)
    assert any("Crit Value" in c or "CV" in c for c in claims)
    assert any("C1" in c for c in claims)
    assert any("Pyro" in c for c in claims)


def test_grounding_verification_fully_grounded():
    """Verify fully grounded result when response assertions match evidence items."""
    bundle = EvidenceBundle(
        items=[
            EvidenceItem(
                source=DataSource.CANONICAL_GAME_DATA,
                evidence_type=EvidenceType.CANONICAL_GAME_FACT,
                content="Kaedehara Kazuha is an Anemo character. Base ATK (Lv 90): 297. Base HP: 13348.",
                entity_name="Kaedehara Kazuha",
                game_version="7.0",
            ),
            EvidenceItem(
                source=DataSource.STAT_ENGINE,
                evidence_type=EvidenceType.DETERMINISTIC_CALCULATION,
                content="Calculated stats: Total ATK: 1450 | CRIT Rate: 65.4% | Energy Recharge: 160.0%",
                entity_name="Kaedehara Kazuha",
            ),
        ],
        sources_consulted=[DataSource.CANONICAL_GAME_DATA, DataSource.STAT_ENGINE],
        is_sufficient=True,
    )

    response_text = (
        "Kaedehara Kazuha is an Anemo character. His Lv. 90 Base ATK: 297. "
        "With his current setup, his Total ATK: 1450 and CRIT Rate is 65.4% with 160.0% Energy Recharge."
    )

    result = grounding_service.verify_grounding(response_text, bundle)
    assert result.status == GroundingStatus.FULLY_GROUNDED
    assert result.score >= 0.80
    assert len(result.claims) > 0
    assert result.grounded_claims >= 3
    assert len(result.unsupported_claims) == 0


def test_grounding_verification_partially_grounded_and_ungrounded():
    """Verify partially grounded status when response includes ungrounded fabricated numbers."""
    bundle = EvidenceBundle(
        items=[
            EvidenceItem(
                source=DataSource.CANONICAL_GAME_DATA,
                evidence_type=EvidenceType.CANONICAL_GAME_FACT,
                content="Kazuha Base ATK: 297.",
                entity_name="Kaedehara Kazuha",
            )
        ],
        sources_consulted=[DataSource.CANONICAL_GAME_DATA],
        is_sufficient=True,
    )

    # Response contains 1 verified stat and 3 invented numbers
    fabricated_response = (
        "Kazuha Base ATK: 297. However, his team DPS is 98.4% higher and his CRIT Rate: 95.5% with 280.0% CRIT DMG."
    )

    result = grounding_service.verify_grounding(fabricated_response, bundle)
    # The score should be low and classified as partially grounded or ungrounded
    assert result.status in (GroundingStatus.PARTIALLY_GROUNDED, GroundingStatus.UNGROUNDED)
    assert result.score < 0.80
    assert len(result.unsupported_claims) > 0


def test_grounding_empty_response():
    """Verify empty response returns UNGROUNDED."""
    bundle = EvidenceBundle(items=[], sources_consulted=[], is_sufficient=True)
    result = grounding_service.verify_grounding("", bundle)
    assert result.status == GroundingStatus.UNGROUNDED
    assert result.score == 0.0


# ===================================================================
# 3. Non-Decorative Citation Relevance Filtering Tests
# ===================================================================

def test_filter_meaningful_citations_prunes_unrelated():
    """Verify unreferenced citations are pruned while relevant citations are kept."""
    relevant_citation = Citation(
        source_name="Canonical Game Database",
        source_url="/api/characters/kaedehara_kazuha",
        snippet="5★ Anemo Sword",
        character="Kaedehara Kazuha",
        topic="Canonical Character Specifications",
        citation_type="dataset",
    )
    unrelated_citation = Citation(
        source_name="KeqingMains",
        source_url="https://keqingmains.com/xinyan",
        snippet="Xinyan physical shield guide",
        character="Xinyan",
        topic="Xinyan Guide",
        citation_type="source",
    )
    account_citation = Citation(
        source_name="Enka.Network Account Showcase",
        source_url="https://enka.network/u/817739968",
        snippet="User build details",
        citation_type="account",
    )

    response_text = "Kaedehara Kazuha is a 5-star Anemo sword user with strong grouping."
    claims = [
        SupportedClaim(
            claim_text="Anemo",
            evidence_text="Anemo Sword",
            evidence_type=EvidenceType.CANONICAL_GAME_FACT,
            source="canonical_game_data",
            citation_type=CitationType.DATASET,
            verified=True,
        )
    ]

    filtered = grounding_service.filter_meaningful_citations(
        [relevant_citation, unrelated_citation, account_citation],
        response_text,
        claims,
    )

    assert relevant_citation in filtered
    assert account_citation in filtered  # ACCOUNT citations are always kept
    assert unrelated_citation not in filtered  # Xinyan was not mentioned or claimed


# ===================================================================
# 4. RAG Service End-to-End Grounding Integration Tests
# ===================================================================

@pytest.mark.asyncio
async def test_rag_service_attaches_grounding_metadata():
    """Verify RAGService returns grounding_status, grounding_score, and claims in ChatResponse."""
    with patch("backend.services.gemini_service.gemini_service.generate_content", new_callable=AsyncMock) as mock_gemini:
        mock_gemini.return_value = (
            "Kaedehara Kazuha is a 5-star Anemo character. At Lv. 90, his Base ATK is 297."
        )

        messages = [ChatMessage(role="user", content="What is Kazuha's element and base ATK?")]
        response: ChatResponse = await rag_service.generate_response(messages)

        assert response.grounding_status in ("fully_grounded", "partially_grounded")
        assert response.grounding_score is not None
        assert response.grounding_score > 0.0
        assert isinstance(response.claims, list)
        assert any(c.citation_type == "dataset" for c in response.citations)


@pytest.mark.asyncio
async def test_rag_service_insufficient_evidence_fails_ungrounded():
    """Verify fail-closed insufficient evidence returns ungrounded status."""
    messages = [ChatMessage(role="user", content="How is my Hu Tao build?")]
    # Without UID, account data is required but missing -> fail closed
    response: ChatResponse = await rag_service.generate_response(messages, uid=None)

    assert response.grounding_status == "ungrounded"
    assert response.grounding_score == 0.0
    assert len(response.claims) == 0


@pytest.mark.asyncio
async def test_rag_service_account_query_attaches_account_citations():
    """Verify account build reviews generate ACCOUNT and CALCULATION citations."""
    with patch("backend.services.gemini_service.gemini_service.generate_content", new_callable=AsyncMock) as mock_gemini:
        mock_gemini.return_value = (
            "Your Kaedehara Kazuha is Lv. 90 C2 with Freedom-Sworn. "
            "His Total ATK is 1450 with 160% ER and 850 EM."
        )

        messages = [ChatMessage(role="user", content="Review my Kazuha build")]
        response: ChatResponse = await rag_service.generate_response(messages, uid="817739968")

        assert response.grounding_status in ("fully_grounded", "partially_grounded")
        types = [c.citation_type for c in response.citations]
        assert CitationType.ACCOUNT.value in types


@pytest.mark.asyncio
async def test_rag_service_weapon_comparison_attaches_calculation_citations():
    """Verify weapon comparisons generate CALCULATION citations from stat engine."""
    with patch("backend.services.gemini_service.gemini_service.generate_content", new_callable=AsyncMock) as mock_gemini:
        mock_gemini.return_value = (
            "Comparing Freedom-Sworn vs Iron Sting on Kaedehara Kazuha: Freedom-Sworn grants higher Base ATK."
        )

        messages = [ChatMessage(role="user", content="Compare Freedom-Sworn vs Iron Sting on Kazuha")]
        response: ChatResponse = await rag_service.generate_response(messages)

        types = [c.citation_type for c in response.citations]
        assert CitationType.CALCULATION.value in types


def test_grounding_score_calculation_boundary_conditions():
    """Test boundary conditions for grounding score and status categorization."""
    bundle = EvidenceBundle(
        items=[
            EvidenceItem(
                source=DataSource.CANONICAL_GAME_DATA,
                evidence_type=EvidenceType.CANONICAL_GAME_FACT,
                content="Hu Tao Base ATK: 106, Base HP: 15552, Element: Pyro, Weapon: Polearm.",
                entity_name="Hu Tao",
            )
        ],
        sources_consulted=[DataSource.CANONICAL_GAME_DATA],
        is_sufficient=True,
    )

    # 1. Pure conversational text with no numbers/hard assertions -> fully grounded
    conv_result = grounding_service.verify_grounding("Hello! How can I help you explore Teyvat today?", bundle)
    assert conv_result.status == GroundingStatus.FULLY_GROUNDED
    assert conv_result.score == 1.0

    # 2. Exactly 80% supported -> fully grounded
    text_80 = "Hu Tao is a Pyro character. Base ATK: 106. Base HP: 15552. Polearm user. Invented: 99.9% damage."
    res_80 = grounding_service.verify_grounding(text_80, bundle)
    assert res_80.score >= 0.80
    assert res_80.status == GroundingStatus.FULLY_GROUNDED

    # 3. 50% to 79% supported -> partially grounded
    text_partial = "Hu Tao is a Pyro character. Base ATK: 106. Fake stat 1: 50.5% bonus. Fake stat 2: 88.8% CRIT."
    res_partial = grounding_service.verify_grounding(text_partial, bundle)
    assert 0.50 <= res_partial.score < 0.80
    assert res_partial.status == GroundingStatus.PARTIALLY_GROUNDED
    assert len(res_partial.warnings) > 0

    # 4. Under 50% supported -> ungrounded
    text_ungrounded = "Hu Tao has 11.1% stat, 22.2% stat, 33.3% stat, 44.4% stat, 55.5% stat."
    res_ungrounded = grounding_service.verify_grounding(text_ungrounded, bundle)
    assert res_ungrounded.score < 0.50
    assert res_ungrounded.status == GroundingStatus.UNGROUNDED


def test_supported_claim_contract_serialization():
    """Verify SupportedClaim model serialization conforms to the Phase 10 contract."""
    claim = SupportedClaim(
        claim_text="71.4% CRIT Rate",
        evidence_text="CRIT Rate: 71.4%",
        evidence_type=EvidenceType.DETERMINISTIC_CALCULATION,
        source="stat_engine",
        version="7.0",
        confidence=ConfidenceLevel.HIGH,
        citation_type=CitationType.CALCULATION,
        verified=True,
        verification_notes="Matched stat engine calculation output",
    )
    dump = claim.model_dump()
    assert dump["claim_text"] == "71.4% CRIT Rate"
    assert dump["confidence"] == "high"
    assert dump["citation_type"] == "calculation"
    assert dump["verified"] is True

