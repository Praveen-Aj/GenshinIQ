"""Deterministic evaluation fixture and metrics calculation for GenshinIQ Phase 5 Retrieval.

Contains 32 curated evaluation queries across:
1. Character Mechanics (Kazuha EM, Arlecchino BoL, Furina HP, Bennett ATK, Xiangling ER, Nahida EM)
2. Weapons (Kazuha weapons, Arlecchino weapons, Raiden weapons, Bennett weapons, Neuvillette weapons)
3. Artifacts (Arlecchino sets, Kazuha stats, Furina sets, VV shred, Nahida sets)
4. Game Mechanics (Vaporize/Melt, Swirl scaling, snapshotting, defense reduction, pity system)
5. Farming & Schedules (Resistance books, Gold books, Wednesday materials, Mavuika ascension)
6. Version & Patch History (5.0 patch notes, official combat rules, 1.0 historical meta)
7. Semantic Paraphrases (queries expressing identical intents using varied non-exact terminology)

Calculates:
- Precision@1, Precision@3, Precision@5
- Recall@5
- MRR (Mean Reciprocal Rank)
- nDCG@5 (Normalized Discounted Cumulative Gain at 5)
Separately for:
- Lexical-only (BM25)
- Dense-only (Vector)
- Hybrid (Fused)
"""

import math
from typing import Dict, List, Optional, Set, Tuple
from backend.services.retrieval_service import retrieval_service

