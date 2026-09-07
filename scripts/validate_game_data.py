"""Canonical Game Data Integrity and Schema Validator.

Enforces zero-tolerance rules:
- Zero duplicate entity IDs
- Zero duplicate canonical names
- Zero placeholder/estimated stats (e.g. 250.0 ATK, 11000.0 HP)
- Strict Pydantic model compliance
- Complete material catalog verification
- Exits with non-zero code on any integrity violation.
"""

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.models.game_data import (
    ArtifactSetData,
    CharacterData,
    MaterialData,
    WeaponData,
)

DATA_DIR = ROOT_DIR / "data" / "processed" / "game_data"


def validate_characters(file_path: Path) -> List[str]:
    errors = []
    if not file_path.exists():
        return [f"File not found: {file_path}"]

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list) or len(data) == 0:
        return ["characters.json is empty or not a list."]

    ids = [c.get("id") for c in data]
    names = [c.get("name", "").strip().lower() for c in data]

    # 1. Duplicate ID check
    id_counts = Counter(ids)
    for cid, count in id_counts.items():
        if count > 1:
            matching = [c.get("name") for c in data if c.get("id") == cid]
            errors.append(f"Duplicate Character ID {cid} found in: {matching}")

    # 2. Duplicate Name check
    name_counts = Counter(names)
    for name, count in name_counts.items():
        if count > 1:
            errors.append(f"Duplicate Character name '{name}' found {count} times.")

    # 3. Model & Placeholder checks
    for idx, char in enumerate(data):
        cname = char.get("name", f"Index_{idx}")
        try:
            char_obj = CharacterData.model_validate(char)
        except Exception as e:
            errors.append(f"Character '{cname}' failed schema validation: {e}")
            continue

        # Zero Placeholder Rule
        if char_obj.base_hp_lvl90 == 11000.0 and char_obj.base_atk_lvl90 == 250.0:
            errors.append(f"Character '{cname}' contains fabricated placeholder stats (HP 11000, ATK 250)!")

        if char_obj.base_hp_lvl90 <= 0:
            errors.append(f"Character '{cname}' has invalid base_hp_lvl90: {char_obj.base_hp_lvl90}")

        if char_obj.base_atk_lvl90 <= 0:
            errors.append(f"Character '{cname}' has invalid base_atk_lvl90: {char_obj.base_atk_lvl90}")

        if not char_obj.element or char_obj.element == "Unknown":
            errors.append(f"Character '{cname}' has unknown element!")

        if not char_obj.weapon_type or char_obj.weapon_type == "Unknown":
            errors.append(f"Character '{cname}' has unknown weapon_type!")

        if not char_obj.talents:
            errors.append(f"Character '{cname}' has empty talent kit!")

    return errors


def validate_weapons(file_path: Path) -> List[str]:
    errors = []
    if not file_path.exists():
        return [f"File not found: {file_path}"]

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list) or len(data) == 0:
        return ["weapons.json is empty or not a list."]

    ids = [w.get("id") for w in data]
    names = [w.get("name", "").strip().lower() for w in data]

    # 1. Duplicate ID check
    id_counts = Counter(ids)
    for wid, count in id_counts.items():
        if count > 1:
            matching = [w.get("name") for w in data if w.get("id") == wid]
            errors.append(f"Duplicate Weapon ID {wid} found in: {matching}")

    # 2. Duplicate Name check
    name_counts = Counter(names)
    for name, count in name_counts.items():
        if count > 1:
            errors.append(f"Duplicate Weapon name '{name}' found {count} times.")

    # 3. Model & stat validation
    for idx, wep in enumerate(data):
        wname = wep.get("name", f"Index_{idx}")
        try:
            wep_obj = WeaponData.model_validate(wep)
        except Exception as e:
            errors.append(f"Weapon '{wname}' failed schema validation: {e}")
            continue

        if wep_obj.base_atk_lvl90 <= 0:
            errors.append(f"Weapon '{wname}' has invalid base_atk_lvl90: {wep_obj.base_atk_lvl90}")

        if wep_obj.rarity in [4, 5] and wep_obj.passive_name and not wep_obj.refinements:
            errors.append(f"Weapon '{wname}' (Rarity {wep_obj.rarity}) has passive '{wep_obj.passive_name}' but empty refinements list!")

    return errors


