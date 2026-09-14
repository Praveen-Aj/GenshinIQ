"""Phase 8: Orchestrates query routing, evidence gathering, and grounded response generation.

Replaces the previous binary (account/general) RAG pipeline with a
multi-intent router that selects the appropriate data sources, runs
deterministic calculations where needed, enforces fail-closed behavior
for missing evidence, and produces transparent, grounded responses.
"""

import difflib
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from backend.models.chat import ChatMessage, ChatResponse, Citation
from backend.models.query_router import (
    DataSource,
    DetectedEntity,
    EvidenceBundle,
    EvidenceItem,
    EvidenceType,
    QueryIntent,
    RoutingDecision,
)
from backend.services.gemini_service import gemini_service
from backend.services.knowledge_service import knowledge_service
from backend.services.game_data_service import game_data_service
from backend.services.account_service import account_service
from backend.services.version_service import version_service
from backend.services.query_router import query_router
from backend.services.knowledge_escalation_service import knowledge_escalation_service
from backend.models.knowledge_escalation import FreshnessLevel
from backend.services.grounding_service import grounding_service
from backend.models.grounding import CitationType

logger = logging.getLogger(__name__)


class RAGService:
    """Orchestrates structured data retrieval, deterministic calculations,
    local document search, and Gemini response generation via multi-intent routing."""

    def __init__(self):
        pass

    # ===================================================================
    # Legacy helpers (preserved for backward compat during transition)
    # ===================================================================

    def _classify_query(self, query: str, uid: Optional[str] = None) -> str:
        """Legacy binary classifier. Now delegates to query_router for actual routing."""
        decision = query_router.classify(query, uid=uid)
        if decision.requires_account_data:
            return "account"
        return "general"

    def _detect_character(self, query: str) -> Optional[str]:
        """Detect character name in query. Delegates to query_router."""
        return query_router._detect_character(query)

    def _get_latest_game_version(self) -> str:
        """Return the canonical current live game version."""
        return version_service.get_current_version().version

    # ===================================================================
    # Evidence Gathering
    # ===================================================================

    def _gather_canonical_data(
        self,
        entities: List[DetectedEntity],
    ) -> Tuple[List[EvidenceItem], List[Citation]]:
        """Gather canonical game data evidence for detected entities."""
        items: List[EvidenceItem] = []
        citations: List[Citation] = []

        for entity in entities:
            if entity.entity_type == "character":
                canonical_char = game_data_service.get_character(entity.name)
                if canonical_char:
                    talents_text = "\n".join([
                        f"- {t.name} ({t.type}): {t.description}"
                        for t in (canonical_char.talents or [])
                    ]) if canonical_char.talents else "Standard kit"
                    region_val = getattr(canonical_char, 'region', None) or 'Teyvat'
                    affil_val = getattr(canonical_char, 'affiliation', None) or region_val
                    intro_ver = getattr(canonical_char, 'game_version_introduced', None) or '1.0'

                    content = (
                        f"=== CANONICAL GAME DATABASE: {canonical_char.name.upper()} (Introduced: v{intro_ver}) ===\n"
                        f"Rarity: {canonical_char.rarity} Star | Element: {canonical_char.element} | Weapon: {canonical_char.weapon_type}\n"
                        f"Region: {region_val} | Affiliation: {affil_val}\n"
                        f"Base HP (Lv 90): {canonical_char.base_hp_lvl90} | Base ATK: {canonical_char.base_atk_lvl90} | Base DEF: {canonical_char.base_def_lvl90}\n"
                        f"Ascension Stat: {canonical_char.ascension_stat} ({canonical_char.ascension_stat_val_lvl90})\n"
                        f"Talents:\n{talents_text}\n"
                        f"=================================================="
                    )
                    items.append(EvidenceItem(
                        source=DataSource.CANONICAL_GAME_DATA,
                        evidence_type=EvidenceType.CANONICAL_GAME_FACT,
                        content=content,
                        entity_name=canonical_char.name,
                        game_version=intro_ver,
                    ))
                    citations.append(grounding_service.build_dataset_citation(
                        entity_name=canonical_char.name,
                        entity_type="character",
                        attributes_summary=f"{canonical_char.rarity}★ {canonical_char.element} {canonical_char.weapon_type} | Base ATK Lv90: {canonical_char.base_atk_lvl90}",
                        game_version=intro_ver,
                    ))

                    # Character Knowledge Package
                    try:
                        from backend.services.character_knowledge_service import character_knowledge_service
                        pkg = character_knowledge_service.get_character_package(entity.name)
                        if pkg:
                            pkg_content = (
                                f"=== RELEASE & APPLICABILITY: {canonical_char.name.upper()} ===\n"
                                f"Release Status: {pkg.release_status.value} ({pkg.applicability_reason})\n"
                                f"Canonical Data Available: {pkg.has_canonical_data}\n"
                                f"Verified Mechanics Available: {pkg.has_verified_mechanics}\n"
                                f"Expert KQM/TCL Guide Available: {pkg.has_expert_guide}\n"
                                f"Quality State: {pkg.quality_state.value}\n"
                                f"=================================================="
                            )
                            current_ver_val = version_service.get_current_version().version
                            items.append(EvidenceItem(
                                source=DataSource.CANONICAL_GAME_DATA,
                                evidence_type=EvidenceType.CANONICAL_GAME_FACT,
                                content=pkg_content,
                                entity_name=canonical_char.name,
                                game_version=current_ver_val,
                            ))
                            if pkg.derived_calculations:
                                calc_strs = [f"- {c.name}: {c.output} (Formula: {c.formula})" for c in pkg.derived_calculations]
                                items.append(EvidenceItem(
                                    source=DataSource.STAT_ENGINE,
                                    evidence_type=EvidenceType.DETERMINISTIC_CALCULATION,
                                    content=(
                                        f"=== DETERMINISTIC DERIVED STATS: {canonical_char.name.upper()} ===\n"
                                        + "\n".join(calc_strs) + "\n"
                                        + "=================================================="
                                    ),
                                    entity_name=canonical_char.name,
                                ))
                                citations.append(grounding_service.build_calculation_citation(
                                    character_name=canonical_char.name,
                                    calculation_summary=f"Derived stats for {canonical_char.name}: {', '.join(calc_strs[:2])}",
                                    formula_reference="Canonical Stat Engine Scaling",
                                    game_version=current_ver_val,
                                ))
                            if pkg.knowledge_gaps:
                                gap_strs = [f"- {g}: Registered KNOWLEDGE_GAP (Awaiting expert guide)" for g in pkg.knowledge_gaps]
                                items.append(EvidenceItem(
                                    source=DataSource.KNOWLEDGE_BASE,
                                    evidence_type=EvidenceType.THEORYCRAFTING,
                                    content=(
                                        f"=== CATALOGED THEORYCRAFTING GAPS: {canonical_char.name.upper()} ===\n"
                                        + "\n".join(gap_strs) + "\n"
                                        + "NOTE: Provide verified stats and talents. For missing items above, state clearly they are awaiting expert publication without fabricating text.\n"
                                        + "=================================================="
                                    ),
                                    entity_name=canonical_char.name,
                                ))
                    except Exception as e:
                        logger.warning(f"Could not load knowledge package for {entity.name}: {e}")

            elif entity.entity_type == "weapon":
                weapon = game_data_service.get_weapon(entity.name)
                if weapon:
                    sub_stat_str = f"Secondary Stat: {weapon.sub_stat_type or 'None'} ({weapon.sub_stat_val_lvl90 or 'N/A'})\n"
                    content = (
                        f"=== CANONICAL WEAPON: {weapon.name.upper()} ===\n"
                        f"Type: {weapon.weapon_type} | Rarity: {weapon.rarity}★\n"
                        f"Base ATK (Lv 90): {weapon.base_atk_lvl90}\n"
                        f"{sub_stat_str}"
                        f"Passive: {weapon.passive_name}: {weapon.passive_desc}\n"
                        f"=================================================="
                    )
                    items.append(EvidenceItem(
                        source=DataSource.CANONICAL_GAME_DATA,
                        evidence_type=EvidenceType.CANONICAL_GAME_FACT,
                        content=content,
                        entity_name=weapon.name,
                    ))
                    citations.append(grounding_service.build_dataset_citation(
                        entity_name=weapon.name,
                        entity_type="weapon",
                        attributes_summary=f"{weapon.rarity}★ {weapon.weapon_type}, Base ATK {weapon.base_atk_lvl90}, {weapon.sub_stat_type or ''} {weapon.sub_stat_val_lvl90 or ''}".strip(),
                    ))

            elif entity.entity_type == "artifact_set":
                artifact = game_data_service.get_artifact_set(entity.name)
                if artifact:
                    content = (
                        f"=== CANONICAL ARTIFACT SET: {artifact.name.upper()} ===\n"
                        f"2pc: {artifact.two_piece_bonus}\n"
                        f"4pc: {artifact.four_piece_bonus}\n"
                        f"=================================================="
                    )
                    items.append(EvidenceItem(
                        source=DataSource.CANONICAL_GAME_DATA,
                        evidence_type=EvidenceType.CANONICAL_GAME_FACT,
                        content=content,
                        entity_name=artifact.name,
                    ))
                    citations.append(grounding_service.build_dataset_citation(
                        entity_name=artifact.name,
                        entity_type="artifact_set",
                        attributes_summary=f"2pc: {artifact.two_piece_bonus}",
                    ))

        return items, citations

    def _gather_knowledge(
        self,
        query: str,
        entities: List[DetectedEntity],
        existing_citation_urls: set,
    ) -> Tuple[List[EvidenceItem], List[Citation]]:
        """Search knowledge base for relevant documents."""
        items: List[EvidenceItem] = []
        citations: List[Citation] = []

        # 1. Direct character guide lookup
        for entity in entities:
            if entity.entity_type == "character":
                char_docs = knowledge_service.list_documents(character=entity.name)
                for doc in char_docs:
                    eval_res = version_service.evaluate_staleness(doc.metadata.game_version)
                    stale_note = f"\n[VERSION WARNING: {eval_res.warning}]" if eval_res.is_stale else ""
                    items.append(EvidenceItem(
                        source=DataSource.KNOWLEDGE_BASE,
                        evidence_type=EvidenceType.THEORYCRAFTING,
                        content=(
                            f"=== KNOWLEDGE SOURCE: {doc.title} (v{doc.metadata.game_version}, {doc.metadata.source}){stale_note} ===\n"
                            f"URL: {doc.metadata.source_url}\n"
                            f"Content:\n{doc.content}\n"
                            f"=================================================="
                        ),
                        entity_name=entity.name,
                        is_stale=eval_res.is_stale,
                        staleness_note=eval_res.warning if eval_res.is_stale else "",
                        game_version=doc.metadata.game_version,
                    ))
                    if doc.metadata.source_url not in existing_citation_urls:
                        existing_citation_urls.add(doc.metadata.source_url)
                        citations.append(self._doc_to_citation(doc))

        # 2. Search additional knowledge base articles
        search_query = query
        char_entities = [e for e in entities if e.entity_type == "character"]
        if char_entities and char_entities[0].name.lower() not in query.lower():
            search_query = f"{query} {char_entities[0].name}"

        search_results = knowledge_service.search_documents(search_query, limit=3)
        for res in search_results:
            doc = knowledge_service.get_document(res.id)
            if not doc:
                continue
            if doc.metadata.source_url in existing_citation_urls:
                continue
            eval_res = version_service.evaluate_staleness(doc.metadata.game_version)
            stale_note = f"\n[VERSION WARNING: {eval_res.warning}]" if eval_res.is_stale else ""
            items.append(EvidenceItem(
                source=DataSource.KNOWLEDGE_BASE,
                evidence_type=EvidenceType.THEORYCRAFTING,
                content=(
                    f"=== KNOWLEDGE SOURCE: {doc.title} (v{doc.metadata.game_version}, {doc.metadata.source}){stale_note} ===\n"
                    f"URL: {doc.metadata.source_url}\n"
                    f"Content:\n{doc.content}\n"
                    f"=================================================="
                ),
                entity_name=doc.metadata.character,
                is_stale=eval_res.is_stale,
                staleness_note=eval_res.warning if eval_res.is_stale else "",
                game_version=doc.metadata.game_version,
            ))
            existing_citation_urls.add(doc.metadata.source_url)
            citations.append(self._doc_to_citation(doc))

        return items, citations

    async def _gather_account_data(
        self,
        uid: str,
        entities: List[DetectedEntity],
        routing: RoutingDecision,
    ) -> Tuple[List[EvidenceItem], List[Citation], Optional[str]]:
        """Gather account data from Enka showcase and/or GOOD inventory."""
        items: List[EvidenceItem] = []
        citations: List[Citation] = []
        account_summary = None

        char_entities = [e for e in entities if e.entity_type == "character"]
        char_name = char_entities[0].name if char_entities else None

        try:
            showcase = await account_service.get_showcase(uid=uid)

            if char_name:
                char_build = next(
                    (c for c in showcase.characters if c.name.lower() == char_name.lower()),
                    None
                )
                if char_build:
                    account_summary = self._format_showcase_character(char_build)
                    items.append(EvidenceItem(
                        source=DataSource.ACCOUNT_SHOWCASE,
                        evidence_type=EvidenceType.ACCOUNT_FACT,
                        content=account_summary,
                        entity_name=char_name,
                    ))
                    citations.append(grounding_service.build_account_citation(
                        uid=uid,
                        character_name=char_name,
                        build_summary=f"{char_build.name} Lv.{char_build.level} C{char_build.constellation}",
                    ))
                else:
                    items.append(EvidenceItem(
                        source=DataSource.ACCOUNT_SHOWCASE,
                        evidence_type=EvidenceType.ACCOUNT_FACT,
                        content=(
                            f"=== SYSTEM NOTICE ===\n"
                            f"User has requested information on their '{char_name}', but it was not "
                            f"found in their showcase. Their active showcase characters are: "
                            f"{', '.join([c.name for c in showcase.characters])}.\n"
                            f"====================="
                        ),
                        entity_name=char_name,
                    ))
            else:
                chars_summary = ", ".join([f"{c.name} (Lv. {c.level} C{c.constellation})" for c in showcase.characters])
                items.append(EvidenceItem(
                    source=DataSource.ACCOUNT_SHOWCASE,
                    evidence_type=EvidenceType.ACCOUNT_FACT,
                    content=(
                        f"=== USER'S SHOWCASE OVERVIEW ===\n"
                        f"Nickname: {showcase.profile.nickname}\n"
                        f"Adventure Rank: {showcase.profile.level}\n"
                        f"World Level: {showcase.profile.world_level}\n"
                        f"Showcase Characters: {chars_summary}\n"
                        f"================================"
                    ),
                ))
                citations.append(grounding_service.build_account_citation(
                    uid=uid,
                    character_name=None,
                    build_summary=f"Overview for {showcase.profile.nickname} (AR {showcase.profile.level})",
                ))

        except Exception as e:
            logger.error(f"Failed to load user showcase for RAG: {e}")
            items.append(EvidenceItem(
                source=DataSource.ACCOUNT_SHOWCASE,
                evidence_type=EvidenceType.ACCOUNT_FACT,
                content=(
                    f"=== SYSTEM ERROR ===\n"
                    f"Failed to fetch user showcase data for UID {uid}.\n"
                    f"===================="
                ),
            ))

        # GOOD inventory stat engine integration
        if routing.requires_stat_engine and char_name:
            try:
                from backend.services.stat_engine import stat_engine_service
                build_snapshot = stat_engine_service.get_account_character_build(
                    char_name, game_version=self._get_latest_game_version()
                )
                if build_snapshot:
                    calc = build_snapshot.calculated_stats
                    breakdown_parts = []
                    if calc:
                        breakdown_parts.append(
                            f"=== DETERMINISTIC STAT ENGINE RESULTS: {char_name.upper()} ===\n"
                            f"Calculation Status: {build_snapshot.status.value}\n"
                            f"Character: {build_snapshot.character_name} Lv.{build_snapshot.level}\n"
                            f"Weapon: {build_snapshot.weapon_name or 'None'} Lv.{build_snapshot.weapon_level}\n"
                            f"Constellation: C{build_snapshot.constellation}\n"
                            f"\n--- Computed Combat Stats (Deterministic) ---\n"
                            f"Total ATK: {round(calc.total_atk)}\n"
                            f"Total HP: {round(calc.total_hp)}\n"
                            f"Total DEF: {round(calc.total_def)}\n"
                            f"CRIT Rate: {round(calc.crit_rate * 100, 1)}%\n"
                            f"CRIT DMG: {round(calc.crit_dmg * 100, 1)}%\n"
                            f"Energy Recharge: {round(calc.energy_recharge * 100, 1)}%\n"
                            f"Elemental Mastery: {round(calc.elemental_mastery)}\n"
                            f"Crit Value (CV): {round(calc.crit_value, 1)}\n"
                        )
                        if calc.damage_bonuses:
                            for elem, val in calc.damage_bonuses.items():
                                if val > 0.001:
                                    breakdown_parts.append(f"{elem} DMG Bonus: {round(val * 100, 1)}%\n")

                        breakdown_parts.append(
                            f"\n--- Source: Phase 7 Deterministic Stat Engine ---\n"
                            f"These values are calculated using canonical game scaling tables,\n"
                            f"NOT from Gemini reasoning. Do NOT recalculate these values.\n"
                            f"=================================================="
                        )

                    items.append(EvidenceItem(
                        source=DataSource.STAT_ENGINE,
                        evidence_type=EvidenceType.DETERMINISTIC_CALCULATION,
                        content="".join(breakdown_parts),
                        entity_name=char_name,
                    ))
                    if calc:
                        citations.append(grounding_service.build_calculation_citation(
                            character_name=char_name,
                            calculation_summary=f"Computed combat stats for {char_name}: ATK {round(calc.total_atk)}, CR {round(calc.crit_rate * 100, 1)}%, CD {round(calc.crit_dmg * 100, 1)}%, CV {round(calc.crit_value, 1)}",
                            formula_reference="Additive Combat Stat Scaling",
                        ))

                    if build_snapshot.warnings:
                        items.append(EvidenceItem(
                            source=DataSource.STAT_ENGINE,
                            evidence_type=EvidenceType.DETERMINISTIC_CALCULATION,
                            content=(
                                f"=== STAT ENGINE WARNINGS ===\n"
                                + "\n".join(f"- {w}" for w in build_snapshot.warnings) + "\n"
                                + "=================================================="
                            ),
                            entity_name=char_name,
                        ))
            except Exception as e:
                logger.warning(f"Stat engine calculation failed for {char_name}: {e}")

        return items, citations, account_summary

    def _gather_version_context(self) -> List[EvidenceItem]:
        """Gather current version context."""
        items: List[EvidenceItem] = []
        try:
            current_ver = version_service.get_current_version()
            items.append(EvidenceItem(
                source=DataSource.VERSION_SERVICE,
                evidence_type=EvidenceType.VERSION_CONTEXT,
                content=(
                    f"=== CURRENT GAME VERSION ===\n"
                    f"Version: {current_ver.version} ('{current_ver.name}')\n"
                    f"Region: {current_ver.major_region}\n"
                    f"Verification: {current_ver.verification_status}\n"
                    f"=================================================="
                ),
                game_version=current_ver.version,
            ))
        except Exception as e:
            logger.warning(f"Failed to gather version context: {e}")
        return items

    def _gather_farming_data(
        self,
        entities: List[DetectedEntity],
    ) -> List[EvidenceItem]:
        """Gather farming/material data for detected characters."""
        items: List[EvidenceItem] = []

        for entity in entities:
            if entity.entity_type == "character":
                canonical_char = game_data_service.get_character(entity.name)
                if canonical_char and hasattr(canonical_char, 'ascension_materials') and canonical_char.ascension_materials:
                    mats_text = "\n".join([f"- {m}" for m in canonical_char.ascension_materials])
                    items.append(EvidenceItem(
                        source=DataSource.CANONICAL_GAME_DATA,
                        evidence_type=EvidenceType.CANONICAL_GAME_FACT,
                        content=(
                            f"=== ASCENSION MATERIALS: {entity.name.upper()} ===\n"
                            f"{mats_text}\n"
                            f"=================================================="
                        ),
                        entity_name=entity.name,
                    ))

                if canonical_char and hasattr(canonical_char, 'talent_materials') and canonical_char.talent_materials:
                    tmats_text = "\n".join([f"- {m}" for m in canonical_char.talent_materials])
                    items.append(EvidenceItem(
                        source=DataSource.CANONICAL_GAME_DATA,
                        evidence_type=EvidenceType.CANONICAL_GAME_FACT,
                        content=(
                            f"=== TALENT MATERIALS: {entity.name.upper()} ===\n"
                            f"{tmats_text}\n"
                            f"=================================================="
                        ),
                        entity_name=entity.name,
                    ))

        return items

    # ===================================================================
    # Evidence Assembly & Sufficiency Check
    # ===================================================================

    async def _assemble_evidence(
        self,
        query: str,
        routing: RoutingDecision,
        uid: Optional[str] = None,
    ) -> Tuple[EvidenceBundle, List[Citation]]:
        """Assemble evidence from all required and optional sources."""
        all_items: List[EvidenceItem] = []
        all_citations: List[Citation] = []
        sources_consulted: List[DataSource] = []
        sources_unavailable: List[DataSource] = []
        citation_urls: set = set()
        account_summary = None

        # 1. Canonical game data
        if DataSource.CANONICAL_GAME_DATA in routing.required_sources or \
           DataSource.CANONICAL_GAME_DATA in routing.optional_sources:
            canon_items, canon_cites = self._gather_canonical_data(routing.detected_entities)
            all_items.extend(canon_items)
            all_citations.extend(canon_cites)
            sources_consulted.append(DataSource.CANONICAL_GAME_DATA)

        # 2. Knowledge base
        if DataSource.KNOWLEDGE_BASE in routing.required_sources or \
           DataSource.KNOWLEDGE_BASE in routing.optional_sources:
            for c in all_citations:
                if c.source_url:
                    citation_urls.add(c.source_url)
            kb_items, kb_cites = self._gather_knowledge(query, routing.detected_entities, citation_urls)
            all_items.extend(kb_items)
            all_citations.extend(kb_cites)
            sources_consulted.append(DataSource.KNOWLEDGE_BASE)

        # 3. Account data
        if uid and (DataSource.ACCOUNT_SHOWCASE in routing.required_sources or
                    DataSource.ACCOUNT_SHOWCASE in routing.optional_sources or
                    DataSource.ACCOUNT_INVENTORY in routing.required_sources or
                    DataSource.ACCOUNT_INVENTORY in routing.optional_sources):
            acct_items, acct_cites, acct_summary = await self._gather_account_data(uid, routing.detected_entities, routing)
            all_items.extend(acct_items)
            all_citations.extend(acct_cites)
            sources_consulted.append(DataSource.ACCOUNT_SHOWCASE)
            if routing.requires_stat_engine:
                sources_consulted.append(DataSource.STAT_ENGINE)
            account_summary = acct_summary
        elif DataSource.ACCOUNT_SHOWCASE in routing.required_sources:
            sources_unavailable.append(DataSource.ACCOUNT_SHOWCASE)
        elif DataSource.ACCOUNT_INVENTORY in routing.required_sources:
            sources_unavailable.append(DataSource.ACCOUNT_INVENTORY)

        # 4. Version context
        if DataSource.VERSION_SERVICE in routing.required_sources or \
           DataSource.VERSION_SERVICE in routing.optional_sources:
            ver_items = self._gather_version_context()
            all_items.extend(ver_items)
            sources_consulted.append(DataSource.VERSION_SERVICE)

        # 5. Farming-specific data
        if routing.primary_intent == QueryIntent.FARMING or \
           QueryIntent.FARMING in routing.secondary_intents:
            farm_items = self._gather_farming_data(routing.detected_entities)
            all_items.extend(farm_items)

        # 6. Stat engine (standalone, without account)
        if routing.requires_stat_engine and DataSource.STAT_ENGINE not in sources_consulted:
            # Run stat engine for weapon comparison or general stat calculations
            self._run_standalone_stat_engine(routing, all_items, all_citations)
            sources_consulted.append(DataSource.STAT_ENGINE)

        # 7. Phase 9: Quality & Freshness Check -> Knowledge Escalation
        temp_bundle = EvidenceBundle(
            items=all_items,
            sources_consulted=list(set(sources_consulted)),
            sources_unavailable=sources_unavailable,
            is_sufficient=True,
        )
        escalation_decision = knowledge_escalation_service.evaluate_escalation(
            query, routing, temp_bundle, routing.detected_entities
        )

        is_sufficient = True
        insufficiency_reason = ""

        if escalation_decision.should_escalate:
            logger.info(f"Phase 9 Escalation triggered: {escalation_decision.trigger.value} | {escalation_decision.reason}")
            escalation_result = await knowledge_escalation_service.escalate(query, escalation_decision)

            if escalation_result.success and escalation_result.items:
                sources_consulted.append(DataSource.EXTERNAL_ESCALATION)
                for esc_item in escalation_result.items:
                    all_items.append(EvidenceItem(
                        source=DataSource.EXTERNAL_ESCALATION,
                        evidence_type=EvidenceType.EXTERNAL_EVIDENCE,
                        content=(
                            f"=== EXTERNAL ESCALATION EVIDENCE: {esc_item.source_name.upper()} ===\n"
                            f"Source URL: {esc_item.source_url} | Tier: {int(esc_item.source_tier)} ({esc_item.source_type})\n"
                            f"Game Version: {esc_item.game_version or 'N/A'} | Freshness: {esc_item.freshness.value}\n"
                            f"Retrieved At: {esc_item.retrieved_at}\n"
                            f"Validation Notes: {esc_item.validation_notes}\n\n"
                            f"{esc_item.content}\n"
                            f"=================================================="
                        ),
                        entity_name=routing.detected_entities[0].name if routing.detected_entities else None,
                        is_stale=(esc_item.freshness == FreshnessLevel.STALE),
                        staleness_note=esc_item.validation_notes,
                        game_version=esc_item.game_version,
                    ))
                    all_citations.append(Citation(
                        source_name=esc_item.source_name,
                        source_url=esc_item.source_url,
                        snippet=esc_item.content[:160] + "..." if len(esc_item.content) > 160 else esc_item.content,
                        character=routing.detected_entities[0].name if routing.detected_entities else None,
                        topic="External Escalated Evidence",
                        game_version=esc_item.game_version,
                        source_type=esc_item.source_type.value if hasattr(esc_item.source_type, 'value') else str(esc_item.source_type),
                        authority_tier=int(esc_item.source_tier),
                    ))
            elif not escalation_result.success:
                # Escalation failed for a query requiring external/fresh verification -> Fail Closed
                logger.warning(f"Phase 9 Escalation failed: {escalation_result.failure_reason}")
                sources_unavailable.append(DataSource.EXTERNAL_ESCALATION)
                is_sufficient = False
                insufficiency_reason = escalation_result.failure_reason or (
                    "I couldn't verify sufficiently current information for this question."
                )

        # Check required local sources
        if sources_unavailable:
            required_missing = [s for s in sources_unavailable if s in routing.required_sources or s == DataSource.EXTERNAL_ESCALATION]
            if required_missing:
                is_sufficient = False
                if not insufficiency_reason:
                    insufficiency_reason = (
                        f"Required data sources unavailable: {', '.join(s.value for s in required_missing)}. "
                        f"Cannot provide a grounded answer without these sources."
                    )

        bundle = EvidenceBundle(
            items=all_items,
            sources_consulted=list(set(sources_consulted)),
            sources_unavailable=sources_unavailable,
            is_sufficient=is_sufficient,
            insufficiency_reason=insufficiency_reason,
        )

        return bundle, all_citations

    def _run_standalone_stat_engine(
        self,
        routing: RoutingDecision,
        items: List[EvidenceItem],
        citations: Optional[List[Citation]] = None,
    ) -> None:
        """Run stat engine for weapon comparisons or standalone calculations."""
        if routing.primary_intent == QueryIntent.WEAPON_COMPARISON:
            weapon_entities = [e for e in routing.detected_entities if e.entity_type == "weapon"]
            char_entities = [e for e in routing.detected_entities if e.entity_type == "character"]
            char_name = char_entities[0].name if char_entities else None

            if len(weapon_entities) >= 2 and char_name:
                try:
                    from backend.services.stat_engine import stat_engine_service
                    results = []
                    for weapon_entity in weapon_entities[:2]:
                        snapshot = stat_engine_service.calculate_build_stats(
                            character_name_or_id=char_name,
                            weapon_name_or_id=weapon_entity.name,
                            game_version=self._get_latest_game_version(),
                        )
                        if snapshot and snapshot.calculated_stats:
                            calc = snapshot.calculated_stats
                            results.append(
                                f"--- {weapon_entity.name} on {char_name} ---\n"
                                f"Total ATK: {round(calc.total_atk)} | "
                                f"CRIT Rate: {round(calc.crit_rate * 100, 1)}% | "
                                f"CRIT DMG: {round(calc.crit_dmg * 100, 1)}% | "
                                f"ER: {round(calc.energy_recharge * 100, 1)}% | "
                                f"EM: {round(calc.elemental_mastery)}"
                            )

                    if results:
                        items.append(EvidenceItem(
                            source=DataSource.STAT_ENGINE,
                            evidence_type=EvidenceType.DETERMINISTIC_CALCULATION,
                            content=(
                                f"=== WEAPON COMPARISON (Deterministic) ===\n"
                                + "\n".join(results) + "\n"
                                + "Source: Phase 7 Stat Engine. Do NOT recalculate these values.\n"
                                + "=================================================="
                            ),
                            entity_name=char_name,
                        ))
                        if citations is not None:
                            citations.append(grounding_service.build_calculation_citation(
                                character_name=char_name,
                                calculation_summary=f"Weapon comparison for {char_name} ({', '.join(w.name for w in weapon_entities[:2])})",
                                formula_reference="Deterministic Stat Engine Weapon Delta",
                            ))
                except Exception as e:
                    logger.warning(f"Stat engine weapon comparison failed: {e}")

    # ===================================================================
    # Formatting Helpers
    # ===================================================================

    def _format_showcase_character(self, char_build) -> str:
        """Helper to format a player's character build stats for prompt context."""
        stats = char_build.stats.model_dump() if char_build.stats else {}

        # Format artifacts
        artifacts_formatted = []
        for art in char_build.artifacts or []:
            substats_str = ", ".join([f"{sub.name}: +{sub.formatted}" for sub in art.substats])
            artifacts_formatted.append(
                f"- {art.slot.upper()} ({art.set_name}): +{art.level} "
                f"| Main: {art.main_stat.name} (+{art.main_stat.formatted}) "
                f"| Substats: [{substats_str}]"
            )
        artifacts_list = "\n".join(artifacts_formatted) if artifacts_formatted else "None"

        # Format stats list
        dmg_bonuses_str = ""
        if stats.get("damage_bonuses"):
            dmg_bonuses_str = "\n".join([
                f"- {elem} DMG Bonus: {round(val * 100, 1)}%"
                for elem, val in stats["damage_bonuses"].items() if val > 0.01
            ])

        weapon_str = "None"
        if char_build.weapon:
            w = char_build.weapon
            weapon_str = f"{w.name} (Lv. {w.level}/90, R{w.refinement})"

        talents_str = "None"
        if char_build.talents:
            talents_str = ", ".join([
                f"Talent {i+1}: Lv. {t.boosted_level}"
                for i, t in enumerate(char_build.talents)
            ])

        return f"""=== USER'S OWN {char_build.name.upper()} BUILD DETAILS ===
Character: {char_build.name}
Level: {char_build.level}/90
Constellation: C{char_build.constellation}
Friendship: Lv. {char_build.fetter_level}

Weapon Equipped: {weapon_str}
Talents: {talents_str}

Character Combat Stats:
- Max HP: {round(stats.get('max_hp', 0))}
- ATK: {round(stats.get('atk', 0))}
- DEF: {round(stats.get('defense', 0))}
- Elemental Mastery: {round(stats.get('elemental_mastery', 0))}
- CRIT Rate: {round(stats.get('crit_rate', 0.05) * 100, 1)}%
- CRIT DMG: {round(stats.get('crit_dmg', 0.5) * 100, 1)}%
- Energy Recharge: {round(stats.get('energy_recharge', 1.0) * 100, 1)}%
{dmg_bonuses_str}

Artifact Pieces Equipped:
{artifacts_list}
=================================================="""

    def _doc_to_citation(self, doc) -> Citation:
        """Convert a KnowledgeDocument to a Citation."""
        return grounding_service.build_source_citation(doc)

    def _build_fallback_response(
        self,
        intent: str,
        query: str,
        citations: List[Citation],
        account_summary: Optional[str] = None,
    ) -> str:
        """Create a grounded fallback when Gemini is temporarily unavailable."""
        if account_summary:
            return (
                "Gemini is temporarily busy, so I'm using the grounded account context I already fetched.\n\n"
                f"{account_summary}\n\n"
                "If you want, I can retry the full review once the model is available again."
            )

        if citations:
            cited_sources = "\n".join(
                f"- {c.topic or 'Reference'}: {c.source_name} (v{c.game_version})"
                for c in citations[:3]
            )
            return (
                "Gemini is temporarily busy, but I did find local references for your question.\n\n"
                f"Here are the strongest sources I found for \u201c{query}\u201d:\n"
                f"{cited_sources}\n\n"
                "Try again in a moment and I'll generate the full answer."
            )

        if intent == "account":
            return (
                "Gemini is temporarily busy, and I couldn't assemble enough account context to give a confident build review.\n\n"
                "Please try again in a moment, or refresh your showcase and resend the question."
            )

        return (
            "Gemini is temporarily busy right now.\n\n"
            "I couldn't generate a grounded answer yet, but the app is still working and you can try the question again shortly."
        )

    def _build_insufficient_evidence_response(
        self,
        routing: RoutingDecision,
        bundle: EvidenceBundle,
    ) -> str:
        """Build a fail-closed response when required evidence is unavailable."""
        if bundle.insufficiency_reason and "I couldn't verify sufficiently current" in bundle.insufficiency_reason:
            return (
                f"{bundle.insufficiency_reason}\n\n"
                f"**Routing Decision**: {routing.reasoning}\n\n"
                "This is a safety measure to prevent hallucinated, outdated, or ungrounded answers. "
                "The local database lacks sufficiently fresh evidence for this request and approved external sources "
                "could not verify current-version data."
            )

        missing_str = f"**Missing Sources**: {', '.join(s.value for s in bundle.sources_unavailable)}\n\n" if bundle.sources_unavailable else ""
        reason_str = f"**Reason**: {bundle.insufficiency_reason}\n\n" if bundle.insufficiency_reason else ""

        return (
            "I cannot provide a reliable answer to this question because required data sources "
            "are currently unavailable or current-version information could not be verified.\n\n"
            f"{missing_str}"
            f"{reason_str}"
            f"**Routing Decision**: {routing.reasoning}\n\n"
            "This is a safety measure to prevent hallucinated or ungrounded answers. "
            "Please ensure your account data is loaded (if this is an account question) "
            "or try a different question."
        )

    # ===================================================================
    # System Instruction Construction
    # ===================================================================

    def _build_system_instruction(self, routing: RoutingDecision) -> str:
        """Build Gemini system instruction tailored to the routing decision."""
        current_date_str = datetime.now().strftime("%B %Y")
        current_ver = version_service.get_current_version()

        base_instruction = (
            "You are GenshinIQ, a personal Genshin Impact AI assistant. Your goal is to provide highly accurate, "
            "grounded character build reviews and game theorycrafting advice. You must adhere to the following rules:\n"
            f"0. CRITICAL CONTEXT: The current date is {current_date_str}. The current active version is Version {current_ver.version} ('{current_ver.name}', {current_ver.major_region}). "
            "Character release status is strictly governed by the canonical release status provided in the context blocks. "
            "Characters marked UNRELEASED_PREVIEW or UPCOMING_CONFIRMED have canonical client attributes (Element, Weapon, Stats, Talents), "
            "but live gameplay guides and rotations are NOT APPLICABLE.\n"
            "1. FACTUAL KIT & STAT QUESTIONS: For questions such as 'What is this character's Element?', 'What does this talent do?', 'What are their base stats?', "
            "ALWAYS answer definitively using the verified canonical game data in the context. NEVER state 'I don't have enough information about this character' for factual attributes present in canonical data.\n"
            "2. RELEASED CHARACTERS LACKING EXPERT GUIDES: If a released character lacks a peer-reviewed KQM guide, "
            "answer factual questions from canonical data. For optimal rotations, team DPS, or ER thresholds, explicitly qualify that specific limitation.\n"
            "3. UNRELEASED CHARACTERS: Answer factual questions about element, weapon, and base stats from canonical client data, while stating that live build guides and rotations are NOT_APPLICABLE until official release.\n"
            "4. NO BLIND FAILURE: Do NOT default to 'I don't have enough information'. Retrieve and present all verified canonical game data, account stats, and mechanical rules available. "
            "If a specific expert calculation is not published, answer using verified facts and explicitly qualify only the genuinely unknown portion.\n"
            "5. USER SHOWCASE: For questions about the user's specific account showcase, answer strictly using the USER'S OWN BUILD DETAILS block.\n"
            "6. CITE SOURCES: Structure your answer using clean markdown headings and bullet points. Cite KQM, TCL, or Official patch notes appropriately. If a document has a [VERSION WARNING: ...], note that it originates from an earlier patch.\n"
        )

        # Add intent-specific instructions
        if routing.requires_stat_engine:
            base_instruction += (
                "7. DETERMINISTIC CALCULATIONS: The context includes results from the Phase 7 Deterministic Stat Engine. "
                "These calculations (Total ATK, HP, DEF, CRIT values, ER, EM, CV, damage bonuses) are AUTHORITATIVE. "
                "Do NOT recalculate, estimate, or override these values. Use them directly and explain their significance. "
                "Your role is to INTERPRET and EXPLAIN the deterministic results, not to perform arithmetic.\n"
            )

        if routing.primary_intent == QueryIntent.WEAPON_COMPARISON or \
           QueryIntent.WEAPON_COMPARISON in routing.secondary_intents:
            base_instruction += (
                "8. WEAPON COMPARISON: If deterministic weapon comparison stats are provided, present them clearly side-by-side. "
                "Explain the practical implications of stat differences (e.g., 'The +15% ER from Favonius would let you run ATK% Sands instead of ER Sands'). "
                "Do NOT invent damage numbers not provided by the stat engine.\n"
            )

        if routing.primary_intent == QueryIntent.FARMING or \
           QueryIntent.FARMING in routing.secondary_intents:
            base_instruction += (
                "9. FARMING & MATERIALS: When answering material questions, provide exact material names and quantities from canonical data. "
                "If the user has account data loaded, compare required vs owned quantities.\n"
            )

        base_instruction += (
            "10. EXTERNAL ESCALATED EVIDENCE: The context may include externally retrieved evidence validated by Phase 9. "
            "Adhere strictly to the source authority tier and freshness tags (CURRENT, RECENT, STALE). "
            "If evidence is marked STALE, explicitly state it comes from an older patch and do NOT present it as current live game behavior. "
            "Do NOT extrapolate beyond the verified facts provided.\n"
        )

        return base_instruction

    # ===================================================================
    # Main Entry Point
    # ===================================================================

    async def generate_response(
        self,
        messages: List[ChatMessage],
        uid: Optional[str] = None
    ) -> ChatResponse:
        """Orchestrates Phase 8 routed RAG generation.

        1. Routes query through multi-intent classifier
        2. Gathers evidence from required sources (canonical, knowledge, account, stat engine)
        3. Checks evidence sufficiency (fail-closed gate)
        4. Calls Gemini with structured evidence + intent-aware system instruction
        5. Returns ChatResponse with routing transparency
        """
        if not messages:
            return ChatResponse(
                content="Hello! How can I help you today?",
                intent="general",
                citations=[],
                query_intents=[],
                sources_used=[],
                evidence_types=[],
                grounding_status="fully_grounded",
                grounding_score=1.0,
                claims=[],
            )

        # Get latest query
        latest_msg = messages[-1]
        query = latest_msg.content

        # Phase 8: Multi-intent routing
        routing = query_router.classify(query, uid=uid)
        logger.info(f"Query routing: {routing.primary_intent.value} | {routing.reasoning}")

        # Legacy intent for backward compat
        legacy_intent = "account" if routing.requires_account_data else "general"

        # Assemble evidence from all required sources
        bundle, citations = await self._assemble_evidence(query, routing, uid=uid)

        # Fail-closed gate: if required evidence is missing, return controlled response
        if not bundle.is_sufficient:
            logger.warning(f"Insufficient evidence for query: {bundle.insufficiency_reason}")
            return ChatResponse(
                content=self._build_insufficient_evidence_response(routing, bundle),
                intent=legacy_intent,
                citations=citations,
                query_intents=[i.value for i in routing.all_intents],
                sources_used=[s.value for s in bundle.sources_consulted],
                evidence_types=bundle.evidence_types_used,
                grounding_status="ungrounded",
                grounding_score=0.0,
                claims=[],
            )

        # Build system instruction
        system_instruction = self._build_system_instruction(routing)

        # Build prompt message history
        contents = []
        for msg in messages[:-1]:
            role = "user" if msg.role == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg.content}]
            })

        # Format latest message with evidence context
        context_str = "\n\n".join(item.content for item in bundle.items)
        prompt_with_context = (
            f"Context Information:\n"
            f"---------------------\n"
            f"{context_str}\n"
            f"---------------------\n\n"
            f"User Query: {query}"
        )

        contents.append({
            "role": "user",
            "parts": [{"text": prompt_with_context}]
        })

        # Generate response via Gemini
        response_content = await gemini_service.generate_content(
            contents=contents,
            system_instruction=system_instruction
        )

        if response_content.startswith("Error") or "high demand" in response_content.lower() or "quota" in response_content.lower():
            # Extract account summary from evidence for fallback
            account_summary = None
            for item in bundle.items:
                if item.source == DataSource.ACCOUNT_SHOWCASE and item.evidence_type == EvidenceType.ACCOUNT_FACT:
                    if "USER'S OWN" in item.content:
                        account_summary = item.content
                        break

            response_content = self._build_fallback_response(
                intent=legacy_intent,
                query=query,
                citations=citations,
                account_summary=account_summary,
            )

        # Phase 10: Grounding Verification & Non-decorative Relevance Filtering
        verification = grounding_service.verify_grounding(response_content, bundle, routing)
        filtered_citations = grounding_service.filter_meaningful_citations(citations, response_content, verification.claims)

        return ChatResponse(
            content=response_content,
            intent=legacy_intent,
            citations=filtered_citations,
            query_intents=[i.value for i in routing.all_intents],
            sources_used=[s.value for s in bundle.sources_consulted],
            evidence_types=bundle.evidence_types_used,
            grounding_status=verification.status.value,
            grounding_score=verification.score,
            claims=[c.model_dump() for c in verification.claims],
        )


rag_service = RAGService()
