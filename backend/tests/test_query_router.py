"""Permanent automated test suite for Phase 8: Query Routing & Tool Orchestration.

Tests cover:
1. Granular intent classification (12 intents)
2. Game entity detection (characters, weapons, artifacts)
3. Source and tool requirement determination
4. Deterministic stat engine routing
5. Fail-closed safety behavior when required evidence is missing
6. Routing transparency fields in ChatResponse
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.chat import ChatMessage
from backend.models.query_router import (
    DataSource,
    EvidenceType,
    QueryIntent,
)
from backend.services.query_router import query_router
from backend.services.rag_service import rag_service

client = TestClient(app)


# ===========================================================================
# 1. Intent Classification Tests
# ===========================================================================

class TestQueryClassification:
    """Verify granular intent classification across different query types."""

    def test_basic_game_fact(self):
        decision = query_router.classify("What is Furina's element?")
        assert decision.primary_intent == QueryIntent.BASIC_GAME_FACT
        assert DataSource.CANONICAL_GAME_DATA in decision.required_sources

    def test_basic_game_fact_base_stats(self):
        decision = query_router.classify("What is Raiden Shogun's base ATK at level 90?")
        assert decision.primary_intent in (QueryIntent.BASIC_GAME_FACT, QueryIntent.STAT_CALCULATION)
        assert DataSource.CANONICAL_GAME_DATA in decision.required_sources

    def test_character_build(self):
        decision = query_router.classify("How should I build Nahida?")
        assert decision.primary_intent == QueryIntent.CHARACTER_BUILD
        assert DataSource.CANONICAL_GAME_DATA in decision.required_sources
        assert DataSource.KNOWLEDGE_BASE in decision.required_sources

    def test_account_build_review(self):
        decision = query_router.classify("Is my Arlecchino build good?", uid="817739968")
        assert decision.primary_intent == QueryIntent.ACCOUNT_BUILD_REVIEW
        assert decision.requires_account_data is True
        assert DataSource.ACCOUNT_SHOWCASE in decision.required_sources
        assert DataSource.STAT_ENGINE in decision.required_sources

    def test_account_build_review_alternate_phrasing(self):
        decision = query_router.classify("Rate my Kazuha build", uid="817739968")
        assert decision.primary_intent == QueryIntent.ACCOUNT_BUILD_REVIEW
        assert decision.requires_account_data is True

    def test_weapon_comparison(self):
        decision = query_router.classify("Which weapon is better: Mistplitter Reforged or Amenoma Kageuchi?")
        assert decision.primary_intent == QueryIntent.WEAPON_COMPARISON
        assert decision.requires_stat_engine is True
        assert DataSource.STAT_ENGINE in decision.required_sources

    def test_artifact_analysis(self):
        decision = query_router.classify("Should I swap my artifact goblet for higher crit value?")
        assert decision.primary_intent == QueryIntent.ARTIFACT_ANALYSIS
        assert decision.requires_stat_engine is True

    def test_stat_calculation(self):
        decision = query_router.classify("Calculate total ATK scaling for Bennett with Aquila Favonia")
        assert decision.primary_intent in (QueryIntent.STAT_CALCULATION, QueryIntent.WEAPON_COMPARISON)
        assert decision.requires_stat_engine is True

    def test_team_building(self):
        decision = query_router.classify("What are the best team comps for Alhaitham?")
        assert decision.primary_intent == QueryIntent.TEAM_BUILDING
        assert DataSource.CANONICAL_GAME_DATA in decision.required_sources
        assert DataSource.KNOWLEDGE_BASE in decision.required_sources

    def test_farming(self):
        decision = query_router.classify("What materials do I need to ascend Raiden Shogun?")
        assert decision.primary_intent == QueryIntent.FARMING
        assert DataSource.CANONICAL_GAME_DATA in decision.required_sources

    def test_version_sensitive(self):
        decision = query_router.classify("What changes were introduced in patch 5.4?")
        assert decision.primary_intent == QueryIntent.VERSION_SENSITIVE
        assert decision.requires_version_check is True
        assert DataSource.VERSION_SERVICE in decision.required_sources

    def test_knowledge_search(self):
        decision = query_router.classify("How does internal cooldown ICD work on elemental reactions?")
        assert decision.primary_intent == QueryIntent.KNOWLEDGE_SEARCH
        assert DataSource.KNOWLEDGE_BASE in decision.required_sources


# ===========================================================================
# 2. Entity Detection Tests
# ===========================================================================

class TestEntityDetection:
    """Verify entity detection for characters, weapons, and artifacts."""

    def test_character_detection(self):
        decision = query_router.classify("What is Furina's best artifact set?")
        char_entities = [e for e in decision.detected_entities if e.entity_type == "character"]
        assert len(char_entities) >= 1
        assert char_entities[0].name == "Furina"

    def test_weapon_detection(self):
        decision = query_router.classify("Compare Engulfing Lightning vs The Catch")
        weapon_entities = [e for e in decision.detected_entities if e.entity_type == "weapon"]
        weapon_names = [e.name for e in weapon_entities]
        assert "Engulfing Lightning" in weapon_names
        assert "The Catch" in weapon_names

    def test_multi_entity_detection(self):
        decision = query_router.classify("Is Aqua Simulacra good on Yelan with Emblem of Severed Fate?")
        entities_by_type = {}
        for e in decision.detected_entities:
            entities_by_type.setdefault(e.entity_type, []).append(e.name)
        assert "Yelan" in entities_by_type.get("character", [])
        assert "Aqua Simulacra" in entities_by_type.get("weapon", [])


# ===========================================================================
# 3. Routing Decisions & Source Requirements
# ===========================================================================

class TestSourceRequirements:
    """Verify that required and optional sources match routing rules."""

    def test_account_indicator_without_uid_still_requires_account(self):
        decision = query_router.classify("How is my Arlecchino build?")
        assert decision.requires_account_data is True
        assert DataSource.ACCOUNT_SHOWCASE in decision.required_sources

    def test_general_query_does_not_require_account_sources(self):
        decision = query_router.classify("What is the best weapon for Kazuha?")
        assert decision.requires_account_data is False
        assert DataSource.ACCOUNT_SHOWCASE not in decision.required_sources

    def test_stat_engine_required_for_weapon_comparison(self):
        decision = query_router.classify("Compare Freedom-Sworn and Iron Sting for Kazuha")
        assert decision.requires_stat_engine is True
        assert DataSource.STAT_ENGINE in decision.required_sources


# ===========================================================================
# 4. Fail-Closed & RAG Integration Tests
# ===========================================================================

class TestRAGRoutingIntegration:
    """Test full RAG generation pipeline with Phase 8 routing."""

    @pytest.mark.anyio
    async def test_fail_closed_on_missing_account_data(self):
        """When account data is required but no UID is provided, fail closed safely."""
        messages = [
            ChatMessage(role="user", content="Review my Arlecchino build and tell me what artifacts to swap")
        ]
        # No UID provided -> ACCOUNT_SHOWCASE cannot be fetched
        response = await rag_service.generate_response(messages=messages, uid=None)

        assert "cannot provide a reliable answer" in response.content.lower() or "missing sources" in response.content.lower()
        assert "ACCOUNT_SHOWCASE" in response.content
        assert response.intent == "account"

    @pytest.mark.anyio
    @patch("backend.services.gemini_service.gemini_service.generate_content", new_callable=AsyncMock)
    async def test_successful_grounded_response_with_transparency(self, mock_gemini):
        """Verify that response contains Phase 8 routing transparency metadata."""
        mock_gemini.return_value = "Nahida builds prioritize Elemental Mastery up to 1000 EM."

        messages = [
            ChatMessage(role="user", content="What is the best build for Nahida?")
        ]

        response = await rag_service.generate_response(messages=messages)

        assert response.content == "Nahida builds prioritize Elemental Mastery up to 1000 EM."
        assert len(response.query_intents) > 0
        assert "CHARACTER_BUILD" in response.query_intents
        assert len(response.sources_used) > 0
        assert "CANONICAL_GAME_DATA" in response.sources_used or "KNOWLEDGE_BASE" in response.sources_used
        assert len(response.evidence_types) > 0
        mock_gemini.assert_called_once()

    @pytest.mark.anyio
    @patch("backend.services.gemini_service.gemini_service.generate_content", new_callable=AsyncMock)
    async def test_account_grounded_with_stat_engine(self, mock_gemini):
        """Verify that account queries invoke stat engine and populate transparency."""
        mock_gemini.return_value = "Your Arlecchino has 2,100 ATK and solid 70/180 CRIT ratio."

        messages = [
            ChatMessage(role="user", content="Is my Arlecchino build good?")
        ]

        response = await rag_service.generate_response(messages=messages, uid="817739968")

        assert response.intent == "account"
        assert "ACCOUNT_BUILD_REVIEW" in response.query_intents
        assert "ACCOUNT_SHOWCASE" in response.sources_used
        assert "STAT_ENGINE" in response.sources_used
        mock_gemini.assert_called_once()


# ===========================================================================
# 5. API Endpoint Transparency Test
# ===========================================================================

def test_api_chat_transparency():
    """Verify that POST /api/chat returns query_intents, sources_used, and evidence_types."""
    with patch("backend.services.gemini_service.gemini_service.generate_content", new_callable=AsyncMock) as mock_gemini:
        mock_gemini.return_value = "Raiden Shogun requires around 250% Energy Recharge."

        payload = {
            "messages": [
                {"role": "user", "content": "How much ER does Raiden Shogun need?"}
            ]
        }

        response = client.post("/api/chat", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "content" in data
        assert "query_intents" in data
        assert isinstance(data["query_intents"], list)
        assert "sources_used" in data
        assert isinstance(data["sources_used"], list)
        assert "evidence_types" in data
        assert isinstance(data["evidence_types"], list)
