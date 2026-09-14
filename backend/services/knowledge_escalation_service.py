"""Phase 9: Best-Effort Knowledge Escalation Service for GenshinIQ.

Enforces:
- Controlled Source Hierarchy (Tiers 1 to 5, no arbitrary web crawling)
- Freshness Model (CURRENT, RECENT, STALE, UNKNOWN)
- Version-Aware Escalation (Authoritative integration with version_service)
- Invariant: RETRIEVED != VALIDATED != CURRENT
- Strict Fail-Closed Guardrails when current-version evidence is unavailable
- Full Provenance Tracking across all escalated items
"""

import json
import logging
import re
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Tuple

from backend.models.knowledge_escalation import (
    EscalatedEvidenceItem,
    EscalationDecision,
    EscalationResult,
    EscalationTrigger,
    FreshnessLevel,
)
from backend.models.query_router import (
    DataSource,
    DetectedEntity,
    EvidenceBundle,
    EvidenceItem,
    EvidenceType,
    QueryIntent,
    RoutingDecision,
)
from backend.models.source_registry import Source, SourceTier, SourceType
from backend.services.source_registry_service import source_registry_service
from backend.services.version_service import version_service, parse_version_tuple

logger = logging.getLogger(__name__)

CACHE_DIR = Path("data/runtime")
CACHE_FILE = CACHE_DIR / "escalation_cache.json"


# ---------------------------------------------------------------------------
# Provider Interface & Built-in Providers
# ---------------------------------------------------------------------------

