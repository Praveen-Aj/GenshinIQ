# GenshinIQ — Comprehensive Technical Implementation Details

## 1. Architectural Overview & Core Principles

GenshinIQ is a personal Genshin Impact AI assistant engineered around a single core directive:
> **Deliver accurate, current, source-grounded answers and reason over actual in-game account/build data with zero hallucinations.**

Unlike generic LLMs that rely on imprecise memory or static web training data, GenshinIQ enforces a **structured data > LLM memory** paradigm. Game scalings, base stats, artifact substats, and player inventories are deterministically processed through canonical code providers before any context is passed to the Gemini LLM.

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Frontend Presentation Layer                         │
│   - Dark Celestial Glassmorphic Interface                                   │
│   - Enka CDN Asset Pipeline + Inline Vector Elemental Glyphs                │
│   - Character Showcase Carousel & Splash Art Hero Banners                   │
│   - Today's Domain Rotation & Farming Planner                               │
│   - Interactive Build Review Triggers (Direct Bridging to Chat)             │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ REST / JSON (HTTP)
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                            FastAPI Backend Router                           │
│   - /api/health                                                             │
│   - /api/account/{uid} (Showcase & character build lookups)                 │
│   - /api/data/{characters, weapons, artifacts, materials, search}           │
│   - /api/knowledge/{documents, search}                                      │
│   - /api/chat (Query understanding, context assembly, Gemini generation)    │
└──────────┬───────────────────────────┬───────────────────────────┬──────────┘
           │                           │                           │
┌──────────▼──────────┐     ┌──────────▼──────────┐     ┌──────────▼──────────┐
│   Account Service   │     │  Game Data Service  │     │  Knowledge Service  │
│ - Enka.Network API  │     │ - Canonical JSON DB │     │ - Curated KQM Guides│
│ - FightProp Mapper  │     │ - O(1) Memory Index │     │ - Mechanics Notes   │
│ - TTL Disk Caching  │     │ - Global Search     │     │ - Patch Notes Docs  │
│ - Profile Avatar Map│     │ - Stat Formulae     │     │ - Source Hierarchy  │
└──────────┬──────────┘     └──────────┬──────────┘     └──────────┬──────────┘
           │                           │                           │
           └───────────────────────────┼───────────────────────────┘
                                       │ Context Injection
                            ┌──────────▼──────────┐
                            │     RAG Service     │
                            │ - Intent Classifier │
                            │ - Context Packager  │
                            │ - Fail-Closed Rules │
                            │ - Citation Builder  │
                            └──────────┬──────────┘
                                       │
                            ┌──────────▼──────────┐
                            │    Gemini Service   │
                            │ - gemini-2.5-flash  │
                            │ - 30s Async Client  │
                            │ - Grounded Prompt   │
                            └─────────────────────┘
```

---

## 2. Phase 1: Live Account Integration & Enka.Network Normalizer

### 2.1 Enka API Integration & TTL Disk Caching
- **Endpoint**: `https://enka.network/api/uid/{uid}`.
- **Cache Architecture**: To prevent IP rate limiting and minimize latency, showcase responses are serialized to `data/runtime/showcases/{uid}.json` with an in-memory TTL check (default: 300 seconds).
- **Cache Bypass**: The frontend provides a dedicated **Bypass Cache** button triggering `/api/account/{uid}?refresh=true`.

### 2.1.1 Provenance Manifest
- **Endpoint**: `/api/data/manifest`.
- **Purpose**: Returns live hashes, record counts, and source/version summaries for canonical game data and curated knowledge documents.
- **Cache Location**: Runtime showcase cache is separated from committed fixtures under `data/runtime/showcases/`.

### 2.2 Player Profile Resolution
The player's profile is parsed from `playerInfo`:
- **UID, Nickname, Adventure Rank (AR), World Level (WL)**.
- **Spiral Abyss Record**: Normalizes `towerFloorIndex` and `towerLevelIndex` (e.g. `Floor 12-3`).
- **Profile Picture Avatar**: Extracts `playerInfo.profilePicture.avatarId` (e.g. `10000060`), resolves it through `CHARACTER_DATABASE` to the canonical character name (**Yelan**), and sets `avatar_icon` for CDN display.

