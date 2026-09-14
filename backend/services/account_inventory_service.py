"""Account Inventory Service for GenshinIQ (Phase 6).

Handles:
- Ingestion & validation of GOOD v3 (Genshin Open Object Description) exports
- Preservation of raw GOOD JSON alongside normalized AccountSnapshot
- Deterministic canonical entity resolution (characters, weapons, artifact sets, materials)
- Multiple weapon copy & artifact instance identity preservation
- Deterministic snapshot diffing
- Runtime disk caching in data/runtime/account/
"""

import hashlib
import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.models.account import (
    AccountArtifactInstance,
    AccountCharacterInstance,
    AccountDiff,
    AccountMaterialInstance,
    AccountSnapshot,
    AccountSummary,
    AccountWeaponInstance,
    ResolutionStatus,
    SnapshotMetadata,
    UnresolvedRecord,
)
from backend.services.game_data_service import game_data_service

logger = logging.getLogger("genshiniq.account_inventory")

ACCOUNT_RUNTIME_DIR = Path("data/runtime/account")
DEFAULT_GOOD_FILE = Path("genshinData_GOOD_2026_09_07_22_00.json")

# Stat Key to Human-Readable Name Map
STAT_KEY_MAP: Dict[str, str] = {
    "hp": "HP",
    "hp_": "HP%",
    "atk": "ATK",
    "atk_": "ATK%",
    "def": "DEF",
    "def_": "DEF%",
    "eleMas": "Elemental Mastery",
    "enerRech_": "Energy Recharge",
    "critRate_": "CRIT Rate",
    "critDMG_": "CRIT DMG",
    "heal_": "Healing Bonus",
    "pyro_dmg_": "Pyro DMG Bonus",
    "hydro_dmg_": "Hydro DMG Bonus",
    "anemo_dmg_": "Anemo DMG Bonus",
    "electro_dmg_": "Electro DMG Bonus",
    "dendro_dmg_": "Dendro DMG Bonus",
    "cryo_dmg_": "Cryo DMG Bonus",
    "geo_dmg_": "Geo DMG Bonus",
    "physical_dmg_": "Physical DMG Bonus",
}

# Common Character Nicknames/Variants to Canonical Names
CHARACTER_ALIASES: Dict[str, str] = {
    "hutao": "Hu Tao",
    "hu tao": "Hu Tao",
    "kaedeharakazuha": "Kaedehara Kazuha",
    "kazuha": "Kaedehara Kazuha",
    "kamisatoayaka": "Kamisato Ayaka",
    "ayaka": "Kamisato Ayaka",
    "kamisatoayato": "Kamisato Ayato",
    "ayato": "Kamisato Ayato",
    "sangonomiyakokomi": "Sangonomiya Kokomi",
    "kokomi": "Sangonomiya Kokomi",
    "aratakiitto": "Arataki Itto",
    "itto": "Arataki Itto",
    "kukishinobu": "Kuki Shinobu",
    "shinobu": "Kuki Shinobu",
    "yaemiko": "Yae Miko",
    "miko": "Yae Miko",
    "shikanoinheizou": "Shikanoin Heizou",
    "heizou": "Shikanoin Heizou",
    "kujousara": "Kujou Sara",
    "sara": "Kujou Sara",
    "raidenshogun": "Raiden Shogun",
    "raiden": "Raiden Shogun",
    "shogun": "Raiden Shogun",
    "alhaitham": "Alhaitham",
    "traveler": "Traveler",
}


def normalize_lookup_key(text: str) -> str:
    """Normalize string to lowercase alphanumeric for robust matching."""
    if not text:
        return ""
    return re.sub(r"[^a-z0-9]", "", text.lower())


class AccountInventoryException(Exception):
    """Base exception for account inventory validation and resolution errors."""
    pass


