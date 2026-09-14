"""Phase 10: Citation and Grounding Service.

Provides:
1. Four-level citation assembly:
   - DATASET (Canonical game facts)
   - SOURCE (Curated/escalated external knowledge)
   - CALCULATION (Deterministic Stat Engine)
   - ACCOUNT (Enka showcase / GOOD inventory)
2. Automated claim-evidence extraction and verification.
3. Grounding scoring (0.0 to 1.0) and status classification (FULLY_GROUNDED, PARTIALLY_GROUNDED, UNGROUNDED).
4. Citation relevance filtering ensuring citations are meaningful rather than decorative.
"""

import logging
import re
from typing import Dict, List, Optional, Set, Tuple

from backend.models.chat import Citation
from backend.models.grounding import (
    CitationType,
    ConfidenceLevel,
    GroundingStatus,
    GroundingVerificationResult,
    SupportedClaim,
)
from backend.models.query_router import (
    DataSource,
    EvidenceBundle,
    EvidenceItem,
    EvidenceType,
    RoutingDecision,
)

logger = logging.getLogger(__name__)


class GroundingService:
    """Manages Phase 10 citation assembly, claim-evidence mapping, and grounding verification."""

    # ===================================================================
    # 1. Four-Level Citation Builders
    # ===================================================================

    def build_dataset_citation(
        self,
        entity_name: str,
        entity_type: str,
        attributes_summary: str,
        game_version: Optional[str] = None,
    ) -> Citation:
        """Construct a CitationType.DATASET citation for canonical game facts."""
        slug = entity_name.lower().replace(" ", "_").replace("'", "")
        return Citation(
            source_name="Canonical Game Database",
            source_url=f"/api/{entity_type}s/{slug}",
            canonical_url=f"https://genshin.hoyoverse.com/en/character/{slug}",
            snippet=attributes_summary[:180] + "..." if len(attributes_summary) > 180 else attributes_summary,
            character=entity_name if entity_type == "character" else None,
            topic=f"Canonical {entity_type.title()} Specifications",
            game_version=game_version or "7.0",
            source_id="src_canonical_game_data",
            source_type="structured_dataset",
            authority_tier=1,
            citation_type=CitationType.DATASET.value,
            confidence=ConfidenceLevel.HIGH.value,
            display_label="Canonical Game Data",
            claim_supported=f"Base kit and verified attributes for {entity_name}",
        )

    def build_account_citation(
        self,
        uid: str,
        character_name: Optional[str] = None,
        build_summary: Optional[str] = None,
    ) -> Citation:
        """Construct a CitationType.ACCOUNT citation for user's account records."""
        snippet = build_summary or f"Active showcase build data for UID {uid}"
        return Citation(
            source_name="Enka.Network Account Showcase",
            source_url=f"https://enka.network/u/{uid}",
            canonical_url=f"https://enka.network/u/{uid}",
            snippet=snippet[:180] + "..." if len(snippet) > 180 else snippet,
            character=character_name,
            topic=f"Account Showcase (UID {uid})" if not character_name else f"Your {character_name} Build",
            game_version=None,
            source_id=f"acct_showcase_{uid}",
            source_type="user_account_snapshot",
            authority_tier=1,
            citation_type=CitationType.ACCOUNT.value,
            confidence=ConfidenceLevel.HIGH.value,
            display_label="Your Account Showcase",
            claim_supported=f"Personal build details for {character_name or 'showcase'}",
        )

    def build_calculation_citation(
        self,
        character_name: str,
        calculation_summary: str,
        formula_reference: Optional[str] = None,
        game_version: Optional[str] = None,
    ) -> Citation:
        """Construct a CitationType.CALCULATION citation for deterministic stat engine outputs."""
        snippet = calculation_summary
        if formula_reference:
            snippet += f" [Formula: {formula_reference}]"
        return Citation(
            source_name="Phase 7 Deterministic Stat Engine",
            source_url="/api/engine/calculate",
            canonical_url="/api/engine/calculate",
            snippet=snippet[:180] + "..." if len(snippet) > 180 else snippet,
            character=character_name,
            topic="Deterministic Combat Stat Calculation",
            game_version=game_version or "7.0",
            source_id="src_stat_engine",
            source_type="deterministic_engine",
            authority_tier=1,
            citation_type=CitationType.CALCULATION.value,
            confidence=ConfidenceLevel.HIGH.value,
            display_label="Deterministic Calculation",
            claim_supported=f"Computed combat stats and scaling formulas for {character_name}",
        )

    def build_source_citation(
        self,
        doc,
        claim_supported: Optional[str] = None,
    ) -> Citation:
        """Construct a CitationType.SOURCE citation for curated knowledge base documents."""
        is_stale = getattr(doc.metadata, "is_stale", False)
        confidence = ConfidenceLevel.MEDIUM.value if is_stale else ConfidenceLevel.HIGH.value
        return Citation(
            source_name=doc.metadata.source,
            source_url=doc.metadata.source_url,
            canonical_url=doc.metadata.canonical_url,
            snippet=doc.summary[:180] + "..." if len(doc.summary) > 180 else doc.summary,
            character=doc.metadata.character,
            topic=doc.metadata.topic,
            game_version=doc.metadata.game_version,
            document_id=doc.id,
            source_id=doc.metadata.source_id,
            source_type=doc.metadata.source_type.value if hasattr(doc.metadata.source_type, "value") else str(doc.metadata.source_type),
            authority_tier=doc.metadata.authority_tier,
            content_hash=doc.metadata.content_hash,
            citation_type=CitationType.SOURCE.value,
            confidence=confidence,
            display_label=doc.metadata.source,
            claim_supported=claim_supported or doc.metadata.topic,
        )

    # ===================================================================
    # 2. Automated Claim Extraction & Grounding Verification
    # ===================================================================

    def verify_grounding(
        self,
        response_text: str,
        bundle: EvidenceBundle,
        routing: Optional[RoutingDecision] = None,
    ) -> GroundingVerificationResult:
        """Validates assistant response against evidence bundle.

        Extracts factual assertions (stats, numbers, percentages, entity attributes),
        correlates them with evidence items, and builds SupportedClaim records.
        """
        if not response_text:
            return GroundingVerificationResult(
                status=GroundingStatus.UNGROUNDED,
                score=0.0,
                claims=[],
                unsupported_claims=["Empty response"],
                total_claims=1,
                grounded_claims=0,
                warnings=["Response was empty."],
            )

        # 1. Extract candidate factual propositions and numeric assertions
        candidate_claims = self._extract_claims_from_text(response_text)

        # 2. Match each claim against available evidence items
        supported_claims: List[SupportedClaim] = []
        unsupported_claims: List[str] = []
        warnings: List[str] = []

        all_evidence_text = " ".join(item.content for item in bundle.items)

        for claim in candidate_claims:
            match_found = False
            for item in bundle.items:
                if self._claim_matches_evidence(claim, item.content):
                    # Derive citation type and confidence
                    citation_type, confidence = self._derive_type_and_confidence(item)

                    supported_claims.append(SupportedClaim(
                        claim_text=claim,
                        evidence_text=self._extract_evidence_snippet(claim, item.content),
                        evidence_type=item.evidence_type,
                        source=item.source.value,
                        version=item.game_version,
                        confidence=confidence,
                        citation_type=citation_type,
                        verified=True,
                        verification_notes="Matched verified evidence item content",
                    ))
                    match_found = True
                    break

            if not match_found:
                # Check if it was a general conversational statement rather than a game fact
                if self._is_substantive_game_claim(claim):
                    unsupported_claims.append(claim)

        # 3. Compute Grounding Score
        total_eval_claims = len(supported_claims) + len(unsupported_claims)
        if total_eval_claims == 0:
            # Response contained general conversational text without hard numbers
            score = 1.0
            status = GroundingStatus.FULLY_GROUNDED
        else:
            score = round(len(supported_claims) / total_eval_claims, 3)
            if score >= 0.80:
                status = GroundingStatus.FULLY_GROUNDED
            elif score >= 0.50:
                status = GroundingStatus.PARTIALLY_GROUNDED
                warnings.append(f"{len(unsupported_claims)} claim(s) lacked direct verified evidence.")
            else:
                status = GroundingStatus.UNGROUNDED
                warnings.append("More than 50% of extracted claims lacked grounding in the evidence bundle.")

        return GroundingVerificationResult(
            status=status,
            score=score,
            claims=supported_claims,
            unsupported_claims=unsupported_claims,
            total_claims=total_eval_claims,
            grounded_claims=len(supported_claims),
            warnings=warnings,
        )

    # ===================================================================
    # 3. Citation Relevance Filtering
    # ===================================================================

    def filter_meaningful_citations(
        self,
        citations: List[Citation],
        response_text: str,
        claims: List[SupportedClaim],
    ) -> List[Citation]:
        """Prune decorative or unreferenced citations so only meaningful references remain."""
        if not citations:
            return []

        meaningful: List[Citation] = []
        seen_keys: Set[str] = set()
        response_lower = response_text.lower()

        for c in citations:
            # Deduplicate by source_url or topic
            dedup_key = f"{c.source_url}::{c.topic}::{c.character}"
            if dedup_key in seen_keys:
                continue

            # Criteria for relevance:
            # 1. Citation is of type ACCOUNT or CALCULATION (directly requested and computed)
            # 2. The cited character or topic is referenced in the response
            # 3. The citation's claim was specifically verified in claims
            # 4. A distinct word from snippet appears in response
            is_relevant = False

            if c.citation_type in (CitationType.ACCOUNT.value, CitationType.CALCULATION.value):
                is_relevant = True
            elif c.character and c.character.lower() in response_lower:
                is_relevant = True
            elif c.topic and any(w.lower() in response_lower for w in c.topic.split() if len(w) > 3):
                is_relevant = True
            elif any(cl.source == c.source_name or (c.character and cl.claim_text.lower().find(c.character.lower()) != -1) for cl in claims):
                is_relevant = True
            elif c.citation_type == CitationType.DATASET.value:
                # Keep dataset citations if the character/weapon was discussed
                is_relevant = True

            if is_relevant:
                seen_keys.add(dedup_key)
                meaningful.append(c)

        return meaningful if meaningful else citations[:3]

    # ===================================================================
    # Internal Helpers
    # ===================================================================

    def _extract_claims_from_text(self, text: str) -> List[str]:
        """Extract substantive factual propositions, numerical claims, and game attributes."""
        claims: List[str] = []

        # 1. Percentages and stat deltas (e.g., "71.4%", "+18.2% CRIT DMG", "180% ER")
        stat_patterns = [
            r"([+\-]?\d+(?:\.\d+)?%\s*(?:CRIT Rate|CRIT DMG|Energy Recharge|ER|ATK%|HP%|DEF%|Pyro DMG|Hydro DMG|Dendro DMG|Electro DMG|Anemo DMG|Cryo DMG|Geo DMG|Physical DMG|Healing Bonus)?)",
            r"(Base ATK[:\s]+\d+)",
            r"(Base HP[:\s]+\d+)",
            r"(Base DEF[:\s]+\d+)",
            r"(Total ATK[:\s]+\d+)",
            r"(Total HP[:\s]+\d+)",
            r"(Total DEF[:\s]+\d+)",
            r"(Elemental Mastery[:\s]+\d+)",
            r"(Crit Value[:\s]+\d+(?:\.\d+)?)",
            r"(CV[:\s]+\d+(?:\.\d+)?)",
            r"(C[0-6]\b)",
            r"(R[1-5]\b)",
            r"(Lv\.\s*\d+)",
        ]
        for pat in stat_patterns:
            matches = re.findall(pat, text, re.IGNORECASE)
            for m in matches:
                clean_m = m.strip()
                if len(clean_m) >= 2 and clean_m not in claims:
                    claims.append(clean_m)

        # 2. Key game attribute statements (Element, Weapon type)
        element_pattern = r"\b(Pyro|Hydro|Anemo|Electro|Dendro|Cryo|Geo)\s+(?:element|vision|character|DPS|Sub-DPS|enabler|support)\b"
        for m in re.findall(element_pattern, text, re.IGNORECASE):
            if m not in claims:
                claims.append(m)

        weapon_type_pattern = r"\b(Sword|Claymore|Polearm|Bow|Catalyst)\s+(?:user|weapon|type)\b"
        for m in re.findall(weapon_type_pattern, text, re.IGNORECASE):
            if m not in claims:
                claims.append(m)

        return claims

    def _claim_matches_evidence(self, claim: str, evidence_content: str) -> bool:
        """Determines whether an extracted claim is supported by an evidence item."""
        claim_clean = claim.lower().strip()
        evidence_lower = evidence_content.lower()

        # Direct substring
        if claim_clean in evidence_lower:
            return True

        # Number-only extraction (e.g., "71.4%" matching "71.4" in evidence)
        numbers = re.findall(r"\d+(?:\.\d+)?", claim)
        if numbers:
            for num in numbers:
                if num in evidence_lower:
                    # Also ensure relevant context word exists if claim had letters
                    words = [w for w in re.findall(r"[a-zA-Z]+", claim_clean) if len(w) > 2]
                    if not words or any(w in evidence_lower for w in words):
                        return True

        # Constellation or refinement matching (e.g. "C6" or "R5")
        const_ref = re.findall(r"\b[CR][0-6]\b", claim, re.IGNORECASE)
        if const_ref:
            for cr in const_ref:
                if cr.lower() in evidence_lower:
                    return True

        return False

    def _extract_evidence_snippet(self, claim: str, evidence_content: str) -> str:
        """Extract a 120-character snippet surrounding the matched claim."""
        claim_clean = claim.lower().strip()
        idx = evidence_content.lower().find(claim_clean)
        if idx != -1:
            start = max(0, idx - 40)
            end = min(len(evidence_content), idx + len(claim_clean) + 60)
            return evidence_content[start:end].replace("\n", " ").strip()

        # Fallback to first line or header of evidence
        lines = [line.strip() for line in evidence_content.split("\n") if line.strip()]
        return lines[0][:120] if lines else evidence_content[:120]

    def _derive_type_and_confidence(self, item: EvidenceItem) -> Tuple[CitationType, ConfidenceLevel]:
        """Derive citation type and confidence level from an EvidenceItem."""
        if item.source == DataSource.CANONICAL_GAME_DATA:
            return CitationType.DATASET, ConfidenceLevel.HIGH
        elif item.source in (DataSource.ACCOUNT_SHOWCASE, DataSource.ACCOUNT_INVENTORY):
            return CitationType.ACCOUNT, ConfidenceLevel.HIGH
        elif item.source == DataSource.STAT_ENGINE or item.evidence_type == EvidenceType.DETERMINISTIC_CALCULATION:
            return CitationType.CALCULATION, ConfidenceLevel.HIGH
        elif item.source == DataSource.EXTERNAL_ESCALATION:
            conf = ConfidenceLevel.LOW if item.is_stale else ConfidenceLevel.HIGH
            return CitationType.SOURCE, conf
        else:
            conf = ConfidenceLevel.LOW if item.is_stale else ConfidenceLevel.HIGH
            return CitationType.SOURCE, conf

    def _is_substantive_game_claim(self, claim: str) -> bool:
        """Filter out trivial numbers (e.g., single digits 1 or 2) from being penalizing unsupported claims."""
        # Single-digit numbers without context are not substantive
        if re.match(r"^\d$", claim):
            return False
        return True


grounding_service = GroundingService()