# 32 Ground-Truth Curated Queries
EVALUATION_QUERIES = [
    # 1. Character Mechanics (6)
    {
        "id": "CM01",
        "query": "How does Kazuha Elemental Mastery scaling work?",
        "category": "Character Mechanics",
        "expected_docs": ["kqm_kaedehara_kazuha_guide"],
        "expected_chunks": ["kqm_kaedehara_kazuha_guide#core-mechanics-swirl-buffing"],
        "partially_relevant_docs": ["wiki_kazuha"],
        "prohibited_characters": ["Alhaitham", "Nahida", "Bennett"],
    },
    {
        "id": "CM02",
        "query": "How does Arlecchino Bond of Life mechanic work and stack?",
        "category": "Character Mechanics",
        "expected_docs": ["mechanics_bond_of_life", "kqm_arlecchino_extended_guide"],
        "expected_chunks": ["mechanics_bond_of_life#overview", "kqm_arlecchino_extended_guide#core-mechanics-bond-of-life"],
        "partially_relevant_docs": ["wiki_arlecchino"],
        "prohibited_characters": ["Furina", "Neuvillette"],
    },
    {
        "id": "CM03",
        "query": "How does Furina Fanfare and HP fluctuation buff the team?",
        "category": "Character Mechanics",
        "expected_docs": ["kqm_furina_guide"],
        "expected_chunks": ["kqm_furina_guide#overview-playstyle", "kqm_furina_guide#core-mechanics-fanfare-stacks"],
        "partially_relevant_docs": ["wiki_furina"],
        "prohibited_characters": ["Zhongli", "Alhaitham"],
    },
    {
        "id": "CM04",
        "query": "How does Bennett's attack buff calculate from base attack?",
        "category": "Character Mechanics",
        "expected_docs": ["kqm_bennett_extended_guide"],
        "expected_chunks": ["kqm_bennett_extended_guide#core-mechanics-fantastic-voyage-buff"],
        "partially_relevant_docs": ["wiki_bennett"],
        "prohibited_characters": ["Xiangling", "Kazuha"],
    },
    {
        "id": "CM05",
        "query": "How much Energy Recharge does Xiangling need in national team?",
        "category": "Character Mechanics",
        "expected_docs": ["kqm_xiangling_extended_guide"],
        "expected_chunks": ["kqm_xiangling_extended_guide#energy-management-funneling"],
        "partially_relevant_docs": ["wiki_xiangling"],
        "prohibited_characters": ["Raiden Shogun", "Furina"],
    },
    {
        "id": "CM06",
        "query": "How does Nahida Elemental Mastery scaling affect Tri-Karma Purification?",
        "category": "Character Mechanics",
        "expected_docs": ["kqm_nahida_extended_guide"],
        "expected_chunks": ["kqm_nahida_extended_guide#core-mechanics-tri-karma-purification"],
        "partially_relevant_docs": ["wiki_nahida"],
        "prohibited_characters": ["Alhaitham", "Tighnari"],
    },

    # 2. Weapons (5)
    {
        "id": "WP01",
        "query": "What is the best weapon for Kaedehara Kazuha Freedom-Sworn vs Xiphos?",
        "category": "Weapons",
        "expected_docs": ["kqm_kaedehara_kazuha_guide"],
        "expected_chunks": ["kqm_kaedehara_kazuha_guide#weapon-rankings"],
        "partially_relevant_docs": ["wiki_kazuha"],
        "prohibited_characters": ["Bennett", "Alhaitham"],
    },
    {
        "id": "WP02",
        "query": "What weapon is best for Arlecchino Crimson Moon Semblance alternatives?",
        "category": "Weapons",
        "expected_docs": ["kqm_arlecchino_extended_guide"],
        "expected_chunks": ["kqm_arlecchino_extended_guide#weapon-rankings"],
        "partially_relevant_docs": ["wiki_arlecchino"],
        "prohibited_characters": ["Hu Tao", "Xiangling"],
    },
    {
        "id": "WP03",
        "query": "What are the best weapons for Raiden Shogun Engulfing vs Catch?",
        "category": "Weapons",
        "expected_docs": ["kqm_raiden_shogun_guide"],
        "expected_chunks": ["kqm_raiden_shogun_guide#weapon-rankings"],
        "partially_relevant_docs": ["wiki_raiden"],
        "prohibited_characters": ["Xiangling", "Zhongli"],
    },
    {
        "id": "WP04",
        "query": "What support weapon is best for Bennett Favonius vs Sapwood vs Aquila?",
        "category": "Weapons",
        "expected_docs": ["kqm_bennett_extended_guide"],
        "expected_chunks": ["kqm_bennett_extended_guide#weapon-rankings"],
        "partially_relevant_docs": ["wiki_bennett"],
        "prohibited_characters": ["Kazuha", "Alhaitham"],
    },
    {
        "id": "WP05",
        "query": "What is the best weapon for Neuvillette Tome of the Eternal Flow?",
        "category": "Weapons",
        "expected_docs": ["kqm_neuvillette_guide"],
        "expected_chunks": ["kqm_neuvillette_guide#weapon-rankings"],
        "partially_relevant_docs": ["wiki_neuvillette"],
        "prohibited_characters": ["Furina", "Wriothesley"],
    },

    # 3. Artifacts (5)
    {
        "id": "AR01",
        "query": "What are the recommended artifact sets for Arlecchino Fragment of Harmonic Whimsy?",
        "category": "Artifacts",
        "expected_docs": ["kqm_arlecchino_extended_guide", "artifact_fragment_of_harmonic_whimsy"],
        "expected_chunks": ["kqm_arlecchino_extended_guide#recommended-artifact-sets"],
        "partially_relevant_docs": ["wiki_arlecchino"],
        "prohibited_characters": ["Alhaitham", "Zhongli"],
    },
    {
        "id": "AR02",
        "query": "What artifact main stats and substats does Kaedehara Kazuha want?",
        "category": "Artifacts",
        "expected_docs": ["kqm_kaedehara_kazuha_guide", "artifact_viridescent_venerer"],
        "expected_chunks": ["kqm_kaedehara_kazuha_guide#stat-priorities-er-requirements", "kqm_kaedehara_kazuha_guide#recommended-artifact-sets"],
        "partially_relevant_docs": ["wiki_kazuha"],
        "prohibited_characters": ["Bennett"],
    },
    {
        "id": "AR03",
        "query": "What artifact set is best for Furina Golden Troupe 4-piece?",
        "category": "Artifacts",
        "expected_docs": ["kqm_furina_guide", "artifact_golden_troupe"],
        "expected_chunks": ["kqm_furina_guide#recommended-artifact-sets"],
        "partially_relevant_docs": ["wiki_furina"],
        "prohibited_characters": ["Neuvillette", "Nahida"],
    },
    {
        "id": "AR04",
        "query": "How does Viridescent Venerer 4-piece resistance shred work?",
        "category": "Artifacts",
        "expected_docs": ["artifact_viridescent_venerer", "mechanics_defense_resistance_math"],
        "expected_chunks": ["artifact_viridescent_venerer#viridescent-venerer-artifact-set-bonuses-piece-details"],
        "partially_relevant_docs": ["kqm_kaedehara_kazuha_guide"],
        "prohibited_characters": [],
    },
    {
        "id": "AR05",
        "query": "What artifact set should Nahida use Deepwood Memories vs Gilded Dreams?",
        "category": "Artifacts",
        "expected_docs": ["kqm_nahida_extended_guide", "artifact_deepwood_memories", "artifact_gilded_dreams"],
        "expected_chunks": ["kqm_nahida_extended_guide#recommended-artifact-sets"],
        "partially_relevant_docs": ["wiki_nahida"],
        "prohibited_characters": ["Alhaitham"],
    },

    # 4. Game Mechanics (5)
    {
        "id": "GM01",
        "query": "How do Vaporize and Melt amplifying reaction damage multipliers calculate?",
        "category": "Mechanics",
        "expected_docs": ["mechanics_damage_formula", "mechanics_elemental_reactions"],
        "expected_chunks": ["mechanics_damage_formula#6-amplifying-reaction-multiplier"],
        "partially_relevant_docs": ["official_combat_system_mechanics"],
        "prohibited_characters": [],
    },
    {
        "id": "GM02",
        "query": "How does Swirl reaction damage scale with character level and Elemental Mastery?",
        "category": "Mechanics",
        "expected_docs": [
            "mechanics_elemental_reactions",
            "mechanics_snapshotting_dynamic_buffs",
            "kqm_kaedehara_kazuha_guide",
        ],
        "expected_chunks": [
            "mechanics_elemental_reactions#2-transformative-reactions",
            "mechanics_snapshotting_dynamic_buffs#4-transformative-reaction-exception",
            "kqm_kaedehara_kazuha_guide#core-mechanics-swirl-buffing",
        ],
        "partially_relevant_docs": ["official_combat_system_mechanics"],
        "prohibited_characters": [],
    },
    {
        "id": "GM03",
        "query": "What abilities snapshot buffs in Genshin Impact and how does it work?",
        "category": "Mechanics",
        "expected_docs": ["mechanics_snapshotting_dynamic_buffs"],
        "expected_chunks": ["mechanics_snapshotting_dynamic_buffs#1-what-is-snapshotting", "mechanics_snapshotting_dynamic_buffs#2-abilities-that-snapshot"],
        "partially_relevant_docs": ["kqm_xiangling_extended_guide"],
        "prohibited_characters": [],
    },
    {
        "id": "GM04",
        "query": "How does enemy defense reduction and defense ignore affect the damage formula?",
        "category": "Mechanics",
        "expected_docs": ["mechanics_defense_resistance_math", "mechanics_damage_formula"],
        "expected_chunks": ["mechanics_damage_formula#4-enemy-def-multiplier", "mechanics_defense_resistance_math#1-defense-multiplier-formula"],
        "partially_relevant_docs": [],
        "prohibited_characters": [],
    },
    {
        "id": "GM05",
        "query": "What is the soft pity and hard pity rate on character event banners?",
        "category": "Mechanics",
        "expected_docs": ["mechanics_pity_wish_system"],
        "expected_chunks": ["mechanics_pity_wish_system#1-character-event-wish-rates-pity", "mechanics_pity_wish_system#3-capturing-radiance-mechanic-version-50"],
        "partially_relevant_docs": [],
        "prohibited_characters": [],
    },

    # 5. Farming & Domain Schedules (4)
    {
        "id": "FM01",
        "query": "What domain drops Resistance talent books on Tuesday and Friday?",
        "category": "Farming",
        "expected_docs": ["structured_daily_talent_books_schedule"],
        "expected_chunks": ["structured_daily_talent_books_schedule#2-tuesday-friday-and-sunday"],
        "partially_relevant_docs": ["kqm_bennett_extended_guide"],
        "prohibited_characters": [],
    },
    {
        "id": "FM02",
        "query": "What day can you farm Gold talent books in Liyue Taishan Mansion?",
        "category": "Farming",
        "expected_docs": ["structured_daily_talent_books_schedule"],
        "expected_chunks": ["structured_daily_talent_books_schedule#3-wednesday-saturday-and-sunday"],
        "partially_relevant_docs": ["kqm_zhongli_extended_guide"],
        "prohibited_characters": [],
    },
    {
        "id": "FM03",
        "query": "What weapon ascension materials are available on Wednesday and Saturday?",
        "category": "Farming",
        "expected_docs": ["structured_daily_weapon_materials_schedule"],
        "expected_chunks": ["structured_daily_weapon_materials_schedule#3-wednesday-saturday-and-sunday"],
        "partially_relevant_docs": [],
        "prohibited_characters": [],
    },
    {
        "id": "FM04",
        "query": "What materials does Mavuika need for ascension?",
        "category": "Farming",
        "expected_docs": ["wiki_mavuika"],
        "expected_chunks": ["wiki_mavuika#ascension-materials"],
        "partially_relevant_docs": ["kqm_mavuika_guide"],
        "prohibited_characters": [],
    },

    # 6. Version & Patch History (3)
    {
        "id": "VH01",
        "query": "What new mechanics were introduced in the version 5.0 Natlan patch notes?",
        "category": "Version/History",
        "expected_docs": ["official_patch_5_0_nightsoul_notes"],
        "expected_chunks": ["official_patch_5_0_nightsoul_notes#1-nightsouls-blessing"],
        "partially_relevant_docs": [],
        "prohibited_characters": [],
    },
    {
        "id": "VH02",
        "query": "What are the official combat rules and elemental interaction mechanics?",
        "category": "Version/History",
        "expected_docs": ["official_combat_system_mechanics"],
        "expected_chunks": ["official_combat_system_mechanics#overview-core-elements"],
        "partially_relevant_docs": ["mechanics_elemental_reactions"],
        "prohibited_characters": [],
    },
    {
        "id": "VH03",
        "query": "What was the original 1.0 national team meta with Bennett and Xiangling in older versions?",
        "category": "Version/History",
        "expected_docs": [
            "mechanics_team_archetypes",
            "kqm_xiangling_extended_guide",
            "kqm_bennett_extended_guide",
        ],
        "expected_chunks": [
            "mechanics_team_archetypes#1-the-national-team-vaporizemeltoverload",
        ],
        "partially_relevant_docs": ["wiki_bennett", "wiki_xiangling"],
        "prohibited_characters": [],
    },

    # 7. Semantic Paraphrases / Terminology Mismatches (4)
    {
        "id": "SP01",
        "query": "Why stack EM on Kazuha?",
        "category": "Semantic Paraphrase",
        "expected_docs": ["kqm_kaedehara_kazuha_guide"],
        "expected_chunks": ["kqm_kaedehara_kazuha_guide#core-mechanics-swirl-buffing", "kqm_kaedehara_kazuha_guide#stat-priorities-er-requirements"],
        "partially_relevant_docs": ["wiki_kazuha"],
        "prohibited_characters": ["Nahida", "Alhaitham"],
    },
    {
        "id": "SP02",
        "query": "How does Kazuha increase elemental damage for the party?",
        "category": "Semantic Paraphrase",
        "expected_docs": ["kqm_kaedehara_kazuha_guide"],
        "expected_chunks": ["kqm_kaedehara_kazuha_guide#core-mechanics-swirl-buffing"],
        "partially_relevant_docs": ["wiki_kazuha", "artifact_viridescent_venerer"],
        "prohibited_characters": ["Bennett", "Furina"],
    },
    {
        "id": "SP03",
        "query": "How does Bennett's attack buff work?",
        "category": "Semantic Paraphrase",
        "expected_docs": ["kqm_bennett_extended_guide"],
        "expected_chunks": ["kqm_bennett_extended_guide#core-mechanics-fantastic-voyage-buff"],
        "partially_relevant_docs": ["wiki_bennett"],
        "prohibited_characters": ["Xiangling", "Kazuha"],
    },
    {
        "id": "SP04",
        "query": "How much energy does Xiangling need to burst on cooldown?",
        "category": "Semantic Paraphrase",
        "expected_docs": ["kqm_xiangling_extended_guide"],
        "expected_chunks": ["kqm_xiangling_extended_guide#energy-management-funneling"],
        "partially_relevant_docs": ["wiki_xiangling"],
        "prohibited_characters": ["Raiden Shogun", "Furina"],
    },
]


