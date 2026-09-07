"""Service to orchestrate query understanding, document retrieval, and grounded response generation."""

import difflib
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from backend.models.chat import ChatMessage, ChatResponse, Citation
from backend.services.gemini_service import gemini_service
from backend.services.knowledge_service import knowledge_service
from backend.services.game_data_service import game_data_service
from backend.services.account_service import account_service
from backend.services.version_service import version_service

logger = logging.getLogger(__name__)


class RAGService:
    """Orchestrates structured data retrieval, local document search, and Gemini response generation."""

    def __init__(self):
        pass

    def _get_latest_game_version(self) -> str:
        """Return the canonical current live game version."""
        return version_service.get_current_version().version

    def _classify_query(self, query: str, uid: Optional[str] = None) -> str:
        """
        Classifies query intent as 'account' or 'general'.
        """
        query_lower = query.lower()
        
        # 1. General guide / theorycrafting indicators take precedence
        general_indicators = [
            r"\brecommend",
            r"\bguide\b",
            r"\baccording to\b",
            r"\bkqm\b",
            r"\bwiki\b",
            r"\bbest\b",
            r"\boption",
            r"\bhow to build\b",
            r"\bshould i\b",
            r"\bwhat is the best\b",
        ]
        for pattern in general_indicators:
            if re.search(pattern, query_lower):
                return "general"

        # 2. Strong account indicators
        account_keywords = [
            r"\bmy\b",
            r"\bmine\b",
            r"\bi have\b",
            r"\bi've\b",
            r"\bshowcase\b",
            r"\bi am\b",
            r"\bdo i\b",
            r"\bmy account\b",
        ]
        for pattern in account_keywords:
            if re.search(pattern, query_lower):
                return "account"

        # 3. Specific build detail questions on characters
        char_name = self._detect_character(query)
        if char_name:
            build_indicators = [
                r"\bweapon level\b",
                r"\brefinement\b",
                r"\bconstellation\b",
                r"\btalent\b",
                r"\bequipped\b",
                r"\bactive\b",
            ]
            for pattern in build_indicators:
                if re.search(pattern, query_lower):
                    return "account"

        return "general"

    def _detect_character(self, query: str) -> Optional[str]:
        """
        Scans query for canonical character names.
        Returns matched character name (properly capitalized) or None.
        """
        query_lower = query.lower()
        
        # 1. Scan enka mappings first (contains Snezhnaya / newest characters like Citlali)
        try:
            from backend.services.enka_mappings import CHARACTER_DATABASE
            for mapping in CHARACTER_DATABASE.values():
                char_name = mapping[0]
                pattern = rf"\b{re.escape(char_name.lower())}\b"
                if re.search(pattern, query_lower):
                    return char_name
        except Exception:
            pass

        # 2. Fallback to database characters
        characters = game_data_service.list_characters()
        for char in characters:
            # Match word boundary for character name
            pattern = rf"\b{re.escape(char.name.lower())}\b"
            if re.search(pattern, query_lower):
                return char.name

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
                "Gemini is temporarily busy, so I’m using the grounded account context I already fetched.\n\n"
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
                f"Here are the strongest sources I found for “{query}”:\n"
                f"{cited_sources}\n\n"
                "Try again in a moment and I’ll generate the full answer."
            )

        if intent == "account":
            return (
                "Gemini is temporarily busy, and I couldn’t assemble enough account context to give a confident build review.\n\n"
                "Please try again in a moment, or refresh your showcase and resend the question."
            )

        return (
            "Gemini is temporarily busy right now.\n\n"
            "I couldn’t generate a grounded answer yet, but the app is still working and you can try the question again shortly."
        )

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

    async def generate_response(
        self,
        messages: List[ChatMessage],
        uid: Optional[str] = None
    ) -> ChatResponse:
        """
        Orchestrates RAG generation.
        1. Classifies intent of the latest user query.
        2. Searches knowledge base and gets top matches.
        3. If intent is 'account', retrieves user's active character build.
        4. Injects context and system anti-hallucination instruction.
        5. Calls Gemini API and returns formatted grounded response.
        """
        if not messages:
            return ChatResponse(content="Hello! How can I help you today?", intent="general", citations=[])

        # Get latest query
        latest_msg = messages[-1]
        query = latest_msg.content
        
        intent = self._classify_query(query, uid=uid)
        char_name = self._detect_character(query)
        
        context_blocks = []
        citations = []
        
        # 1. Direct character guide lookup & canonical game data injection
        if char_name:
            # 1a. Pull all curated knowledge documents directly linked to this character
            char_docs = knowledge_service.list_documents(character=char_name)
            for doc in char_docs:
                eval_res = version_service.evaluate_staleness(doc.metadata.game_version)
                stale_note = f"\n[VERSION WARNING: {eval_res.warning}]" if eval_res.is_stale else ""
                context_blocks.append(
                    f"=== KNOWLEDGE SOURCE: {doc.title} (v{doc.metadata.game_version}, {doc.metadata.source}){stale_note} ===\n"
                    f"URL: {doc.metadata.source_url}\n"
                    f"Content:\n{doc.content}\n"
                    f"=================================================="
                )
                citations.append(
                    Citation(
                        source_name=doc.metadata.source,
                        source_url=doc.metadata.source_url,
                        snippet=doc.summary,
                        character=doc.metadata.character,
                        topic=doc.metadata.topic,
                        game_version=doc.metadata.game_version
                    )
                )

            # 1b. Inject canonical game data (base stats, talents, element, weapon)
            canonical_char = game_data_service.get_character(char_name)
            if canonical_char:
                talents_text = "\n".join([
                    f"- {t.name} ({t.type}): {t.description}"
                    for t in (canonical_char.talents or [])
                ]) if canonical_char.talents else "Standard kit"
                region_val = getattr(canonical_char, 'region', None) or 'Teyvat'
                affil_val = getattr(canonical_char, 'affiliation', None) or region_val
                intro_ver = getattr(canonical_char, 'game_version_introduced', None) or '1.0'
                context_blocks.append(
                    f"=== CANONICAL GAME DATABASE: {canonical_char.name.upper()} (Introduced: v{intro_ver}) ===\n"
                    f"Rarity: {canonical_char.rarity} Star | Element: {canonical_char.element} | Weapon: {canonical_char.weapon_type}\n"
                    f"Region: {region_val} | Affiliation: {affil_val}\n"
                    f"Base HP (Lv 90): {canonical_char.base_hp_lvl90} | Base ATK: {canonical_char.base_atk_lvl90} | Base DEF: {canonical_char.base_def_lvl90}\n"
                    f"Ascension Stat: {canonical_char.ascension_stat} ({canonical_char.ascension_stat_val_lvl90})\n"
                    f"Talents:\n{talents_text}\n"
                    f"=================================================="
                )

        # 2. Search additional knowledge base articles
        search_query = query
        if char_name and char_name.lower() not in query.lower():
            search_query = f"{query} {char_name}"

        search_results = knowledge_service.search_documents(search_query, limit=3)
        account_summary = None
        for res in search_results:
            doc = knowledge_service.get_document(res.id)
            if not doc:
                continue
            # Avoid duplicate citations
            if any(c.source_url == doc.metadata.source_url for c in citations if c.source_url):
                continue
            eval_res = version_service.evaluate_staleness(doc.metadata.game_version)
            stale_note = f"\n[VERSION WARNING: {eval_res.warning}]" if eval_res.is_stale else ""
            context_blocks.append(
                f"=== KNOWLEDGE SOURCE: {doc.title} (v{doc.metadata.game_version}, {doc.metadata.source}){stale_note} ===\n"
                f"URL: {doc.metadata.source_url}\n"
                f"Content:\n{doc.content}\n"
                f"=================================================="
            )
            citations.append(
                Citation(
                    source_name=doc.metadata.source,
                    source_url=doc.metadata.source_url,
                    snippet=doc.summary,
                    character=doc.metadata.character,
                    topic=doc.metadata.topic,
                    game_version=doc.metadata.game_version
                )
            )

        # 3. Gather account details if uid is provided
        account_found = False
        if uid:
            try:
                showcase = await account_service.get_showcase(uid=uid)
                if char_name:
                    char_build = next(
                        (c for c in showcase.characters if c.name.lower() == char_name.lower()),
                        None
                    )
                    if char_build:
                        account_summary = self._format_showcase_character(char_build)
                        context_blocks.append(account_summary)
                        account_found = True
                    elif intent == "account":
                        context_blocks.append(
                            f"=== SYSTEM NOTICE ===\n"
                            f"User has requested information on their '{char_name}', but it was not "
                            f"found in their showcase. Their active showcase characters are: "
                            f"{', '.join([c.name for c in showcase.characters])}.\n"
                            f"====================="
                        )
                elif intent == "account":
                    chars_summary = ", ".join([f"{c.name} (Lv. {c.level} C{c.constellation})" for c in showcase.characters])
                    context_blocks.append(
                        f"=== USER'S SHOWCASE OVERVIEW ===\n"
                        f"Nickname: {showcase.profile.nickname}\n"
                        f"Adventure Rank: {showcase.profile.level}\n"
                        f"World Level: {showcase.profile.world_level}\n"
                        f"Showcase Characters: {chars_summary}\n"
                        f"================================"
                    )
            except Exception as e:
                logger.error(f"Failed to load user showcase for RAG: {e}")
                if intent == "account":
                    context_blocks.append(
                        f"=== SYSTEM ERROR ===\n"
                        f"Failed to fetch user showcase data for UID {uid}.\n"
                        f"===================="
                    )

        # 4. Assemble Prompt & Guardrails
        current_date_str = datetime.now().strftime("%B %Y")
        current_ver = version_service.get_current_version()
        
        system_instruction = (
            "You are GenshinIQ, a personal Genshin Impact AI assistant. Your goal is to provide highly accurate, "
            "grounded character build reviews and game theorycrafting advice. You must adhere to the following rules:\n"
            f"0. CRITICAL CONTEXT: The current date is {current_date_str}. The current live version of Genshin Impact is Version {current_ver.version} ('{current_ver.name}', {current_ver.major_region}). "
            "All characters including Natlan characters (such as Mavuika, Citlali, Kinich, Mualani, Xilonen, Chasca, Yumemizuki Mizuki) are officially released characters. "
            "When provided with character guides or canonical game data in the context, you MUST provide full, authoritative build recommendations (best weapons, artifact sets, main/substats, talent crowning order, and team comps). "
            "If a knowledge source has a [VERSION WARNING: ...], note appropriately that the advice originates from an earlier patch.\n"
            "1. For questions about the user's specific account showcase, builds, or specific local character guide statistics, "
            "answer strictly using the supplied context block. Do not invent stats or builds.\n"
            "2. For general Genshin Impact questions that are not fully covered in the local context, you are permitted to answer using your general knowledge of the game. "
            "In this case, note clearly in your response that you are answering from general knowledge.\n"
            "3. If a question cannot be answered either by the local context or your general knowledge, state that information is insufficient.\n"
            "4. Be concise, structure your answer using clean markdown headings and bullet points.\n"
            "5. Cite the KQM or official source when referring to recommendations or facts. Link elements matching their URLs when appropriate."
        )

        # Build prompt message history
        # Convert history messages to Gemini format
        contents = []
        for msg in messages[:-1]:
            role = "user" if msg.role == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg.content}]
            })

        # Format latest message with context
        context_str = "\n\n".join(context_blocks)
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

        # Generate response
        response_content = await gemini_service.generate_content(
            contents=contents,
            system_instruction=system_instruction
        )

        if response_content.startswith("Error:") or "high demand" in response_content.lower():
            response_content = self._build_fallback_response(
                intent=intent,
                query=query,
                citations=citations,
                account_summary=account_summary,
            )

        return ChatResponse(
            content=response_content,
            intent=intent,
            citations=citations
        )


rag_service = RAGService()
