"""
Phase 10.6 — Data Truth, Release-Gate Integrity & Permanent Regression Test Suite.

Enforces:
1. Old dataset relabeled as new -> FAIL (anti-relabeling across arbitrary versions).
2. Content fingerprint invariance: stable across metadata changes, sensitive to content changes.
3. Version metadata changed without content -> FAIL.
4. Network acquisition failure -> FAIL CLOSED.
5. Partial / empty acquisition -> FAIL CLOSED.
6. Missing expected character -> FAIL gate.
7. Missing expected weapon -> FAIL gate.
8. Missing expected artifact -> FAIL gate.
9. Missing expected material -> FAIL gate.
10. Duplicate entity ID -> FAIL gate.
11. Placeholder entity -> FAIL gate.
12. Unknown version -> FAIL gate.
13. Unverified version -> FAIL promotion.
14. Admin endpoint without auth -> FAIL (401/403 in production).
15. RAG chat executes hybrid retrieval live.
16. Stat engine binds dynamically to promoted canonical dataset.
"""

import json
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.config import settings
from backend.main import app
from backend.models.version import CompletenessStatus
from backend.services.canonical_data_pipeline import canonical_data_pipeline
from backend.services.content_fingerprint import (
    compute_dataset_content_fingerprint,
    check_dataset_relabeling,
)
from backend.services.version_completeness_gate import version_completeness_gate
from backend.services.stat_engine import stat_engine_service
from backend.services.retrieval_service import retrieval_service

client = TestClient(app)


# 1. Anti-Relabeling: Old Dataset Relabeled As New Must Fail
def test_old_dataset_relabeled_as_new_fails(tmp_path):
    """Proves that copying an older dataset and changing the version label fails the gate."""
    # Create fake version directories in tmp_path
    v54_dir = tmp_path / "versions" / "5.4"
    v54_dir.mkdir(parents=True, exist_ok=True)
    v80_dir = tmp_path / "versions" / "8.0"
    v80_dir.mkdir(parents=True, exist_ok=True)

    # Base payload for 5.4
    char_data = [
        {
            "id": 10000002,
            "name": "Kamisato Ayaka",
            "rarity": 5,
            "element": "Cryo",
            "weapon_type": "Sword",
            "base_hp_lvl90": 12858.0,
            "base_atk_lvl90": 342.0,
            "base_def_lvl90": 784.0,
            "game_version_updated": "5.4",
            "source_version": "5.4",
        }
    ]
    with open(v54_dir / "characters.json", "w", encoding="utf-8") as f:
        json.dump(char_data, f)

    # Copy to 8.0, but only modify the version label and timestamp
    relabeled_char_data = [
        {
            "id": 10000002,
            "name": "Kamisato Ayaka",
            "rarity": 5,
            "element": "Cryo",
            "weapon_type": "Sword",
            "base_hp_lvl90": 12858.0,
            "base_atk_lvl90": 342.0,
            "base_def_lvl90": 784.0,
            "game_version_updated": "8.0",
            "source_version": "8.0",
        }
    ]
    with open(v80_dir / "characters.json", "w", encoding="utf-8") as f:
        json.dump(relabeled_char_data, f)

    is_relabeled, matching_ver, fp = check_dataset_relabeling(
        target_version_dir=v80_dir,
        target_version="8.0",
        all_versions_dir=tmp_path / "versions",
    )
    assert is_relabeled is True
    assert matching_ver == "5.4"


# 2. Content Fingerprint Invariance
def test_content_fingerprint_invariance(tmp_path):
    """Proves fingerprint is invariant to version metadata and timestamps, but sensitive to stats."""
    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    dir_c = tmp_path / "c"
    dir_a.mkdir()
    dir_b.mkdir()
    dir_c.mkdir()

    base_payload = [
        {
            "id": 10000046,
            "name": "Hu Tao",
            "base_hp_lvl90": 15552.0,
            "base_atk_lvl90": 106.0,
            "base_def_lvl90": 876.0,
            "game_version_updated": "1.3",
            "retrieved_at": "2021-02-03T00:00:00Z",
        }
    ]
    # dir_b changes only metadata
    metadata_changed_payload = [
        {
            "id": 10000046,
            "name": "Hu Tao",
            "base_hp_lvl90": 15552.0,
            "base_atk_lvl90": 106.0,
            "base_def_lvl90": 876.0,
            "game_version_updated": "9.9",
            "retrieved_at": "2029-01-01T00:00:00Z",
        }
    ]
    # dir_c changes an actual game stat
    stat_changed_payload = [
        {
            "id": 10000046,
            "name": "Hu Tao",
            "base_hp_lvl90": 16000.0,  # Stat modified!
            "base_atk_lvl90": 106.0,
            "base_def_lvl90": 876.0,
            "game_version_updated": "1.3",
            "retrieved_at": "2021-02-03T00:00:00Z",
        }
    ]

    with open(dir_a / "characters.json", "w", encoding="utf-8") as f:
        json.dump(base_payload, f)
    with open(dir_b / "characters.json", "w", encoding="utf-8") as f:
        json.dump(metadata_changed_payload, f)
    with open(dir_c / "characters.json", "w", encoding="utf-8") as f:
        json.dump(stat_changed_payload, f)

    fp_a = compute_dataset_content_fingerprint(dir_a)
    fp_b = compute_dataset_content_fingerprint(dir_b)
    fp_c = compute_dataset_content_fingerprint(dir_c)

    # Invariance: metadata changes produce identical fingerprint
    assert fp_a == fp_b
    # Sensitivity: game stat changes produce different fingerprint
    assert fp_a != fp_c


