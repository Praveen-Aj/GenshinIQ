"""Production hybrid retrieval and ranking engine for GenshinIQ (Phase 5).

Provides version-aware, authority-aware, provenance-grounded evidence retrieval
combining BM25 Okapi lexical search and dense semantic vector embeddings.

CORE PRINCIPLE:
Retrieval is an evidence-selection mechanism, NOT an authority mechanism.
Retrieval ranking selects and orders candidate evidence without altering its
underlying canonical authority tier, truth status, or provenance.
"""

import math
import re
import time
from typing import Dict, List, Optional, Set, Tuple

from backend.models.knowledge import (
    EvidenceBundle,
    QuerySignals,
    RetrievedEvidence,
    SemanticChunk,
)
from backend.services.bm25_service import bm25_service, BM25Index, tokenize
from backend.services.embedding_service import embedding_service, EmbeddingService
from backend.services.game_data_service import game_data_service
from backend.services.source_registry_service import source_registry_service


# Authority multipliers: gentle influence to break ties without overwhelming relevance
AUTHORITY_WEIGHTS = {
    1: 1.20,  # Tier 1: Official HoYoverse
    2: 1.15,  # Tier 2: KQM / KQM TCL Curated Theorycrafting
    3: 1.05,  # Tier 3: Maintained Structured Data (Ambr.top, etc.)
    4: 1.00,  # Tier 4: Statistical / Analytical Community Data
    5: 0.90,  # Tier 5: General Community Guides
}

# Freshness multipliers for non-historical queries
FRESHNESS_WEIGHTS = {
    "current": 1.15,
    "recent_compatible": 1.05,
    "unknown": 0.95,
    "stale": 0.75,
    "historical": 0.50,
}

# Common Genshin mechanics keywords for signal extraction
MECHANICS_KEYWORDS = {
    "elemental mastery", "energy recharge", "crit rate", "crit dmg",
    "icd", "internal cooldown", "swirl", "vaporize", "melt", "hyperbloom",
    "burgeon", "quicken", "aggravate", "spread", "electro-charged", "freeze",
    "overload", "crystallize", "shred", "res shred", "def shred",
    "damage formula", "gauge unit", "snapshot", "dynamic buff",
    "nightsoul", "bond of life", "pity", "soft pity", "hard pity",
    "interruption resistance", "poise",
}

HISTORICAL_TRIGGERS = [
    r"\b(in|patch|v|version)\s*([1-6]\.[0-9]+)",
    r"\b([1-6]\.[0-9]+)\b",
    r"\bbefore\s+(v|version\s+)?([5-7]\.[0-9]+)",
    r"\bhistorical\b",
    r"\bhistory\b",
    r"\boriginal\b",
    r"\boriginally\b",
    r"\bback\s+in\b",
    r"\bold\s+version\b",
    r"\bpreviously\b",
]


