"""Phase 8: Multi-intent Query Router & Tool Selector for GenshinIQ.

Classifies user queries into granular intent categories and determines
which data sources, tools, and deterministic engines are required to
produce a grounded, trustworthy answer.

Routing Rules:
- Gemini MUST NOT bypass the stat engine for calculable questions.
- If required evidence is unavailable, fail closed.
- Version-sensitive questions must verify evidence freshness.
- Account questions require account data; do not hallucinate account state.
"""

import difflib
import logging
import re
from typing import List, Optional, Tuple

from backend.models.query_router import (
    DataSource,
    DetectedEntity,
    QueryIntent,
    RoutingDecision,
)
from backend.services.game_data_service import game_data_service

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pattern banks for intent classification
# ---------------------------------------------------------------------------

# Indicators that the user is asking about THEIR OWN account / build
_ACCOUNT_PATTERNS = [
    r"\bmy\b",
    r"\bmine\b",
    r"\bi have\b",
    r"\bi've\b",
    r"\bi own\b",
    r"\bmy account\b",
    r"\bmy roster\b",
    r"\bmy team\b",
    r"\bmy build\b",
    r"\bmy (\w+) build\b",
    r"\bdo i\b",
    r"\bshould i\b",  # contextual — may combine with build
    r"\bmy inventory\b",
    r"\bmy artifacts?\b",
    r"\bmy weapons?\b",
    r"\bmy characters?\b",
]

# Build review indicators (account-specific build evaluation)
_BUILD_REVIEW_PATTERNS = [
    r"\bis my .+ build (good|bad|okay|ok|optimal|fine)\b",
    r"\breview my\b",
    r"\brate my\b",
    r"\bhow('?s| is) my .+ build\b",
    r"\bevaluate my\b",
    r"\bcheck my\b",
    r"\bimprove my\b",
    r"\boptimize my\b",
    r"\bwhat('?s| is) wrong with my\b",
]

# General build advice indicators (not account-specific)
_CHARACTER_BUILD_PATTERNS = [
    r"\bhow (to|should i|do i) build\b",
    r"\bbest (build|weapon|weapons|artifact|artifacts|set|sets) for\b",
    r"\brecommend.* (build|weapon|weapons|artifact|artifacts|set|sets)\b",
    r"\bwhat (weapon|weapons|artifact|artifacts|set|sets) (should|for|is best|are best)\b",
    r"\bguide\b",
    r"\bbis\b",
    r"\bf2p\b",
    r"\boptimal build\b",
    r"\b(main|sub)stat priorit\b",
]

# Weapon comparison indicators
_WEAPON_COMPARISON_PATTERNS = [
    r"\bwhich (weapon|is better|one is better)\b",
    r"\bcompare .*(weapon|sword|claymore|bow|polearm|catalyst)\b",
    r"\bcompare\b",
    r"\bcomparison\b",
    r"\b(\w+) (vs?|versus|or|compared to) (\w+)\b",
    r"\bbetter( weapon)? (for|on)\b",
    r"\b(weapon|sword|claymore|bow|polearm|catalyst) comparison\b",
]

# Artifact analysis indicators
_ARTIFACT_PATTERNS = [
    r"\bartifact.*(replace|swap|upgrade|change|improve)\b",
    r"\bwhich artifact (should|to|do)\b",
    r"\b(replace|swap|upgrade|change) .*(artifact|piece|flower|feather|plume|sands|goblet|circlet)\b",
    r"\bartifact (analysis|review|evaluation)\b",
    r"\bsubstat.*(roll|value|priority)\b",
    r"\bcrit (value|ratio|cv)\b",
]

# Stat calculation indicators
_STAT_CALCULATION_PATTERNS = [
    r"\b(what|how much|calculate|compute) .*(atk|hp|def|dmg|crit|er|em|damage|stat)\b",
    r"\b(base|total|final) (atk|hp|def)\b",
    r"\bstat.*(with|at|using)\b",
    r"\bdamage (calculation|formula|with|output)\b",
    r"\batk (with|at|using)\b",
    r"\bcalculate\b",
]

# Team building indicators
_TEAM_BUILDING_PATTERNS = [
    r"\b(build|make|suggest|recommend|create).*(team|comp|composition|party)\b",
    r"\bteam (for|with|using|around)\b",
    r"\bbest team\b",
    r"\bwho (goes|works|synergizes|pairs) (well )?with\b",
    r"\bteammates? for\b",
    r"\bcomp(osition)? for\b",
]

