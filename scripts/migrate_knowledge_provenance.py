"""Migration script to backfill and correct Phase 3 provenance across all knowledge documents.

Corrects mislabeled community wiki articles, registers source_id, adds canonical_url,
computes deterministic content_hash, and links version freshness against live v7.0.
"""

import hashlib
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.models.knowledge import KnowledgeDocument, compute_content_hash
from backend.models.source_registry import SourceTier, SourceType
from backend.services.source_registry_service import source_registry_service
from backend.services.version_service import version_service

KNOWLEDGE_DIR = ROOT_DIR / "data" / "knowledge"


def migrate_document(file_path: Path) -> dict:
    with open(file_path, "r", encoding="utf-8") as f:
        doc_data = json.load(f)

    doc_id = doc_data["id"]
    meta = doc_data.get("metadata", {})
    content = doc_data.get("content", "")

    # 1. Determine Source Identification and Classification
    if doc_id.startswith("official_"):
        source_id = "src_hoyoverse_patch_notes"
        source_name = "HoYoverse Patch Notes & Maintenance Notices"
        source_type = SourceType.OFFICIAL
        authority_tier = SourceTier.TIER_1_OFFICIAL
        canonical_url = "https://genshin.hoyoverse.com/en/news"
        source_url = meta.get("source_url") or "https://www.hoyoverse.com/en-us/news/125260"
    elif doc_id.startswith("kqm_"):
        source_id = "src_kqm_guides"
        source_name = "KeqingMains Guides (KQM)"
        source_type = SourceType.KQM
        authority_tier = SourceTier.TIER_2_THEORYCRAFTING
        char_slug = meta.get("character", "").lower().replace(" ", "-").replace("'", "")
        canonical_url = f"https://keqingmains.com/{char_slug}/" if char_slug else "https://keqingmains.com/"
        source_url = meta.get("source_url") or canonical_url
    elif doc_id.startswith("mechanics_"):
        # Vetted game mechanics from KQM TCL
        source_id = "src_kqm_tcl"
        source_name = "KQM Theorycrafting Library (TCL)"
        source_type = SourceType.TCL
        authority_tier = SourceTier.TIER_2_THEORYCRAFTING
        canonical_url = "https://library.keqingmains.com/"
        source_url = meta.get("source_url") or "https://library.keqingmains.com/"
    elif doc_id.startswith("wiki_") or doc_id.startswith("artifact_"):
        # Community wiki articles previously mislabeled as AUTHORITATIVE
        source_id = "src_genshin_fandom_wiki"
        source_name = "Genshin Impact Community Wiki (Fandom)"
        source_type = SourceType.COMMUNITY
        authority_tier = SourceTier.TIER_5_COMMUNITY
        source_url = meta.get("source_url") or "https://genshin-impact.fandom.com/"
        canonical_url = meta.get("source_url") or "https://genshin-impact.fandom.com/wiki/Genshin_Impact_Wiki"
    else:
        source_id = "src_community_general"
        source_name = "Genshin Community Discussions"
        source_type = SourceType.COMMUNITY
        authority_tier = SourceTier.TIER_5_COMMUNITY
        canonical_url = "https://www.reddit.com/r/Genshin_Impact/"
        source_url = meta.get("source_url") or canonical_url

    # 2. Content Hash (Deterministic SHA-256)
    content_hash = compute_content_hash(content)

    # 3. Version Freshness Assessment
    game_ver = meta.get("game_version", "5.4")
    eval_res = version_service.evaluate_staleness(game_ver)
    if eval_res.is_current:
        freshness_status = "current"
    elif eval_res.version_distance <= 2:
        freshness_status = "recent_compatible"
    else:
        freshness_status = "stale"

    # 4. Dates
    published_at = meta.get("published_at")
    updated_at = meta.get("updated_at")
    retrieved_at = meta.get("retrieved_at") or "2026-09-08T00:00:00Z"

    # Assemble updated metadata
    updated_meta = {
        "source_id": source_id,
        "source": source_name,
        "source_url": source_url,
        "canonical_url": canonical_url,
        "source_type": source_type.value,
        "authority_tier": int(authority_tier.value),
        "character": meta.get("character"),
        "topic": meta.get("topic", "General"),
        "game_version": game_ver,
        "published_at": published_at,
        "updated_at": updated_at,
        "retrieved_at": retrieved_at,
        "content_hash": content_hash,
        "freshness_status": freshness_status,
        "tags": meta.get("tags", []),
    }

    doc_data["metadata"] = updated_meta
    return doc_data


def main():
    print("=== Migrating Knowledge Documents to Phase 3 Provenance Architecture ===")
    migrated_count = 0
    errors = 0

    tier_counts = {}
    type_counts = {}

    for file_path in sorted(KNOWLEDGE_DIR.glob("*.json")):
        try:
            migrated_doc = migrate_document(file_path)
            # Validate with Pydantic model
            validated = KnowledgeDocument.model_validate(migrated_doc)
            assert validated.verify_hash(), f"Hash verification failed for {file_path.name}"

            # Verify against source registry
            is_valid_prov = source_registry_service.validate_provenance(
                validated.metadata.source_id,
                claimed_tier=validated.metadata.authority_tier,
                claimed_type=validated.metadata.source_type,
            )
            assert is_valid_prov, f"Provenance validation failed against registry for {file_path.name}"

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(migrated_doc, f, indent=2, ensure_ascii=False)

            migrated_count += 1
            tier_key = validated.metadata.authority_tier.name
            type_key = validated.metadata.source_type.value
            tier_counts[tier_key] = tier_counts.get(tier_key, 0) + 1
            type_counts[type_key] = type_counts.get(type_key, 0) + 1

        except Exception as e:
            print(f"Error migrating {file_path.name}: {e}")
            errors += 1

    print(f"\n[DONE] Successfully migrated and validated {migrated_count} documents (Errors: {errors}).")
    print(f"Tier Breakdown: {tier_counts}")
    print(f"Type Breakdown: {type_counts}")


if __name__ == "__main__":
    main()