class QuerySignalExtractor:
    """Extracts canonical entities, mechanics, topic, and temporal signals from user queries."""

    def __init__(self):
        self._character_aliases: Dict[str, str] = {}
        self._sorted_character_aliases: List[Tuple[str, str]] = []
        self._weapon_aliases: Dict[str, str] = {}
        self._sorted_weapon_aliases: List[Tuple[str, str]] = []
        self._artifact_aliases: Dict[str, str] = {}
        self._sorted_artifact_aliases: List[Tuple[str, str]] = []
        self._initialized = False

    def _ensure_vocab(self):
        """Lazy load canonical entity names and build alias maps."""
        if self._initialized:
            return

        try:
            # 1. Characters: map full names and single-word unique components to canonical names
            chars = game_data_service.list_characters()
            for c in chars:
                canonical = c.name
                self._character_aliases[canonical.lower()] = canonical

                # Multi-word character mappings (e.g. 'Kaedehara Kazuha' -> 'kazuha', 'kaedehara')
                parts = canonical.lower().split()
                if len(parts) > 1:
                    for p in parts:
                        if len(p) > 2 and p not in {"traveler", "the"}:
                            self._character_aliases[p] = canonical

            # Common informal aliases
            self._character_aliases.update({
                "kazuha": "Kaedehara Kazuha",
                "kaedehara": "Kaedehara Kazuha",
                "raiden": "Raiden Shogun",
                "shogun": "Raiden Shogun",
                "ei": "Raiden Shogun",
                "ayaka": "Kamisato Ayaka",
                "ayato": "Kamisato Ayato",
                "kokomi": "Sangonomiya Kokomi",
                "itto": "Arataki Itto",
                "yae": "Yae Miko",
                "shinobu": "Kuki Shinobu",
                "heizou": "Shikanoin Heizou",
                "sara": "Kujou Sara",
                "hutao": "Hu Tao",
                "hu tao": "Hu Tao",
            })

            # Sort character aliases by length descending (longest first for span matching)
            self._sorted_character_aliases = sorted(
                self._character_aliases.items(), key=lambda x: len(x[0]), reverse=True
            )

            # 2. Weapons
            weapons = game_data_service.list_weapons()
            for w in weapons:
                canonical_w = w.name
                self._weapon_aliases[canonical_w.lower()] = canonical_w
                self._weapon_aliases[canonical_w.lower().replace("-", " ")] = canonical_w

            # Weapon informal aliases
            self._weapon_aliases.update({
                "freedom sworn": "Freedom-Sworn",
                "freedom-sworn": "Freedom-Sworn",
                "fav sword": "Favonius Sword",
                "fav lance": "Favonius Lance",
                "the catch": "The Catch",
                "catch": "The Catch",
                "xiphos": "Xiphos' Moonlight",
                "xiphos moonlight": "Xiphos' Moonlight",
                "engulfing": "Engulfing Lightning",
                "sapwood": "Sapwood Blade",
                "aquila": "Aquila Favonia",
                "tome": "Tome of the Eternal Flow",
            })
            self._sorted_weapon_aliases = sorted(
                self._weapon_aliases.items(), key=lambda x: len(x[0]), reverse=True
            )

            # 3. Artifact Sets
            artifacts = game_data_service.list_artifact_sets()
            for a in artifacts:
                canonical_a = a.name
                self._artifact_aliases[canonical_a.lower()] = canonical_a

            # Artifact informal aliases
            self._artifact_aliases.update({
                "vv": "Viridescent Venerer",
                "viridescent": "Viridescent Venerer",
                "eosf": "Emblem of Severed Fate",
                "emblem": "Emblem of Severed Fate",
                "deepwood": "Deepwood Memories",
                "gilded": "Gilded Dreams",
                "whimsy": "Fragment of Harmonic Whimsy",
                "crimson witch": "Crimson Witch of Flames",
                "cw": "Crimson Witch of Flames",
                "marechaussee": "Marechaussee Hunter",
                "golden troupe": "Golden Troupe",
            })
            self._sorted_artifact_aliases = sorted(
                self._artifact_aliases.items(), key=lambda x: len(x[0]), reverse=True
            )
        except Exception:
            pass

        self._initialized = True

    def extract(self, query: str, explicit_mode: Optional[str] = None) -> QuerySignals:
        """Extract structured signals with canonical entity resolution."""
        self._ensure_vocab()
        q_lower = query.lower().strip()

        # 1. Canonical Character Extraction with span tracking
        detected_chars: Set[str] = set()
        matched_char_spans: List[Tuple[int, int]] = []
        for alias, canonical in self._sorted_character_aliases:
            for match in re.finditer(rf"\b{re.escape(alias)}\b", q_lower):
                s, e = match.span()
                if any(ms <= s and e <= me for ms, me in matched_char_spans):
                    continue
                matched_char_spans.append((s, e))
                detected_chars.add(canonical)

        # 2. Canonical Weapon Extraction with span tracking
        detected_weapons: Set[str] = set()
        matched_w_spans: List[Tuple[int, int]] = []
        for alias, canonical in self._sorted_weapon_aliases:
            for match in re.finditer(rf"\b{re.escape(alias)}\b", q_lower):
                s, e = match.span()
                if any(ms <= s and e <= me for ms, me in matched_w_spans):
                    continue
                matched_w_spans.append((s, e))
                detected_weapons.add(canonical)

        # 3. Canonical Artifact Extraction with span tracking
        detected_artifacts: Set[str] = set()
        matched_a_spans: List[Tuple[int, int]] = []
        for alias, canonical in self._sorted_artifact_aliases:
            for match in re.finditer(rf"\b{re.escape(alias)}\b", q_lower):
                s, e = match.span()
                if any(ms <= s and e <= me for ms, me in matched_a_spans):
                    continue
                matched_a_spans.append((s, e))
                detected_artifacts.add(canonical)

        # 4. Mechanics keywords
        detected_mechanics = []
        for term in MECHANICS_KEYWORDS:
            if term in q_lower:
                detected_mechanics.append(term)

        # 5. Detect historical query intent
        is_historical = False
        for pattern in HISTORICAL_TRIGGERS:
            if re.search(pattern, q_lower):
                is_historical = True
                break

        # 6. Determine retrieval mode if not explicitly supplied
        retrieval_mode = explicit_mode
        if not retrieval_mode:
            if is_historical:
                retrieval_mode = "historical"
            elif any(w in q_lower for w in ["farm", "schedule", "domain", "talent book", "boss material"]):
                retrieval_mode = "farming"
            elif detected_mechanics or any(w in q_lower for w in ["formula", "scaling", "mechanic", "gauge", "icd"]):
                retrieval_mode = "mechanics"
            elif detected_artifacts or any(w in q_lower for w in ["artifact", "set bonus", "substat"]):
                retrieval_mode = "artifact"
            elif detected_weapons or any(w in q_lower for w in ["weapon", "sword", "bow", "polearm", "claymore", "catalyst", "bis"]):
                retrieval_mode = "weapon"
            elif any(w in q_lower for w in ["guide", "build", "rotation", "team"]):
                retrieval_mode = "guide"
            elif detected_chars:
                retrieval_mode = "character"
            elif any(w in q_lower for w in ["patch", "update", "notes", "version"]):
                retrieval_mode = "version"
            else:
                retrieval_mode = "general"

        return QuerySignals(
            query=query,
            detected_characters=sorted(list(detected_chars)),
            detected_weapons=sorted(list(detected_weapons)),
            detected_artifacts=sorted(list(detected_artifacts)),
            detected_mechanics=sorted(list(set(detected_mechanics))),
            retrieval_mode=retrieval_mode,
            is_historical_query=is_historical,
        )