# Farming / material indicators
_FARMING_PATTERNS = [
    r"\b(what|which) material\b",
    r"\bmaterials?\b",
    r"\bascend(ing)?\b",
    r"\bascension( material)?\b",
    r"\btalent (material|book)\b",
    r"\bfarm(ing)?\b",
    r"\blevel(ing)? .*(material|cost|need)\b",
    r"\bwhat do i need (to|for)\b",
    r"\bmaterials? (for|to|needed)\b",
    r"\bdomain (for|to farm)\b",
    r"\bweekly boss\b",
    r"\blocal special(ty|ties)\b",
]

# Version-sensitive indicators
_VERSION_SENSITIVE_PATTERNS = [
    r"\b(latest|newest|recent|current) (patch|version|update|change|banner|character|characters|weapon|weapons|abyss|theater|event|events|meta)\b",
    r"\b(latest|newest|recent|current)\b.*\b(patch|version|character|characters|abyss|meta)\b",
    r"\bpatch notes?\b",
    r"\bwhat('?s| has| is)? (new|changed)\b",
    r"\bwhat changes\b",
    r"\bchanges? (in|were|introduced)\b",
    r"\b(patch|version|v) \d+\.\d+\b",
    r"\b(patch|version)\b",
    r"\b(nerf|buff|rework|adjust)\b",
    r"\b(new|upcoming|released) character\b",
    r"\bbanner\b",
    r"\b(spiral abyss|abyss|imaginarium theater)\b",
]

# Knowledge / mechanics search indicators
_KNOWLEDGE_SEARCH_PATTERNS = [
    r"\bhow does .* (work|function|interact|trigger|scale)\b",
    r"\bmechanic(s)?\b",
    r"\bicd\b",
    r"\binternal cooldown\b",
    r"\belemental (reaction|resonance|gauge|aura)\b",
    r"\bsnapshotting?\b",
    r"\bpoise\b",
    r"\binterruption resistance\b",
    r"\bdefense (shred|reduction)\b",
    r"\bresistance (shred|reduction)\b",
    r"\benergy (particle|generation|recharge)\b",
    r"\bgauge unit\b",
]

# Basic game fact indicators (simple factual lookups)
_BASIC_FACT_PATTERNS = [
    r"\bwhat (is|does|are)\b",
    r"\bwhat element\b",
    r"\bwhat weapon type\b",
    r"\bwhat('?s| is) .*(element|weapon|rarity|region|talent|burst|skill|passive|constellation)\b",
    r"\bwho is\b",
    r"\btell me about\b",
    r"\bshow me\b",
    r"\bdescri(be|ption)\b",
]


