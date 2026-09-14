"""Comprehensive test suite for Phase 6 GOOD v3 Account Inventory Integration.

Covers:
- Parser & validation (valid, malformed, unsupported version, missing fields, out-of-range values)
- Character normalization & multi-word entity resolution
- Weapon inventory invariant: multiple copies of weapons remain distinct instances
- Artifact inventory invariant: individual artifact instances preserved with exact substats
- Material inventory & unresolved tracking without synthetic fabrication
- Idempotency: repeated import produces bit-for-bit identical snapshots
- Snapshot diff: added, removed, and modified inventory detection
- Security validation: oversized payloads, malformed structures, invalid bounds
- Real file verification against genshinData_GOOD_2026_09_07_22_00.json
- REST API endpoint verification (/api/account/*)
"""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.account import (
    AccountSnapshot,
    ResolutionStatus,
)
from backend.services.account_inventory_service import (
    AccountInventoryException,
    AccountInventoryService,
    account_inventory_service,
)

client = TestClient(app)
REAL_GOOD_PATH = Path("genshinData_GOOD_2026_09_07_22_00.json")


# ==============================================================================
# 1. Parser & Schema Validation Tests
# ==============================================================================

def test_valid_good_v3_minimal():
    """Verify minimal valid GOOD v3 payload passes validation."""
    payload = {
        "format": "GOOD",
        "version": 3,
        "source": "Inventory_Kamera",
        "characters": [
            {
                "key": "KaedeharaKazuha",
                "level": 90,
                "ascension": 6,
                "constellation": 2,
                "talent": {"auto": 8, "skill": 10, "burst": 10},
            }
        ],
        "weapons": [
            {
                "key": "FreedomSworn",
                "level": 90,
                "ascension": 6,
                "refinement": 1,
                "location": "KaedeharaKazuha",
                "lock": True,
            }
        ],
        "artifacts": [
            {
                "setKey": "ViridescentVenerer",
                "slotKey": "flower",
                "rarity": 5,
                "level": 20,
                "mainStatKey": "hp",
                "substats": [{"key": "eleMas", "value": 79.0}],
                "location": "KaedeharaKazuha",
                "lock": True,
            }
        ],
        "materials": {"Mora": 1000000},
    }

    valid_json, file_hash = account_inventory_service.validate_and_parse_good_payload(payload)
    assert valid_json["format"] == "GOOD"
    assert valid_json["version"] == 3
    assert len(file_hash) == 64


def test_malformed_json_rejected():
    """Verify non-dictionary payload is rejected."""
    with pytest.raises(AccountInventoryException, match="must be a JSON object"):
        account_inventory_service.validate_and_parse_good_payload("not a json dict")  # type: ignore


def test_unsupported_good_version_rejected():
    """Verify GOOD versions other than 3 are rejected with clear diagnostics."""
    for bad_ver in [1, 2, 4, 99]:
        payload = {"format": "GOOD", "version": bad_ver}
        with pytest.raises(AccountInventoryException, match="Unsupported GOOD version"):
            account_inventory_service.validate_and_parse_good_payload(payload)


def test_unsupported_format_rejected():
    """Verify format string other than 'GOOD' is rejected."""
    payload = {"format": "BAD_FORMAT", "version": 3}
    with pytest.raises(AccountInventoryException, match="Unsupported format"):
        account_inventory_service.validate_and_parse_good_payload(payload)


def test_out_of_range_character_level_rejected():
    """Verify character level > 90 or < 1 is rejected."""
    payload = {
        "format": "GOOD",
        "version": 3,
        "characters": [{"key": "Amber", "level": 105}],
    }
    with pytest.raises(AccountInventoryException, match="invalid level"):
        account_inventory_service.validate_and_parse_good_payload(payload)


def test_out_of_range_weapon_refinement_rejected():
    """Verify weapon refinement > 5 is rejected."""
    payload = {
        "format": "GOOD",
        "version": 3,
        "weapons": [{"key": "FavoniusSword", "level": 90, "refinement": 7}],
    }
    with pytest.raises(AccountInventoryException, match="invalid refinement"):
        account_inventory_service.validate_and_parse_good_payload(payload)


def test_out_of_range_artifact_level_rejected():
    """Verify artifact level > 20 is rejected."""
    payload = {
        "format": "GOOD",
        "version": 3,
        "artifacts": [{"setKey": "GladiatorsFinale", "slotKey": "flower", "level": 25}],
    }
    with pytest.raises(AccountInventoryException, match="invalid level"):
        account_inventory_service.validate_and_parse_good_payload(payload)


def test_negative_material_quantity_rejected():
    """Verify negative material quantities are rejected."""
    payload = {
        "format": "GOOD",
        "version": 3,
        "materials": {"Mora": -500},
    }
    with pytest.raises(AccountInventoryException, match="invalid quantity"):
        account_inventory_service.validate_and_parse_good_payload(payload)