signal_extractor = QuerySignalExtractor()


class RetrievalService:
    """Unified hybrid retrieval pipeline combining lexical, semantic, and metadata scoring."""

    def __init__(
        self,
        bm25: Optional[BM25Index] = None,
        embed: Optional[EmbeddingService] = None,
    ):
        self.bm25 = bm25 or bm25_service
        self.embed = embed or embedding_service

    def retrieve(
        self,
        query: str,
        mode: Optional[str] = None,
        method: str = "hybrid",
        top_k: int = 5,
        candidate_k: int = 40,
        character_filter: Optional[str] = None,
        tier_filter: Optional[int] = None,
        max_chunks_per_doc: int = 2,
    ) -> EvidenceBundle:
        """Execute hybrid, bm25_only, or dense_only retrieval pipeline and return an EvidenceBundle."""
        start_time = time.perf_counter()
        clean_query = query.strip()
        if not clean_query:
            return EvidenceBundle(
                query=query,
                signals=QuerySignals(query=query),
                items=[],
                total_candidates_examined=0,
                latency_ms=0.0,
                retrieval_status="EMPTY",
                embedding_model=self.embed.provider.model_name,
            )

        # 1. Query Signals Extraction
        signals = signal_extractor.extract(clean_query, explicit_mode=mode)

        # If a character was detected in signals and no explicit character_filter was provided,
        # we can soft-boost the character rather than hard-filtering, unless explicitly requested.
        effective_char_filter = character_filter

        # 2. Candidate Retrieval from Selected Backends
        bm25_candidates: List[Tuple[SemanticChunk, float]] = []
        vector_candidates: List[Tuple[SemanticChunk, float]] = []
        retrieval_status = "OK"

        if method != "dense_only":
            try:
                bm25_candidates = self.bm25.search(
                    query=clean_query,
                    top_k=candidate_k,
                    character_filter=effective_char_filter,
                    tier_filter=tier_filter,
                )
            except Exception:
                bm25_candidates = []
                retrieval_status = "LEXICAL_DEGRADED"

        if method != "bm25_only":
            try:
                vector_candidates = self.embed.search(
                    query=clean_query,
                    top_k=candidate_k,
                    character_filter=effective_char_filter,
                    tier_filter=tier_filter,
                )
            except Exception:
                vector_candidates = []
                retrieval_status = "VECTOR_DEGRADED" if retrieval_status == "OK" else "EMPTY"

        # Check total candidates
        if not bm25_candidates and not vector_candidates:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return EvidenceBundle(
                query=query,
                signals=signals,
                items=[],
                total_candidates_examined=0,
                latency_ms=round(elapsed_ms, 2),
                retrieval_status="EMPTY",
                embedding_model=self.embed.provider.model_name,
            )

        if method == "hybrid":
            if not vector_candidates and bm25_candidates:
                retrieval_status = "VECTOR_DEGRADED"
            elif not bm25_candidates and vector_candidates:
                retrieval_status = "LEXICAL_DEGRADED"
        else:
            retrieval_status = "OK"

        # 3. Score Normalization
        bm25_scores = {chunk.chunk_id: score for chunk, score in bm25_candidates}
        vector_scores = {chunk.chunk_id: score for chunk, score in vector_candidates}

        norm_bm25 = self._min_max_normalize(bm25_scores)
        norm_vector = self._min_max_normalize(vector_scores)

        # Collect unique candidate chunks
        all_chunks: Dict[str, SemanticChunk] = {}
        for chunk, _ in bm25_candidates:
            all_chunks[chunk.chunk_id] = chunk
        for chunk, _ in vector_candidates:
            all_chunks[chunk.chunk_id] = chunk

        total_examined = len(all_chunks)

        # 4. Provenance Validation & Filtering
        valid_chunks: List[SemanticChunk] = []
        for chunk in all_chunks.values():
            src = source_registry_service.get_source(chunk.source_id)
            if not src:
                # Reject unregistered provenance
                continue
            if chunk.authority_tier != src.tier:
                # Reject tier tampering
                continue
            valid_chunks.append(chunk)

        # 5. Composite Ranking
        scored_evidence: List[RetrievedEvidence] = []
        for chunk in valid_chunks:
            cid = chunk.chunk_id
            s_lex = norm_bm25.get(cid, 0.0)
            s_sem = norm_vector.get(cid, 0.0)

            # Base relevance fusion based on selected method
            if method == "hybrid":
                if cid in norm_bm25 and cid in norm_vector:
                    # Both lexical and dense matched: reinforce composite relevance
                    base_score = (0.60 * s_lex + 0.40 * s_sem) * 1.15
                    retrieval_method = "hybrid"
                elif cid in norm_bm25:
                    base_score = s_lex * 0.60
                    retrieval_method = "bm25_only"
                else:
                    base_score = s_sem * 0.40
                    retrieval_method = "vector_only"
            elif method == "bm25_only":
                base_score = s_lex
                retrieval_method = "bm25_only"
            else:  # dense_only
                base_score = s_sem
                retrieval_method = "vector_only"

            # Apply Authority Tier Multiplier (gentle bias, never overrides relevance)
            auth_multiplier = AUTHORITY_WEIGHTS.get(int(chunk.authority_tier), 1.0)

            # Apply Version/Freshness Multiplier
            if signals.is_historical_query:
                # Historical queries do not penalize older or stale versions
                fresh_multiplier = 1.0
            else:
                fresh_multiplier = FRESHNESS_WEIGHTS.get(chunk.freshness_status, 1.0)

            # Apply Signal Match Boosts
            signal_multiplier = 1.0

            # 1. Entity Alignment: Strongly boost matching character, downweight conflicting characters
            if signals.detected_characters:
                if chunk.character:
                    matched_char = any(
                        dc.lower() in chunk.character.lower() or chunk.character.lower() in dc.lower()
                        for dc in signals.detected_characters
                    )
                    if matched_char:
                        signal_multiplier *= 2.2
                    else:
                        # Chunk belongs to a completely different character
                        signal_multiplier *= 0.20
            elif signals.retrieval_mode == "mechanics":
                # General mechanics query with NO character mentioned:
                # Prioritize universal mechanics and isolate character-specific fluff
                if chunk.character is None or chunk.topic == "Game Mechanics":
                    signal_multiplier *= 1.35
                elif chunk.character is not None:
                    signal_multiplier *= 0.65

            # 2. Mode & Topic Alignment Boosts
            cid_lower = chunk.chunk_id.lower()
            heading_lower = chunk.section_heading.lower()
            if signals.retrieval_mode == "artifact":
                if "artifact" in cid_lower or "artifact" in heading_lower:
                    signal_multiplier *= 1.4
            elif signals.retrieval_mode == "weapon":
                if "weapon" in cid_lower or "weapon" in heading_lower:
                    signal_multiplier *= 1.4
            elif signals.retrieval_mode == "farming":
                if "material" in cid_lower or "farming" in cid_lower or "schedule" in cid_lower or "ascension" in heading_lower:
                    signal_multiplier *= 1.4
            elif signals.retrieval_mode == "mechanics" and (chunk.character is None or chunk.topic == "Game Mechanics"):
                if "mechanic" in cid_lower or "formula" in cid_lower or "scaling" in heading_lower or "reaction" in cid_lower:
                    signal_multiplier *= 1.25

            # Final composite score
            composite_score = base_score * auth_multiplier * fresh_multiplier * signal_multiplier

            evidence = RetrievedEvidence(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                title=chunk.title,
                section_heading=chunk.section_heading,
                content=chunk.content,
                source_id=chunk.source_id,
                source=chunk.source,
                source_url=chunk.source_url,
                canonical_url=chunk.canonical_url,
                source_type=chunk.source_type,
                authority_tier=chunk.authority_tier,
                character=chunk.character,
                topic=chunk.topic,
                game_version=chunk.game_version,
                freshness_status=chunk.freshness_status,
                affected_systems=chunk.affected_systems,
                content_hash=chunk.content_hash,
                lexical_score=round(s_lex, 4),
                semantic_score=round(s_sem, 4),
                composite_score=round(composite_score, 4),
                retrieval_method=retrieval_method,
                rank=1,
            )
            scored_evidence.append(evidence)

        # Sort by composite score descending
        scored_evidence.sort(key=lambda x: x.composite_score, reverse=True)

        # 6. Deduplication and Diversity Filtering
        final_items = self._deduplicate_and_diversify(
            scored_evidence,
            max_chunks_per_doc=max_chunks_per_doc,
            top_k=top_k,
        )

        # Assign final 1-indexed ranks
        for idx, item in enumerate(final_items):
            item.rank = idx + 1

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return EvidenceBundle(
            query=query,
            signals=signals,
            items=final_items,
            total_candidates_examined=total_examined,
            latency_ms=round(elapsed_ms, 2),
            retrieval_status=retrieval_status,
            embedding_model=self.embed.provider.model_name,
        )

    def _min_max_normalize(self, score_dict: Dict[str, float]) -> Dict[str, float]:
        """Normalize raw scores to [0.0, 1.0]."""
        if not score_dict:
            return {}
        vals = list(score_dict.values())
        min_v = min(vals)
        max_v = max(vals)
        if math.isclose(max_v, min_v, abs_tol=1e-7):
            return {k: 1.0 for k in score_dict}
        diff = max_v - min_v
        return {k: (v - min_v) / diff for k, v in score_dict.items()}

    def _deduplicate_and_diversify(
        self,
        candidates: List[RetrievedEvidence],
        max_chunks_per_doc: int,
        top_k: int,
    ) -> List[RetrievedEvidence]:
        """Select top candidates while enforcing per-document limits and suppressing near-duplicates."""
        selected: List[RetrievedEvidence] = []
        doc_counts: Dict[str, int] = {}
        selected_token_sets: List[Set[str]] = []

        for cand in candidates:
            # 1. Enforce max chunks per document
            doc_id = cand.document_id
            if doc_counts.get(doc_id, 0) >= max_chunks_per_doc:
                continue

            # 2. Near-duplicate suppression via token Jaccard similarity (> 0.85)
            cand_tokens = set(tokenize(cand.content))
            if not cand_tokens:
                continue

            is_near_duplicate = False
            for prev_tokens in selected_token_sets:
                intersection = len(cand_tokens & prev_tokens)
                union = len(cand_tokens | prev_tokens)
                jaccard = intersection / union if union > 0 else 0.0
                if jaccard > 0.85:
                    is_near_duplicate = True
                    break

            if is_near_duplicate:
                continue

            selected.append(cand)
            doc_counts[doc_id] = doc_counts.get(doc_id, 0) + 1
            selected_token_sets.append(cand_tokens)

            if len(selected) >= top_k:
                break

        return selected


retrieval_service = RetrievalService()