class QueryRouter:
    """Multi-intent query classifier and tool/source selector.

    Examines the user query and determines:
    1. Primary and secondary intents
    2. Required and optional data sources
    3. Whether deterministic stat engine is needed
    4. Whether account data is required
    5. Whether version-specific filtering is needed
    6. Detected game entities (characters, weapons, artifact sets)
    """

    def classify(self, query: str, uid: Optional[str] = None) -> RoutingDecision:
        """Classify a user query into intents and determine required sources.

        Args:
            query: The user's natural language question.
            uid: Optional user UID (presence implies account data may be available).

        Returns:
            RoutingDecision with classified intents and required sources.
        """
        q_lower = query.lower().strip()
        detected_entities = self._detect_entities(query)

        has_account_indicator = self._matches_any(q_lower, _ACCOUNT_PATTERNS)
        has_uid = uid is not None and uid.strip() != ""

        # Score each intent category
        scores: dict[QueryIntent, float] = {}

        # 1. Build review (account-specific evaluation)
        if self._matches_any(q_lower, _BUILD_REVIEW_PATTERNS):
            scores[QueryIntent.ACCOUNT_BUILD_REVIEW] = 10.0

        # 2. Artifact analysis
        if self._matches_any(q_lower, _ARTIFACT_PATTERNS):
            if has_account_indicator:
                scores[QueryIntent.ARTIFACT_ANALYSIS] = 9.0
            else:
                scores[QueryIntent.ARTIFACT_ANALYSIS] = 5.0

        # Count detected weapons
        weapon_entities = [e for e in detected_entities if e.entity_type == "weapon"]

        # 3. Weapon comparison
        if len(weapon_entities) >= 2 or self._matches_any(q_lower, _WEAPON_COMPARISON_PATTERNS):
            if len(weapon_entities) >= 2:
                scores[QueryIntent.WEAPON_COMPARISON] = 9.0
            elif weapon_entities or "weapon" in q_lower:
                scores[QueryIntent.WEAPON_COMPARISON] = 8.5
            else:
                scores[QueryIntent.WEAPON_COMPARISON] = 7.0

        # 4. Stat calculation
        if self._matches_any(q_lower, _STAT_CALCULATION_PATTERNS):
            if has_account_indicator:
                scores[QueryIntent.STAT_CALCULATION] = 9.0
            else:
                scores[QueryIntent.STAT_CALCULATION] = 7.0

        # 5. Team building
        if self._matches_any(q_lower, _TEAM_BUILDING_PATTERNS):
            scores[QueryIntent.TEAM_BUILDING] = 7.5

        # 6. Farming / materials
        if self._matches_any(q_lower, _FARMING_PATTERNS):
            scores[QueryIntent.FARMING] = 8.5

        # 7. Version-sensitive
        if self._matches_any(q_lower, _VERSION_SENSITIVE_PATTERNS):
            scores[QueryIntent.VERSION_SENSITIVE] = 8.5

        # 8. Character build (general, not account-specific)
        if self._matches_any(q_lower, _CHARACTER_BUILD_PATTERNS):
            # Don't override a stronger account build review
            if QueryIntent.ACCOUNT_BUILD_REVIEW not in scores:
                scores[QueryIntent.CHARACTER_BUILD] = 6.5

        # 9. Knowledge / mechanics search
        if self._matches_any(q_lower, _KNOWLEDGE_SEARCH_PATTERNS):
            scores[QueryIntent.KNOWLEDGE_SEARCH] = 6.0

        # 10. Basic game fact
        if self._matches_any(q_lower, _BASIC_FACT_PATTERNS) and detected_entities:
            # Only activate if we detected a specific entity to look up
            if QueryIntent.CHARACTER_BUILD not in scores and QueryIntent.ACCOUNT_BUILD_REVIEW not in scores:
                scores[QueryIntent.BASIC_GAME_FACT] = 5.0

        # Account indicator boosts — if "my" is present, boost account-related intents
        if has_account_indicator:
            for intent in [QueryIntent.ACCOUNT_BUILD_REVIEW, QueryIntent.STAT_CALCULATION,
                           QueryIntent.ARTIFACT_ANALYSIS, QueryIntent.TEAM_BUILDING,
                           QueryIntent.FARMING, QueryIntent.WEAPON_COMPARISON]:
                if intent in scores:
                    scores[intent] += 3.0
            # If no specific intent matched but "my" is present, default to account build review
            if not scores and detected_entities:
                char_entities = [e for e in detected_entities if e.entity_type == "character"]
                if char_entities:
                    scores[QueryIntent.ACCOUNT_BUILD_REVIEW] = 5.0

        # Fallback: if nothing matched
        if not scores:
            if detected_entities:
                # Has an entity but no specific intent — probably a factual question
                scores[QueryIntent.BASIC_GAME_FACT] = 3.0
            else:
                # General question with no detected entity
                scores[QueryIntent.KNOWLEDGE_SEARCH] = 2.0

        # Sort by score descending
        sorted_intents = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        primary_intent = sorted_intents[0][0]
        secondary_intents = [intent for intent, score in sorted_intents[1:] if score >= 4.0]

        # Check for multi-source: if multiple high-scoring intents from different domains
        if len(sorted_intents) >= 2 and sorted_intents[1][1] >= 6.0:
            # The question needs multiple tools
            if primary_intent != QueryIntent.MULTI_SOURCE:
                secondary_intents = [primary_intent] + secondary_intents
                primary_intent = QueryIntent.MULTI_SOURCE

        # Determine required and optional sources
        required_sources, optional_sources = self._determine_sources(
            primary_intent, secondary_intents, has_account_indicator, has_uid, detected_entities
        )

        requires_account = has_account_indicator or primary_intent == QueryIntent.ACCOUNT_BUILD_REVIEW
        requires_stat = primary_intent in (
            QueryIntent.STAT_CALCULATION,
            QueryIntent.ACCOUNT_BUILD_REVIEW,
            QueryIntent.WEAPON_COMPARISON,
            QueryIntent.ARTIFACT_ANALYSIS,
        ) or any(si in (
            QueryIntent.STAT_CALCULATION,
            QueryIntent.ACCOUNT_BUILD_REVIEW,
            QueryIntent.WEAPON_COMPARISON,
            QueryIntent.ARTIFACT_ANALYSIS,
        ) for si in secondary_intents)

        requires_version = primary_intent == QueryIntent.VERSION_SENSITIVE or \
            QueryIntent.VERSION_SENSITIVE in secondary_intents

        reasoning = self._build_reasoning(primary_intent, secondary_intents, detected_entities, has_account_indicator)

        return RoutingDecision(
            primary_intent=primary_intent,
            secondary_intents=secondary_intents,
            required_sources=required_sources,
            optional_sources=optional_sources,
            detected_entities=detected_entities,
            requires_account_data=requires_account,
            requires_stat_engine=requires_stat,
            requires_version_check=requires_version,
            reasoning=reasoning,
        )

    # -----------------------------------------------------------------------
    # Entity Detection
    # -----------------------------------------------------------------------

    def _detect_entities(self, query: str) -> List[DetectedEntity]:
        """Detect game entities (characters, weapons, artifact sets) in the query."""
        entities: List[DetectedEntity] = []
        q_lower = query.lower()

        # 1. Detect characters
        char_name = self._detect_character(query)
        if char_name:
            entities.append(DetectedEntity(
                entity_type="character",
                name=char_name,
                matched_text=char_name,
            ))

        # 2. Detect weapons (fuzzy match against canonical weapon list)
        weapons = game_data_service.list_weapons()
        for w in weapons:
            clean_name = w.name.strip("\"'")
            if re.search(rf"\b{re.escape(clean_name.lower())}\b", q_lower):
                entities.append(DetectedEntity(
                    entity_type="weapon",
                    name=clean_name,
                    matched_text=clean_name,
                ))

        # 3. Detect artifact sets
        artifact_sets = game_data_service.list_artifact_sets()
        for a in artifact_sets:
            if re.search(rf"\b{re.escape(a.name.lower())}\b", q_lower):
                entities.append(DetectedEntity(
                    entity_type="artifact_set",
                    name=a.name,
                    matched_text=a.name,
                ))

        return entities

    def _detect_character(self, query: str) -> Optional[str]:
        """Detect a character name in the query using canonical data + Enka mappings.

        Reuses the proven character detection logic from the existing RAG service.
        """
        query_lower = query.lower()

        # 1. Enka mappings first (newest characters)
        try:
            from backend.services.enka_mappings import CHARACTER_DATABASE
            for mapping in CHARACTER_DATABASE.values():
                char_name = mapping[0]
                pattern = rf"\b{re.escape(char_name.lower())}\b"
                if re.search(pattern, query_lower):
                    return char_name
        except Exception:
            pass

        # 2. Canonical game data characters (exact full name match first)
        characters = game_data_service.list_characters()
        for char in characters:
            pattern = rf"\b{re.escape(char.name.lower())}\b"
            if re.search(pattern, query_lower):
                return char.name

        # 2b. Name part matching (e.g. "Kazuha" for "Kaedehara Kazuha", "Ayaka" for "Kamisato Ayaka")
        for char in characters:
            parts = char.name.lower().split()
            if len(parts) > 1:
                for part in parts:
                    if len(part) >= 4 and re.search(rf"\b{re.escape(part)}\b", query_lower):
                        return char.name

        # 3. Fuzzy match fallback
        candidate_names = [char.name.lower() for char in characters]
        if candidate_names:
            query_tokens = [token for token in re.findall(r"[a-z0-9]+", query_lower) if len(token) >= 3]
            for token in query_tokens:
                close = difflib.get_close_matches(token, candidate_names, n=1, cutoff=0.82)
                if close:
                    matched_name = close[0]
                    for char in characters:
                        if char.name.lower() == matched_name:
                            return char.name

        return None

    # -----------------------------------------------------------------------
    # Source Determination
    # -----------------------------------------------------------------------

    def _determine_sources(
        self,
        primary: QueryIntent,
        secondaries: List[QueryIntent],
        has_account_indicator: bool,
        has_uid: bool,
        detected_entities: List[DetectedEntity],
    ) -> Tuple[List[DataSource], List[DataSource]]:
        """Determine required and optional data sources based on intents."""

        required: set[DataSource] = set()
        optional: set[DataSource] = set()

        all_intents = [primary] + secondaries

        for intent in all_intents:
            r, o = self._sources_for_intent(intent)
            required.update(r)
            optional.update(o)

        # Account sources are only required if we have account indicators
        account_sources = {DataSource.ACCOUNT_SHOWCASE, DataSource.ACCOUNT_INVENTORY}
        if not has_account_indicator:
            # Move account sources from required to optional
            for src in account_sources:
                if src in required:
                    required.discard(src)
                    optional.add(src)

        # Gemini reasoning is always at least optional (for natural language explanation)
        optional.add(DataSource.GEMINI_REASONING)

        # Don't double-count
        optional -= required

        return sorted(required, key=lambda x: x.value), sorted(optional, key=lambda x: x.value)

    def _sources_for_intent(self, intent: QueryIntent) -> Tuple[set[DataSource], set[DataSource]]:
        """Map an intent to its required and optional sources."""
        SOURCE_MAP: dict[QueryIntent, Tuple[set[DataSource], set[DataSource]]] = {
            QueryIntent.BASIC_GAME_FACT: (
                {DataSource.CANONICAL_GAME_DATA},
                {DataSource.KNOWLEDGE_BASE, DataSource.VERSION_SERVICE},
            ),
            QueryIntent.CHARACTER_BUILD: (
                {DataSource.CANONICAL_GAME_DATA, DataSource.KNOWLEDGE_BASE},
                {DataSource.VERSION_SERVICE, DataSource.ACCOUNT_SHOWCASE},
            ),
            QueryIntent.ACCOUNT_BUILD_REVIEW: (
                {DataSource.CANONICAL_GAME_DATA, DataSource.KNOWLEDGE_BASE,
                 DataSource.ACCOUNT_SHOWCASE, DataSource.STAT_ENGINE},
                {DataSource.ACCOUNT_INVENTORY, DataSource.VERSION_SERVICE},
            ),
            QueryIntent.WEAPON_COMPARISON: (
                {DataSource.CANONICAL_GAME_DATA, DataSource.STAT_ENGINE},
                {DataSource.KNOWLEDGE_BASE, DataSource.ACCOUNT_SHOWCASE, DataSource.ACCOUNT_INVENTORY},
            ),
            QueryIntent.ARTIFACT_ANALYSIS: (
                {DataSource.CANONICAL_GAME_DATA, DataSource.STAT_ENGINE},
                {DataSource.ACCOUNT_SHOWCASE, DataSource.ACCOUNT_INVENTORY, DataSource.KNOWLEDGE_BASE},
            ),
            QueryIntent.STAT_CALCULATION: (
                {DataSource.CANONICAL_GAME_DATA, DataSource.STAT_ENGINE},
                {DataSource.ACCOUNT_SHOWCASE, DataSource.ACCOUNT_INVENTORY},
            ),
            QueryIntent.TEAM_BUILDING: (
                {DataSource.CANONICAL_GAME_DATA, DataSource.KNOWLEDGE_BASE},
                {DataSource.ACCOUNT_SHOWCASE, DataSource.ACCOUNT_INVENTORY, DataSource.VERSION_SERVICE},
            ),
            QueryIntent.FARMING: (
                {DataSource.CANONICAL_GAME_DATA},
                {DataSource.ACCOUNT_INVENTORY, DataSource.KNOWLEDGE_BASE, DataSource.VERSION_SERVICE},
            ),
            QueryIntent.VERSION_SENSITIVE: (
                {DataSource.VERSION_SERVICE, DataSource.KNOWLEDGE_BASE},
                {DataSource.CANONICAL_GAME_DATA},
            ),
            QueryIntent.KNOWLEDGE_SEARCH: (
                {DataSource.KNOWLEDGE_BASE},
                {DataSource.CANONICAL_GAME_DATA, DataSource.VERSION_SERVICE},
            ),
            QueryIntent.MULTI_SOURCE: (
                {DataSource.CANONICAL_GAME_DATA, DataSource.KNOWLEDGE_BASE},
                {DataSource.STAT_ENGINE, DataSource.ACCOUNT_SHOWCASE, DataSource.VERSION_SERVICE},
            ),
            QueryIntent.INSUFFICIENT_EVIDENCE: (
                set(),
                set(),
            ),
        }
        return SOURCE_MAP.get(intent, (set(), set()))

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _matches_any(text: str, patterns: List[str]) -> bool:
        """Check if any regex pattern matches the text."""
        for pattern in patterns:
            if re.search(pattern, text):
                return True
        return False

    @staticmethod
    def _build_reasoning(
        primary: QueryIntent,
        secondaries: List[QueryIntent],
        entities: List[DetectedEntity],
        has_account: bool,
    ) -> str:
        """Build a human-readable reasoning string for the routing decision."""
        parts = [f"Primary intent: {primary.value}"]
        if secondaries:
            parts.append(f"Secondary: {', '.join(s.value for s in secondaries)}")
        if entities:
            parts.append(f"Entities: {', '.join(f'{e.entity_type}:{e.name}' for e in entities)}")
        if has_account:
            parts.append("Account context requested")
        return " | ".join(parts)


# Singleton instance
query_router = QueryRouter()
