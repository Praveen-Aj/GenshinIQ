"""Service to load, index, and query curated Genshin knowledge base documents."""

import os
import json
import logging
from typing import Dict, List, Optional
from pathlib import Path

from backend.models.knowledge import KnowledgeDocument, KnowledgeSearchResult, SourceType

logger = logging.getLogger(__name__)


class KnowledgeService:
    """Manages indexing, retrieval, and search of curated Genshin knowledge documents."""

    def __init__(self, knowledge_dir: Optional[str] = None):
        self.knowledge_dir = Path(knowledge_dir or os.path.join("data", "knowledge"))
        # In-memory indices
        self.documents: Dict[str, KnowledgeDocument] = {}
        self.by_character: Dict[str, List[KnowledgeDocument]] = {}
        self.by_topic: Dict[str, List[KnowledgeDocument]] = {}
        
        self.load_documents()

    def load_documents(self) -> None:
        """Load and index all curated JSON knowledge base documents."""
        self.documents.clear()
        self.by_character.clear()
        self.by_topic.clear()

        if not self.knowledge_dir.exists():
            logger.warning(f"Knowledge directory {self.knowledge_dir} does not exist. Creating it.")
            self.knowledge_dir.mkdir(parents=True, exist_ok=True)
            return

        for file_path in self.knowledge_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                doc = KnowledgeDocument.model_validate(data)
                self.documents[doc.id] = doc

                # Index by character
                char = doc.metadata.character
                if char:
                    char_lower = char.lower()
                    if char_lower not in self.by_character:
                        self.by_character[char_lower] = []
                    self.by_character[char_lower].append(doc)

                # Index by topic
                topic_lower = doc.metadata.topic.lower()
                if topic_lower not in self.by_topic:
                    self.by_topic[topic_lower] = []
                self.by_topic[topic_lower].append(doc)

                logger.info(f"Loaded knowledge document: '{doc.id}' (Title: {doc.title})")
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
        game_version: Optional[str] = None,
    ) -> List[KnowledgeDocument]:
        """List all documents matching optional filters."""
        results = list(self.documents.values())

        if character:
            char_lower = character.lower()
            results = [doc for doc in results if doc.metadata.character and doc.metadata.character.lower() == char_lower]

        if topic:
            topic_lower = topic.lower()
            results = [doc for doc in results if doc.metadata.topic.lower() == topic_lower]

        if source_type:
            results = [doc for doc in results if doc.metadata.source_type == source_type]

        if game_version:
            results = [doc for doc in results if doc.metadata.game_version == game_version]

        return results

    def search_documents(self, query: str, limit: int = 5) -> List[KnowledgeSearchResult]:
        """
        Simple keyword search over titles, summaries, and contents.
        Returns ranked KnowledgeSearchResult list.
        """
        if not query or not query.strip():
            return []

        import re
        cleaned_query = re.sub(r"[^\w\s]", " ", query)
        search_terms = [term.lower() for term in cleaned_query.split() if term]
        matches: List[KnowledgeSearchResult] = []

        for doc in self.documents.values():
            score = 0.0
            
            # Weighted scoring
            title_lower = doc.title.lower()
            summary_lower = doc.summary.lower()
            content_lower = doc.content.lower()
            char_lower = doc.metadata.character.lower() if doc.metadata.character else ""
            tags_lower = [t.lower() for t in doc.metadata.tags]

            for term in search_terms:
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
                # Build snippet from summary or content matches
                snippet = doc.summary
                content_match_idx = content_lower.find(search_terms[0])
                if content_match_idx != -1:
                    start = max(0, content_match_idx - 60)
                    end = min(len(doc.content), content_match_idx + 140)
                    snippet = "..." + doc.content[start:end].replace("\n", " ").strip() + "..."

                matches.append(
                    KnowledgeSearchResult(
                        id=doc.id,
                        title=doc.title,
                        source=doc.metadata.source,
                        source_type=doc.metadata.source_type,
                        character=doc.metadata.character,
                        topic=doc.metadata.topic,
                        game_version=doc.metadata.game_version,
                        summary=doc.summary,
                        snippet=snippet,
                        relevance_score=score,
                    )
                )

        # Sort by relevance score descending
        matches.sort(key=lambda x: x.relevance_score, reverse=True)
        return matches[:limit]


# Global service instance
knowledge_service = KnowledgeService()