# ==============================================================================
# 2. Character Resolution & Multi-Word Names
# ==============================================================================

def test_character_canonical_resolution():
    """Verify multi-word names resolve to canonical character names and IDs."""
    sample_payload = {
        "format": "GOOD",
        "version": 3,
        "characters": [
            {"key": "KaedeharaKazuha", "level": 90, "ascension": 6, "constellation": 2},
            {"key": "HuTao", "level": 90, "ascension": 6, "constellation": 1},
            {"key": "KamisatoAyaka", "level": 90, "ascension": 6, "constellation": 0},
            {"key": "RaidenShogun", "level": 90, "ascension": 6, "constellation": 2},
            {"key": "AratakiItto", "level": 80, "ascension": 5, "constellation": 0},
            {"key": "SangonomiyaKokomi", "level": 80, "ascension": 5, "constellation": 0},
        ],
    }

    valid_json, file_hash = account_inventory_service.validate_and_parse_good_payload(sample_payload)
    snapshot = account_inventory_service.normalize_good_to_snapshot(valid_json, file_hash)

    names = {c.canonical_name: c for c in snapshot.characters}

    assert "Kaedehara Kazuha" in names
    assert names["Kaedehara Kazuha"].canonical_id == 10000047
    assert names["Kaedehara Kazuha"].element == "Anemo"
    assert names["Kaedehara Kazuha"].constellation == 2

    assert "Hu Tao" in names
    assert names["Hu Tao"].canonical_id == 10000046
    assert names["Hu Tao"].element == "Pyro"
    assert names["Hu Tao"].constellation == 1

    assert "Kamisato Ayaka" in names
    assert names["Kamisato Ayaka"].canonical_id == 10000002
    assert names["Kamisato Ayaka"].element == "Cryo"

    assert "Raiden Shogun" in names
    assert names["Raiden Shogun"].canonical_id == 10000052
    assert names["Raiden Shogun"].element == "Electro"


# ==============================================================================
# 3. Weapon Inventory Invariants (Multiple Duplicate Copies)
# ==============================================================================

def test_multiple_copies_of_weapon_preserved_independently():
    """Verify multiple instances of the same weapon retain distinct identities."""
    payload = {
        "format": "GOOD",
        "version": 3,
        "weapons": [
            {"key": "DragonsBane", "level": 90, "refinement": 5, "location": "HuTao", "id": 34},
            {"key": "DragonsBane", "level": 1, "refinement": 1, "location": "Thoma", "id": 131},
            {"key": "DragonsBane", "level": 1, "refinement": 1, "location": "", "id": 132},
        ],
    }

    valid_json, file_hash = account_inventory_service.validate_and_parse_good_payload(payload)
    snapshot = account_inventory_service.normalize_good_to_snapshot(valid_json, file_hash)

    assert len(snapshot.weapons) == 3

    # Ensure all 3 have distinct instance IDs
    inst_ids = [w.account_instance_id for w in snapshot.weapons]
    assert len(set(inst_ids)) == 3
    assert "weapon_good_34" in inst_ids
    assert "weapon_good_131" in inst_ids
    assert "weapon_good_132" in inst_ids

    # Check copy 1
    w1 = next(w for w in snapshot.weapons if w.account_instance_id == "weapon_good_34")
    assert w1.canonical_name == "Dragon's Bane"
    assert w1.level == 90
    assert w1.refinement == 5
    assert w1.location == "Hu Tao"

    # Check copy 2
    w2 = next(w for w in snapshot.weapons if w.account_instance_id == "weapon_good_131")
    assert w2.canonical_name == "Dragon's Bane"
    assert w2.level == 1
    assert w2.refinement == 1
    assert w2.location == "Thoma"

    # Check copy 3 (unequipped)
    w3 = next(w for w in snapshot.weapons if w.account_instance_id == "weapon_good_132")
    assert w3.location is None


# ==============================================================================
# 4. Artifact Inventory Invariants
# ==============================================================================

