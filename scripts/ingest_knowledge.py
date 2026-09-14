"""GenshinIQ Knowledge Base Ingestion Engine.

Automated, repeatable, and auditable ingestion pipeline for:
- Tier 1: HoYoverse Official & In-Game Archives
- Tier 2: KeqingMains Guides & KQM Theorycrafting Library (TCL)
- Tier 3: Maintained Structured Game Data Bridges
- Tier 4: Statistical Summaries
- Tier 5: Community Resources

Enforces Phase 3 provenance schema, deterministic SHA-256 hashing,
dynamic version freshness, and deduplication.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.models.knowledge import KnowledgeDocument, KnowledgeMetadata, SourceType, compute_content_hash
from backend.models.source_registry import SourceTier
from backend.services.source_registry_service import source_registry_service
from backend.services.version_service import version_service

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = ROOT_DIR / "data" / "knowledge"
GAPS_FILE = ROOT_DIR / "data" / "canonical" / "knowledge_gaps.json"


class KnowledgeIngestionPipeline:
    """Manages the ingestion, validation, hashing, and writing of knowledge documents."""

    def __init__(self, target_dir: Optional[Path] = None):
        self.target_dir = target_dir or KNOWLEDGE_DIR
        self.target_dir.mkdir(parents=True, exist_ok=True)
        self.current_version = version_service.get_current_version().version

    def ingest_document(
        self,
        doc_id: str,
        title: str,
        source_id: str,
        source_url: str,
        canonical_url: str,
        topic: str,
        summary: str,
        content: str,
        character: Optional[str] = None,
        game_version: Optional[str] = None,
        published_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> KnowledgeDocument:
        """Ingests, validates, hashes, and persists a single knowledge document."""
        # 1. Source registry verification
        source_rec = source_registry_service.get_source(source_id)
        if not source_rec:
            raise ValueError(f"Unknown source_id: '{source_id}'. Must exist in data/canonical/source_registry.json")

        tier = source_rec.tier
        source_type = SourceType(source_rec.source_type.value)
        source_name = source_rec.name

        # 2. Version and Freshness Evaluation
        effective_version = game_version or self.current_version
        staleness = version_service.evaluate_staleness(effective_version)
        freshness_status = "current" if not staleness.is_stale and effective_version == self.current_version else (
            "recent_compatible" if not staleness.is_stale else "stale"
        )

        # 3. Deterministic Content Hashing
        content_hash = compute_content_hash(content)
        retrieved_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00Z")

        # 4. Construct Metadata
        metadata = KnowledgeMetadata(
            source_id=source_id,
            source=source_name,
            source_url=source_url,
            canonical_url=canonical_url,
            source_type=source_type,
            authority_tier=tier,
            character=character,
            topic=topic,
            game_version=effective_version,
            published_at=published_at,
            updated_at=updated_at,
            retrieved_at=retrieved_at,
            content_hash=content_hash,
            freshness_status=freshness_status,
            tags=tags or [],
        )

        # 5. Construct Document & Verify Hash Integrity
        doc = KnowledgeDocument(
            id=doc_id,
            title=title,
            metadata=metadata,
            summary=summary,
            content=content,
        )

        if not doc.verify_hash():
            raise ValueError(f"Content hash verification failed for document '{doc_id}'")

        # 6. Save to disk
        out_file = self.target_dir / f"{doc_id}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(doc.model_dump(mode="json"), f, indent=2, ensure_ascii=False)

        logger.info(f"Ingested [{source_id}] (Tier {tier}, v{effective_version}): {doc_id} -> {out_file.name}")
        return doc


pipeline = KnowledgeIngestionPipeline()