### 2.3 Character Build & FightProp Normalization
Enka returns raw character stats inside a `fightPropMap` keyed by integer IDs. The normalizer resolves all standard combat attributes:
- Base HP (`1001`), Flat HP (`1002`), HP% (`1003`) $\to$ Max HP.
- Base ATK (`1004`), Flat ATK (`1005`), ATK% (`1006`) $\to$ Total ATK.
- Base DEF (`1007`), Flat DEF (`1008`), DEF% (`1009`) $\to$ Total DEF.
- CRIT Rate (`FIGHT_PROP_CRITICAL`), CRIT DMG (`FIGHT_PROP_CRITICAL_HURT`).
- Energy Recharge (`FIGHT_PROP_CHARGE_EFFICIENCY`), Elemental Mastery (`FIGHT_PROP_ELEMENT_MASTERY`).
- Elemental DMG Bonuses (Pyro, Hydro, Cryo, Electro, Anemo, Geo, Dendro, Physical).

### 2.4 Weapon & Artifact Set Resolution
- Weapons are resolved via canonical ID mapping or icon regex (`UI_EquipIcon_*`).
- Artifact pieces are mapped into 5 standard slots: **flower**, **plume**, **sands**, **goblet**, **circlet**. Main stats and rolled substats are normalized with roll counts and percentage flags.
- Artifact set bonuses (2-piece and 4-piece) are computed and displayed alongside pieces.

---

## 3. Phase 2: Canonical Structured Game Data

### 3.1 Datasets
Located in `data/processed/game_data/`:
1. `characters.json`: Detailed records for characters across all nations (Mondstadt, Liyue, Inazuma, Sumeru, Fontaine, Natlan) with elements, rarities, weapon types, base stats, talents, and ascension materials.
2. `weapons.json`: 1-star to 5-star weapons with base ATK scalings, secondary stats, and weapon passives.
3. `artifacts.json`: Canonical artifact sets with 2-piece and 4-piece set bonus descriptions.
4. `materials.json`: Talent books, weapon materials, and common ascension drops categorized by nation and domain rotation days.

### 3.2 In-Memory Indexing & Filtering
`GameDataService` loads all datasets during startup and constructs $O(1)$ dictionary lookups by `id` and lowercase `name`.
- Filter characters by element, rarity, and weapon type.
- Filter weapons by weapon type and rarity.
- Global search endpoint (`/api/data/search?q={query}`) queries across characters, weapons, artifact sets, and materials simultaneously.

---

## 4. Phase 3: Curated Knowledge Base

### 4.1 Document Schema & Source Hierarchy
All curated knowledge articles stored in `data/knowledge/` adhere to strict source categorization:
- **`AUTHORITATIVE`**: Official game mechanics, patch notes, in-game descriptions.
- **`THEORYCRAFTING`**: Peer-reviewed KeqingMains (KQM) guides, frame counts, rotation calculations, crowning recommendations.
- **`STATISTICAL`**: Spiral Abyss usage statistics and popular team compositions.

### 4.2 Seed Knowledge Base
- KQM character guides: Arlecchino, Furina, Raiden Shogun, Alhaitham, etc.
- Mechanics deep-dives: Elemental Gauge Theory, Internal Cooldown (ICD), Bond of Life, Natlan Nightsoul's Blessing & Phlogiston.
- Official version patch notes with release dates and banner schedules.

---

## 5. Phase 4 & 5: Grounded Gemini RAG Assistant

### 5.1 Intent Classification
Incoming messages are analyzed via regex and semantic intent classification:
- **`account`**: Triggered when the user asks about their own builds, weapons, artifact stats, or improvements (e.g. *"Is my Arlecchino build good?"*, *"Review my Skirk"*). The user's live showcase is retrieved and formatted as structured context.
- **`general`**: Triggered for general game mechanics, lore, or recommendations without account dependency (e.g. *"How does Bond of Life work?"*).