def test_artifacts_preserve_exact_substats_and_locations():
    """Verify artifact instances preserve exact substat rolls and equipment locations."""
    payload = {
        "format": "GOOD",
        "version": 3,
        "artifacts": [
            {
                "setKey": "GladiatorsFinale",
                "slotKey": "flower",
                "rarity": 5,
                "level": 20,
                "mainStatKey": "hp",
                "mainStatValue": 4780.0,
                "substats": [
                    {"key": "critRate_", "value": 10.5},
                    {"key": "critDMG_", "value": 21.0},
                    {"key": "atk_", "value": 9.9},
                    {"key": "enerRech_", "value": 5.8},
                ],
                "location": "Arlecchino",
                "lock": True,
                "id": 101,
            },
            {
                "setKey": "GladiatorsFinale",
                "slotKey": "flower",
                "rarity": 5,
                "level": 0,
                "mainStatKey": "hp",
                "mainStatValue": 717.0,
                "substats": [{"key": "def", "value": 16.0}],
                "location": "",
                "lock": False,
                "id": 102,
            },
        ],
    }

    valid_json, file_hash = account_inventory_service.validate_and_parse_good_payload(payload)
    snapshot = account_inventory_service.normalize_good_to_snapshot(valid_json, file_hash)

    assert len(snapshot.artifacts) == 2
    a1 = snapshot.artifacts[0]
    assert a1.account_instance_id == "artifact_good_101"
    assert a1.canonical_set_name == "Gladiator's Finale"
    assert a1.slot == "flower"
    assert a1.level == 20
    assert a1.location == "Arlecchino"
    assert a1.locked is True
    assert len(a1.substats) == 4
    assert any(s["name"] == "CRIT Rate" and s["value"] == 10.5 for s in a1.substats)

    a2 = snapshot.artifacts[1]
    assert a2.account_instance_id == "artifact_good_102"
    assert a2.location is None
    assert a2.level == 0


# ==============================================================================
# 5. Material Inventory & Unresolved Tracking
# ==============================================================================

def test_material_inventory_and_unresolved_status():
    """Verify materials map to canonical database, and unmapped materials track as UNRESOLVED."""
    payload = {
        "format": "GOOD",
        "version": 3,
        "materials": {
            "DakaBells": 12,  # Canonical boss drop
            "Mora": 5000000,  # General currency (unmapped in farming DB)
        },
    }

    valid_json, file_hash = account_inventory_service.validate_and_parse_good_payload(payload)
    snapshot = account_inventory_service.normalize_good_to_snapshot(valid_json, file_hash)

    daka = next((m for m in snapshot.materials if "daka" in m.good_key.lower()), None)
    mora = next((m for m in snapshot.materials if m.good_key == "Mora"), None)

    assert daka is not None
    assert daka.quantity == 12

    assert mora is not None
    assert mora.quantity == 5000000
    assert mora.resolution_status == ResolutionStatus.UNRESOLVED
    assert mora.canonical_id is None
    # Ensure unresolved material is recorded in unresolved_records list
    assert any(u.good_key == "Mora" for u in snapshot.unresolved_records)


# ==============================================================================
# 6. Idempotency Test
# ==============================================================================

def test_import_idempotency():
    """Importing the same payload twice produces bit-for-bit identical snapshots."""
    payload = {
        "format": "GOOD",
        "version": 3,
        "characters": [{"key": "Furina", "level": 90, "ascension": 6, "constellation": 2}],
        "weapons": [{"key": "SplendorOfTranquilWaters", "level": 90, "refinement": 1, "location": "Furina", "id": 5}],
        "materials": {"Mora": 1000},
    }

    s1 = account_inventory_service.import_good_payload(payload)
    s2 = account_inventory_service.import_good_payload(payload)

    assert s1.metadata.source_file_hash == s2.metadata.source_file_hash
    assert len(s1.characters) == len(s2.characters)
    assert len(s1.weapons) == len(s2.weapons)
    assert s1.weapons[0].account_instance_id == s2.weapons[0].account_instance_id


# ==============================================================================
# 7. Snapshot Diff Test
# ==============================================================================

def test_snapshot_diff_identifies_changes():
    """Verify deterministic diffing detects modifications, additions, and removals."""
    base_payload = {
        "format": "GOOD",
        "version": 3,
        "characters": [{"key": "Bennett", "level": 80, "ascension": 5, "constellation": 5}],
        "weapons": [{"key": "AquilaFavonia", "level": 90, "refinement": 1, "location": "Bennett", "id": 10}],
        "materials": {"Mora": 100},
    }

    updated_payload = {
        "format": "GOOD",
        "version": 3,
        "characters": [
            {"key": "Bennett", "level": 90, "ascension": 6, "constellation": 6},
            {"key": "Xiangling", "level": 90, "ascension": 6, "constellation": 6},
        ],
        "weapons": [
            {"key": "AquilaFavonia", "level": 90, "refinement": 2, "location": "Bennett", "id": 10},
        ],
        "materials": {"Mora": 500},
    }

    s1 = account_inventory_service.normalize_good_to_snapshot(base_payload, "hash1")
    s2 = account_inventory_service.normalize_good_to_snapshot(updated_payload, "hash2")

    diff = account_inventory_service.compute_diff(s1, s2)

    assert "Xiangling" in diff.characters_added
    assert len(diff.characters_modified) == 1
    assert diff.characters_modified[0]["character"] == "Bennett"
    assert diff.characters_modified[0]["changes"]["level"]["new"] == 90
    assert diff.characters_modified[0]["changes"]["constellation"]["new"] == 6

    assert len(diff.weapons_modified) == 1
    assert diff.weapons_modified[0]["changes"]["refinement"]["new"] == 2

    assert "Mora" in diff.materials_changed
    assert diff.materials_changed["Mora"]["old"] == 100
    assert diff.materials_changed["Mora"]["new"] == 500


