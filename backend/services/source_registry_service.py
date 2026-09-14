"""Service for loading, querying, and validating canonical sources from the central registry."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from backend.models.source_registry import Source, SourceRegistryData, SourceTier, SourceType

logger = logging.getLogger(__name__)

REGISTRY_PATH = Path("data/canonical/source_registry.json")


class SourceRegistryService:
    """Manages canonical sources and validates document source claims against the registry."""

    def __init__(self, registry_path: Optional[Path] = None):
        self.registry_path = registry_path or REGISTRY_PATH
        self._sources: Dict[str, Source] = {}
        self.load_registry()

    def load_registry(self) -> None:
        """Load sources from data/canonical/source_registry.json."""
        self._sources.clear()
        if not self.registry_path.exists():
            logger.warning(f"Source registry file not found at {self.registry_path}")
            return

        try:
            with open(self.registry_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            registry = SourceRegistryData.model_validate(data)
            for src in registry.sources:
                self._sources[src.source_id] = src

            logger.info(f"Loaded {len(self._sources)} canonical sources from registry.")
        except Exception as e:
            logger.error(f"Failed to load source registry from {self.registry_path}: {e}")

    @property
    def sources(self) -> Dict[str, Source]:
        """Dictionary of registered sources keyed by source_id."""
        return self._sources

    def get_source(self, source_id: str) -> Optional[Source]:
        """Lookup a source by its canonical source_id."""
        return self._sources.get(source_id)

    def list_sources(self, tier: Optional[SourceTier] = None, enabled_only: bool = True) -> List[Source]:
        """List registered sources with optional tier and enabled filtering."""
        sources = list(self._sources.values())
        if enabled_only:
            sources = [s for s in sources if s.enabled]
        if tier is not None:
            sources = [s for s in sources if s.tier == tier]
        return sorted(sources, key=lambda s: (s.tier, s.source_id))

    def validate_provenance(
        self,
        source_id: str,
        claimed_tier: Optional[SourceTier] = None,
        claimed_type: Optional[SourceType] = None,
    ) -> bool:
        """Verify that a source_id exists and conforms to registered tier and type."""
        source = self.get_source(source_id)
        if not source or not source.enabled:
            return False

        if claimed_tier is not None and source.tier != claimed_tier:
            logger.warning(
                f"Source tier mismatch for {source_id}: registered={source.tier}, claimed={claimed_tier}"
            )
            return False

        if claimed_type is not None and source.source_type != claimed_type:
            logger.warning(
                f"Source type mismatch for {source_id}: registered={source.source_type}, claimed={claimed_type}"
            )
            return False

        return True


source_registry_service = SourceRegistryService()
