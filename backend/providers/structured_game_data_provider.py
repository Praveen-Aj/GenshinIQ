"""Concrete structured game data provider loading canonical records from JSON repository."""

import json
from pathlib import Path
from typing import List, Optional, Dict
from backend.models.game_data import (
    CharacterData,
    WeaponData,
    ArtifactSetData,
    MaterialData,
    SearchResult,
)
from backend.providers.base_game_data import (
    CharacterProvider,
    WeaponProvider,
    ArtifactProvider,
    MaterialProvider,
)

GAME_DATA_DIR = Path("data/processed/game_data")


class StructuredGameDataProvider(
    CharacterProvider, WeaponProvider, ArtifactProvider, MaterialProvider
):
    """Loads and indexes canonical Genshin data with high-performance memory lookups."""

    def __init__(self, data_dir: Path = GAME_DATA_DIR):
        self.data_dir = data_dir
        self._characters_by_id: Dict[int, CharacterData] = {}
        self._characters_by_name: Dict[str, CharacterData] = {}

        self._weapons_by_id: Dict[int, WeaponData] = {}
        self._weapons_by_name: Dict[str, WeaponData] = {}

        self._artifacts_by_id: Dict[int, ArtifactSetData] = {}
        self._artifacts_by_name: Dict[str, ArtifactSetData] = {}

        self._materials_by_id: Dict[int, MaterialData] = {}
        self._materials_by_name: Dict[str, MaterialData] = {}

        self._load_all_data()

    def _load_all_data(self) -> None:
        """Load JSON datasets and build indexes."""
        # 1. Characters
        char_file = self.data_dir / "characters.json"
        if char_file.exists():
            with open(char_file, "r", encoding="utf-8") as f:
                for item in json.load(f):
                    char = CharacterData(**item)
                    self._characters_by_id[char.id] = char
                    self._characters_by_name[char.name.lower()] = char

        # 2. Weapons
        weapon_file = self.data_dir / "weapons.json"
        if weapon_file.exists():
            with open(weapon_file, "r", encoding="utf-8") as f:
                for item in json.load(f):
                    wep = WeaponData(**item)
                    self._weapons_by_id[wep.id] = wep
                    self._weapons_by_name[wep.name.lower()] = wep

        # 3. Artifacts
        art_file = self.data_dir / "artifacts.json"
        if art_file.exists():
            with open(art_file, "r", encoding="utf-8") as f:
                for item in json.load(f):
                    art = ArtifactSetData(**item)
                    self._artifacts_by_id[art.id] = art
                    self._artifacts_by_name[art.name.lower()] = art

        # 4. Materials
        mat_file = self.data_dir / "materials.json"
        if mat_file.exists():
            with open(mat_file, "r", encoding="utf-8") as f:
                for item in json.load(f):
                    mat = MaterialData(**item)
                    self._materials_by_id[mat.id] = mat
                    self._materials_by_name[mat.name.lower()] = mat

    # CharacterProvider Implementation
    def get_character(self, name_or_id: str) -> Optional[CharacterData]:
        clean = str(name_or_id).strip()
        if clean.isdigit() and int(clean) in self._characters_by_id:
            return self._characters_by_id[int(clean)]
        return self._characters_by_name.get(clean.lower())

    def list_characters(
        self,
        element: Optional[str] = None,
        weapon_type: Optional[str] = None,
        rarity: Optional[int] = None,
    ) -> List[CharacterData]:
        results = list(self._characters_by_id.values())
        if element:
            elem_lower = element.lower()
            results = [c for c in results if c.element.lower() == elem_lower]
        if weapon_type:
            wep_lower = weapon_type.lower()
            results = [c for c in results if c.weapon_type.lower() == wep_lower]
        if rarity:
            results = [c for c in results if c.rarity == rarity]
        return results

    # WeaponProvider Implementation
    def get_weapon(self, name_or_id: str) -> Optional[WeaponData]:
        clean = str(name_or_id).strip()
        if clean.isdigit() and int(clean) in self._weapons_by_id:
            return self._weapons_by_id[int(clean)]
        return self._weapons_by_name.get(clean.lower())

    def list_weapons(
        self,
        weapon_type: Optional[str] = None,
        rarity: Optional[int] = None,
    ) -> List[WeaponData]:
        results = list(self._weapons_by_id.values())
        if weapon_type:
            wep_lower = weapon_type.lower()
            results = [w for w in results if w.weapon_type.lower() == wep_lower]
        if rarity:
            results = [w for w in results if w.rarity == rarity]
        return results

    # ArtifactProvider Implementation
    def get_artifact_set(self, name_or_id: str) -> Optional[ArtifactSetData]:
        clean = str(name_or_id).strip()
        if clean.isdigit() and int(clean) in self._artifacts_by_id:
            return self._artifacts_by_id[int(clean)]
        return self._artifacts_by_name.get(clean.lower())

    def list_artifact_sets(self) -> List[ArtifactSetData]:
        return list(self._artifacts_by_id.values())

    # MaterialProvider Implementation
    def get_material(self, name_or_id: str) -> Optional[MaterialData]:
        clean = str(name_or_id).strip()
        if clean.isdigit() and int(clean) in self._materials_by_id:
            return self._materials_by_id[int(clean)]
        return self._materials_by_name.get(clean.lower())

    def list_materials(self, material_type: Optional[str] = None) -> List[MaterialData]:
        results = list(self._materials_by_id.values())
        if material_type:
            mat_lower = material_type.lower()
            results = [m for m in results if m.type.lower() == mat_lower]
        return results

    # Unified Search
    def search_all(self, query: str) -> List[SearchResult]:
        q = query.lower().strip()
        if not q:
            return []

        hits: List[SearchResult] = []

        # Search characters
        for char in self._characters_by_id.values():
            if q in char.name.lower() or (char.title and q in char.title.lower()) or (char.description and q in char.description.lower()):
                hits.append(
                    SearchResult(
                        id=char.id,
                        name=char.name,
                        category="character",
                        element_or_type=char.element,
                        rarity=char.rarity,
                        description=char.description or f"{char.rarity}-Star {char.element} {char.weapon_type}",
                    )
                )

        # Search weapons
        for wep in self._weapons_by_id.values():
            if q in wep.name.lower() or (wep.passive_name and q in wep.passive_name.lower()) or (wep.passive_desc and q in wep.passive_desc.lower()):
                hits.append(
                    SearchResult(
                        id=wep.id,
                        name=wep.name,
                        category="weapon",
                        element_or_type=wep.weapon_type,
                        rarity=wep.rarity,
                        description=wep.passive_desc or f"{wep.rarity}-Star {wep.weapon_type}",
                    )
                )

        # Search artifacts
        for art in self._artifacts_by_id.values():
            if q in art.name.lower() or q in art.bonus_2pc.lower() or (art.bonus_4pc and q in art.bonus_4pc.lower()):
                hits.append(
                    SearchResult(
                        id=art.id,
                        name=art.name,
                        category="artifact",
                        element_or_type="Artifact Set",
                        rarity=max(art.rarities) if art.rarities else 5,
                        description=art.bonus_2pc,
                    )
                )

        # Search materials
        for mat in self._materials_by_id.values():
            if q in mat.name.lower() or (mat.description and q in mat.description.lower()):
                hits.append(
                    SearchResult(
                        id=mat.id,
                        name=mat.name,
                        category="material",
                        element_or_type=mat.type,
                        rarity=mat.rarity,
                        description=mat.description,
                    )
                )

        return hits


game_data_provider = StructuredGameDataProvider()