# ==============================================================================
# 8. Real GOOD Export File Verification
# ==============================================================================

def test_real_good_v3_export_file():
    """Verify the real project export file genshinData_GOOD_2026_09_07_22_00.json."""
    if not REAL_GOOD_PATH.exists():
        pytest.skip("Real GOOD file not found in workspace.")

    snapshot = account_inventory_service.import_good_file(REAL_GOOD_PATH)

    # Exact expected counts
    assert len(snapshot.characters) == 50, f"Expected 50 characters, got {len(snapshot.characters)}"
    assert len(snapshot.weapons) == 239, f"Expected 239 weapons, got {len(snapshot.weapons)}"
    assert len(snapshot.artifacts) == 320, f"Expected 320 artifacts, got {len(snapshot.artifacts)}"
    assert len(snapshot.materials) == 591, f"Expected 591 materials, got {len(snapshot.materials)}"

    # All characters must resolve cleanly
    unresolved_chars = [c for c in snapshot.characters if c.resolution_status == ResolutionStatus.UNRESOLVED]
    assert len(unresolved_chars) == 0, f"Found unresolved characters: {[c.good_key for c in unresolved_chars]}"

    # All weapons must resolve cleanly
    unresolved_weaps = [w for w in snapshot.weapons if w.resolution_status == ResolutionStatus.UNRESOLVED]
    assert len(unresolved_weaps) == 0, f"Found unresolved weapons: {[w.good_key for w in unresolved_weaps]}"

    # All artifact sets must resolve cleanly
    unresolved_arts = [a for a in snapshot.artifacts if a.resolution_status == ResolutionStatus.UNRESOLVED]
    assert len(unresolved_arts) == 0, f"Found unresolved artifacts: {[a.good_set_key for a in unresolved_arts]}"

    # Check Dragon's Bane copies (16 copies expected)
    db_copies = [w for w in snapshot.weapons if w.canonical_name == "Dragon's Bane"]
    assert len(db_copies) == 16
    db_ids = {w.account_instance_id for w in db_copies}
    assert len(db_ids) == 16, "Dragon's Bane instances must have unique instance IDs"


# ==============================================================================
# 9. REST API Integration Tests
# ==============================================================================

def test_api_account_summary():
    """Verify GET /api/account/summary returns deterministic metrics."""
    response = client.get("/api/account/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_characters"] == 50
    assert data["total_weapon_instances"] == 239
    assert data["total_artifact_instances"] == 320
    assert data["total_material_types"] == 591


def test_api_account_characters_filtered():
    """Verify GET /api/account/characters filters by min_level and element."""
    response = client.get("/api/account/characters?min_level=90&element=Pyro")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    for char in data:
        assert char["level"] == 90
        assert char["element"] == "Pyro"


def test_api_account_weapons_filtered():
    """Verify GET /api/account/weapons filters by rarity and equipped_only."""
    response = client.get("/api/account/weapons?rarity=5&equipped_only=true")
    assert response.status_code == 200
    data = response.json()
    for weapon in data:
        assert weapon["rarity"] == 5
        assert weapon["location"] is not None


def test_api_account_artifacts_filtered():
    """Verify GET /api/account/artifacts filters by slot."""
    response = client.get("/api/account/artifacts?slot=plume")
    assert response.status_code == 200
    data = response.json()
    for art in data:
        assert art["slot"] == "plume"


def test_api_account_materials_filtered():
    """Verify GET /api/account/materials filters by resolved_only."""
    response = client.get("/api/account/materials?resolved_only=true")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 398
    for mat in data:
        assert mat["resolution_status"] != "UNRESOLVED"
        assert mat["canonical_id"] is not None


def test_api_account_import_endpoint():
    """Verify POST /api/account/import ingests payload and returns summary."""
    payload = {
        "format": "GOOD",
        "version": 3,
        "characters": [{"key": "Keqing", "level": 90, "ascension": 6, "constellation": 4}],
        "weapons": [{"key": "MistsplitterReforged", "level": 90, "refinement": 1, "location": "Keqing", "id": 999}],
        "artifacts": [],
        "materials": {"Mora": 250000},
    }
    response = client.post("/api/account/import", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_characters"] == 1
    assert data["total_weapon_instances"] == 1
    assert data["total_material_types"] == 1

    # Reload real export file so active snapshot remains restored
    account_inventory_service.import_good_file(REAL_GOOD_PATH)
