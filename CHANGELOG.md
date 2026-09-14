# Changelog

All notable changes to the **GenshinIQ** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-09-14

### Added
- **Phase 3: Canonical Data Pipeline Rebuild**: Complete rebuild of the game data pipeline using verified datamined sources (AnimeGameData). Zero fabricated stats, zero duplicate IDs, deterministic character level 90 scalings, and property-specific avatar curve lookups.
- **Phase 4: Game Version Architecture**: Explicit decoupled version model (current game version, latest known, project target, document content version). DISCOVER → VERIFY → PROMOTE lifecycle with fail-closed gates. Change-aware freshness semantics (CURRENT, RECENT_COMPATIBLE, STALE, HISTORICAL).
- **Phase 5: Hybrid Retrieval Architecture**: Production-grade BM25 Okapi lexical search + local subword dense vector similarity (256-dim) with hybrid score fusion, provenance-validated composite reranking, authority tier multipliers, freshness weighting, entity alignment boosts, and deduplication. Evaluation benchmark: Precision@1 = 100%, Recall@5 = 100%, MRR = 0.9844.
- **Phase 6: GOOD v3 Account Import**: Full account inventory import from Genshin Optimizer exports. Canonical entity resolution (EXACT_MATCH, ALIAS_MATCH, LEGACY_MATCH, UNRESOLVED). Idempotent ingestion, deterministic instance IDs, multi-copy weapon support, individual artifact identity, raw preservation with hash manifests, and snapshot diffing.
- **Phase 7: Deterministic Stat Engine**: Pure mathematical build calculation pipeline. Character base stats (level curves, ascension phases) + weapon base ATK + artifact main/substats + set bonuses. Zero AI-generated values. Reproducible build snapshots, build comparisons with exact attribute deltas, auditable contribution breakdowns.
- **Phase 8: Knowledge Contract & Escalation System**: Multi-tier knowledge escalation service with freshness tracking and version-aware revalidation. Knowledge contracts defining completeness requirements per character. Source registry with registered providers, authority tiers, and derivation relationships. Version completeness gates and knowledge gap detection.
- **Phase 9: Source Provenance & Audit Architecture**: Comprehensive source registry service with registered providers, authority tier validation, and automated provenance auditing. Version delta service for tracking patch-level changes across knowledge documents. Audit scenario test suites for provenance chain integrity.
- **Phase 10: Citation & Grounding System**: 4-level citation assembly (DATASET, SOURCE, CALCULATION, ACCOUNT). Automated claim extraction and corroboration logic against evidence bundles. Grounding score/status classification (FULLY_GROUNDED, PARTIALLY_GROUNDED, UNGROUNDED). Non-decorative citation relevance filtering. Frontend grounding transparency badges and expandable citation drawers.
- **Extended Knowledge Base**: 10 extended KQM guides (Alhaitham, Bennett, Citlali, Hu Tao, Mavuika, Nahida, Xiangling, Xingqiu, Yelan, Zhongli). 5 game mechanics documents (defense/resistance math, poise/interruption, snapshotting/dynamic buffs, aura coexistence/dual reactions, combat system mechanics). Structured daily farming schedules (talent books, weapon materials, weekly boss conversions). Official patch 7.0 notes.
- **Automated Test Suite**: Expanded to **342 test cases** across 26 test modules covering canonical data pipeline, version discovery, GOOD account import, stat engine, source registry, knowledge contracts, knowledge escalation, retrieval evaluation, query routing, citation grounding, and full regression.

### Changed
- **Data Pipeline**: Replaced community API (`genshin.jmp.blue`) data fetching with verified datamined source pipeline. All game data now traceable to AnimeGameData canonical repository.
- **Knowledge Provenance**: All wiki documents reclassified from `AUTHORITATIVE` to correct `COMMUNITY` tier. KQM extended guides properly tagged as `THEORYCRAFTING`.
- **Retrieval**: Upgraded from simple keyword search to hybrid BM25 + dense vector retrieval with composite reranking.
- **Frontend**: Enhanced app.js with grounding transparency badges, citation drawers, and improved character detection for multi-word names.
- **Query Router**: Enhanced intent classification with multi-word character name part matching for improved account query detection.

---

## [0.3.0] - 2026-09-07

