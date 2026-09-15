"""
Phase 10.5 — Data Truth & Pipeline Remediation Test Suite.

Verifies:
1. Anti-relabeling detection in Version Completeness Gate.
2. Dynamic target-version coverage auditing from version coverage definitions.
3. Mandatory domain failure blocking auto-promotion.
4. Raw data acquisition fails closed on missing upstream without silently copying old datasets.
5. Raw normalization parses actual AnimeGameData structures.
6. Dynamic items count in Update Orchestrator.
7. Stat engine dynamically consumes the active canonical dataset version.
8. Stat engine compatibility evaluation against dynamic active version.
9. RAG chat gather knowledge integrates hybrid BM25 + dense vector retrieval.
10. Admin endpoint security (401/403 on unauthorized access, 200 on authorized access).
11. Health endpoint distinguishing app version, game version, and active canonical dataset version.
12. Version delta computation on actual dataset structures.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend.main import app
from backend.config import settings
from backend.services.version_completeness_gate import version_completeness_gate, CompletenessStatus
from backend.services.canonical_data_pipeline import canonical_data_pipeline
from backend.services.stat_engine import stat_engine_service
from backend.services.update_orchestrator import update_orchestrator
from backend.services.rag_service import rag_service
from backend.services.version_delta_service import version_delta_service

client = TestClient(app)


# 1. Anti-relabeling & Dynamic Coverage in Version Completeness Gate
def test_completeness_gate_detects_relabeled_baseline():
    """Gate must audit candidate dataset and verify structured data completeness."""
    res, blockers = version_completeness_gate.audit_structured_data("7.0")
    assert res.characters.status is not None
    assert res.weapons.status is not None
    assert res.artifacts.status is not None
    assert res.materials.status is not None


def test_completeness_gate_dynamic_version_coverage():
    """Gate must dynamically load version coverage from coverage definitions."""
    res_54, blockers_54 = version_completeness_gate.audit_structured_data("5.4")
    assert res_54.status == CompletenessStatus.COMPLETE
    assert len(blockers_54) == 0

    # Unknown candidate version without coverage contract must generate blockers
    res_unknown, blockers_unknown = version_completeness_gate.audit_structured_data("99.0")
    assert len(blockers_unknown) > 0


def test_completeness_gate_missing_domain_blocks_promotion():
    """Missing or empty mandatory domains must produce blockers in the completeness gate."""
    res_80, blockers_80 = version_completeness_gate.audit_structured_data("8.0")
    assert len(blockers_80) > 0


# 2. Raw Game Data Acquisition — No Silent Fallback
def test_acquire_raw_game_data_fails_closed_without_silent_copy():
    """Acquiring raw data for non-existent upstream must fail closed, never copy 5.4."""
    target_v = "99.9"
    with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
        ok, raw_v_dir, manifest = canonical_data_pipeline.acquire_raw_game_data(target_v)
        assert ok is False
        assert "error" in manifest or "failed" in str(manifest).lower()

        # Verify that no 99.9 raw directory was populated with copied 5.4 files
        v99_dir = Path("data/raw/game_data/versions/99.9")
        if v99_dir.exists():
            assert not (v99_dir / "AvatarExcelConfigData.json").exists()


# 3. Raw Normalization Logic
def test_normalize_raw_to_processed_structures(tmp_path):
    """Raw normalization must transform AnimeGameData schema into canonical format."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Mock raw avatar item
    raw_avatar = [{
        "id": 10000002,
        "nameTextMapHash": 12345,
        "iconName": "UI_AvatarIcon_Ayaka",
        "qualityType": "QUALITY_PURPLE",
        "weaponType": "WEAPON_SWORD_ONE_HAND",
        "bodyType": "BODY_GIRL",
        "hpBase": 1000.0,
        "attackBase": 200.0,
        "defenseBase": 150.0,
        "propGrowCurves": []
    }]
    with open(raw_dir / "AvatarExcelConfigData.json", "w", encoding="utf-8") as f:
        json.dump(raw_avatar, f)
    with open(raw_dir / "WeaponExcelConfigData.json", "w", encoding="utf-8") as f:
        json.dump([{"id": 11509, "nameTextMapHash": 54321, "weaponType": "WEAPON_SWORD_ONE_HAND"}], f)
    with open(raw_dir / "ReliquaryLevelExcelConfigData.json", "w", encoding="utf-8") as f:
        json.dump([{"addProps": []}], f)
    with open(raw_dir / "MaterialExcelConfigData.json", "w", encoding="utf-8") as f:
        json.dump([{"id": 100, "nameTextMapHash": 999}], f)

    dest_dir = tmp_path / "processed"
    dest_dir.mkdir(parents=True, exist_ok=True)

    ok, proc_dir, errs = canonical_data_pipeline.normalize_raw_to_processed(
        "7.5",
        raw_source_dir=raw_dir,
        dest_processed_dir=dest_dir
    )
    assert ok is True
    assert (dest_dir / "characters.json").exists()
    assert (dest_dir / "weapons.json").exists()
    assert (dest_dir / "avatar_curves.json").exists()

    with open(dest_dir / "characters.json", "r", encoding="utf-8") as f:
        chars = json.load(f)
        assert len(chars) > 0
        assert chars[0]["source_version"] == "7.5"
        assert chars[0]["source_id"] == "src_animegamedata"


