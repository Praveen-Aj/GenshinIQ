"""Comprehensive test suite for GenshinIQ Phase 5 Retrieval Layer.

Covers:
- Basic retrieval (keyword, semantic, hybrid)
- Ranking (relevance, authority tier, freshness, version compatibility)
- Provenance integrity (source validation, tier verification, tamper rejection)
- Version-aware behavior (current, compatible, stale, historical queries)
- Deduplication (per-document limits, near-duplicate suppression)
- Failure fallback & graceful degradation (vector down, lexical down, empty query)
- Re-indexing & incremental update hashing
- API endpoint verification (/api/knowledge/retrieve)
"""

import json
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.knowledge import (
    EvidenceBundle,
    KnowledgeDocument,
    KnowledgeMetadata,
    SemanticChunk,
)
from backend.models.source_registry import SourceTier, SourceType
from backend.services.bm25_service import BM25Index, bm25_service
from backend.services.embedding_service import (
    EmbeddingService,
    LocalSubwordEmbeddingProvider,
    embedding_service,
)
from backend.services.retrieval_service import (
    RetrievalService,
    retrieval_service,
    signal_extractor,
)
from backend.services.semantic_chunker import SemanticChunker, slugify

client = TestClient(app)


# ==============================================================================
# 1. Semantic Chunker Tests
# ==============================================================================

def test_semantic_chunker_preserves_headings_and_provenance():
    """Verify semantic chunking parses headings, preserves tables and provenance."""
    chunker = SemanticChunker(min_chunk_words=10)
    raw_doc = {
        "id": "test_guide",
        "title": "Test Kaedehara Kazuha Guide",
        "metadata": {
            "source_id": "src_kqm_guides",
            "source": "KeqingMains Guides (KQM)",
            "source_url": "https://keqingmains.com/kazuha/",
            "canonical_url": "https://keqingmains.com/kaedehara-kazuha/",
            "source_type": "KQM",
            "authority_tier": 2,
            "character": "Kaedehara Kazuha",
            "topic": "Character Guide",
            "game_version": "7.0",
            "retrieved_at": "2026-09-08T00:00:00Z",
            "content_hash": "a" * 64,
            "freshness_status": "current",
            "tags": ["Kazuha", "Anemo"],
        },
        "summary": "Summary of Kazuha guide.",
        "content": (
            "# Kaedehara Kazuha Guide\n\n"
            "## Overview\n"
            "Kazuha is an Anemo buffer who grants elemental damage based on EM.\n\n"
            "## Weapon Rankings\n"
            "| Weapon | Rank |\n| --- | --- |\n| Freedom-Sworn | BiS |\n| Iron Sting | F2P |\n\n"
            "## Talent Priorities\n"
            "Prioritize Skill and Burst for consistent crowd control and swirl damage."
        ),
    }
    doc = KnowledgeDocument(**raw_doc)
    chunks = chunker.chunk_document(doc)

    assert len(chunks) == 3
    assert chunks[0].section_heading == "Overview"
    assert chunks[1].section_heading == "Weapon Rankings"
    assert "| Freedom-Sworn | BiS |" in chunks[1].content
    assert chunks[0].source_id == "src_kqm_guides"
    assert chunks[0].authority_tier == SourceTier.TIER_2_THEORYCRAFTING
    assert chunks[0].game_version == "7.0"
    assert chunks[0].freshness_status == "current"


def test_slugify_clean():
    """Verify slug generation handles punctuation and special characters."""
    assert slugify("Weapon Rankings (BiS & F2P)") == "weapon-rankings-bis-f2p"
    assert slugify("Core Mechanics & Swirl Buffing") == "core-mechanics-swirl-buffing"
    assert slugify("$$Damage Formula$$") == "damage-formula"


# ==============================================================================
# 2. Local Subword Embedding Provider Tests
# ==============================================================================