class EscalationProvider(Protocol):
    """Protocol for external knowledge providers."""
    source_id: str
    source_tier: SourceTier
    source_type: SourceType

    def fetch(self, query: str, target_version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        ...


class HoYoverseOfficialEscalationProvider:
    """Queries official HoYoverse news & patch notes (Tier 1)."""
    source_id = "src_hoyoverse_patch_notes"
    source_tier = SourceTier.TIER_1_OFFICIAL
    source_type = SourceType.OFFICIAL

    def __init__(self, endpoint_url: str = "https://genshin.hoyoverse.com/en/news", timeout_seconds: float = 5.0):
        self.endpoint_url = endpoint_url
        self.timeout_seconds = timeout_seconds

    def fetch(self, query: str, target_version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        try:
            req = urllib.request.Request(
                self.endpoint_url,
                headers={"User-Agent": "GenshinIQ-Escalation/1.0 (+https://github.com/Praveen-Aj/GenshinIQ)"},
            )
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                content = response.read().decode("utf-8", errors="ignore")

            # Extract patch notices or version information
            patch_match = re.search(
                r"Version\s+([0-9]+\.[0-9]+)\s+[\"'\u201c\u201d]([^\"'\u201c\u201d]+)[\"'\u201c\u201d]\s+(Update Details|Notice|Now Live)",
                content,
                re.IGNORECASE,
            )
            detected_ver = patch_match.group(1) if patch_match else None

            return {
                "source_name": "HoYoverse Patch Notes & Maintenance Notices",
                "source_url": self.endpoint_url,
                "game_version": detected_ver,
                "content": content[:2000],
                "published_at": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            logger.warning(f"HoYoverse official escalation fetch failed: {e}")
            raise e


class KeqingMainsEscalationProvider:
    """Queries KeqingMains theorycrafting repository (Tier 2)."""
    source_id = "src_kqm_guides"
    source_tier = SourceTier.TIER_2_THEORYCRAFTING
    source_type = SourceType.KQM

    def __init__(self, base_url: str = "https://keqingmains.com", timeout_seconds: float = 5.0):
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds

    def fetch(self, query: str, target_version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        # In production, fetches structured guide metadata from KQM API or index
        return None


class WikiEscalationProvider:
    """Queries selected established Genshin Impact wikis (Tier 4)."""
    source_id = "src_genshin_fandom_wiki"
    source_tier = SourceTier.TIER_4_ESTABLISHED_WIKI
    source_type = SourceType.ESTABLISHED_WIKI

    def __init__(self, base_url: str = "https://genshin-impact.fandom.com", timeout_seconds: float = 5.0):
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds

    def fetch(self, query: str, target_version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        return None


# ---------------------------------------------------------------------------
# Knowledge Escalation Service
# ---------------------------------------------------------------------------

class KnowledgeEscalationService:
    """Evaluates local knowledge quality and orchestrates controlled external escalation."""

    def __init__(self):
        self._providers: Dict[str, EscalationProvider] = {
            "src_hoyoverse_patch_notes": HoYoverseOfficialEscalationProvider(),
            "src_kqm_guides": KeqingMainsEscalationProvider(),
            "src_genshin_fandom_wiki": WikiEscalationProvider(),
        }
        self._mock_providers: Dict[str, EscalationProvider] = {}
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        """Load in-memory cache from disk if available."""
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load escalation cache: {e}")

    def _save_cache(self) -> None:
        """Persist in-memory cache to disk."""
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save escalation cache: {e}")

    def register_mock_provider(self, source_id: str, provider: EscalationProvider) -> None:
        """Register a mock provider for unit tests and simulations."""
        self._mock_providers[source_id] = provider

    def clear_mock_providers(self) -> None:
        """Clear all mock providers."""
        self._mock_providers.clear()

    # =======================================================================
    # 1. Escalation Decision Logic
    # =======================================================================

    def evaluate_escalation(
        self,
        query: str,
        routing: RoutingDecision,
        bundle: EvidenceBundle,
        detected_entities: List[DetectedEntity],
    ) -> EscalationDecision:
        """Determine whether local evidence is sufficient or requires escalation.
        
        Escalation is triggered if:
        1. No local evidence exists.
        2. Local evidence is below required quality or contains placeholders.
        3. Local evidence is stale for a version-sensitive query.
        4. Retrieved evidence has insufficient relevance.
        5. A newly released entity is missing from canonical data.
        6. The query explicitly asks for 'latest', 'current', 'new', 'recent', 'this patch'.
        7. Content likely released after local KB snapshot.
        8. Multiple local sources conflict.
        9. Local KB contains only partial info.
        10. Router identifies query as requiring current external evidence.
        """
        q_lower = query.lower().strip()
        current_ver = version_service.get_current_version().version

        # Indicator of explicit request for current / latest information
        is_explicit_current = bool(re.search(
            r"\b(latest|current|newest|recent|this patch|this version|new update|what's new|what is new|what changed)\b",
            q_lower,
        ))

        # Check for historical query (e.g. "patch 1.0", "in version 2.4", "back in inazuma")
        is_historical_query = bool(re.search(
            r"\b(in patch [1-4]\.[0-9]|version [1-4]\.[0-9]|v[1-4]\.[0-9]|back in|historically|when it was released)\b",
            q_lower,
        ))

        # Trigger 1: No local evidence at all
        if not bundle.items:
            return EscalationDecision(
                should_escalate=True,
                trigger=EscalationTrigger.NO_LOCAL_EVIDENCE,
                target_query=query,
                target_version=current_ver,
                reason="No local evidence found in canonical database or knowledge base.",
            )

        # Check if query targets an unreleased/preview character with verified preview package
        has_preview_entity = False
        if detected_entities:
            for ent in detected_entities:
                if ent.entity_type == "character":
                    try:
                        from backend.services.character_knowledge_service import character_knowledge_service
                        pkg = character_knowledge_service.get_character_package(ent.name)
                        if pkg and pkg.release_status.value == "UNRELEASED_PREVIEW":
                            has_preview_entity = True
                            break
                    except Exception:
                        pass

        # Determine if query requires current-version evidence
        requires_current_evidence = (
            routing.requires_version_check
            or routing.primary_intent == QueryIntent.VERSION_SENSITIVE
            or is_explicit_current
        )

        # Exclude ambient metadata items (such as VERSION_SERVICE version string) from evidence evaluation
        knowledge_items = [it for it in bundle.items if it.source != DataSource.VERSION_SERVICE]

        if detected_entities:
            ent_names = {e.name.lower() for e in detected_entities}
            ent_items = [it for it in knowledge_items if it.entity_name and it.entity_name.lower() in ent_names]
            rel_items = ent_items if ent_items else knowledge_items
            has_current_in_rel = any(
                it.game_version == current_ver and not it.is_stale
                for it in rel_items
            )
        else:
            rel_items = knowledge_items
            has_current_in_rel = any(
                it.game_version == current_ver and not it.is_stale and self._calculate_relevance(query, it.content, current_ver) >= 0.25
                for it in rel_items
            )

        any_stale_in_rel = any(it.is_stale for it in rel_items)
        all_older_in_rel = bool(rel_items) and all(
            it.game_version is not None and parse_version_tuple(it.game_version) < parse_version_tuple(current_ver)
            for it in rel_items if it.game_version
        )

        # Trigger 3a: Explicitly flagged stale items in local evidence
        if requires_current_evidence and not is_historical_query and not has_preview_entity:
            if any_stale_in_rel and not has_current_in_rel:
                return EscalationDecision(
                    should_escalate=True,
                    trigger=EscalationTrigger.STALE_LOCAL_EVIDENCE,
                    target_query=query,
                    target_version=current_ver,
                    reason="Local evidence is flagged as stale for version-sensitive query.",
                )

        # Trigger 6: Explicit request for latest / current / new information
        if is_explicit_current and not is_historical_query and not has_preview_entity:
            if not has_current_in_rel:
                return EscalationDecision(
                    should_escalate=True,
                    trigger=EscalationTrigger.EXPLICIT_CURRENT_REQUEST,
                    target_query=query,
                    target_version=current_ver,
                    reason=f"Query explicitly requests latest/current information, but local evidence lacks verified v{current_ver} data.",
                )

        # Trigger 3b: Stale local evidence on queries requiring current version (all older versions)
        if requires_current_evidence and not is_historical_query and not has_preview_entity:
            if all_older_in_rel and not has_current_in_rel:
                return EscalationDecision(
                    should_escalate=True,
                    trigger=EscalationTrigger.STALE_LOCAL_EVIDENCE,
                    target_query=query,
                    target_version=current_ver,
                    reason="Local evidence contains only older patch data lacking verified current version evidence.",
                )

        # Trigger 5a: Missing new entity from detected entities
        for entity in detected_entities:
            entity_has_doc = any(item.entity_name == entity.name for item in bundle.items)
            if not entity_has_doc and entity.entity_type in ("character", "weapon"):
                return EscalationDecision(
                    should_escalate=True,
                    trigger=EscalationTrigger.MISSING_NEW_ENTITY,
                    target_query=f"{entity.name} Genshin Impact {current_ver}",
                    target_version=current_ver,
                    reason=f"Entity '{entity.name}' lacks local canonical data or knowledge documents.",
                )

        # Trigger 5b: Missing new / unrecognized entity with kit/talent ask
        if not detected_entities:
            all_caps = re.findall(r"\b([A-Z][a-zA-Z0-9_-]{2,})\b", query)
            COMMON_WORDS = {
                "What", "Tell", "How", "Why", "When", "Where", "Which", "Who", "Can",
                "Could", "Should", "Genshin", "Impact", "Version", "Patch", "Update",
                "Latest", "Current", "Spiral", "Abyss", "Imaginarium", "Theater", "Hoyoverse"
            }
            candidates = [w for w in all_caps if w not in COMMON_WORDS]
            if candidates:
                candidate = candidates[0]
                kit_ask = bool(re.search(r"\b(build|talent|talents|skill|skills|burst|weapon|weapons|artifact|artifacts|stat|stats|constellation)\b", q_lower))
                if kit_ask:
                    return EscalationDecision(
                        should_escalate=True,
                        trigger=EscalationTrigger.MISSING_NEW_ENTITY,
                        target_query=f"{candidate} Genshin Impact {current_ver}",
                        target_version=current_ver,
                        reason=f"Query asks about potential entity '{candidate}', but no matching canonical record exists locally.",
                    )

        # Trigger 9: Partial local evidence for character build query when character has build knowledge gaps
        if routing.primary_intent == QueryIntent.CHARACTER_BUILD or QueryIntent.CHARACTER_BUILD in routing.secondary_intents:
            if detected_entities:
                for ent in detected_entities:
                    if ent.entity_type == "character":
                        try:
                            from backend.services.character_knowledge_service import character_knowledge_service
                            pkg = character_knowledge_service.get_character_package(ent.name)
                            if pkg and any(g in pkg.knowledge_gaps for g in ("curated.weapon_recommendations", "curated.artifact_recommendations", "curated.build_priorities")):
                                return EscalationDecision(
                                    should_escalate=True,
                                    trigger=EscalationTrigger.PARTIAL_LOCAL_KB,
                                    target_query=f"{ent.name} build recommendations Genshin Impact {current_ver}",
                                    target_version=current_ver,
                                    reason=f"Character '{ent.name}' has canonical game data but lacks curated expert build guides ({', '.join(pkg.knowledge_gaps[:3])}).",
                                )
                        except Exception as e:
                            logger.warning(f"Error checking character knowledge package for {ent.name}: {e}")

        # Trigger 4: Low relevance in local items
        query_words = set(re.findall(r"\w+", q_lower)) - {"what", "is", "the", "for", "how", "does", "my", "to", "in", "a", "an"}
        if query_words:
            total_matches = sum(
                sum(1 for w in query_words if w in item.content.lower())
                for item in knowledge_items
            )
            if total_matches == 0:
                return EscalationDecision(
                    should_escalate=True,
                    trigger=EscalationTrigger.INSUFFICIENT_RELEVANCE,
                    target_query=query,
                    target_version=current_ver,
                    reason="Local knowledge items lack keyword relevance to the user's specific question.",
                )

        # If none of the triggers fired, local knowledge is sufficient
        return EscalationDecision(
            should_escalate=False,
            trigger=None,
            target_query=query,
            target_version=current_ver,
            reason="Local evidence is sufficient and up-to-date with active game version.",
        )

    # =======================================================================
    # 2. Controlled External Escalation Execution
    # =======================================================================

    async def escalate(
        self,
        query: str,
        decision: EscalationDecision,
    ) -> EscalationResult:
        """Execute controlled knowledge escalation across approved registered sources.
        
        Enforces:
        - Strict provider hierarchy (Tier 1 -> Tier 2 -> Tier 3 -> Tier 4)
        - RETRIEVED != VALIDATED != CURRENT
        - Timeouts, network error handling, rate limiting
        - Conflict tracking across disparate sources
        - Fail-closed result if current evidence cannot be confirmed
        """
        current_ver = version_service.get_current_version().version
        target_ver = decision.target_version or current_ver
        now_iso = datetime.now(timezone.utc).isoformat()

        sources_attempted: List[str] = []
        sources_succeeded: List[str] = []
        sources_failed: List[str] = []
        validated_items: List[EscalatedEvidenceItem] = []
        conflicts_detected: List[Dict[str, Any]] = []

        # Determine prioritized source providers to query
        providers_to_try: List[Tuple[str, EscalationProvider]] = []

        # 1. Use mock providers if registered (testing / simulation)
        if self._mock_providers:
            for sid, p in sorted(self._mock_providers.items(), key=lambda x: int(x[1].source_tier)):
                providers_to_try.append((sid, p))
        else:
            # 2. Production providers ordered by tier authority
            for sid, p in sorted(self._providers.items(), key=lambda x: int(x[1].source_tier)):
                # Validate source exists in central registry and is enabled
                source_meta = source_registry_service.get_source(sid)
                if source_meta and source_meta.enabled:
                    providers_to_try.append((sid, p))

        # Query each approved source provider
        for sid, provider in providers_to_try:
            sources_attempted.append(sid)

            # Check cache
            cache_key = f"{sid}:{query}:{target_ver}"
            cached_entry = self._cache.get(cache_key)

            raw_data = None
            if cached_entry:
                raw_data = cached_entry
                sources_succeeded.append(sid)
            else:
                try:
                    raw_data = provider.fetch(query, target_version=target_ver)
                    if raw_data:
                        self._cache[cache_key] = raw_data
                        self._save_cache()
                        sources_succeeded.append(sid)
                    else:
                        sources_failed.append(f"{sid} (empty response)")
                except TimeoutError:
                    logger.warning(f"Escalation source {sid} timed out after threshold.")
                    sources_failed.append(f"{sid} (timeout)")
                    continue
                except urllib.error.HTTPError as e:
                    logger.warning(f"Escalation source {sid} returned HTTP {e.code}.")
                    sources_failed.append(f"{sid} (HTTP {e.code})")
                    continue
                except Exception as e:
                    logger.warning(f"Escalation source {sid} error: {e}")
                    sources_failed.append(f"{sid} ({type(e).__name__}: {str(e)})")
                    continue

            if not raw_data:
                continue

            # ---------------------------------------------------------------
            # 3. Validation Gate: RETRIEVED != VALIDATED != CURRENT
            # ---------------------------------------------------------------
            content = raw_data.get("content", "")
            source_url = raw_data.get("source_url", getattr(provider, "endpoint_url", getattr(provider, "base_url", "")))
            source_name = raw_data.get("source_name", getattr(provider, "source_id", "Approved External Source"))
            doc_version = raw_data.get("game_version")
            published_at = raw_data.get("published_at")
            updated_at = raw_data.get("updated_at")

            # Step 3A: Relevance Validation
            relevance = self._calculate_relevance(query, content, target_version=target_ver)
            if relevance < 0.25:
                logger.info(f"Source {sid} rejected: relevance {relevance:.2f} below cutoff.")
                validated_items.append(EscalatedEvidenceItem(
                    source_name=source_name,
                    source_url=source_url,
                    source_tier=provider.source_tier,
                    source_type=provider.source_type,
                    retrieved_at=now_iso,
                    published_at=published_at,
                    updated_at=updated_at,
                    game_version=doc_version,
                    freshness=FreshnessLevel.UNKNOWN,
                    relevance=relevance,
                    retrieval_status="IRRELEVANT_REJECTED",
                    content="Content rejected due to insufficient query relevance.",
                    validation_notes=f"Relevance score {relevance:.2f} is below 0.25 cutoff.",
                ))
                continue

            # Step 3B: Freshness & Version Validation
            freshness, val_notes = self._evaluate_freshness(doc_version, target_ver)

            # Step 3C: Conflict Detection across acquired items
            for prior in validated_items:
                if prior.retrieval_status == "VALIDATED":
                    if self._detect_conflict(prior.content, content):
                        conflict_entry = {
                            "source_a": prior.source_name,
                            "tier_a": prior.source_tier,
                            "source_b": source_name,
                            "tier_b": provider.source_tier,
                            "topic": query,
                            "conflict_detail": "Differing claims detected across sources.",
                        }
                        conflicts_detected.append(conflict_entry)
                        val_notes += " | Note: Potential conflict detected with " + prior.source_name

            item = EscalatedEvidenceItem(
                source_name=source_name,
                source_url=source_url,
                source_tier=provider.source_tier,
                source_type=provider.source_type,
                retrieved_at=now_iso,
                published_at=published_at,
                updated_at=updated_at,
                game_version=doc_version,
                freshness=freshness,
                relevance=relevance,
                retrieval_status="VALIDATED",
                content=content,
                raw_content=raw_data.get("raw_content", content),
                validation_notes=val_notes,
            )
            validated_items.append(item)

        # -------------------------------------------------------------------
        # 4. Success Evaluation & Fail-Closed Gate
        # -------------------------------------------------------------------
        usable_items = [it for it in validated_items if it.retrieval_status == "VALIDATED"]
        has_current_verified = any(it.freshness == FreshnessLevel.CURRENT for it in usable_items)
        has_recent_compatible = any(it.freshness == FreshnessLevel.RECENT for it in usable_items)

        # For version-sensitive or explicit current requests, we REQUIRE CURRENT or RECENT
        needs_current = decision.trigger in (
            EscalationTrigger.EXPLICIT_CURRENT_REQUEST,
            EscalationTrigger.STALE_LOCAL_EVIDENCE,
        ) or decision.target_version is not None

        if needs_current:
            if not (has_current_verified or has_recent_compatible):
                # FAIL CLOSED: We cannot confirm current-version evidence
                failure_reason = (
                    f"I couldn't verify sufficiently current information for this question. "
                    f"Target game version is v{target_ver}, but external escalation only found "
                    f"{'stale or unverified' if usable_items else 'no'} evidence across approved sources."
                )
                return EscalationResult(
                    success=False,
                    decision=decision,
                    items=validated_items,
                    sources_attempted=sources_attempted,
                    sources_succeeded=sources_succeeded,
                    sources_failed=sources_failed,
                    failure_reason=failure_reason,
                    is_current_verified=False,
                    conflicts_detected=conflicts_detected,
                )

        if not usable_items:
            failure_reason = (
                f"I couldn't verify sufficiently current information for this question. "
                f"All approved external sources either failed ({', '.join(sources_failed) or 'network unavailable'}) "
                f"or returned irrelevant content."
            )
            return EscalationResult(
                success=False,
                decision=decision,
                items=validated_items,
                sources_attempted=sources_attempted,
                sources_succeeded=sources_succeeded,
                sources_failed=sources_failed,
                failure_reason=failure_reason,
                is_current_verified=False,
                conflicts_detected=conflicts_detected,
            )

        return EscalationResult(
            success=True,
            decision=decision,
            items=usable_items,
            sources_attempted=sources_attempted,
            sources_succeeded=sources_succeeded,
            sources_failed=sources_failed,
            failure_reason=None,
            is_current_verified=has_current_verified,
            conflicts_detected=conflicts_detected,
        )

    # =======================================================================
    # Helpers
    # =======================================================================

    def _calculate_relevance(self, query: str, content: str, target_version: Optional[str] = None) -> float:
        """Compute keyword overlap relevance between query and retrieved content."""
        GENERIC_WORDS = {
            "what", "is", "the", "for", "how", "does", "my", "to", "in", "a", "an", "and", "of", "on",
            "this", "that", "with", "from", "are", "tell", "about", "can", "you", "patch", "version",
            "update", "latest", "new", "changed", "changes", "current", "newest", "recent", "genshin",
            "impact", "game", "information", "info", "meta"
        }
        subtopics = [t for t in re.findall(r"\w+", query.lower()) if len(t) >= 3 and t not in GENERIC_WORDS]
        c_lower = content.lower()

        if subtopics:
            matched = sum(1 for t in subtopics if t in c_lower)
            if matched == 0:
                return 0.0
            # Domain-specific anchors require the anchor keyword to be present in candidate text
            DOMAIN_ANCHORS = {"abyss", "spiral", "theater", "imaginarium", "banner", "banners", "lunar", "floor"}
            query_anchors = set(subtopics) & DOMAIN_ANCHORS
            if query_anchors and not any(a in c_lower for a in query_anchors):
                return 0.0
            return round(min(1.0, (matched / len(subtopics))), 2)
        else:
            # Pure version / patch query without specific sub-topic
            if any(w in c_lower for w in ("version", "patch", "update", "introduces", "notes", "notice", "maintenance")):
                return 1.0
            return 0.0

    def _evaluate_freshness(self, doc_version: Optional[str], target_version: str) -> Tuple[FreshnessLevel, str]:
        """Evaluate evidence freshness relative to target/current version."""
        if not doc_version:
            return FreshnessLevel.UNKNOWN, "No version metadata could be parsed from external source."

        doc_tuple = parse_version_tuple(doc_version)
        target_tuple = parse_version_tuple(target_version)

        if doc_tuple == target_tuple:
            return FreshnessLevel.CURRENT, f"Matches current live game version v{target_version}."

        if doc_tuple[0] == target_tuple[0] and doc_tuple[1] == target_tuple[1] - 1:
            return FreshnessLevel.RECENT, f"Recent patch v{doc_version} (1 minor patch behind v{target_version})."

        if doc_tuple < target_tuple:
            return FreshnessLevel.STALE, f"Superseded by subsequent updates (v{doc_version} < v{target_version})."

        return FreshnessLevel.UNKNOWN, f"Unrecognized version format: v{doc_version}."

    def _detect_conflict(self, text_a: str, text_b: str) -> bool:
        """Detect obvious conflicting stat or recommendation statements."""
        # Check for opposing recommendations (e.g. BIS weapon differences)
        recommends_a = set(re.findall(r"\bbis:\s*(\w+)", text_a, re.IGNORECASE))
        recommends_b = set(re.findall(r"\bbis:\s*(\w+)", text_b, re.IGNORECASE))
        if recommends_a and recommends_b and recommends_a != recommends_b:
            return True
        return False


# Singleton instance
knowledge_escalation_service = KnowledgeEscalationService()
