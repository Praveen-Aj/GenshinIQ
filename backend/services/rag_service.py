"""Service to orchestrate query understanding, document retrieval, and grounded response generation."""

import logging
import re
from typing import Dict, List, Optional, Tuple

from backend.models.chat import ChatMessage, ChatResponse, Citation
from backend.services.gemini_service import gemini_service
from backend.services.knowledge_service import knowledge_service
from backend.services.game_data_service import game_data_service
from backend.services.account_service import account_service

logger = logging.getLogger(__name__)


class RAGService:
    """Orchestrates structured data retrieval, local document search, and Gemini response generation."""

    def __init__(self):
        pass

    def _classify_query(self, query: str) -> str:
        """
        Classifies query intent as 'account' or 'general'.
        If query references 'my', 'mine', 'showcase', etc., it's 'account'.
        """
        query_lower = query.lower()
        account_keywords = [
            r"\bmy\b",
            r"\bmine\b",
            r"\bi have\b",
            r"\bi've\b",
            r"\bshowcase\b",
            r"\bme\b",
            r"\bi am\b",
        ]
        for pattern in account_keywords:
            if re.search(pattern, query_lower):
                return "account"
        return "general"

    def _detect_character(self, query: str) -> Optional[str]:
        """
        Scans query for canonical character names.
        Returns matched character name (properly capitalized) or None.
        """
        query_lower = query.lower()
        characters = game_data_service.list_characters()
        
        for char in characters:
            # Match word boundary for character name
            pattern = rf"\b{re.escape(char.name.lower())}\b"
            if re.search(pattern, query_lower):
                return char.name
        return None

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
        
        intent = self._classify_query(query)
        char_name = self._detect_character(query)
        
        context_blocks = []
        citations = []
        
        # 1. Search knowledge base
        search_results = knowledge_service.search_documents(query, limit=3)
        for res in search_results:
            doc = knowledge_service.get_document(res.id)
            if doc:
                context_blocks.append(
                    f"=== KNOWLEDGE SOURCE: {doc.title} ({doc.metadata.source}) ===\n"
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

        # 2. Gather account details if intent is account
        account_found = False
        if intent == "account" and uid:
            try:
                showcase = await account_service.get_showcase(uid=uid)
                if char_name:
                    # Find character build matching char_name
                    char_build = next(
                        (c for c in showcase.characters if c.name.lower() == char_name.lower()),
                        None
                    )
                    if char_build:
                        context_blocks.append(self._format_showcase_character(char_build))
                        account_found = True
                    else:
                        # Character not in showcase
                        context_blocks.append(
                            f"=== SYSTEM NOTICE ===\n"
                            f"User has requested information on their '{char_name}', but it was not "
                            f"found in their showcase. Their active showcase characters are: "
                            f"{', '.join([c.name for c in showcase.characters])}.\n"
                            f"====================="
                        )
                else:
                    # Generic account query, include overview of showcase
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
                context_blocks.append(
                    f"=== SYSTEM ERROR ===\n"
                    f"Failed to fetch user showcase data for UID {uid}.\n"
                    f"===================="
                )

        # 3. Assemble Prompt & Guardrails
        system_instruction = (
            "You are GenshinIQ, a personal Genshin Impact AI assistant. Your goal is to provide highly accurate, "
            "grounded character build reviews and game theorycrafting advice. You must adhere to the following rules:\n"
            "1. Answer ONLY from the supplied evidence, structured data, or user account build details in the context block.\n"
            "2. Do NOT invent or hallucinate game mechanics, statistics, or character recommendations. Keep recommendations aligned with official or KQM guidelines.\n"
            "3. If the supplied context does not contain enough reliable information to answer the question, state exactly: "
            "'I don't have enough reliable information to answer that.' and explain what is missing.\n"
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

        return ChatResponse(
            content=response_content,
            intent=intent,
            citations=citations
        )


rag_service = RAGService()
