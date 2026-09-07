# Changelog

All notable changes to the **GenshinIQ** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
