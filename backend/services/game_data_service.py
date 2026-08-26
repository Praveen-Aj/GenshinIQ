"""Unified Game Data Service providing high-level lookups and search."""

from typing import List, Optional
from backend.models.game_data import (
    CharacterData,
    WeaponData,
    ArtifactSetData,
    MaterialData,
    SearchResult,
)
from backend.providers.structured_game_data_provider import (
    game_data_provider,
    StructuredGameDataProvider,
)


class GameDataService:
    """Service facade for canonical game data lookups."""

    def __init__(self, provider: Optional[StructuredGameDataProvider] = None):
        self.provider = provider or game_data_provider

    def get_character(self, name_or_id: str) -> Optional[CharacterData]:
        return self.provider.get_character(name_or_id)

    def list_characters(
        self,
        element: Optional[str] = None,
        weapon_type: Optional[str] = None,
        rarity: Optional[int] = None,
    ) -> List[CharacterData]:
        return self.provider.list_characters(element=element, weapon_type=weapon_type, rarity=rarity)

    def get_weapon(self, name_or_id: str) -> Optional[WeaponData]:
        return self.provider.get_weapon(name_or_id)

    def list_weapons(
        self,
        weapon_type: Optional[str] = None,
        rarity: Optional[int] = None,
    ) -> List[WeaponData]:
        return self.provider.list_weapons(weapon_type=weapon_type, rarity=rarity)

    def get_artifact_set(self, name_or_id: str) -> Optional[ArtifactSetData]:
        return self.provider.get_artifact_set(name_or_id)

    def list_artifact_sets(self) -> List[ArtifactSetData]:
        return self.provider.list_artifact_sets()

    def get_material(self, name_or_id: str) -> Optional[MaterialData]:
        return self.provider.get_material(name_or_id)

    def list_materials(self, material_type: Optional[str] = None) -> List[MaterialData]:
        return self.provider.list_materials(material_type=material_type)

    def search(self, query: str) -> List[SearchResult]:
        return self.provider.search_all(query=query)


game_data_service = GameDataService()