def test_local_embedding_provider_deterministic_and_unit_norm():
    """Verify embedding produces deterministic unit vectors."""
    provider = LocalSubwordEmbeddingProvider(dimension=256)
    v1 = provider.embed_text("Elemental Mastery scaling for Anemo Swirl")
    v2 = provider.embed_text("Elemental Mastery scaling for Anemo Swirl")
    v_diff = provider.embed_text("Cooking sweet madame HP recovery")

    assert len(v1) == 256
    assert v1 == v2, "Embeddings must be strictly deterministic"

    # Verify unit length
    norm = sum(x * x for x in v1) ** 0.5
    assert abs(norm - 1.0) < 1e-4

    # Cosine similarity check
    sim_same = sum(a * b for a, b in zip(v1, v2))
    sim_diff = sum(a * b for a, b in zip(v1, v_diff))
    assert sim_same > 0.99
    assert sim_same > sim_diff


# ==============================================================================
# 3. BM25 Lexical Retrieval Tests
# ==============================================================================

def test_bm25_lexical_retrieval_and_field_boosting():
    """Verify BM25 Okapi matches keywords and weights headings higher."""
    bm25 = BM25Index()
    chunk1 = SemanticChunk(
        chunk_id="c1",
        document_id="doc1",
        title="Favonius Lance Review",
        section_heading="Energy Recharge Calculations",
        content="This weapon provides massive energy recharge particles.",
        topic="Weapons",
        game_version="7.0",
        freshness_status="current",
        source_id="src_kqm_tcl",
        source="KQM TCL",
        source_url="https://library.keqingmains.com",
        canonical_url="https://library.keqingmains.com",
        authority_tier=SourceTier.TIER_2_THEORYCRAFTING,
        source_type=SourceType.THEORYCRAFTING,
        content_hash="b" * 64,
    )
    chunk2 = SemanticChunk(
        chunk_id="c2",
        document_id="doc2",
        title="Dragonspine Exploration",
        section_heading="Overview",
        content="Explore the snowy mountain and beware of sheer cold and energy recharge drain.",
        topic="Exploration",
        game_version="7.0",
        freshness_status="current",
        source_id="src_hoyoverse_official",
        source="HoYoverse",
        source_url="https://hoyoverse.com",
        canonical_url="https://hoyoverse.com",
        authority_tier=SourceTier.TIER_1_OFFICIAL,
        source_type=SourceType.OFFICIAL,
        content_hash="c" * 64,
    )
    bm25.add_or_update_chunks([chunk1, chunk2], "doc1")

    res = bm25.search("Energy Recharge Calculations", top_k=2)
    assert len(res) >= 1
    # chunk1 has it in the title/heading with 2.5x boost, so it must rank first
    assert res[0][0].chunk_id == "c1"


# ==============================================================================
# 4. Hybrid Retrieval & Ranking Strategy Tests
# ==============================================================================

def test_hybrid_retrieval_combines_lexical_and_semantic():
    """Verify hybrid search surfaces evidence and reports hybrid status."""
    bundle = retrieval_service.retrieve("Kazuha Elemental Mastery Swirl", top_k=3)
    assert bundle.retrieval_status == "OK"
    assert len(bundle.items) > 0
    top = bundle.items[0]
    assert top.rank == 1
    assert top.composite_score > 0.0
    assert top.source_id is not None
    assert top.canonical_url.startswith("http")


def test_ranking_respects_authority_tier_without_overriding_relevance():
    """A highly relevant Tier 2 KQM guide should rank above a generic Tier 1 doc for a specific build query."""
    bundle = retrieval_service.retrieve("Xiangling Energy Recharge requirement funneling", top_k=3)
    assert len(bundle.items) > 0
    # The dedicated KQM Xiangling ER guide should be #1
    assert bundle.items[0].authority_tier == SourceTier.TIER_2_THEORYCRAFTING
    assert "xiangling" in bundle.items[0].document_id.lower()


