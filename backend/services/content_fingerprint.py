"""Content-Aware Dataset Fingerprinting Engine for GenshinIQ.

Computes deterministic cryptographic fingerprints over canonical game content,
excluding volatile metadata (timestamps, version labels, file paths, source tags).
Ensures dataset identity is content-aware and prevents older datasets from being
relabeled and promoted as new releases.
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Keys strictly excluded from content fingerprinting
VOLATILE_METADATA_KEYS = {
    "game_version_updated",
    "source_version",
    "source_id",
    "retrieved_at",
    "dataset_version",
    "timestamp",
    "validation_state",
    "verification_status",
    "content_hash",
    "file_hashes",
    "last_updated",
    "created_at",
}


def _strip_volatile_fields(obj: Any) -> Any:
    """Recursively strip volatile metadata keys from dicts and lists."""
    if isinstance(obj, dict):
        return {
            k: _strip_volatile_fields(v)
            for k, v in sorted(obj.items())
            if k not in VOLATILE_METADATA_KEYS
        }
    elif isinstance(obj, list):
        return [_strip_volatile_fields(item) for item in obj]
    return obj


def compute_dataset_content_fingerprint(version_dir: Path) -> str:
    """Compute a deterministic SHA-256 fingerprint over the canonical content of version_dir.
    
    Includes:
    - characters.json (sorted by ID)
    - weapons.json (sorted by ID)
    - artifacts.json (sorted by ID)
    - materials.json (sorted by ID)
    - avatar_curves.json
    - weapon_curves.json
    - artifact_levels.json
    
    Excludes all volatile version tags, source versions, file hashes, and timestamps.
    """
    version_dir = Path(version_dir)
    canonical_files = [
        "characters.json",
        "weapons.json",
        "artifacts.json",
        "materials.json",
        "avatar_curves.json",
        "weapon_curves.json",
        "artifact_levels.json",
    ]

    hasher = hashlib.sha256()

    for fname in canonical_files:
        fpath = version_dir / fname
        if not fpath.exists():
            continue
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            cleaned_data = _strip_volatile_fields(raw_data)

            # Sort lists of dicts by 'id' or 'name' for strict deterministic ordering
            if isinstance(cleaned_data, list):
                cleaned_data = sorted(
                    cleaned_data,
                    key=lambda x: str(x.get("id", "")) if isinstance(x, dict) else str(x),
                )

            # Deterministic JSON canonical string
            serialized = json.dumps(cleaned_data, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
            hasher.update(fname.encode("utf-8"))
            hasher.update(b":")
            hasher.update(serialized.encode("utf-8"))
            hasher.update(b"\n")
        except Exception as e:
            logger.warning(f"Error computing content fingerprint for {fpath}: {e}")

    return hasher.hexdigest()


def check_dataset_relabeling(
    target_version_dir: Path,
    target_version: str,
    all_versions_dir: Path,
) -> Tuple[bool, Optional[str], str]:
    """Check if target_version is an identical relabeled copy of an earlier dataset version.
    
    Returns:
    (is_relabeled, matching_older_version, target_fingerprint)
    """
    target_fp = compute_dataset_content_fingerprint(target_version_dir)
    all_versions_dir = Path(all_versions_dir)

    if not all_versions_dir.exists():
        return False, None, target_fp

    from backend.services.version_service import parse_version_tuple
    target_tup = parse_version_tuple(target_version)

    for v_dir in all_versions_dir.iterdir():
        if not v_dir.is_dir() or v_dir.name == target_version:
            continue
        older_version = v_dir.name
        older_tup = parse_version_tuple(older_version)

        # Only compare against older versions
        if older_tup < target_tup:
            older_fp = compute_dataset_content_fingerprint(v_dir)
            if older_fp == target_fp and target_fp != hashlib.sha256().hexdigest():
                return True, older_version, target_fp

    return False, None, target_fp
