"""
Base definitions and protocol interfaces for GenshinIQ Source Adapters.
Every source adapter implements discover(), fetch(), parse(), normalize(), and validate().
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class VersionLifecycleState(str, Enum):
    """Formal lifecycle progression for a game update version."""
    DISCOVERED = "DISCOVERED"
    ACQUIRED = "ACQUIRED"
    PARSED = "PARSED"
    NORMALIZED = "NORMALIZED"
    VALIDATED = "VALIDATED"
    VERSIONED = "VERSIONED"
    PROVENANCE_VERIFIED = "PROVENANCE_VERIFIED"
    COMPLETENESS_AUDIT = "COMPLETENESS_AUDIT"
    CANDIDATE = "CANDIDATE"
    PROMOTED = "PROMOTED"
    ACTIVE = "ACTIVE"
    REJECTED = "REJECTED"


class AdapterDiscoveredItem(BaseModel):
    """Item discovered by an adapter during source polling/discovery."""
    source_id: str
    target_version: str
    entity_type: str
    identifier: str
    title_or_name: str
    uri_or_url: str
    retrieved_at: str
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)


class AdapterValidationResult(BaseModel):
    """Validation outcome for content normalized by an adapter."""
    is_valid: bool
    source_id: str
    target_version: str
    entity_count: int = 0
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class SourceAdapter(ABC):
    """
    Abstract Base Class for all GenshinIQ Source Adapters.
    Enforces a uniform, decoupled interface across official, datamined, theorycrafting, and account sources.
    """

    def __init__(self, source_id: str, domains: List[str], authority_tier: int):
        self.source_id = source_id
        self.domains = domains
        self.authority_tier = authority_tier

    @abstractmethod
    def discover(self, target_version: Optional[str] = None) -> List[AdapterDiscoveredItem]:
        """Check the source for newly released or updated data/documents."""
        pass

    @abstractmethod
    def fetch(self, item: AdapterDiscoveredItem) -> Dict[str, Any]:
        """Acquire raw payload from the upstream source with network resilience."""
        pass

    @abstractmethod
    def parse(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parse raw HTML/JSON/Config table into intermediate structure."""
        pass

    @abstractmethod
    def normalize(self, parsed_data: Dict[str, Any], target_version: str) -> Dict[str, Any]:
        """Convert intermediate structure into canonical GenshinIQ schema."""
        pass

    @abstractmethod
    def validate(self, normalized_data: Dict[str, Any]) -> AdapterValidationResult:
        """Validate normalized entities against domain rules and schema invariants."""
        pass