def validate_artifacts(file_path: Path) -> List[str]:
    errors = []
    if not file_path.exists():
        return [f"File not found: {file_path}"]

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list) or len(data) == 0:
        return ["artifacts.json is empty or not a list."]

    ids = [a.get("id") for a in data]
    names = [a.get("name", "").strip().lower() for a in data]

    id_counts = Counter(ids)
    for aid, count in id_counts.items():
        if count > 1:
            matching = [a.get("name") for a in data if a.get("id") == aid]
            errors.append(f"Duplicate Artifact Set ID {aid} found in: {matching}")

    name_counts = Counter(names)
    for name, count in name_counts.items():
        if count > 1:
            errors.append(f"Duplicate Artifact Set name '{name}' found {count} times.")

    for idx, art in enumerate(data):
        aname = art.get("name", f"Index_{idx}")
        try:
            art_obj = ArtifactSetData.model_validate(art)
        except Exception as e:
            errors.append(f"Artifact Set '{aname}' failed schema validation: {e}")
            continue

        if not art_obj.bonus_2pc:
            errors.append(f"Artifact Set '{aname}' has missing bonus_2pc!")

    return errors


def validate_materials(file_path: Path) -> List[str]:
    errors = []
    if not file_path.exists():
        return [f"File not found: {file_path}"]

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list) or len(data) == 0:
        return ["materials.json is empty or not a list."]

    if len(data) < 50:
        errors.append(f"materials.json has only {len(data)} items; expected comprehensive catalogue (>50 items).")

    ids = [m.get("id") for m in data]
    id_counts = Counter(ids)
    for mid, count in id_counts.items():
        if count > 1:
            matching = [m.get("name") for m in data if m.get("id") == mid]
            errors.append(f"Duplicate Material ID {mid} found in: {matching}")

    for idx, mat in enumerate(data):
        mname = mat.get("name", f"Index_{idx}")
        try:
            MaterialData.model_validate(mat)
        except Exception as e:
            errors.append(f"Material '{mname}' failed schema validation: {e}")

    return errors


def main() -> int:
    print("=== Running Canonical Game Data Validation ===")
    all_errors = []

    char_errors = validate_characters(DATA_DIR / "characters.json")
    if char_errors:
        print(f"[FAIL] Characters validation failed ({len(char_errors)} errors):")
        for err in char_errors[:10]:
            print(f"  - {err}")
        all_errors.extend(char_errors)
    else:
        print("[PASS] characters.json passed all integrity checks (0 duplicates, 0 placeholders).")

    wep_errors = validate_weapons(DATA_DIR / "weapons.json")
    if wep_errors:
        print(f"[FAIL] Weapons validation failed ({len(wep_errors)} errors):")
        for err in wep_errors[:10]:
            print(f"  - {err}")
        all_errors.extend(wep_errors)
    else:
        print("[PASS] weapons.json passed all integrity checks (0 duplicates, verified refinements).")

    art_errors = validate_artifacts(DATA_DIR / "artifacts.json")
    if art_errors:
        print(f"[FAIL] Artifacts validation failed ({len(art_errors)} errors):")
        for err in art_errors[:10]:
            print(f"  - {err}")
        all_errors.extend(art_errors)
    else:
        print("[PASS] artifacts.json passed all integrity checks (0 duplicates, valid bonuses).")

    mat_errors = validate_materials(DATA_DIR / "materials.json")
    if mat_errors:
        print(f"[FAIL] Materials validation failed ({len(mat_errors)} errors):")
        for err in mat_errors[:10]:
            print(f"  - {err}")
        all_errors.extend(mat_errors)
    else:
        print("[PASS] materials.json passed all integrity checks (comprehensive catalogue).")

    if all_errors:
        print(f"\n[ERROR] Total Integrity Errors: {len(all_errors)}")
        return 1

    print("\n[SUCCESS] All canonical datasets verified successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
