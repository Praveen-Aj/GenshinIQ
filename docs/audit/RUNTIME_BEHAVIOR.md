# GenshinIQ — Runtime Behavior & Five-Tab Assessment

**Audit Date:** 2026-09-07  
**Testing Environment:** Headless Chrome Subagent on `http://127.0.0.1:8000/`  
**Recording Artifact:** `audit_five_tabs_1788789911579.webp`

---

## 1. Five-Tab Evaluation

### Tab 1: Chat Assistant (`#tab-btn-chat`)
- **Visual Presentation:**
  - Celestial glassmorphic dark theme, responsive layout.
  - Welcome greeting message with prompt chips:
    - *"Is my Arlecchino build good?"*
    - *"What weapon is best for Furina?"*
    - *"How does Bond of Life work?"*
- **Execution & Output:**
  - Tested *"How does Bond of Life work?"*.
  - Returned structured markdown explaining Bond of Life HP thresholds, Masque of the Red Death, weapon/character interactions (Arlecchino, Crimson Moon's Semblance), and an expandable `Sources Cited (3)` panel.
- **Architectural Gaps:**
  - Query classification is simple binary regex (`general` vs. `account`).
  - No deterministic calculation engine called (e.g. CV calculations, talent priority weighting, or DPS delta).
  - Citations are based on entire article summaries rather than claim-level evidence links.

### Tab 2: My Account (`#tab-btn-account`)
- **Visual Presentation:**
  - UID import bar pre-filled with default UID `817739968`.
  - Player profile overview card: nickname (`praveen`), Adventure Rank (`AR 60`), World Level (`WL 9`), Achievement count (`1,273`), Spiral Abyss (`Floor 12-3`), and player avatar.
  - 12-character showcase carousel: Mavuika, Arlecchino, Yelan, Neuvillette, Furina, Skirk, Citlali, Nefer, Shenhe, Zibai, Kaedehara Kazuha, Navia.
  - Active character detail pane: Level 90/90, C0/C6 badge, Friendship level, talent levels, equipped weapon, combat attributes grid, and artifact set bonuses with individual piece stats.
  - Daily Domain Farming Planner: Lists active domains for current day-of-week matching showcase characters.
- **Architectural Gaps:**
  - Domain farming rotation schedule is hardcoded directly inside `frontend/app.js` (`ROTATION_SCHEDULE`) rather than generated dynamically from canonical game data.
  - Character icons are resolved from a hardcoded JavaScript dictionary (`CHARACTER_ICONS`).
  - "My Account" is currently 100% synonymous with the Enka public showcase; does not distinguish between full account inventory, GOOD imports, or tracked roster.
  - Action buttons (`[Ask Teams]`, `⚡ Optimize`) merely prefill the chat input box with static query strings rather than calling dedicated calculation engines.

### Tab 3: Characters & Data (`#tab-btn-characters`)
- **Visual Presentation:**
  - Sub-tabs for `Characters`, `Weapons`, `Artifact Sets`.
  - Real-time search bar and elemental filter chips (Pyro, Hydro, Anemo, Electro, Dendro, Cryo, Geo).
  - Left column: item card grid with thumbnail icons, element badges, and star rarity.
  - Right column: inspector pane showing full details, base attributes, talent kit, constellations, and `✨ Ask AI Guide` button.
- **Architectural Gaps:**
  - Data layer contains 62 characters with placeholder base stats (`base_atk=250.0`, `base_hp=11000.0`, `ascension_stat="CRIT Rate" 19.2%`).
  - Weapons catalog contains 163 weapons with generic tier-based estimated base attacks and empty refinement progressions.
  - Materials tab is completely missing from the UI; only 6 materials exist in the backend.

### Tab 4: Guides & Mechanics (`#tab-btn-knowledge`)
- **Visual Presentation:**
  - Metric summary chips: 163 documents (149 Authoritative, 12 Theorycrafting, 8 Mechanics, 1 Patch Notes, v5.4).
  - Sub-tabs: `All Guides`, `Character Guides`, `Mechanics`, `Patch Notes`.
  - Left column: filterable list of articles with source badges (`KQM`, `AUTHORITATIVE`, `THEORYCRAFTING`).
  - Right column: rich markdown reader displaying full text, canonical URLs, and publication dates.
- **Architectural Gaps:**
  - Misclassification of source types: Community Fandom Wiki documents are tagged as `AUTHORITATIVE`.
  - Version filtering is purely string-based; no detection of stale documents when patches advance.
  - Documents are stored as giant monolithic JSON files rather than chunked semantic sections.

### Tab 5: System Health (`#tab-btn-diagnostics`)
- **Visual Presentation:**
  - Live cards displaying:
    - Manifest status (`Live manifest loaded`)
    - Cache directory (`data/runtime/showcases`)
    - Knowledge document count (163)
    - Game data index (88 characters, 181 weapons, 50 artifact sets)
    - Source mix breakdown
    - API status (HTTP 200, healthy)
    - Environment (`development`)
    - Enka target URL (`https://enka.network/api`)
  - Live `/api/health` JSON payload viewer with `Copy Snapshot` button.
- **Architectural Gaps:**
  - Lacks dataset validation health checks (duplicate record count, placeholder record count, invalid record count).
  - Lacks Knowledge Gap queue tracking.
  - Lacks latency, reachability, and rate-limit tracking for external APIs.