def judge_relevance(item_doc_id: str, item_chunk_id: str, item_char: Optional[str], q_data: dict) -> str:
    """Classify retrieved evidence item as RELEVANT, PARTIALLY_RELEVANT, or IRRELEVANT."""
    # Check prohibited character violation
    if item_char and q_data.get("prohibited_characters"):
        for pc in q_data["prohibited_characters"]:
            if pc.lower() in item_char.lower():
                return "IRRELEVANT"

    # Check exact chunk matches first
    if item_chunk_id in q_data.get("expected_chunks", []):
        return "RELEVANT"

    # Check expected document IDs
    if item_doc_id in q_data.get("expected_docs", []):
        return "RELEVANT"

    # Check partially relevant document IDs
    if item_doc_id in q_data.get("partially_relevant_docs", []):
        return "PARTIALLY_RELEVANT"

    return "IRRELEVANT"


def evaluate_query_results(items: list, q_data: dict) -> dict:
    """Compute P@1, P@3, P@5, Recall@5, MRR, nDCG@5 for one query."""
    judgments = [
        judge_relevance(item.document_id, item.chunk_id, item.character, q_data)
        for item in items[:5]
    ]

    # Precision@K
    rel_flags = [1 if j in ("RELEVANT", "PARTIALLY_RELEVANT") else 0 for j in judgments]
    p_at_1 = rel_flags[0] if len(rel_flags) > 0 else 0.0
    p_at_3 = sum(rel_flags[:3]) / min(3, len(rel_flags)) if rel_flags else 0.0
    p_at_5 = sum(rel_flags[:5]) / min(5, len(rel_flags)) if rel_flags else 0.0

    # Recall@5: Did we find at least one relevant document in top 5?
    found_relevant = any(j == "RELEVANT" for j in judgments)
    recall_at_5 = 1.0 if found_relevant else (0.5 if any(j == "PARTIALLY_RELEVANT" for j in judgments) else 0.0)

    # MRR (Mean Reciprocal Rank)
    mrr = 0.0
    for idx, j in enumerate(judgments):
        if j == "RELEVANT":
            mrr = 1.0 / (idx + 1)
            break
        elif j == "PARTIALLY_RELEVANT" and mrr == 0.0:
            mrr = 0.5 / (idx + 1)

    # nDCG@5
    # Graded gain: RELEVANT = 2, PARTIALLY_RELEVANT = 1, IRRELEVANT = 0
    gains = [2.0 if j == "RELEVANT" else (1.0 if j == "PARTIALLY_RELEVANT" else 0.0) for j in judgments]
    dcg = 0.0
    for idx, g in enumerate(gains):
        dcg += g / math.log2(idx + 2)  # idx + 2 because rank 1 -> log2(2) = 1

    # Ideal DCG: top items all RELEVANT (gain = 2)
    ideal_gains = sorted(gains, reverse=True)
    if not any(ideal_gains):
        ideal_gains = [2.0, 2.0, 2.0, 2.0, 2.0]
    idcg = sum(g / math.log2(idx + 2) for idx, g in enumerate(ideal_gains))
    ndcg_at_5 = (dcg / idcg) if idcg > 0 else 0.0

    return {
        "p_at_1": p_at_1,
        "p_at_3": p_at_3,
        "p_at_5": p_at_5,
        "recall_at_5": recall_at_5,
        "mrr": mrr,
        "ndcg_at_5": round(ndcg_at_5, 4),
        "judgments": judgments,
    }