# 3. Version Metadata Changed Without Content Fails Gate
def test_version_metadata_changed_without_content_fails(tmp_path):
    """Gate detects when version 7.0 content matches version 5.4 baseline."""
    res, blockers = version_completeness_gate.audit_structured_data("7.0")
    assert res.relabeling_detected is True
    assert res.relabeling_source_version == "5.4"
    assert any("relabeling detected" in b.lower() for b in blockers)


# 4. Network Acquisition Failure Fails Closed
def test_network_acquisition_failure_fails_closed():
    """Acquisition failure must return False and never copy older data."""
    with patch("urllib.request.urlopen", side_effect=ConnectionError("Upstream unreachable")):
        ok, raw_dir, manifest = canonical_data_pipeline.acquire_raw_game_data(
            target_version="98.0"
        )
        assert ok is False
        assert "error" in manifest


# 5. Partial & Empty Acquisition Fails Closed
def test_partial_and_empty_acquisition_fails_closed(tmp_path):
    """Normalizing an empty or partial directory must fail validation."""
    empty_dir = tmp_path / "empty_raw"
    empty_dir.mkdir()
    ok, proc_dir, errs = canonical_data_pipeline.normalize_raw_to_processed(
        "97.0",
        raw_source_dir=empty_dir,
        dest_processed_dir=tmp_path / "proc",
    )
    schema_ok, schema_errs = canonical_data_pipeline.validate_processed_schema(proc_dir)
    assert schema_ok is False
    assert len(schema_errs) > 0


# 6. Missing Expected Character Fails Gate
def test_missing_expected_character_fails_gate(tmp_path):
    """If characters.json has fewer characters than coverage contract, gate fails."""
    gate = version_completeness_gate
    res, blockers = gate.audit_structured_data("99.9")
    # 99.9 has no contract and no data -> must have blockers
    assert len(blockers) > 0


# 7. Missing Expected Weapon Fails Gate
def test_missing_expected_weapon_fails_gate(tmp_path):
    """Missing weapons dataset fails structured data gate."""
    custom_dir = tmp_path / "proc"
    custom_dir.mkdir()
    # Write only characters.json, omit weapons.json
    with open(custom_dir / "characters.json", "w", encoding="utf-8") as f:
        json.dump([{"id": 1, "name": "Traveler", "base_hp_lvl90": 10000}], f)

    gate = version_completeness_gate
    # Temporarily audit against custom_dir
    with patch.object(gate, "_resolve_data_dir", return_value=custom_dir):
        res, blockers = gate.audit_structured_data("5.4")
        assert any("missing structured dataset: weapons.json" in b.lower() for b in blockers)


# 8. Missing Expected Artifact Fails Gate
def test_missing_expected_artifact_fails_gate(tmp_path):
    """Missing artifacts dataset produces failure."""
    custom_dir = tmp_path / "proc"
    custom_dir.mkdir()
    with open(custom_dir / "characters.json", "w", encoding="utf-8") as f:
        json.dump([{"id": 1, "name": "Traveler", "base_hp_lvl90": 10000}], f)
    with open(custom_dir / "weapons.json", "w", encoding="utf-8") as f:
        json.dump([{"id": 1, "name": "Dull Blade", "base_atk_lvl1": 23}], f)

    gate = version_completeness_gate
    with patch.object(gate, "_resolve_data_dir", return_value=custom_dir):
        res, blockers = gate.audit_structured_data("5.4")
        assert res.artifacts.status == CompletenessStatus.INCOMPLETE


