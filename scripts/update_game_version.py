"""Automated Game Version Update & Discovery Pipeline.

Follows strict version discovery principles:
1. Validates candidate version against approved official sources and canonical registry.
2. Promotes exactly one verified release as current.
3. Preserves complete historical version archive.
4. Tracks changed systems for change-aware staleness invalidation.
5. Rebuilds data manifest and logs clear audit output.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.services.version_service import version_service
from scripts.build_manifest import main as rebuild_manifest


def update_game_version(
    version: str,
    name: str,
    release_date: str,
    major_region: str,
    changed_systems: list[str] = None,
    source_url: str = "https://genshin.hoyoverse.com/en/news",
):
    print(f"=== Starting Canonical Game Version Promotion to v{version} ===")
    status_before = version_service.get_status()
    print(f"Current Version Before: v{status_before.current_version} ({status_before.patch_name})")

    # Update version registry
    new_status = version_service.update_version_state(
        new_version=version,
        name=name,
        release_date=release_date,
        major_region=major_region,
        is_released=True,
        is_current=True,
        changed_systems=changed_systems or [],
        source_url=source_url,
    )

    print(f"[SUCCESS] Promoted to Current Version: v{new_status.current_version} ({new_status.patch_name})")
    print(f"Tracked Versions Total: {new_status.total_tracked_versions}")
    print(f"Discovery Status: {new_status.discovery_status}")

    # Rebuild manifest
    print("\n--- Rebuilding Manifest with Updated Version Anchor ---")
    rebuild_manifest()

    print("\n=== Version Promotion Audit Complete ===")
    return new_status


def main():
    parser = argparse.ArgumentParser(description="GenshinIQ Version Discovery & Update Pipeline")
    parser.add_argument("--check", action="store_true", help="Perform automated discovery against approved official source")
    parser.add_argument("--no-auto-promote", action="store_true", help="Discover and verify without promoting")
    parser.add_argument("--version", type=str, help="Manual version promotion fallback (e.g. 7.1)")
    parser.add_argument("--name", type=str, help="Official patch name")
    parser.add_argument("--release-date", type=str, help="Release date YYYY-MM-DD")
    parser.add_argument("--region", type=str, default="Teyvat", help="Major region associated with the patch")
    parser.add_argument("--changed-systems", nargs="*", default=[], help="Systems/characters modified in this patch")
    args = parser.parse_args()

    # Manual promotion fallback
    if args.version:
        update_game_version(
            version=args.version,
            name=args.name or f"Version {args.version}",
            release_date=args.release_date or "2026-10-14",
            major_region=args.region,
            changed_systems=args.changed_systems,
        )
        return

    # Automated discovery & verification (--check or default)
    curr_before = version_service.get_current_version().version
    print("=== GenshinIQ Version Discovery & Verification ===")
    print(f"Current registry version: {curr_before}")
    print("Checking approved official source (src_hoyoverse_patch_notes)...")

    result = version_service.check_and_update(auto_promote=not args.no_auto_promote)

    if result.discovery_status in ["CACHED_OFFLINE", "MALFORMED_DATA"]:
        print("Discovery: FAILED")
        print("Fallback: LAST_VERIFIED")
        print(f"Effective current version: {result.effective_current_version}")
        print(f"Status Note: {result.message}")
        return

    discovered = result.discovered_version or curr_before
    print(f"Discovered version: {discovered}")
    print(f"Verification: {result.verification_status}")

    if result.update_available:
        print("Update available: YES")
        if result.promoted:
            print(f"[PROMOTED] Current version updated to v{result.effective_current_version}")
            print(f"Historical records preserved ({len(version_service.list_versions())} total patches).")
            print("\n--- Rebuilding Manifest with Updated Version Anchor ---")
            rebuild_manifest()
            print("\n=== Automated Version Promotion Complete ===")
        else:
            print(f"Update detected but auto-promotion was skipped (--no-auto-promote).")
    else:
        print("Update required: NO")
        print(f"Effective current version: {result.effective_current_version}")
        if result.message:
            print(f"Audit: {result.message}")


if __name__ == "__main__":
    main()
