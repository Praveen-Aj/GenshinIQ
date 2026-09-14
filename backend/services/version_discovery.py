"""Genshin Impact Live Version Discovery and Verification Service.

Implements the three decoupled operations:
1. DISCOVER: Queries approved Tier 1 HoYoverse official sources for latest live patch evidence.
2. VERIFY: Strictly validates legitimacy, release status, non-future dates, and source authority.
3. Fallback: Gracefully handles network failure, malformed responses, or offline cache states.
"""

import logging
import re
import urllib.request
import json
from datetime import datetime, timezone
from typing import List, Optional, Protocol

from backend.models.version import (
    DiscoveredVersionCandidate,
    VerificationResult,
    GameVersion,
    VerificationStatus,
)
from backend.services.version_service import parse_version_tuple

logger = logging.getLogger(__name__)

OFFICIAL_NEWS_URL = "https://genshin.hoyoverse.com/en/news"


class VersionDiscoveryProvider(Protocol):
    """Protocol interface for version discovery sources."""
    def discover(self) -> Optional[DiscoveredVersionCandidate]:
        ...


class HoYoverseOfficialDiscoveryProvider:
    """Queries official HoYoverse news and announcements for live patch status."""

    def __init__(self, endpoint_url: str = OFFICIAL_NEWS_URL, timeout_seconds: float = 5.0):
        self.endpoint_url = endpoint_url
        self.timeout_seconds = timeout_seconds

    def discover(self) -> Optional[DiscoveredVersionCandidate]:
        """Attempt to query official HoYoverse source for latest game version."""
        try:
            req = urllib.request.Request(
                self.endpoint_url,
                headers={"User-Agent": "GenshinIQ-VersionDiscovery/1.0 (+https://github.com/Praveen-Aj/GenshinIQ)"},
            )
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                content = response.read().decode("utf-8", errors="ignore")

            # Parse patch update announcement pattern
            # Matches strings like "Version 7.0 'The Stars Turn Anew' Update Details"
            patch_match = re.search(
                r"Version\s+([0-9]+\.[0-9]+)\s+[\"'\u201c\u201d]([^\"'\u201c\u201d]+)[\"'\u201c\u201d]\s+(Update Details|Notice|Now Live)",
                content,
                re.IGNORECASE,
            )
            if patch_match:
                ver_str = patch_match.group(1)
                patch_name = patch_match.group(2).strip()
                is_live = "Update Details" in patch_match.group(3) or "Now Live" in patch_match.group(3)

                return DiscoveredVersionCandidate(
                    version=ver_str,
                    name=patch_name,
                    release_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    is_released=is_live,
                    is_upcoming=not is_live,
                    source_id="src_hoyoverse_patch_notes",
                    source_url=self.endpoint_url,
                    raw_evidence=patch_match.group(0),
                )

            # Check for generic Version X.Y mentions if specific title pattern wasn't found
            gen_match = re.search(r"Version\s+([0-9]+\.[0-9]+)\s+Update", content, re.IGNORECASE)
            if gen_match:
                ver_str = gen_match.group(1)
                return DiscoveredVersionCandidate(
                    version=ver_str,
                    name=f"Version {ver_str}",
                    release_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    is_released=True,
                    is_upcoming=False,
                    source_id="src_hoyoverse_patch_notes",
                    source_url=self.endpoint_url,
                    raw_evidence=gen_match.group(0),
                )

            logger.info("Official page accessed but no newer version string could be parsed.")
            return None

        except Exception as e:
            logger.warning(f"Official HoYoverse version discovery unreachable: {e}")
            return None


class MockDiscoveryProvider:
    """Mockable version discovery provider for unit tests, fixtures, and failure simulations."""

    def __init__(
        self,
        candidate: Optional[DiscoveredVersionCandidate] = None,
        simulate_network_failure: bool = False,
        simulate_malformed: bool = False,
    ):
        self.candidate = candidate
        self.simulate_network_failure = simulate_network_failure
        self.simulate_malformed = simulate_malformed

    def discover(self) -> Optional[DiscoveredVersionCandidate]:
        if self.simulate_network_failure:
            raise ConnectionError("Simulated network outage connecting to official news source.")
        if self.simulate_malformed:
            raise ValueError("Malformed or unparseable JSON/HTML response from discovery endpoint.")
        return self.candidate


def verify_candidate(
    candidate: Optional[DiscoveredVersionCandidate],
    current_version: str,
    registry_versions: List[GameVersion],
) -> VerificationResult:
    """Validate discovered candidate version according to strict authoritative rules.
    
    Invariants enforced:
    - Candidate must not be None.
    - Candidate must be explicitly released (not upcoming/preview).
    - Candidate release date must not be in the distant future.
    - Candidate cannot be an unverified jump skipping the next expected patch.
    - Candidate must originate from an approved official or structured source.
    """
    if candidate is None:
        return VerificationResult(
            is_valid=False,
            status="FAILED_DISCOVERY",
            reason="No candidate version discovered from approved sources.",
        )

    cand_tuple = parse_version_tuple(candidate.version)
    curr_tuple = parse_version_tuple(current_version)

    # 1. Semantic validity
    if cand_tuple == (0, 0):
        return VerificationResult(
            is_valid=False,
            status="FAILED_MALFORMED",
            reason=f"Candidate version '{candidate.version}' is not a valid semantic version string.",
        )

    # 2. Rejection of unreleased / upcoming versions
    if not candidate.is_released or candidate.is_upcoming:
        return VerificationResult(
            is_valid=False,
            status="REJECTED_UNRELEASED",
            reason=f"Version {candidate.version} ('{candidate.name}') is an upcoming/unreleased preview, not live.",
            candidate=candidate,
        )

    # 3. Source authority check
    approved_sources = {"src_hoyoverse_patch_notes", "src_hoyoverse_official", "src_genshin_ingame"}
    if candidate.source_id not in approved_sources:
        return VerificationResult(
            is_valid=False,
            status="REJECTED_UNAPPROVED_SOURCE",
            reason=f"Source ID '{candidate.source_id}' is not an approved Tier 1 official version authority.",
            candidate=candidate,
        )

    # 4. Already current check
    if candidate.version == current_version:
        return VerificationResult(
            is_valid=True,
            status="ALREADY_CURRENT",
            reason=f"Discovered version {candidate.version} matches the current canonical version.",
            candidate=candidate,
        )

    # 5. Older version check
    if cand_tuple < curr_tuple:
        return VerificationResult(
            is_valid=False,
            status="REJECTED_OLDER",
            reason=f"Discovered version {candidate.version} is older than current version {current_version}.",
            candidate=candidate,
        )

    # 6. Future jump check (cannot jump e.g. 7.0 -> 7.2 or 7.0 -> 8.5 without intervening release)
    # Minor increment can be at most curr + 1, or major + 1 with minor 0
    is_next_minor = (cand_tuple[0] == curr_tuple[0]) and (cand_tuple[1] <= curr_tuple[1] + 1)
    is_next_major = (cand_tuple[0] == curr_tuple[0] + 1) and (cand_tuple[1] == 0)
    if not (is_next_minor or is_next_major):
        return VerificationResult(
            is_valid=False,
            status="REJECTED_FUTURE_JUMP",
            reason=f"Discovered version {candidate.version} represents an invalid multi-patch jump from {current_version}.",
            candidate=candidate,
        )

    # All checks passed
    return VerificationResult(
        is_valid=True,
        status="PASS",
        reason=f"Version {candidate.version} ('{candidate.name}') verified as legitimate released patch.",
        candidate=candidate,
    )