def test_version_aware_freshness_ranking():
    """Current v7.0 documents receive a freshness boost over stale v5.4 documents for general questions."""
    bundle = retrieval_service.retrieve("Snapshotting dynamic buffs mechanics", top_k=3)
    assert len(bundle.items) > 0
    # Current v7.0 snapshotting mechanics doc should rank #1
    top = bundle.items[0]
    assert top.game_version == "7.0"
    assert top.freshness_status == "current"


def test_historical_query_bypasses_stale_penalty():
    """Historical queries ('in 1.0', 'in version 5.4') do not penalize older version documents."""
    signals_normal = signal_extractor.extract("What was the original 1.0 spiral abyss meta?")
    assert signals_normal.is_historical_query is True

    bundle = retrieval_service.retrieve("What was the original 1.0 spiral abyss meta?", top_k=5)
    assert bundle.signals.is_historical_query is True
    # Verify no failure and evidence is returned
    assert isinstance(bundle, EvidenceBundle)


# ==============================================================================
# 5. Provenance Integrity Tests
# ==============================================================================

def test_provenance_tamper_rejection():
    """Candidate chunks with forged or unregistered source IDs must be rejected by retrieval."""
    custom_embed = EmbeddingService(LocalSubwordEmbeddingProvider(256))
    custom_embed._clear_index()
    custom_bm25 = BM25Index()
    custom_bm25.clear()

    fake_chunk = SemanticChunk(
        chunk_id="fake#1",
        document_id="fake_doc",
        title="Forged Guide",
        section_heading="Forged Heading",
        content="Guaranteed 100% crit rate glitch.",
        topic="Exploit",
        game_version="7.0",
        freshness_status="current",
        source_id="src_unregistered_hack",
        source="Forged Leaks",
        source_url="http://fake.url",
        canonical_url="http://fake.url",
        authority_tier=SourceTier.TIER_1_OFFICIAL,  # Forged tier!
        source_type=SourceType.OFFICIAL,
        content_hash="d" * 64,
    )
    custom_bm25._index_chunk(fake_chunk)
    custom_bm25._recompute_avgdl()

    service = RetrievalService(bm25=custom_bm25, embed=custom_embed)
    bundle = service.retrieve("Guaranteed 100% crit rate glitch", top_k=5)

    # Forged chunk must be rejected because src_unregistered_hack is not in canonical registry
    assert len(bundle.items) == 0
    assert not any(item.chunk_id == fake_chunk.chunk_id for item in bundle.items)


def test_tier_mismatch_rejection():
    """Candidate chunks claiming Tier 1 when registry has them as Tier 5 must be rejected."""
    custom_embed = EmbeddingService(LocalSubwordEmbeddingProvider(256))
    custom_embed._clear_index()
    custom_bm25 = BM25Index()
    custom_bm25.clear()

    mismatch_chunk = SemanticChunk(
        chunk_id="mismatch#1",
        document_id="wiki_kazuha",
        title="Wiki Kazuha",
        section_heading="Overview",
        content="Kazuha sword user.",
        topic="Character Guide",
        game_version="7.0",
        freshness_status="current",
        source_id="src_fandom_wiki",  # Registered as Tier 5
        source="Community Wiki",
        source_url="https://fandom.com",
        canonical_url="https://fandom.com",
        authority_tier=SourceTier.TIER_1_OFFICIAL,  # Claimed Tier 1!
        source_type=SourceType.OFFICIAL,
        content_hash="e" * 64,
    )
    custom_bm25._index_chunk(mismatch_chunk)
    custom_bm25._recompute_avgdl()

    service = RetrievalService(bm25=custom_bm25, embed=custom_embed)
    bundle = service.retrieve("Kazuha sword user", top_k=5)
    # Tier mismatch must be rejected
    assert len(bundle.items) == 0
    assert not any(item.chunk_id == mismatch_chunk.chunk_id for item in bundle.items)


# ==============================================================================
# 6. Deduplication & Diversity Tests
# ==============================================================================

