"""Abstract interfaces for Genshin structured data providers."""

from abc import ABC, abstractmethod
from typing import List, Optional
from backend.models.game_data import (
    CharacterData,
    WeaponData,
    ArtifactSetData,
    MaterialData,
    SearchResult,
)


class CharacterProvider(ABC):
    """Abstract interface for querying character data."""

    @abstractmethod
    def get_character(self, name_or_id: str) -> Optional[CharacterData]:
        """Get single character by ID or name."""
        pass

    @abstractmethod
    def list_characters(
        self,
        element: Optional[str] = None,
        weapon_type: Optional[str] = None,
        rarity: Optional[int] = None,
    ) -> List[CharacterData]:
        """List characters with optional filters."""
        pass


class WeaponProvider(ABC):
    """Abstract interface for querying weapon data."""

    @abstractmethod
    def get_weapon(self, name_or_id: str) -> Optional[WeaponData]:
        """Get single weapon by ID or name."""
        pass

    @abstractmethod
    def list_weapons(
        self,
        weapon_type: Optional[str] = None,
        rarity: Optional[int] = None,
    ) -> List[WeaponData]:
        """List weapons with optional filters."""
        pass


class ArtifactProvider(ABC):
    """Abstract interface for querying artifact set data."""

    @abstractmethod
    def get_artifact_set(self, name_or_id: str) -> Optional[ArtifactSetData]:
        """Get single artifact set by ID or name."""
        pass

    @abstractmethod
    def list_artifact_sets(self) -> List[ArtifactSetData]:
        """List all artifact sets."""
        pass


class MaterialProvider(ABC):
    """Abstract interface for querying material data."""

    @abstractmethod
    def get_material(self, name_or_id: str) -> Optional[MaterialData]:
        """Get single material by ID or name."""
        pass

    @abstractmethod
    def list_materials(self, material_type: Optional[str] = None) -> List[MaterialData]:
        """List materials with optional type filter."""
        pass
