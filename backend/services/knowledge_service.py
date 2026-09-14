"""Service to load, index, and query curated Genshin knowledge base documents."""

import difflib
import os
import json
import logging
import re
from typing import Any, Dict, List, Optional
from pathlib import Path

from backend.models.knowledge import KnowledgeDocument, KnowledgeSearchResult, SourceType, compute_content_hash
from backend.models.source_registry import SourceTier
from backend.models.version import StalenessEvaluation
from backend.services.source_registry_service import source_registry_service
from backend.services.version_service import version_service

logger = logging.getLogger(__name__)


class KnowledgeService:
    """Manages indexing, retrieval, and search of curated Genshin knowledge documents with provenance validation."""

    def __init__(self, knowledge_dir: Optional[str] = None):
        self.knowledge_dir = Path(knowledge_dir or os.path.join("data", "knowledge"))
        # In-memory indices
        self.documents: Dict[str, KnowledgeDocument] = {}
        self.by_character: Dict[str, List[KnowledgeDocument]] = {}
        self.by_topic: Dict[str, List[KnowledgeDocument]] = {}
        self.by_source_id: Dict[str, List[KnowledgeDocument]] = {}
        self.by_tier: Dict[SourceTier, List[KnowledgeDocument]] = {}
        self.search_aliases: List[str] = []
        
        self.load_documents()

    def load_documents(self) -> None:
        """Load, validate, and index all curated JSON knowledge base documents."""
        self.documents.clear()
        self.by_character.clear()
        self.by_topic.clear()
        self.by_source_id.clear()
        self.by_tier.clear()
        self.search_aliases.clear()

        if not self.knowledge_dir.exists():
            logger.warning(f"Knowledge directory {self.knowledge_dir} does not exist. Creating it.")
            self.knowledge_dir.mkdir(parents=True, exist_ok=True)
            return

        for file_path in self.knowledge_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                doc = KnowledgeDocument.model_validate(data)

                # 1. Content Hash Verification
                if not doc.verify_hash():
                    logger.warning(f"Document {doc.id} content_hash mismatch; recalculating deterministic hash.")
                    doc.metadata.content_hash = compute_content_hash(doc.content)

                # 2. Source Registry Provenance Validation
                is_valid = source_registry_service.validate_provenance(
                    doc.metadata.source_id,
                    claimed_tier=doc.metadata.authority_tier,
                    claimed_type=doc.metadata.source_type,
                )
                if not is_valid:
                    logger.error(f"Rejecting document {doc.id}: failed source registry provenance validation!")
                    continue

                self.documents[doc.id] = doc

                # Index by character
                char = doc.metadata.character
                if char:
                    char_lower = char.lower()
                    if char_lower not in self.by_character:
                        self.by_character[char_lower] = []
                    self.by_character[char_lower].append(doc)
                    self.search_aliases.append(char_lower)

                # Index by topic
                topic_lower = doc.metadata.topic.lower()
                if topic_lower not in self.by_topic:
                    self.by_topic[topic_lower] = []
                self.by_topic[topic_lower].append(doc)
                self.search_aliases.append(doc.title.lower())
                self.search_aliases.extend(tag.lower() for tag in doc.metadata.tags)

                # Index by source_id and authority tier
                src_id = doc.metadata.source_id
                if src_id not in self.by_source_id:
                    self.by_source_id[src_id] = []
                self.by_source_id[src_id].append(doc)

                tier = doc.metadata.authority_tier
                if tier not in self.by_tier:
                    self.by_tier[tier] = []
                self.by_tier[tier].append(doc)

                logger.info(f"Loaded knowledge document: '{doc.id}' (Title: {doc.title}, Source: {src_id})")
            except Exception as e:
                logger.error(f"Failed to load knowledge document {file_path}: {e}")

    def get_document(self, doc_id: str) -> Optional[KnowledgeDocument]:
        """Retrieve a specific knowledge document by ID."""
        return self.documents.get(doc_id)

    def list_documents(
        self,
        character: Optional[str] = None,
        topic: Optional[str] = None,
        source_type: Optional[SourceType] = None,
        source_id: Optional[str] = None,
        authority_tier: Optional[SourceTier] = None,
        game_version: Optional[str] = None,
        only_current: bool = False,
        max_staleness_patches: Optional[int] = None,
    ) -> List[KnowledgeDocument]:
        """List all documents matching optional filters, including version, tier, and staleness constraints."""
        results = list(self.documents.values())
        curr_version = version_service.get_current_version().version

        if character:
            char_lower = character.lower()
            results = [doc for doc in results if doc.metadata.character and doc.metadata.character.lower() == char_lower]

        if topic:
            topic_lower = topic.lower()
            results = [doc for doc in results if doc.metadata.topic.lower() == topic_lower]

        if source_type:
            results = [doc for doc in results if doc.metadata.source_type == source_type]

        if source_id:
            results = [doc for doc in results if doc.metadata.source_id == source_id]

        if authority_tier is not None:
            results = [doc for doc in results if doc.metadata.authority_tier == authority_tier]

        if game_version:
            clean_req = game_version.strip().lstrip("v")
            results = [doc for doc in results if doc.metadata.game_version.lstrip("v") == clean_req]

        if only_current:
            results = [doc for doc in results if doc.metadata.game_version.lstrip("v") == curr_version]

        if max_staleness_patches is not None:
            results = [
                doc for doc in results
                if version_service.calculate_distance(doc.metadata.game_version) <= max_staleness_patches
            ]

        return results

    def evaluate_document(self, doc_id: str) -> Optional[StalenessEvaluation]:
        """Evaluate staleness for a specific document ID."""
        doc = self.documents.get(doc_id)
        if not doc:
            return None
        return version_service.evaluate_staleness(doc.metadata.game_version)

    def get_stale_documents(self, stale_threshold_patches: int = 4) -> List[Dict[str, Any]]:
        """Retrieve all documents considered stale relative to the active game version."""
        stale_list = []
        for doc in self.documents.values():
            eval_res = version_service.evaluate_staleness(
                doc.metadata.game_version,
                stale_threshold_patches=stale_threshold_patches,
            )
            if eval_res.is_stale:
                stale_list.append({
                    "document_id": doc.id,
                    "title": doc.title,
                    "topic": doc.metadata.topic,
                    "document_version": doc.metadata.game_version,
                    "current_version": eval_res.current_version,
                    "version_distance": eval_res.version_distance,
                    "is_stale": True,
                    "warning": eval_res.warning,
                })
        return stale_list

    def search_documents(
        self,
        query: str,
        limit: int = 5,
        prefer_current: bool = True,
    ) -> List[KnowledgeSearchResult]:
        """
        Hybrid semantic & lexical search over knowledge chunks with provenance and version awareness.
        Falls back to keyword search if retrieval engine returns empty.
        """
        if not query or not query.strip():
            return []

        try:
            from backend.services.retrieval_service import retrieval_service
            bundle = retrieval_service.retrieve(query=query, top_k=limit * 2)
            if bundle.items:
                results: List[KnowledgeSearchResult] = []
                seen_doc_ids = set()
                for item in bundle.items:
                    if item.document_id in seen_doc_ids:
                        continue
                    seen_doc_ids.add(item.document_id)
                    doc = self.documents.get(item.document_id)
                    snippet = item.content.replace("\n", " ").strip()
                    if len(snippet) > 220:
                        snippet = snippet[:220] + "..."
                    results.append(
                        KnowledgeSearchResult(
                            id=item.document_id,
                            title=item.title,
                            source_id=item.source_id,
                            source=item.source,
                            canonical_url=item.canonical_url,
                            source_type=item.source_type,
                            authority_tier=item.authority_tier,
                            character=item.character,
                            topic=item.topic,
                            game_version=item.game_version,
                            summary=doc.summary if doc else item.section_heading,
                            snippet=snippet,
                            content_hash=item.content_hash,
                            relevance_score=item.composite_score,
                            chunk_id=item.chunk_id,
                            section_heading=item.section_heading,
                        )
                    )
                    if len(results) >= limit:
                        break
                if results:
                    return results
        except Exception:
            pass

        # Fallback to keyword search
        cleaned_query = re.sub(r"[^\w\s]", " ", query)
        stop_words = {
            "what", "are", "the", "is", "of", "for", "in", "on", "to", "a", "an",
            "with", "about", "my", "how", "who", "do", "does", "did", "was", "were",
            "describe", "explain", "get", "show", "give", "tell", "which", "whose", "it"
        }
        search_terms = [term.lower() for term in cleaned_query.split() if term and term.lower() not in stop_words]
        if not search_terms:
            search_terms = [term.lower() for term in cleaned_query.split() if term]

        expanded_terms = list(search_terms)
        if self.search_aliases:
            for term in search_terms:
                if len(term) < 3:
                    continue
                close = difflib.get_close_matches(term, self.search_aliases, n=2, cutoff=0.82)
                for match in close:
                    if match not in expanded_terms:
                        expanded_terms.append(match)

        matches: List[KnowledgeSearchResult] = []

        for doc in self.documents.values():
            score = 0.0
            
            # Weighted scoring
            title_lower = doc.title.lower()
            summary_lower = doc.summary.lower()
            content_lower = doc.content.lower()
            char_lower = doc.metadata.character.lower() if doc.metadata.character else ""
            tags_lower = [t.lower() for t in doc.metadata.tags]

            for term in expanded_terms:
                if term in title_lower:
                    score += 5.0
                if term in char_lower:
                    score += 4.0
                if term in summary_lower:
                    score += 2.0
                if term in content_lower:
                    score += 1.0
                if any(term in tag for tag in tags_lower):
                    score += 3.0

            if score > 0:
                # 1. Authority Tier Weighting: Tier 1 (Official) & Tier 2 (Theorycrafting) prioritized over Tier 5 (Community)
                tier_multipliers = {
                    SourceTier.TIER_1_OFFICIAL: 1.25,
                    SourceTier.TIER_2_THEORYCRAFTING: 1.20,
                    SourceTier.TIER_3_STRUCTURED_DATA: 1.10,
                    SourceTier.TIER_4_STATISTICAL: 1.05,
                    SourceTier.TIER_5_COMMUNITY: 0.90,
                }
                score *= tier_multipliers.get(doc.metadata.authority_tier, 1.0)

                # 2. Version boost: prioritize current live version documents
                if prefer_current:
                    dist = version_service.calculate_distance(doc.metadata.game_version)
                    if dist == 0:
                        score *= 1.15  # 15% boost for current live version
                    elif dist <= 2:
                        score *= 1.05  # 5% boost for recent compatible version
                    elif dist > 4:
                        score *= max(0.65, 1.0 - dist * 0.04)  # downrank distant/stale documents

                # Build snippet from summary or content matches
                snippet = doc.summary
                content_match_idx = content_lower.find(expanded_terms[0])
                if content_match_idx != -1:
                    start = max(0, content_match_idx - 60)
                    end = min(len(doc.content), content_match_idx + 140)
                    snippet = "..." + doc.content[start:end].replace("\n", " ").strip() + "..."

                matches.append(
                    KnowledgeSearchResult(
                        id=doc.id,
                        title=doc.title,
                        source_id=doc.metadata.source_id,
                        source=doc.metadata.source,
                        canonical_url=doc.metadata.canonical_url,
                        source_type=doc.metadata.source_type,
                        authority_tier=doc.metadata.authority_tier,
                        character=doc.metadata.character,
                        topic=doc.metadata.topic,
                        game_version=doc.metadata.game_version,
                        summary=doc.summary,
                        snippet=snippet,
                        content_hash=doc.metadata.content_hash,
                        relevance_score=round(score, 2),
                    )
                )

        # Sort by relevance score descending
        matches.sort(key=lambda x: x.relevance_score, reverse=True)
        return matches[:limit]


# Global service instance
knowledge_service = KnowledgeService()