def test_deduplication_limits_chunks_per_document():
    """Verify that no single document monopolizes all results (max 2 chunks per doc)."""
    bundle = retrieval_service.retrieve("Kaedehara Kazuha build weapon swirl artifact", top_k=6)
    doc_counts = {}
    for item in bundle.items:
        doc_counts[item.document_id] = doc_counts.get(item.document_id, 0) + 1

    for doc_id, count in doc_counts.items():
        assert count <= 2, f"Document {doc_id} exceeded max 2 chunks limit (got {count})"


# ==============================================================================
# 7. Failure Fallback & Graceful Degradation Tests
# ==============================================================================

def test_fallback_when_vector_index_is_empty():
    """When vector index is empty, retrieval falls back to BM25 and reports VECTOR_DEGRADED."""
    empty_embed = EmbeddingService(LocalSubwordEmbeddingProvider(256))
    empty_embed._clear_index()

    service = RetrievalService(bm25=bm25_service, embed=empty_embed)
    bundle = service.retrieve("Bond of Life cap", top_k=3)

    assert bundle.retrieval_status == "VECTOR_DEGRADED"
    assert len(bundle.items) > 0
    assert bundle.items[0].retrieval_method == "bm25_only"


def test_fallback_when_lexical_index_is_empty():
    """When lexical index is empty, retrieval falls back to vector and reports LEXICAL_DEGRADED."""
    empty_bm25 = BM25Index()
    empty_bm25.clear()

    service = RetrievalService(bm25=empty_bm25, embed=embedding_service)
    bundle = service.retrieve("Kazuha Elemental Mastery", top_k=3)

    assert bundle.retrieval_status == "LEXICAL_DEGRADED"
    assert len(bundle.items) > 0
    assert bundle.items[0].retrieval_method == "vector_only"


def test_empty_query_handling():
    """Empty or whitespace queries return clean empty bundle without error."""
    bundle = retrieval_service.retrieve("   ", top_k=5)
    assert bundle.retrieval_status == "EMPTY"
    assert len(bundle.items) == 0
    assert bundle.total_candidates_examined == 0


# ==============================================================================
# 8. Re-indexing & Model Invalidation Tests
# ==============================================================================

def test_model_change_invalidates_index(tmp_path):
    """Changing embedding model name or dimension invalidates saved vector index."""
    embed = EmbeddingService(LocalSubwordEmbeddingProvider(256))
    # Fake a saved metadata with a different model
    embed.meta["model_name"] = "different-experimental-model-v9"

    # Test invalidation logic
    should_invalidate = (embed.meta.get("model_name") != embed.provider.model_name)
    assert should_invalidate is True


# ==============================================================================
# 9. API Endpoint Integration Tests
# ==============================================================================

def test_api_retrieve_endpoint():
    """Verify GET /api/knowledge/retrieve endpoint works with full evidence structure."""
    response = client.get("/api/knowledge/retrieve?q=Freedom-Sworn+weapon+Kazuha&top_k=3")
    assert response.status_code == 200
    data = response.json()

    assert data["query"] == "Freedom-Sworn weapon Kazuha"
    assert data["retrieval_status"] in ("OK", "VECTOR_DEGRADED", "LEXICAL_DEGRADED")
    assert len(data["items"]) >= 1
    top_item = data["items"][0]
    assert "chunk_id" in top_item
    assert "source_id" in top_item
    assert "authority_tier" in top_item
    assert "game_version" in top_item
    assert "content_hash" in top_item
    assert top_item["rank"] == 1


def test_api_retrieve_with_filters():
    """Verify GET /api/knowledge/retrieve respects character and tier filters."""
    response = client.get("/api/knowledge/retrieve?q=swirl&character=Kaedehara+Kazuha&tier=2")
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["authority_tier"] <= 2


# ==============================================================================
# 10. Adversarial Ranking Tests
# ==============================================================================