class AccountInventoryService:
    """Service managing the player's full account inventory imported from GOOD v3."""

    def __init__(self, runtime_dir: Optional[Path] = None):
        self.runtime_dir = runtime_dir or ACCOUNT_RUNTIME_DIR
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self._active_snapshot: Optional[AccountSnapshot] = None

        # Build canonical lookup maps
        self._build_canonical_lookups()

    def _build_canonical_lookups(self):
        """Compile fast lookup dictionaries for characters, weapons, artifacts, materials."""
        # 1. Characters: normalized_key -> CharacterData
        chars = game_data_service.list_characters()
        self._character_map: Dict[str, Any] = {}
        for c in chars:
            self._character_map[normalize_lookup_key(c.name)] = c
            self._character_map[c.name.lower()] = c

        # 2. Weapons: normalized_key -> WeaponData
        weapons = game_data_service.list_weapons()
        self._weapon_map: Dict[str, Any] = {}
        for w in weapons:
            self._weapon_map[normalize_lookup_key(w.name)] = w
            self._weapon_map[w.name.lower()] = w

        # 3. Artifact Sets: normalized_key -> ArtifactSetData
        sets = game_data_service.list_artifact_sets()
        self._artifact_set_map: Dict[str, Any] = {}
        for s in sets:
            self._artifact_set_map[normalize_lookup_key(s.name)] = s
            self._artifact_set_map[s.name.lower()] = s

        # 4. Materials: normalized_key -> MaterialData
        mats = game_data_service.list_materials()
        self._material_map: Dict[str, Any] = {}
        for m in mats:
            self._material_map[normalize_lookup_key(m.name)] = m
            self._material_map[m.name.lower()] = m

    # ==========================================================================
    # Validation & Parsing
    # ==========================================================================

    def validate_and_parse_good_payload(self, raw_json: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        """
        Validate GOOD v3 schema invariants, data types, and numeric ranges.
        Returns: (validated_json, sha256_hash)
        Raises AccountInventoryException on invalid schema or corrupted data.
        """
        if not isinstance(raw_json, dict):
            raise AccountInventoryException("GOOD payload must be a JSON object.")

        # 1. Format Check
        fmt = str(raw_json.get("format", "")).upper()
        if fmt != "GOOD":
            raise AccountInventoryException(f"Unsupported format '{fmt}'. Expected 'GOOD'.")

        # 2. Version Check (Must be 3)
        version = raw_json.get("version")
        if version not in (3, 3.0, "3"):
            raise AccountInventoryException(
                f"Unsupported GOOD version '{version}'. GenshinIQ requires GOOD v3."
            )

        # 3. Collection Type Checks
        for col in ["characters", "weapons", "artifacts"]:
            if col in raw_json and not isinstance(raw_json[col], list):
                raise AccountInventoryException(f"Field '{col}' must be a list of objects.")

        if "materials" in raw_json and not isinstance(raw_json["materials"], dict):
            raise AccountInventoryException("Field 'materials' must be a dictionary of {key: quantity}.")

        # 4. Compute SHA-256 hash of raw input
        json_bytes = json.dumps(raw_json, sort_keys=True).encode("utf-8")
        payload_hash = hashlib.sha256(json_bytes).hexdigest()

        # 5. Sanity Range Checks on Characters
        for idx, char in enumerate(raw_json.get("characters", [])):
            if not isinstance(char, dict) or "key" not in char:
                raise AccountInventoryException(f"Character at index {idx} missing 'key' field.")
            lvl = char.get("level", 1)
            if not isinstance(lvl, (int, float)) or lvl < 1 or lvl > 90:
                raise AccountInventoryException(f"Character '{char.get('key')}' has invalid level {lvl}. Must be 1-90.")
            asc = char.get("ascension", 0)
            if not isinstance(asc, int) or asc < 0 or asc > 6:
                raise AccountInventoryException(f"Character '{char.get('key')}' has invalid ascension {asc}. Must be 0-6.")
            cons = char.get("constellation", 0)
            if not isinstance(cons, int) or cons < 0 or cons > 6:
                raise AccountInventoryException(f"Character '{char.get('key')}' has invalid constellation {cons}. Must be 0-6.")

        # 6. Sanity Range Checks on Weapons
        for idx, w in enumerate(raw_json.get("weapons", [])):
            if not isinstance(w, dict) or "key" not in w:
                raise AccountInventoryException(f"Weapon at index {idx} missing 'key' field.")
            lvl = w.get("level", 1)
            if not isinstance(lvl, (int, float)) or lvl < 1 or lvl > 90:
                raise AccountInventoryException(f"Weapon '{w.get('key')}' has invalid level {lvl}. Must be 1-90.")
            ref = w.get("refinement", 1)
            if not isinstance(ref, int) or ref < 1 or ref > 5:
                raise AccountInventoryException(f"Weapon '{w.get('key')}' has invalid refinement {ref}. Must be 1-5.")

        # 7. Sanity Range Checks on Artifacts
        for idx, a in enumerate(raw_json.get("artifacts", [])):
            if not isinstance(a, dict) or "setKey" not in a or "slotKey" not in a:
                raise AccountInventoryException(f"Artifact at index {idx} missing 'setKey' or 'slotKey'.")
            slot = str(a.get("slotKey", "")).lower()
            if slot not in ("flower", "plume", "sands", "goblet", "circlet"):
                raise AccountInventoryException(f"Artifact at index {idx} has invalid slotKey '{slot}'.")
            rarity = a.get("rarity", 5)
            if not isinstance(rarity, int) or rarity < 1 or rarity > 5:
                raise AccountInventoryException(f"Artifact at index {idx} has invalid rarity {rarity}. Must be 1-5.")
            lvl = a.get("level", 0)
            if not isinstance(lvl, (int, float)) or lvl < 0 or lvl > 20:
                raise AccountInventoryException(f"Artifact at index {idx} has invalid level {lvl}. Must be 0-20.")

        # 8. Sanity Range Checks on Materials
        for mkey, qty in raw_json.get("materials", {}).items():
            if not isinstance(qty, (int, float)) or qty < 0:
                raise AccountInventoryException(f"Material '{mkey}' has invalid quantity {qty}. Must be >= 0.")

        return raw_json, payload_hash

    # ==========================================================================
    # Entity Resolution & Normalization
    # ==========================================================================

    def normalize_good_to_snapshot(
        self,
        good_json: Dict[str, Any],
        source_hash: str,
        account_uid: Optional[str] = None,
    ) -> AccountSnapshot:
        """
        Transform raw validated GOOD v3 JSON into a canonical AccountSnapshot.
        Resolves canonical names/IDs while preserving inventory instances.
        """
        unresolved_records: List[UnresolvedRecord] = []

        # 1. Normalize Characters
        normalized_characters: List[AccountCharacterInstance] = []
        for char in good_json.get("characters", []):
            gkey = char["key"]
            norm_key = normalize_lookup_key(gkey)

            canon_char = None
            status = ResolutionStatus.UNRESOLVED

            # Exact or alias check
            if norm_key in self._character_map:
                canon_char = self._character_map[norm_key]
                status = ResolutionStatus.EXACT_MATCH if gkey.lower() == canon_char.name.lower() else ResolutionStatus.ALIAS_MATCH
            elif gkey.lower() in CHARACTER_ALIASES:
                alias_name = CHARACTER_ALIASES[gkey.lower()]
                canon_char = self._character_map.get(normalize_lookup_key(alias_name))
                status = ResolutionStatus.ALIAS_MATCH

            if canon_char:
                c_id = canon_char.id
                c_name = canon_char.name
                elem = canon_char.element
                rarity = canon_char.rarity
                wtype = canon_char.weapon_type
            else:
                c_id = None
                c_name = gkey
                elem = None
                rarity = None
                wtype = None
                unresolved_records.append(
                    UnresolvedRecord(
                        category="character",
                        good_key=gkey,
                        details=char,
                        reason="Character not found in canonical database",
                    )
                )

            normalized_characters.append(
                AccountCharacterInstance(
                    canonical_id=c_id,
                    canonical_name=c_name,
                    good_key=gkey,
                    element=elem,
                    rarity=rarity,
                    weapon_type=wtype,
                    level=int(char.get("level", 1)),
                    ascension=int(char.get("ascension", 0)),
                    constellation=int(char.get("constellation", 0)),
                    talent_levels=char.get("talent", {}),
                    resolution_status=status,
                )
            )

        # 2. Normalize Weapons (Preserving duplicate instances independently)
        normalized_weapons: List[AccountWeaponInstance] = []
        for idx, w in enumerate(good_json.get("weapons", [])):
            gkey = w["key"]
            norm_key = normalize_lookup_key(gkey)
            raw_id = w.get("id")

            canon_w = self._weapon_map.get(norm_key)
            if canon_w:
                w_id = canon_w.id
                w_name = canon_w.name
                w_type = canon_w.weapon_type
                w_rarity = canon_w.rarity
                status = ResolutionStatus.EXACT_MATCH if gkey.lower() == canon_w.name.lower() else ResolutionStatus.ALIAS_MATCH
            else:
                w_id = None
                w_name = gkey
                w_type = None
                w_rarity = None
                status = ResolutionStatus.UNRESOLVED
                unresolved_records.append(
                    UnresolvedRecord(
                        category="weapon",
                        good_key=gkey,
                        details=w,
                        reason="Weapon not found in canonical database",
                    )
                )

            # Assign stable deterministic instance ID
            if raw_id is not None:
                inst_id = f"weapon_good_{raw_id}"
            else:
                # Deterministic fallback ID based on content & sequential index
                inst_id = f"weapon_inst_{w_id or norm_key}_{idx}"

            # Resolve equipped location to canonical character name
            loc_key = w.get("location", "").strip()
            loc_canonical = None
            if loc_key:
                norm_loc = normalize_lookup_key(loc_key)
                if norm_loc in self._character_map:
                    loc_canonical = self._character_map[norm_loc].name
                elif loc_key.lower() in CHARACTER_ALIASES:
                    loc_canonical = CHARACTER_ALIASES[loc_key.lower()]
                else:
                    loc_canonical = loc_key

            normalized_weapons.append(
                AccountWeaponInstance(
                    account_instance_id=inst_id,
                    canonical_id=w_id,
                    canonical_name=w_name,
                    good_key=gkey,
                    weapon_type=w_type,
                    rarity=w_rarity,
                    level=int(w.get("level", 1)),
                    ascension=int(w.get("ascension", 0)),
                    refinement=int(w.get("refinement", 1)),
                    location=loc_canonical,
                    locked=bool(w.get("lock", False)),
                    raw_id=raw_id,
                    resolution_status=status,
                )
            )

        # 3. Normalize Artifacts (Preserving each distinct piece and substats)
        normalized_artifacts: List[AccountArtifactInstance] = []
        for idx, a in enumerate(good_json.get("artifacts", [])):
            set_key = a["setKey"]
            norm_set_key = normalize_lookup_key(set_key)
            raw_id = a.get("id")

            canon_set = self._artifact_set_map.get(norm_set_key)
            if canon_set:
                set_id = canon_set.id
                set_name = canon_set.name
                status = ResolutionStatus.EXACT_MATCH if set_key.lower() == canon_set.name.lower() else ResolutionStatus.ALIAS_MATCH
            else:
                set_id = None
                set_name = set_key
                status = ResolutionStatus.UNRESOLVED
                unresolved_records.append(
                    UnresolvedRecord(
                        category="artifact_set",
                        good_key=set_key,
                        details=a,
                        reason="Artifact set not found in canonical database",
                    )
                )

            # Assign stable deterministic instance ID
            if raw_id is not None:
                inst_id = f"artifact_good_{raw_id}"
            else:
                inst_id = f"artifact_inst_{set_id or norm_set_key}_{a.get('slotKey')}_{idx}"

            # Location resolution
            loc_key = a.get("location", "").strip()
            loc_canonical = None
            if loc_key:
                norm_loc = normalize_lookup_key(loc_key)
                if norm_loc in self._character_map:
                    loc_canonical = self._character_map[norm_loc].name
                elif loc_key.lower() in CHARACTER_ALIASES:
                    loc_canonical = CHARACTER_ALIASES[loc_key.lower()]
                else:
                    loc_canonical = loc_key

            # Substats formatting
            formatted_substats = []
            for s in a.get("substats", []):
                skey = s.get("key", "")
                val = float(s.get("value", 0.0))
                sname = STAT_KEY_MAP.get(skey, skey)
                formatted_substats.append({
                    "key": skey,
                    "name": sname,
                    "value": val,
                })

            main_stat_key = a.get("mainStatKey", "")
            main_stat_name = STAT_KEY_MAP.get(main_stat_key, main_stat_key)

            normalized_artifacts.append(
                AccountArtifactInstance(
                    account_instance_id=inst_id,
                    canonical_set_id=set_id,
                    canonical_set_name=set_name,
                    good_set_key=set_key,
                    slot=str(a.get("slotKey", "")).lower(),
                    rarity=int(a.get("rarity", 5)),
                    level=int(a.get("level", 0)),
                    main_stat_key=main_stat_key,
                    main_stat_name=main_stat_name,
                    main_stat_value=a.get("mainStatValue"),
                    substats=formatted_substats,
                    unactivated_substats=a.get("unactivatedSubstats", []),
                    location=loc_canonical,
                    locked=bool(a.get("lock", False)),
                    raw_id=raw_id,
                    resolution_status=status,
                )
            )

        # 4. Normalize Materials
        normalized_materials: List[AccountMaterialInstance] = []
        for mkey, qty in good_json.get("materials", {}).items():
            norm_key = normalize_lookup_key(mkey)
            canon_m = self._material_map.get(norm_key)

            if canon_m:
                m_id = canon_m.id
                m_name = canon_m.name
                m_type = canon_m.type
                m_rarity = canon_m.rarity
                status = ResolutionStatus.EXACT_MATCH if mkey.lower() == canon_m.name.lower() else ResolutionStatus.ALIAS_MATCH
            else:
                m_id = None
                m_name = None
                m_type = "General / Unmapped"
                m_rarity = None
                status = ResolutionStatus.UNRESOLVED
                unresolved_records.append(
                    UnresolvedRecord(
                        category="material",
                        good_key=mkey,
                        details={"quantity": qty},
                        reason="Material not in canonical farming database",
                    )
                )

            normalized_materials.append(
                AccountMaterialInstance(
                    canonical_id=m_id,
                    canonical_name=m_name,
                    good_key=mkey,
                    quantity=int(qty),
                    material_type=m_type,
                    rarity=m_rarity,
                    resolution_status=status,
                )
            )

        # Build Metadata
        now_utc = datetime.now(timezone.utc).isoformat()
        metadata = SnapshotMetadata(
            imported_at=now_utc,
            good_version=int(good_json.get("version", 3)),
            source=str(good_json.get("source", "Inventory_Kamera")),
            source_file_hash=source_hash,
            parser_version="1.0.0",
            account_uid=account_uid,
            character_count=len(normalized_characters),
            weapon_count=len(normalized_weapons),
            artifact_count=len(normalized_artifacts),
            material_count=len(normalized_materials),
            unresolved_count=len(unresolved_records),
        )

        return AccountSnapshot(
            metadata=metadata,
            characters=normalized_characters,
            weapons=normalized_weapons,
            artifacts=normalized_artifacts,
            materials=normalized_materials,
            unresolved_records=unresolved_records,
        )

    # ==========================================================================
    # Persistence & Snapshot Management
    # ==========================================================================

    def import_good_file(
        self,
        file_path: Path,
        account_uid: Optional[str] = None,
    ) -> AccountSnapshot:
        """Read, validate, normalize, and save GOOD v3 file from disk."""
        if not file_path.exists():
            raise AccountInventoryException(f"GOOD file not found at: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        return self.import_good_payload(raw_data, account_uid=account_uid)

    def import_good_payload(
        self,
        raw_json: Dict[str, Any],
        account_uid: Optional[str] = None,
    ) -> AccountSnapshot:
        """Validate, normalize, and atomically persist raw and normalized snapshots."""
        valid_json, source_hash = self.validate_and_parse_good_payload(raw_json)
        snapshot = self.normalize_good_to_snapshot(valid_json, source_hash, account_uid=account_uid)

        # Persist raw snapshot
        raw_path = self.runtime_dir / "raw_good_snapshot.json"
        with open(raw_path, "w", encoding="utf-8") as f:
            json.dump(valid_json, f, indent=2)

        # Persist normalized snapshot
        norm_path = self.runtime_dir / "normalized_account_snapshot.json"
        with open(norm_path, "w", encoding="utf-8") as f:
            json.dump(snapshot.model_dump(), f, indent=2)

        # Persist snapshot metadata
        meta_path = self.runtime_dir / "snapshot_meta.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(snapshot.metadata.model_dump(), f, indent=2)

        self._active_snapshot = snapshot
        logger.info(
            f"Successfully imported GOOD v3 snapshot ({snapshot.metadata.character_count} chars, "
            f"{snapshot.metadata.weapon_count} weapons, {snapshot.metadata.artifact_count} artifacts, "
            f"{snapshot.metadata.material_count} materials)."
        )
        return snapshot

    def get_active_snapshot(self) -> Optional[AccountSnapshot]:
        """Retrieve active in-memory snapshot, loading from disk or default project export if needed."""
        if self._active_snapshot:
            return self._active_snapshot

        # Try loading persisted runtime snapshot
        norm_path = self.runtime_dir / "normalized_account_snapshot.json"
        if norm_path.exists():
            try:
                with open(norm_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._active_snapshot = AccountSnapshot(**data)
                return self._active_snapshot
            except Exception as e:
                logger.warning(f"Failed loading persisted account snapshot: {e}")

        # Fallback: Auto-import project's default GOOD export if available
        if DEFAULT_GOOD_FILE.exists():
            try:
                logger.info("Initializing account snapshot from default project GOOD export...")
                self._active_snapshot = self.import_good_file(DEFAULT_GOOD_FILE)
                return self._active_snapshot
            except Exception as e:
                logger.error(f"Failed auto-importing default GOOD export: {e}")

        return None

    # ==========================================================================
    # Summary & Deterministic Diff
    # ==========================================================================

    def get_summary(self, snapshot: Optional[AccountSnapshot] = None) -> AccountSummary:
        """Compute deterministic inventory summary metrics without build/optimization calculations."""
        snap = snapshot or self.get_active_snapshot()
        if not snap:
            return AccountSummary(
                total_characters=0,
                built_characters_lvl90=0,
                built_characters_lvl80_plus=0,
                total_weapon_instances=0,
                leveled_weapons_lvl90=0,
                total_artifact_instances=0,
                five_star_artifacts=0,
                plus_20_artifacts=0,
                equipped_artifacts=0,
                total_material_types=0,
                total_mora=0,
                unresolved_material_types=0,
                imported_at="NEVER",
                source_format="NONE",
            )

        # Character metrics
        c_total = len(snap.characters)
        c_lvl90 = sum(1 for c in snap.characters if c.level == 90)
        c_lvl80_plus = sum(1 for c in snap.characters if c.level >= 80)

        # Weapon metrics
        w_total = len(snap.weapons)
        w_lvl90 = sum(1 for w in snap.weapons if w.level == 90)

        # Artifact metrics
        a_total = len(snap.artifacts)
        a_5star = sum(1 for a in snap.artifacts if a.rarity == 5)
        a_plus20 = sum(1 for a in snap.artifacts if a.level == 20)
        a_equipped = sum(1 for a in snap.artifacts if a.location)

        # Material metrics
        m_total = len(snap.materials)
        mora = next((m.quantity for m in snap.materials if m.good_key.lower() == "mora"), 0)
        unresolved_mats = sum(1 for m in snap.materials if m.resolution_status == ResolutionStatus.UNRESOLVED)

        return AccountSummary(
            total_characters=c_total,
            built_characters_lvl90=c_lvl90,
            built_characters_lvl80_plus=c_lvl80_plus,
            total_weapon_instances=w_total,
            leveled_weapons_lvl90=w_lvl90,
            total_artifact_instances=a_total,
            five_star_artifacts=a_5star,
            plus_20_artifacts=a_plus20,
            equipped_artifacts=a_equipped,
            total_material_types=m_total,
            total_mora=mora,
            unresolved_material_types=unresolved_mats,
            imported_at=snap.metadata.imported_at,
            source_format=f"GOOD v{snap.metadata.good_version}",
        )

    def compute_diff(self, old_snapshot: AccountSnapshot, new_snapshot: AccountSnapshot) -> AccountDiff:
        """
        Deterministically compare two snapshots to detect inventory changes.
        """
        # 1. Characters diff
        old_chars = {c.canonical_name: c for c in old_snapshot.characters}
        new_chars = {c.canonical_name: c for c in new_snapshot.characters}

        c_added = [name for name in new_chars if name not in old_chars]
        c_removed = [name for name in old_chars if name not in new_chars]
        c_modified = []

        for name, n_char in new_chars.items():
            if name in old_chars:
                o_char = old_chars[name]
                changes = {}
                if n_char.level != o_char.level:
                    changes["level"] = {"old": o_char.level, "new": n_char.level}
                if n_char.constellation != o_char.constellation:
                    changes["constellation"] = {"old": o_char.constellation, "new": n_char.constellation}
                if n_char.talent_levels != o_char.talent_levels:
                    changes["talents"] = {"old": o_char.talent_levels, "new": n_char.talent_levels}
                if changes:
                    c_modified.append({"character": name, "changes": changes})

        # 2. Weapons diff
        old_weapons = {w.account_instance_id: w for w in old_snapshot.weapons}
        new_weapons = {w.account_instance_id: w for w in new_snapshot.weapons}

        w_added = sum(1 for wid in new_weapons if wid not in old_weapons)
        w_removed = sum(1 for wid in old_weapons if wid not in new_weapons)
        w_modified = []

        for wid, n_w in new_weapons.items():
            if wid in old_weapons:
                o_w = old_weapons[wid]
                changes = {}
                if n_w.level != o_w.level:
                    changes["level"] = {"old": o_w.level, "new": n_w.level}
                if n_w.refinement != o_w.refinement:
                    changes["refinement"] = {"old": o_w.refinement, "new": n_w.refinement}
                if n_w.location != o_w.location:
                    changes["location"] = {"old": o_w.location, "new": n_w.location}
                if changes:
                    w_modified.append({"weapon": n_w.canonical_name, "instance_id": wid, "changes": changes})

        # 3. Artifacts diff
        old_art_ids = {a.account_instance_id for a in old_snapshot.artifacts}
        new_art_ids = {a.account_instance_id for a in new_snapshot.artifacts}

        a_added = len(new_art_ids - old_art_ids)
        a_removed = len(old_art_ids - new_art_ids)

        # 4. Materials diff
        old_mats = {m.good_key: m.quantity for m in old_snapshot.materials}
        new_mats = {m.good_key: m.quantity for m in new_snapshot.materials}

        mat_changes = {}
        all_mat_keys = set(old_mats.keys()) | set(new_mats.keys())
        for mk in all_mat_keys:
            old_qty = old_mats.get(mk, 0)
            new_qty = new_mats.get(mk, 0)
            if old_qty != new_qty:
                mat_changes[mk] = {"old": old_qty, "new": new_qty}

        return AccountDiff(
            characters_added=sorted(c_added),
            characters_modified=c_modified,
            characters_removed=sorted(c_removed),
            weapons_added_count=w_added,
            weapons_removed_count=w_removed,
            weapons_modified=w_modified,
            artifacts_added_count=a_added,
            artifacts_removed_count=a_removed,
            materials_changed=mat_changes,
        )


account_inventory_service = AccountInventoryService()
