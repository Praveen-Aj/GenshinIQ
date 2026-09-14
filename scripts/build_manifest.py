"""Deterministic Data Provenance Manifest Builder.

Computes SHA-256 digests and record counts across game data and knowledge base,
outputting an audit report and manifest snapshot.
"""

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.config import settings

GAME_DATA_DIR = ROOT_DIR / "data" / "processed" / "game_data"
KNOWLEDGE_DIR = ROOT_DIR / "data" / "knowledge"
RUNTIME_CACHE_DIR = ROOT_DIR / "data" / "runtime" / "showcases"


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


def main():
    print("=== Building Data Provenance Manifest ===")
    game_files = []
    game_hashes = []

    for f in sorted(GAME_DATA_DIR.glob("*.json")):
        with open(f, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        count = len(payload) if isinstance(payload, (list, dict)) else 1
        digest = sha256_file(f)
        game_hashes.append(digest)
        sid = "src_project_amber" if f.name in ("characters.json", "weapons.json", "artifacts.json", "materials.json") else "src_animegamedata"
        surl = "https://api.ambr.top/v2/en/" if sid == "src_project_amber" else "https://github.com/Dimbreath/AnimeGameData/tree/master/ExcelBinOutput"
        inv_class = "CATEGORY_A_ENGINE_CONSTANT" if f.name in ("avatar_curves.json", "weapon_curves.json", "artifact_levels.json") else "CATEGORY_B_GAME_CONTENT_STATIC"
        game_files.append({
            "file_name": f.name,
            "record_count": count,
            "sha256": digest,
            "size_bytes": f.stat().st_size,
            "source_id": sid,
            "source_url": surl,
            "source_version": "5.4",
            "dataset_version": "5.4",
            "project_target_version": "7.0",
            "verification_state": "VERIFIED_STRUCTURED",
            "verification_status": "VERIFIED_STRUCTURED",
            "invariance_classification": inv_class,
        })
        print(f"  [GameData] {f.name}: {count} records | SHA256: {digest[:12]}...")

    aggregate_game_sha256 = hashlib.sha256(
        "\n".join(sorted(game_hashes)).encode("utf-8")
    ).hexdigest()

    knowledge_files = list(sorted(KNOWLEDGE_DIR.glob("*.json")))
    knowledge_hashes = [sha256_file(kf) for kf in knowledge_files]
    aggregate_kb_sha256 = hashlib.sha256(
        "\n".join(sorted(knowledge_hashes)).encode("utf-8")
    ).hexdigest()

    source_type_counts = {}
    source_tier_counts = {}
    source_id_counts = {}

    for kf in knowledge_files:
        with open(kf, "r", encoding="utf-8") as handle:
            doc_data = json.load(handle)
            meta = doc_data.get("metadata", {})
            st = meta.get("source_type", "OTHER")
            tier = f"Tier {meta.get('authority_tier', 5)}"
            sid = meta.get("source_id", "src_community_general")
            source_type_counts[st] = source_type_counts.get(st, 0) + 1
            source_tier_counts[tier] = source_tier_counts.get(tier, 0) + 1
            source_id_counts[sid] = source_id_counts.get(sid, 0) + 1

    print(f"  [Knowledge] {len(knowledge_files)} documents | Aggregate SHA256: {aggregate_kb_sha256[:12]}...")
    print(f"    Tiers: {source_tier_counts}")
    print(f"    Types: {source_type_counts}")

    manifest = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "app_version": settings.APP_VERSION,
        "runtime_cache_dir": str(RUNTIME_CACHE_DIR.as_posix()),
        "game_data": {
            "directory": str(GAME_DATA_DIR.as_posix()),
            "source_type": "STRUCTURED_DATA",
            "source_tier": 3,
            "source_provider": "Project Amber (Ambr API v2) & Dimbreath AnimeGameData ExcelBinOutput",
            "official_status": "Community-maintained structured datamining, not direct HoYoverse official API",
            "dataset_version": "5.4",
            "project_target_version": "7.0",
            "verification_state": "VERIFIED_STRUCTURED",
            "aggregate_sha256": aggregate_game_sha256,
            "files": game_files,
        },
        "knowledge_base": {
            "directory": str(KNOWLEDGE_DIR.as_posix()),
            "aggregate_sha256": aggregate_kb_sha256,
            "total_documents": len(knowledge_files),
            "source_type_counts": dict(sorted(source_type_counts.items())),
            "source_tier_counts": dict(sorted(source_tier_counts.items())),
            "source_id_counts": dict(sorted(source_id_counts.items())),
        }
    }

    manifest_file = ROOT_DIR / "data" / "processed" / "manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"\n[SUCCESS] Manifest saved to {manifest_file}")


if __name__ == "__main__":
    main()