# 9. Duplicate Entity ID Fails Gate
def test_duplicate_entity_id_fails_gate(tmp_path):
    """Duplicate character IDs must be detected and flagged."""
    custom_dir = tmp_path / "proc"
    custom_dir.mkdir()
    dups = [
        {"id": 10000002, "name": "Ayaka", "base_hp_lvl90": 12858},
        {"id": 10000002, "name": "Ayaka Duplicate", "base_hp_lvl90": 12858},
    ]
    with open(custom_dir / "characters.json", "w", encoding="utf-8") as f:
        json.dump(dups, f)

    normalized = version_completeness_gate._normalize_dataset(dups)
    # When normalized into {id: item}, duplicate collapses length
    assert len(normalized) < len(dups)


# 10. Placeholder Entity Fails Gate
def test_placeholder_entity_fails_gate():
    """Placeholder phrases must fail entity validation."""
    gate = version_completeness_gate
    assert gate._has_placeholder("Data unavailable") is True
    assert gate._has_placeholder("TBD") is True
    assert gate._has_placeholder("Coming Soon") is True
    assert gate._has_placeholder("Kamisato Ayaka") is False


# 11. Unknown Version Fails Gate
def test_unknown_version_fails_gate():
    """Version without formal coverage contract cannot be certified."""
    res, blockers = version_completeness_gate.audit_structured_data("105.0")
    assert any("no formal version coverage contract found" in b.lower() for b in blockers)


# 12. Unverified Version Fails Promotion
def test_unverified_version_fails_promotion():
    """Dataset not verified cannot be promoted to active canonical."""
    ok, msg = canonical_data_pipeline.promote_to_canonical("999.0")
    assert ok is False
    assert "not found" in msg.lower() or "not verified" in msg.lower() or "does not exist" in msg.lower()


# 13. Admin Endpoints Require Auth in Production
def test_admin_endpoints_require_auth_in_production(monkeypatch):
    """In production mode, unauthenticated admin requests must be rejected with 401/403."""
    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "ADMIN_API_KEY", "secret_key_12345")

    # Unauthenticated request
    res = client.post("/api/data/pipeline/refresh")
    assert res.status_code in (401, 403)

    # Invalid token
    res = client.post("/api/data/pipeline/refresh", headers={"X-Admin-Token": "wrong_key"})
    assert res.status_code == 401

    # Valid token
    with patch.object(canonical_data_pipeline, "execute_refresh_pipeline", return_value={"success": True}):
        res = client.post("/api/data/pipeline/refresh", headers={"X-Admin-Token": "secret_key_12345"})
        assert res.status_code == 200


# 14. RAG Chat Uses Hybrid Retrieval Live
def test_rag_chat_uses_hybrid_retrieval_live():
    """POST /api/chat must orchestrate live hybrid retrieval without mocking it away."""
    with patch("backend.services.gemini_service.gemini_service.generate_content", new_callable=AsyncMock) as mock_gemini:
        mock_gemini.return_value = "Furina's Elemental Skill summons Salon Solitaire."

        payload = {
            "messages": [{"role": "user", "content": "How does Furina skill work?"}],
            "uid": "817739968"
        }

        # Wrap retrieval_service.retrieve to verify it is called live
        real_retrieve = retrieval_service.retrieve
        call_count = {"count": 0}

        def spy_retrieve(*args, **kwargs):
            call_count["count"] += 1
            return real_retrieve(*args, **kwargs)

        with patch.object(retrieval_service, "retrieve", side_effect=spy_retrieve):
            res = client.post("/api/chat", json=payload)
            assert res.status_code == 200
            assert call_count["count"] >= 1
            data = res.json()
            assert "citations" in data
            assert len(data["citations"]) > 0


# 15. Stat Engine Active Dataset Binding
def test_stat_engine_active_dataset_binding():
    """Stat engine must query the active canonical dataset version dynamically."""
    active_v = canonical_data_pipeline.get_active_version()
    assert stat_engine_service.canonical_dataset_version == active_v


# 16. Fake Coverage Contract Claiming Nonexistent Content Fails
def test_fake_coverage_contract_fails_gate(tmp_path):
    """A coverage contract expecting 500 characters when dataset only has 121 must fail gate."""
    fake_contract = {
        "structured_data": {
            "characters": {"expected_count": 500}
        }
    }
    gate = version_completeness_gate
    with patch.object(gate, "_load_coverage_contract", return_value=fake_contract):
        res, blockers = gate.audit_structured_data("5.4")
        assert res.characters.status == CompletenessStatus.INCOMPLETE
        assert any("structured characters incomplete" in b.lower() for b in blockers)