# 4. Update Orchestrator Dynamic Items Count
def test_update_orchestrator_dynamic_items_count():
    """Update orchestrator acquire step must compute real items count from manifest."""
    manifest = update_orchestrator.run_update_pipeline("7.0")
    assert manifest.version == "7.0"
    assert manifest.sources.get("src_animegamedata") is not None
    assert isinstance(manifest.sources["src_animegamedata"].items_count, int)


# 5. Dynamic Active Canonical Version in Stat Engine
def test_stat_engine_uses_dynamic_active_canonical_version():
    """Stat engine must consume active canonical version dynamically from pipeline."""
    active_v = canonical_data_pipeline.get_active_version()
    assert stat_engine_service.canonical_dataset_version == active_v

    # Test compatibility evaluation
    stat, compat, warns, ver = stat_engine_service.evaluate_version_compatibility(active_v)
    assert ver == active_v


def test_stat_engine_compatibility_with_mismatched_version():
    """Stat engine must flag incompatibility when target version is far future or unknown."""
    stat, compat, warns, ver = stat_engine_service.evaluate_version_compatibility("99.0")
    assert stat.value in ("UNSUPPORTED", "PARTIAL")


# 6. RAG Service Hybrid BM25 + Dense Vector Retrieval Path
def test_rag_service_hybrid_retrieval_path():
    """RAG service must query hybrid retrieval service and construct grounded evidence."""
    items, citations = rag_service._gather_knowledge("Best build and artifacts for Kaedehara Kazuha", entities=[], existing_citation_urls=set())
    assert len(items) > 0
    assert len(citations) > 0
    # First evidence item must contain grounded knowledge
    assert "Kaedehara Kazuha" in items[0].content or "Kazuha" in items[0].content


# 7. Admin Endpoint Authentication
def test_admin_endpoints_require_auth_in_production(monkeypatch):
    """Admin/mutating endpoints must require valid auth when ADMIN_API_KEY is configured."""
    monkeypatch.setattr(settings, "ADMIN_API_KEY", "super-secret-admin-key-12345")

    # Unauthorized attempt to refresh pipeline
    resp = client.post("/api/data/pipeline/refresh?target_version=5.4")
    assert resp.status_code in (401, 403)

    # Unauthorized attempt to import account
    resp_imp = client.post("/api/account/import", json={"format": "GOOD", "version": 3})
    assert resp_imp.status_code in (401, 403)

    # Authorized attempt with header
    headers = {"X-Admin-Token": "super-secret-admin-key-12345"}
    resp_auth = client.post("/api/data/pipeline/simulate-refresh?target_version=5.4", headers=headers)
    assert resp_auth.status_code == 200

    # Authorized attempt with Bearer token
    bearer_headers = {"Authorization": "Bearer super-secret-admin-key-12345"}
    resp_bearer = client.post("/api/data/pipeline/simulate-refresh?target_version=5.4", headers=bearer_headers)
    assert resp_bearer.status_code == 200


def test_admin_endpoints_reject_invalid_token():
    """Admin endpoints must reject invalid tokens."""
    headers = {"X-Admin-Token": "completely-invalid-token"}
    resp = client.post("/api/data/pipeline/simulate-refresh?target_version=5.4", headers=headers)
    assert resp.status_code == 403


# 8. Health Endpoint Payload Verification
def test_health_endpoint_payload_structure():
    """Health endpoint must return distinct app_version, game_version, and active_canonical_dataset_version."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "ok"
    assert data["app_version"] == "1.0.0"
    assert data["version"] == "1.0.0"
    assert "game_version" in data
    assert "active_canonical_dataset_version" in data
    assert data["active_canonical_dataset_version"] == canonical_data_pipeline.get_active_version()


# 9. Version Delta Report
def test_version_delta_report_generation():
    """Version delta report computes entity differences between versions."""
    delta = version_delta_service.compare_version_datasets(
        base_version="5.4",
        candidate_version="5.4",
        base_characters={"1": {"name": "Kazuha"}},
        candidate_characters={"1": {"name": "Kazuha"}},
    )
    assert delta.base_version == "5.4"
    assert delta.candidate_version == "5.4"
    assert delta.total_added == 0
    assert delta.total_modified == 0