def run_evaluation_suite(method: str = "hybrid") -> dict:
    """Execute evaluation across all 32 benchmark queries for a given method."""
    query_metrics = []

    for q_data in EVALUATION_QUERIES:
        bundle = retrieval_service.retrieve(
            query=q_data["query"],
            method=method,
            top_k=5,
        )
        res = evaluate_query_results(bundle.items, q_data)
        top_chunk = bundle.items[0].chunk_id if bundle.items else "NONE"
        top_score = bundle.items[0].composite_score if bundle.items else 0.0
        top_source = bundle.items[0].source if bundle.items else "NONE"
        top_tier = int(bundle.items[0].authority_tier) if bundle.items else 0
        top_judgment = res["judgments"][0] if res["judgments"] else "NONE"

        query_metrics.append({
            "id": q_data["id"],
            "query": q_data["query"],
            "category": q_data["category"],
            "method": method,
            "top_chunk": top_chunk,
            "top_score": top_score,
            "top_source": top_source,
            "top_tier": top_tier,
            "top_judgment": top_judgment,
            "p_at_1": res["p_at_1"],
            "p_at_3": res["p_at_3"],
            "p_at_5": res["p_at_5"],
            "recall_at_5": res["recall_at_5"],
            "mrr": res["mrr"],
            "ndcg_at_5": res["ndcg_at_5"],
        })

    n = len(query_metrics)
    summary = {
        "method": method,
        "total_queries": n,
        "mean_p_at_1": round(sum(m["p_at_1"] for m in query_metrics) / n, 4),
        "mean_p_at_3": round(sum(m["p_at_3"] for m in query_metrics) / n, 4),
        "mean_p_at_5": round(sum(m["p_at_5"] for m in query_metrics) / n, 4),
        "mean_recall_at_5": round(sum(m["recall_at_5"] for m in query_metrics) / n, 4),
        "mean_mrr": round(sum(m["mrr"] for m in query_metrics) / n, 4),
        "mean_ndcg_at_5": round(sum(m["ndcg_at_5"] for m in query_metrics) / n, 4),
        "per_query": query_metrics,
    }
    return summary