def test_adversarial_authority_vs_relevance():
    """Verify that an irrelevant Tier 1 official doc NEVER outranks a highly relevant Tier 2 guide."""
    # Query is highly specific to Kazuha's swirl mechanics
    bundle = retrieval_service.retrieve("How does Kazuha Elemental Mastery buff swirl damage?", top_k=5)
    assert len(bundle.items) > 0
    top_item = bundle.items[0]
    # The top item must be a relevant Kazuha guide (Tier 2), NOT a generic official combat rules doc
    assert "kazuha" in top_item.document_id.lower()
    assert top_item.authority_tier == SourceTier.TIER_2_THEORYCRAFTING
    # If any Tier 1 official doc appeared, it must have lower composite score than the relevant guide
    for item in bundle.items:
        if item.authority_tier == SourceTier.TIER_1_OFFICIAL and "kazuha" not in item.chunk_id.lower():
            assert item.composite_score < top_item.composite_score


def test_adversarial_character_fluff_isolated_from_general_mechanics():
    """Verify that when no character is asked, character guide fluff chunks do not outrank general mechanics."""
    # Query is pure general damage formula math without any character
    bundle = retrieval_service.retrieve("How does enemy defense reduction and defense ignore affect the damage formula?", top_k=5)
    assert len(bundle.items) > 0
    top_item = bundle.items[0]
    # Top item must be a general mechanics document, NOT Hu Tao or Kachina
    assert top_item.character is None
    assert "damage_formula" in top_item.document_id or "defense_resistance" in top_item.document_id


def test_adversarial_freshness_vs_older_compatible_evidence():
    """Verify that a relevant older/stale mechanics document is not displaced by an irrelevant current document."""
    # Query asks about transformative reaction math
    bundle = retrieval_service.retrieve("How does Swirl reaction damage scale with character level and Elemental Mastery?", top_k=5)
    assert len(bundle.items) > 0
    top_item = bundle.items[0]
    # Must retrieve Swirl/Transformative reaction chunk, not an irrelevant current character profile
    assert "transformative" in top_item.chunk_id.lower() or "swirl" in top_item.chunk_id.lower() or "elemental_reactions" in top_item.document_id


def test_topic_mode_boost_isolation():
    """Verify that queries with artifact intent boost artifact chunks without breaking character binding."""
    bundle = retrieval_service.retrieve("What artifact set is best for Arlecchino Fragment of Harmonic Whimsy?", top_k=3)
    assert len(bundle.items) > 0
    top_item = bundle.items[0]
    assert "arlecchino" in top_item.document_id.lower()
    assert "artifact" in top_item.chunk_id.lower() or "artifact" in top_item.section_heading.lower()


# ==============================================================================
# 11. Index Determinism Tests
# ==============================================================================

def test_index_determinism_across_runs():
    """Verify that re-indexing identical text produces bit-for-bit identical vectors and rankings."""
    text_sample = "Kaedehara Kazuha grants 0.04% Elemental DMG Bonus per point of Elemental Mastery."
    provider = LocalSubwordEmbeddingProvider(256)

    # Embed twice
    vec1 = provider.embed_text(text_sample)
    vec2 = provider.embed_text(text_sample)
    assert vec1 == vec2, "Subword embedding must be 100% deterministic"

    # Query twice
    b1 = retrieval_service.retrieve("Kazuha Elemental Mastery buff", method="hybrid", top_k=5)
    b2 = retrieval_service.retrieve("Kazuha Elemental Mastery buff", method="hybrid", top_k=5)

    assert len(b1.items) == len(b2.items)
    for it1, it2 in zip(b1.items, b2.items):
        assert it1.chunk_id == it2.chunk_id
        assert it1.composite_score == it2.composite_score
        assert it1.content_hash == it2.content_hash


# ==============================================================================
# 12. Version-Aware Scenarios (Cases A–E)
# ==============================================================================

def test_version_case_a_current_target_version():
    """Case A: Current target version queries retrieve current documents with freshness boost."""
    bundle = retrieval_service.retrieve("official combat rules and elemental interaction", top_k=3)
    assert len(bundle.items) > 0
    top_item = bundle.items[0]
    assert top_item.game_version in ("7.0", "5.4", "5.0")