### Added
- **In-Game Profile Avatar Resolution**: Automatically extracts and maps `playerInfo.profilePicture.avatarId` from Enka.Network to the canonical character name and Enka CDN avatar icon (resolves `10000060` to Yelan for primary UID `817739968`).
- **Today's Domain Rotation & Farming Planner**: Added a flagship GenshinTrack-inspired daily planner widget displaying currently open talent book domains across all 6 nations and highlighting characters from the user's active showcase who can be farmed today.
- **Direct Interactive Action Buttons**:
  - `✨ Ask AI to Review Build`: Directly on the character hero card; instantly switches to the Chat Assistant tab with pre-populated weapon, CRIT ratio, and artifact context.
  - `📖 Theorycrafting Guide`: Queries KQM knowledge base for character-specific talent crowning priority, best team comps, and substat thresholds.
  - `[Ask Teams]`: Spiral Abyss badge shortcut requesting optimized team comps for the player's current floor (`Floor 12-3`).
  - `⚡ Optimize Artifacts`: Header action button on the Equipped Artifacts card.
  - `Ask AI What to Farm`: Domain rotation banner shortcut for optimal resin efficiency recommendations.
- **Resilient Inline Element SVGs**: Added `getElementSvg()` providing crisp, vector-rendered elemental glyphs for all 7 elements (Pyro, Hydro, Anemo, Electro, Dendro, Cryo, Geo), eliminating CDN 404 network failures.
- **Cache-Busting Assets**: Added automated versioning parameters (`?v=20260907_1630`) on `style.css` and `app.js` to ensure browsers receive updated frontend assets immediately.

### Changed
- **Skirk Asset & Element Alignment**:
  - Updated Skirk's Enka CDN avatar mapping to `UI_AvatarIcon_SkirkNew.png`.
  - Realigned Skirk's canonical element from Hydro to **Cryo** in `enka_mappings.py` to match in-game data and Enka store records.
- **Gemini API Timeout Resilience**: Increased `httpx.AsyncClient` timeout from 15.0s to 30.0s with a 10.0s connection timeout in `gemini_service.py` to support deep RAG prompt generation with account builds.
- **Profile Avatar Styling**: Enhanced `.profile-avatar-box`, `.profile-avatar`, and `.profile-avatar img` with `object-fit: cover` and border radius to ensure in-game avatars render cleanly.

---

## [0.2.0] - 2026-09-07

### Added
- **Dark Celestial Glassmorphic Design System**: Complete UI overhaul inspired by GenshinTrack and modern Genshin Impact web applications.
- **Visual Character Grid**: Replaced raw text lists with visual cards featuring 48px character avatars, glowing rarity borders (5-star gold, 4-star purple), and elemental badges.
- **Splash Art Hero Banner**: Dynamically loads full-width official gacha splash art backgrounds (`UI_Gacha_AvatarImg_*`) on character selection.
- **Enka CDN Asset Resolution**: Direct CDN resolution for equipped weapons (`UI_EquipIcon_*`) and artifacts (`UI_RelicIcon_*`).
- **Interactive Constellation Dots**: Visual constellation indicators (lit vs. unlit) for characters C0 through C6.
- **Knowledge Base Markdown Parser**: Client-side markdown renderer for KQM theorycrafting articles, mechanics notes, and official patch notes with collapsible source citations.

---

## [0.1.0] - 2026-09-06

### Added
- **Phase 0: Project Foundation**: FastAPI backend, Pydantic settings, health check endpoint (`/api/health`), and testing infrastructure.
- **Phase 1: Enka Account Integration**: Public Enka.Network showcase importer with TTL disk caching, FightProp map normalization, and combat stat calculation.
- **Phase 2: Canonical Structured Game Data**: Canonical datasets for Characters, Weapons, Artifact Sets, and Materials with $O(1)$ in-memory lookups, multi-attribute filtering, and global search.
- **Phase 3: Curated Knowledge Base**: KeqingMains theorycrafting guides, elemental gauge mechanics, Natlan mechanics, and official patch notes tagged by source hierarchy.
- **Phase 4: Grounded Chat Assistant**: Gemini RAG pipeline with intent classification, canonical evidence retrieval, dynamic game version grounding, and fail-closed guardrails.
- **Phase 5: Account-Grounded Recommendations**: Account build context injection enabling customized weapon comparisons, artifact stat evaluations, and team building advice.
- **Automated Test Suite**: 28 automated pytest test cases covering API endpoints, data models, caching, and RAG context generation.