### 5.2 Dynamic Version Context
To prevent LLM staleness, the assistant calculates the current date and latest game version dynamically from patch note metadata and injects it into the system prompt:
```text
CURRENT GAME ENVIRONMENT:
- System Date: September 2026
- Latest Authoritative Game Version: Version 5.4 (or active patch)
```

### 5.3 Fail-Closed Guardrails
The system prompt strictly commands Gemini:
1. **Never guess or extrapolate missing account data**: If a character is not in the player's showcase, state clearly: *"That character is not in your current public showcase."*
2. **Deterministic arithmetic**: Rely exclusively on provided stat values; do not attempt mental calculations of artifact CV or stat totals.
3. **Source Citations**: Every claim or recommendation must cite specific knowledge articles or account data sources.

### 5.4 Timeout Resilience
`GeminiService` utilizes `httpx.AsyncClient` with a **30.0-second timeout** (and 10.0s connection timeout) to support large RAG prompt payloads and account builds.

---

## 6. Frontend UI & Interactive Enhancements

### 6.1 Design System Tokens (`style.css`)
- **Dark Celestial Theme**: Curated HSL colors (`--bg-body: #0a0d14`, `--accent-gold: #e9be74`, `--accent-cyan: #56e2d5`).
- **Glassmorphism**: Layered cards with frosted background blur (`backdrop-filter: blur(12px)`) and subtle glowing border states.
- **Typography**: Clean hierarchy utilizing Google Fonts **Outfit** for headers/body and **JetBrains Mono** for numerical stats.

### 6.2 Asset Pipeline
- **Enka CDN**: Dynamic image resolution for character portraits (`UI_AvatarIcon_*`), weapons (`UI_EquipIcon_*`), artifacts (`UI_RelicIcon_*`), and full gacha splash art banners (`UI_Gacha_AvatarImg_*`).
- **Inline SVG Elemental Glyphs**: Handcrafted SVG icons for all 7 elements (Pyro, Hydro, Anemo, Electro, Dendro, Cryo, Geo) to eliminate broken 404 network requests.
- **Cache-Busting**: Automated versioning strings (`?v=20260907_1630`) on stylesheet and script links.

### 6.3 Flagship Widgets & Interactivity
- **Today's Domain Rotation & Farming Planner**: Calculates today's day of the week, renders active talent book domains across all 6 nations, and highlights characters from the user's active showcase who can be farmed today.
- **Actionable Buttons**:
  - `✨ Ask AI to Review Build`: Direct bridge from character hero banner to chat assistant.
  - `📖 Theorycrafting Guide`: Direct bridge to character guide advice.
  - `[Ask Teams]`: Spiral Abyss badge shortcut.
  - `⚡ Optimize`: Equipped Artifacts card header action.

---

## 7. Testing & Quality Assurance

### 7.1 Pytest Test Suite
Executed via `.venv\Scripts\pytest backend/tests -v`:
- `test_health.py`: Health check status, environment variables, frontend static file serving.
- `test_enka_import.py`: Normalizer parsing, FightProp calculations, cache TTL, rate limit handling.
- `test_game_data.py`: Character/weapon/artifact lookups, filters, global search.
- `test_knowledge_base.py`: Document ingestion, source hierarchy, search relevance.
- `test_rag.py`: Query classification, prompt construction, dynamic date grounding, chat endpoint.
- **Result**: **33/33 tests passing (100% pass rate)**.

### 7.2 End-to-End Browser Subagent Verification
- Verified on live instance `http://127.0.0.1:8000/`.
- Tested showcase fetching for UID `817739968`.
- Verified player profile picture (Yelan), Skirk avatar (`UI_AvatarIcon_SkirkNew.png`), and Cryo element badge.
- Verified instant chat review generation with Gemini analyzing Mistsplitter Reforged, CRIT 73.8% / 225.0%, and talent priorities.