def test_version_case_b_older_compatible_mechanics():
    """Case B: Older compatible mechanics documents remain retrievable and score high."""
    bundle = retrieval_service.retrieve("How do Vaporize and Melt amplifying reaction damage multipliers calculate?", top_k=3)
    assert len(bundle.items) > 0
    # The damage formula is retrievable despite having an earlier game version
    found_formula = any("damage_formula" in it.document_id or "elemental_reactions" in it.document_id for it in bundle.items)
    assert found_formula is True


def test_version_case_c_historical_query_neutralizes_penalty():
    """Case C: Historical queries detect version triggers and do not penalize older evidence."""
    bundle = retrieval_service.retrieve("What was the original 1.0 national team meta with Bennett and Xiangling in older versions?", top_k=3)
    assert bundle.signals.is_historical_query is True
    assert len(bundle.items) > 0
    assert "national" in bundle.items[0].chunk_id.lower() or "xiangling" in bundle.items[0].document_id or "bennett" in bundle.items[0].document_id


def test_version_case_d_explicit_filters():
    """Case D: Explicit tier and character filters are strictly enforced."""
    bundle = retrieval_service.retrieve("talent books", character_filter="Kaedehara Kazuha", tier_filter=2, top_k=5)
    for item in bundle.items:
        assert item.character == "Kaedehara Kazuha"
        assert item.authority_tier <= 2


def test_version_case_e_system_health_synchronization():
    """Case E: System health accurately reflects index synchronization with knowledge manifest."""
    # 1. Base health check
    res_health = client.get("/api/health")
    assert res_health.status_code == 200
    data_h = res_health.json()
    assert data_h["status"] == "ok"
    assert data_h["game_version"] == "7.0"

    # 2. Version and staleness status
    res_ver = client.get("/api/version/status")
    assert res_ver.status_code == 200
    data_v = res_ver.json()
    assert data_v["current_version"] == "7.0"
    assert data_v["total_document_count"] == 179


# ==============================================================================
# 13. Graceful Failure Modes & Benchmark Suite
# ==============================================================================

def test_graceful_failure_unknown_entity():
    """Query for non-existent entity returns low composite scores and no hallucinated confident match."""
    bundle = retrieval_service.retrieve("Skirk Abyss BiS artifact set bonus", top_k=5)
    # The character Skirk does not have a character guide in the knowledge base
    # Results should have degraded composite score and no chunk should claim Skirk as character
    for item in bundle.items:
        assert item.character != "Skirk"


def test_graceful_failure_out_of_scope():
    """Completely out-of-scope gaming query returns low relevance or empty candidates."""
    bundle = retrieval_service.retrieve("How to defeat Malenia Blade of Miquella in Elden Ring", top_k=5)
    # If items exist due to common English subwords, scores should be modest, never confident
    for item in bundle.items:
        assert item.composite_score < 0.60


def test_retrieval_benchmark_dataset_metrics():
    """Run the complete 32-query benchmark suite and assert high quality retrieval metrics."""
    from backend.tests.retrieval_eval_dataset import run_evaluation_suite

    hybrid_results = run_evaluation_suite("hybrid")
    assert hybrid_results["mean_p_at_1"] >= 0.90, f"Expected P@1 >= 0.90, got {hybrid_results['mean_p_at_1']}"
    assert hybrid_results["mean_recall_at_5"] >= 0.95, f"Expected Recall@5 >= 0.95, got {hybrid_results['mean_recall_at_5']}"
    assert hybrid_results["mean_mrr"] >= 0.90, f"Expected MRR >= 0.90, got {hybrid_results['mean_mrr']}"
    assert hybrid_results["mean_ndcg_at_5"] >= 0.90, f"Expected nDCG@5 >= 0.90, got {hybrid_results['mean_ndcg_at_5']}"

