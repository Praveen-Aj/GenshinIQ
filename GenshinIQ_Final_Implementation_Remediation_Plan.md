# GenshinIQ --- Final Implementation & Remediation Plan

**Document version:** 1.0\
**Date:** 2026-09-07\
**Project:** GenshinIQ --- Personal Genshin Impact AI Assistant\
**Target:** Rebuild the current implementation into a trustworthy,
current, extensible public-quality Genshin assistant.

------------------------------------------------------------------------

# 1. Executive Summary

GenshinIQ already has a strong product direction and a good visual
foundation:

1.  **Chat**
2.  **My Account**
3.  **Characters & Data**
4.  **Guides & Mechanics**
5.  **System Health**

The existing implementation also has the right broad architectural
separation:

-   FastAPI backend
-   Enka account integration
-   structured game data
-   curated knowledge
-   RAG/Gemini
-   frontend presentation

However, the audit shows that the implementation is not yet trustworthy
enough to call itself a current, canonical, source-grounded Genshin
assistant.

The main problems are not primarily UI problems. They are:

-   incorrect or placeholder structured data
-   duplicate/colliding IDs
-   incomplete material coverage
-   stale version metadata
-   misleading provenance
-   multiple competing data-generation paths
-   frontend hard-coded game knowledge
-   weak retrieval/version filtering
-   account/showcase semantics being mixed together
-   unsafe missing-value defaults
-   weak claim-level grounding
-   insufficient tests around correctness
-   documentation claiming stronger guarantees than the implementation
    currently provides

The existing project plan correctly established the principles of
structured data, source hierarchy, version awareness, account grounding,
testing, and phase-by-phase verification. This plan keeps those
principles but updates them based on the full project review and the
product decision that **Chat should be helpful to normal users rather
than routinely responding with an internal-looking "I don't have enough
information" message.**

The revised philosophy is:

> **GenshinIQ should always try to help. It should use the strongest
> available evidence first, combine deterministic game data with curated
> theorycrafting and approved external sources, reason over incomplete
> evidence when necessary, clearly distinguish verified facts from
> calculations/theorycrafting/AI analysis, and continuously identify
> knowledge gaps for developers to improve.**

------------------------------------------------------------------------

# 2. Product Definition

## 2.1 Primary objective

GenshinIQ is primarily an **AI assistant for Genshin Impact**, not
merely a database or showcase viewer.

The assistant should be substantially more useful than a generic LLM
because it has access to:

-   current Genshin game data
-   curated Genshin knowledge
-   theorycrafting
-   the user's imported account/build data
-   deterministic calculations
-   planning tools
-   eventually optimization/simulation

------------------------------------------------------------------------

# 2A. REFERENCE PROJECTS & ROLE SEPARATION

GenshinIQ must explicitly distinguish between data sources, knowledge
sources, account-data formats, and UX/architecture references.

## Primary Reference Projects

### 1. Genshin Track
- **URL**: https://genshintrack.com/dashboard
- **Role**:
  - Primary UX reference for **My Account**
  - Character progression and tracking
  - Farming planner
  - Material and domain schedule tracking
  - Account progress presentation
- **Constraints**:
  - Do not blindly copy its UI. Study its information architecture and interaction patterns.
  - Do not make Genshin Track a runtime dependency.

### 2. Genshin Optimizer (frzyc)
- **URL**: https://frzyc.github.io/genshin-optimizer/#/
- **Repository**: https://github.com/frzyc/genshin-optimizer
- **Role**:
  - Primary technical/functional reference for:
    - Character and weapon stats
    - Artifact inventory data structures
    - Build generation and representation
    - Build comparison
    - Artifact optimization
    - Optimization targets and objectives
    - Stat calculations and deterministic combat formulas
    - GOOD import/export interoperability
- **Constraints**:
  - Study its open-source architecture where useful.
  - Do NOT make Genshin Optimizer a runtime dependency. GenshinIQ must implement its own calculation and optimization services in backend Python code.
  - Do NOT copy numerical values from Genshin Optimizer without verifying their provenance and current version against canonical data sources.

### 3. GenshinOptimizer.com
- **URL**: https://www.genshinoptimizer.com/
- **Role**:
  - Secondary UX / reference implementation for GOOD inventory workflows
  - Artifact optimization workflow
  - Local-first inventory handling
- **Constraints**:
  - Do not make it a runtime dependency.

### 4. GOOD / Inventory Kamera (Account Inventory Interchange Format)
- **Standard**: Genshin Open Object Description (GOOD v3)
- **Role**:
  - Account inventory interchange format, NOT a canonical game data source or knowledge source.
  - Inventory Kamera produces GOOD v3 JSON exports containing:
    - Characters (level, ascension, constellation, talent levels)
    - Weapons (level, ascension, refinement, lock status, location)
    - Artifacts (set, slot, level, rarity, main stat, substats, lock status, location)
    - Materials (inventory counts)
- **Account Inventory Architecture**:
  ``` text
  GOOD v3 export (Inventory Kamera)
        |
        v
  GOOD parser & schema validation
        |
        v
  Canonical ID & alias resolution
        |
        v
  GenshinIQ account inventory model
        |
        v
  Calculators / Build Engine / Artifact Optimizer / Farming Planner / Chat
  ```
- **Crucial Rule on Inventory Instances vs. Canonical Records**:
  - **Do NOT merge GOOD inventory records into canonical game-data JSON.**
  - Multiple weapon or artifact instances with the same underlying item identity (for example, three separate copies of the weapon "Rust", or five "Noblesse Oblige" Flowers with different substats) are **legitimate account inventory instances**.
  - They must **NEVER** be treated as canonical-data duplicate corruption or deduped away.

------------------------------------------------------------------------

# 2B. MANDATORY BEST-IN-CLASS GENSHIN UX / UI ARCHITECTURE & DESIGN SYSTEM

> [!IMPORTANT]
> **MANDATORY DESIGN RULE & BINDING CLAUSE — NOT AN OPTIONAL SUGGESTION**:
> Future implementation MUST follow this UX/UI architecture and release-gate strategy. These requirements are binding and must not be omitted when the corresponding phases are implemented.
> 
> Future UI implementation across GenshinIQ MUST adhere to the UX patterns, visual hierarchy, information density, and asset pipelines defined below.
> The current text-heavy presentation with large blocks of prose is unacceptable for future production UI.
> **DO NOT IMPLEMENT NOW**: These requirements are recorded permanently in this plan to govern Phase 11, Phase 12, Phase 13, Phase 14, Phase 15, and all future UI surfaces. Continue the current work exactly where you are.

### 2B.1 Do Not Design From Scratch When Proven UX Exists (Adopt Proven Patterns)

GenshinIQ must **NOT** invent its entire UX/UI architecture from scratch.
When the relevant UI phases are eventually implemented, study established Genshin tools/sites and **ADAPT** their proven information architecture, interaction patterns, information density, comparison workflows, navigation patterns, and visual hierarchy.

The goal is **NOT** to blindly copy another site's UI, proprietary source code, backend implementations, branding, logos, copyrighted artwork, or reproduce another site's exact page design.
Instead, follow this rigorous design methodology:
$$\text{Study proven UX patterns} \longrightarrow \text{understand why they work} \longrightarrow \text{adapt underlying IA/interaction} \longrightarrow \text{implement original GenshinIQ design system}$$

**The Core Goal**:
$$\mathbf{Familiar\ and\ proven\ Genshin\ UX\ patterns} + \mathbf{original\ GenshinIQ\ implementation} + \mathbf{personalization}$$

Adopt and adapt proven:
- Information architecture (IA) and high-density progression tracking
- Layout patterns and screen compositions
- Visual hierarchy and scannability
- Component concepts (stat cards, talent grids, material deficit counters)
- Information density and cognitive load management
- Navigation and sub-navigation patterns
- Build and gear comparison workflows
- Card and badge structures
- Filtering, sorting, and tag-based discovery
- Inventory and equipment presentation
- Team composition and synergy visualization
- Farming schedules and progression tracking
- Deterministic build optimization workflows

### 2B.2 Primary UX References & Role Distribution

1. **Genshin Track (https://genshintrack.com/dashboard)**:
   - **Role**: Reference for high-density progression tracking, farming/material tracking, character progression presentation, resource visibility, scannable build presentation, weapon rankings, artifact recommendations, team synergies, character splash artwork, entity icons, highlighted key stats, concise summaries, priority indicators, structured expandable drawers, and high-density dashboards.
2. **Genshin Optimizer (frzyc & genshinoptimizer.com)**:
   - **Role**: Reference for inventory-oriented workflows, artifact inventory grids, build comparison, stat deltas, filtering and optimization workflows, artifact/weapon equipment grids, side-by-side comparison workflows, multidimensional filtering/sorting, account-specific recommendations, and optimization-oriented information architecture.
3. **Genshin Wiki & Official Reference Databases**:
   - **Role**: Reference for structured entity presentation, character/weapon/artifact information architecture, canonical game-data presentation, comprehensive factual accuracy, structured entity definitions, scaling tables, and detailed reference sections.
4. **KeqingMains (KQM) & Premier Theorycrafting**:
   - **Role**: Reference for structured theorycrafting, ER breakpoints, rotation presentation, build recommendations, clear priority hierarchy, rotation rationale, weapon/artifact ranking context, and clean separation between factual game rules and theorycrafting recommendations.
5. **Other Established Genshin Tools**:
   - May also be studied and synthesized when useful for specific interactions.

GenshinIQ must synthesize these strengths into a unified, dark celestial glassmorphic interface rather than copying any single site.

### 2B.3 Hard Anti-Text-Wall Requirement

Future UI implementations **MUST NOT** present major Genshin information primarily as large blocks of prose.
This applies especially to:
- Character builds
- Weapons
- Artifacts
- Teams
- Farming
- Materials
- Progression
- Theorycrafting
- Optimization results
- AI recommendations

**Prefer Visual, Scannable Components**:
- **Cards** (Entity cards, stat cards, build cards)
- **Tables** (ER breakpoints, talent scalings, ascension costs)
- **Stat blocks** (Numerical attributes with scaling attributes)
- **Icons** (Characters, weapons, artifacts, materials, elements, weapon types)
- **Badges and Pills** (Roles, rarities, tiers, recommendation status, priority sequence)
- **Progress bars** (Ascension progress, talent completion)
- **Comparison panels** (Side-by-side equipped vs candidate)
- **Expandable sections / Drawers** (Detailed mechanics, full lore, lengthy calculations)
- **Visual hierarchy** (Clear section boundaries, consistent spacing)
- **Compact structured summaries** (1–2 punchy sentences highlighting role and primary mechanic)

Long-form explanatory text can exist, but it **MUST support the structured UI rather than replace it**.
**User Expectation**: A user must be able to understand the core value, build, requirements, and next steps within 5 seconds of scanning the page without reading multiple paragraphs of text.

### 2B.4 Visual Asset Pipeline & Data-Sync Mapping Strategy

For future UI phases, plan for proper visual Genshin assets wherever useful:
- Character portraits
- Character splash artwork where appropriate
- Element icons/SVGs
- Weapon-type icons/SVGs
- Weapon icons
- Artifact icons
- Artifact-set icons
- Material icons
- Rarity indicators (3★ / 4★ / 5★ color codings and star badges)
- Domain/activity badges
- Role indicators (`Main DPS`, `Sub DPS`, `Support`, `Sustain`)

**Zero Placeholder Rule**: Do NOT use generic placeholder blocks where actual game-data-driven visual representation is expected.
**Asset/Data Mapping Strategy**: The implementation must maintain a strict asset/data mapping layer (e.g. mapping canonical IDs and names to verified Enka CDN asset paths, local cached assets, and local SVG fallbacks) so visual assets remain synchronized with canonical game data.

### 2B.5 Standard Character Page Architecture (10-Section Structure)

When the Characters & Data UI is eventually rebuilt in Phase 11, it must follow this mandatory architecture:

1. **Character Header**: Splash banner/portrait, name, rarity stars, element & weapon SVG badges, region, release version badge.
2. **Quick Summary**: Concise role statement (1–2 sentences), visual strength chips, caveat chips.
3. **Your Character / Account State**: Owned vs unowned status, current Level & Ascension, Constellation badge, equipped weapon & refinement, talent levels, and action triggers (`[Ask AI to Review Build]`, `[Optimize Artifacts]`, `[Farming Plan]`).
4. **Base Stats**: Visual stat grid (HP, ATK, DEF, Ascension Stat) with level slider (`Lv. 1`–`Lv. 90`).
5. **Talents**: Visual card per talent, compact scaling summaries, expandable mechanics drawer, talent leveling priority badge (`Burst > Skill >> NA`).
6. **Constellations**: C1–C6 icon grid, active indicator for user's owned constellation, milestone callouts (e.g. `★ C4`), expandable descriptions.
7. **Build**: Ranked weapon cards (`BIS`, `F2P`), ranked artifact set cards, main-stat callouts, substat priority pills, target stat benchmark cards.
8. **Teams**: Visual 4-slot team cards with character portraits, roles, synergy chips, ownership indicators, and visual rotation sequence chips.
9. **Farming / Materials**: Category-grouped material requirement cards, owned vs required counts, deficit indicators, daily domain schedule.
10. **AI Analysis**: Grounded account-aware synthesis bridging game data with user's specific account; actionable next steps.

*Account-specific sections must clearly distinguish the user's actual character state from generic canonical information.*

### 2B.6 GenshinIQ's Core Differentiator (Personalized Recommendations)

The future UI and feature architecture must consistently reflect:
$$\mathbf{Public\ Knowledge} + \mathbf{Canonical\ Game\ Data} + \mathbf{User\ Account\ Data} + \mathbf{User\ Inventory} + \mathbf{Deterministic\ Calculation\ Engine} + \mathbf{AI\ Reasoning} = \mathbf{PERSONALIZED\ RECOMMENDATION}$$

Do NOT build GenshinIQ as merely another static Genshin database/wiki.
Whenever appropriate, the UI should make the distinction between:
- **General recommendation** (canonical / theorycrafting consensus)
- **Recommendation based on the user's account** (roster, character levels, constellations)
- **Recommendation based on the user's inventory** (owned weapons, owned artifacts, owned materials)
- **Deterministically calculated result** (mathematical stat calculations, damage formulas, deficit subtraction)
- **AI interpretation** (Gemini synthesis of trade-offs, gameplay feel, rotation nuances)
visible to the user via distinct visual badges, callouts, and comparative cards.

**Concrete Example**:
- **Generic Website**: *"Favonius Greatsword is a recommended weapon for Aino."*
- **GenshinIQ Personalized Presentation**:
  - *"Favonius Greatsword — Recommended for YOUR Aino"*
  - **Owned Status**: Owned at `R3`, `Lv. 80/80` (currently unequipped in inventory)
  - **Current Equipped**: `The Bell (Lv. 70/70, R1)`
  - **Reasoning**: Switching to Favonius fixes Aino's 180% ER requirement, enabling an ATK% Sands instead of ER Sands (+14.2% overall team output).
  - **Delta Callout**: `+61.3% Energy Recharge`, generates 6 white energy particles on CRIT every 9s.
  - **Actionable Next Steps**: `[Equip Favonius Greatsword]`, `[Ascend to Lv. 90/90 (Deficit: 4 Dvalin's Plume)]`.

### 2B.7 Information Density & Cognitive Load Requirement

Future UI must strictly optimize for:
- High scannability and visual hierarchy
- Low cognitive load through visual grouping and color coding
- Minimal unnecessary scrolling through compact cards and expandable drawers
- Instant decision-making via color-coded badges and priority indicators
- Presentation of structured database entities as structured visual components, NEVER as prose paragraphs

### 2B.8 Scope of Future Phases Governed by This Requirement

This UX requirement is permanently binding for:
- **Phase 11**: Characters & Data Tab Rebuild (Global Encyclopedia)
- **Phase 12**: Guides Tab Rebuild (Character Build Presentation)
- **Phase 13**: Farming & Character Tracking (Personal Progression)
- **Phase 14**: Team Building Engine (Synergy & Composition UI)
- **Phase 15**: Artifact Optimization (Inventory & Deterministic Build UI)
- All future UI surfaces, modal drawers, and build review callouts.

### 2B.9 Universal Visual Acceptance Gate (14-Point Inspection Gate)

For future UI phases, automated tests are **NOT** sufficient.
A UI phase **MUST NOT** be declared complete merely because HTTP 200 works, API tests pass, Python tests pass, or JavaScript has no errors.
Completion requires all 14 of the following criteria:
1. **Automated tests pass**: All unit and integration tests pass without regression.
2. **Backend/API validation passes**: All API contracts, payload schemas, and data structures validate.
3. **No relevant browser console errors**: Zero runtime exceptions, unhandled rejections, or script errors.
4. **Live browser inspection**: Captured and reviewed via automated browser tooling and interactive verification.
5. **Visual comparison against planned UX architecture**: Adheres to the planned layout, card structures, and components.
6. **Verification of information hierarchy**: Clear typography, scannable titles, distinct visual boundaries, and no clutter.
7. **Verification of responsive layout**: Elements render cleanly across standard desktop and mobile viewports.
8. **Verification of visual asset rendering**: Character portraits, splash banners, element SVGs, weapon SVGs, and material icons render crisply with zero 404 broken links.
9. **Verification of account personalization**: User's owned characters, equipped weapons, artifact inventory, and material counts are visibly integrated.
10. **Verification of loading/empty/error states**: Skeleton loaders, informative empty state badges, and fail-closed error boundaries function smoothly.
11. **Verification of filters and interactions**: Search inputs, sort chips, category dropdowns, and drawer toggles respond instantaneously.
12. **Verification of comparison workflows**: Side-by-side equipped vs candidate comparisons and stat delta pills display accurately.
13. **Verification that the UI is not a text wall**: Zero unformatted prose walls; dense information is presented as cards, tables, pills, and expandable drawers.
14. **Verification that the UI resembles a polished production Genshin application**: Matches or exceeds UX benchmarks set by Genshin Track and Genshin Optimizer rather than looking like an internal developer prototype.

### 2B.10 Clean Product Principle: Expose Outcomes, Not Implementation

> [!IMPORTANT]
> **PERMANENT DESIGN PRINCIPLE — NO DATA-SOURCE CLUTTER IN PRODUCTION**:
> **"GenshinIQ should expose outcomes, not implementation."**
> The user should experience: *"What should I do?"* rather than *"Which database / source / pipeline produced this?"*
> 
> - **BAD Production UI**: *"Recommended according to KQM TCL + Genshin Optimizer + community source T5."*
> - **GOOD Production UI**: Clean **"Recommended Build"** displaying the actual weapon, artifacts, stats, ER target, rotation chips, clear gameplay reasoning, and account-specific comparison deltas.
> The engineering complexity must exist underneath the product, never cluttering the user's experience.

#### Prohibition on Exposing Data Sources in Production UI
During development, internal source information is visible for debugging and verification.
In the **production / end-user UI**, GenshinIQ **MUST NOT** expose where its knowledge or recommendations originated. Specifically, do NOT display:
- `"Source: KeqingMains"`, `"Source: KQM"`, `"Source: TCL"`
- `"Source: Genshin Optimizer"`, `"Source: Genshin Wiki"`, `"Source: Honey Hunter"`, `"Source: Reddit"`, `"Source: Genshin Track"`
- Internal source registry names, source IDs, or tier/source classifications (`Tier 1 Official`, `Tier 2 Curated`, `Tier 5 Community`)
- Internal provenance labels, retrieval metadata, or evidence classifications
- This rule applies universally across: Chat, Character pages, Weapons, Artifacts, Guides, Teams, Farming, Artifact optimization, Account pages, Recommendations, AI responses, Tooltips, Cards, Comparison views, Empty states, Error states, Footer, and About/Settings pages.

#### Exception & Consistency Rule for HoYoverse
Official HoYoverse / Genshin Impact notices and game version context can be acknowledged when there is a legitimate user-facing reason to do so (e.g. *"Patch 7.0 Notes"* or game version release markers).
However, the default production experience must NOT expose a detailed source list or provenance dashboard. If external attribution is legally or technically required, handle it strictly in a dedicated, minimal attribution/legal section rather than cluttering product cards.

#### Internal Provenance vs. User-Facing UX Architecture
Make this architectural distinction absolute:
- **INTERNAL LAYER**: Full provenance, source registry, source authority tiers, evidence types, retrieval timestamps, dataset versions, freshness models, conflict logs, confidence scores, validation gates, and internal diagnostics.
- **USER-FACING LAYER**: Clean information, high-density visual cards, actionable recommendations, relevant gameplay explanations, game/version context, and account-grounded state.
*Do NOT remove provenance from backend architecture — keep it rigorous for correctness, auditing, freshness, and trust; keep the frontend consumer-clean.*

### 2B.11 Development Mode vs. Production Mode Architecture

The product must formally distinguish between two operational modes:

| Feature / UI Surface | Development / Internal Mode (`DEBUG=true`) | Production / Release Mode (`DEBUG=false`) |
| :--- | :--- | :--- |
| **System Diagnostics** | System Health tab fully visible with raw diagnostics | Replaced by clean, user-facing **Settings / About** tab |
| **Source Registry** | Source hierarchy, URLs, tiers, & sync state visible | Completely hidden from consumer views |
| **Provenance Badges** | Full provenance, tier badges, and document counts | Replaced by clean recommendation badges (`BIS`, `F2P`) |
| **Chat Routing** | Query intent, router metadata, & evidence types visible | Clean answers with visual cards and relevant calculations |
| **Release Gates** | Hard-gate status, blocker breakdowns, & test controls | Hidden (automated in CI/CD pipeline) |
| **Raw JSON / Debug** | Inspectable payloads and raw evaluation JSON | Zero raw JSON or internal debug terminology |

This distinction must be enforced programmatically via environment configuration rather than manual developer edits prior to release.

### 2B.12 Tab-by-Tab Production Cleanliness Standard

All future UI implementations must enforce this cleanliness standard:
1. **Chat UI**: Clean answers, structured stat cards, actionable advice, and collapsible AI reasoning. Zero router debug badges or evidence tier pills.
2. **Character Detail View**: Build recommendations, stats, talents, constellations, teams, farming, and AI analysis. Zero KQM/TCL labels or source tiers.
3. **Guides Tab**: Scannable build cards, ranked weapon cards, ER breakpoint tables, and `"Recommended Weapon"` vs `"What You Currently Own"`. Zero citation dashboards.
4. **Team Builder**: 4-slot visual composition cards, rotation chips, synergy bullets, and substitute suggestions. Zero pipeline provenance tags.
5. **Farming & Progression**: Material deficit counters, today's domain schedule, and resin plans. Zero exposure of internal knowledge source files.
6. **Artifact Optimizer**: Side-by-side equipped vs candidate comparisons with stat delta visualization (`+18.2% CRIT DMG`). Zero candidate-generation source tags.

> [!NOTE]
> Future implementation MUST follow this UX/UI architecture and release-gate strategy. These requirements are binding and must not be omitted when the corresponding phases are implemented.

------------------------------------------------------------------------

# 3. The Five Main Tabs

These five tabs remain the permanent top-level product structure.

## 3.1 Chat

The primary intelligence interface.

It should answer:

-   Genshin facts
-   mechanics questions
-   build questions
-   weapon comparisons
-   artifact recommendations
-   team-building questions
-   farming questions
-   account-specific questions
-   upgrade priorities
-   current-version questions

Chat should not simply send every question to Gemini.

It should first determine what information/tools are required.

Conceptually:

``` text
User Question
      |
      v
Intent + Entity Detection
      |
      v
Evidence / Tool Planner
      |
      +-------------------+
      |                   |
      v                   v
Account Data          Global Game Data
      |                   |
      +---------+---------+
                |
                v
         Knowledge Retrieval
                |
                v
      Deterministic Calculations
          (when required)
                |
                v
             Gemini
                |
                v
       Answer Quality / Grounding
          + Citation Assembly
                |
                v
              User
```

------------------------------------------------------------------------

## 3.2 My Account

This tab should represent the user's personal Genshin data.

Important terminology change:

### Current implementation

The existing Enka integration is primarily a **public showcase import**.

### Desired product

"My Account" should eventually mean the user's broader personal game
data.

Therefore the UI should clearly distinguish:

-   **Showcase data**
-   **Imported account data**
-   **Tracked/provided data**
-   **Unknown/unavailable data**

Do not claim that an Enka showcase is the complete account roster.

Initial account sources:

1.  Enka public showcase
2.  GOOD import
3.  manual tracking/import where appropriate

Future integrations can expand this.

------------------------------------------------------------------------

## 3.3 Characters & Data

This is the global Genshin encyclopedia.

It should contain both owned and non-owned entities.

Recommended sections:

-   Characters
-   Weapons
-   Artifact Sets
-   Materials
-   Talents
-   Constellations
-   Enemies
-   Reactions
-   Mechanics
-   Domains
-   Regions
-   Farming information

This tab must always read from the canonical backend data layer.

The frontend must never invent or independently maintain canonical
Genshin values.

------------------------------------------------------------------------

## 3.4 Guides & Mechanics

This is the curated knowledge library.

Recommended categories:

-   Character Guides
-   Build Guides
-   Theorycrafting
-   Mechanics
-   Reactions
-   Teams
-   Farming
-   Patch Notes
-   Abyss
-   Source Browser

Every document should expose useful provenance:

-   source
-   source type
-   version
-   published date
-   updated date
-   canonical URL
-   retrieval date

------------------------------------------------------------------------

## 3.5 System Health

This should become a real trust/operations dashboard.

It should show:

### Application

-   API status
-   version
-   environment
-   response latency

### Game Data

-   current version
-   last successful sync
-   dataset age
-   record counts
-   duplicate count
-   invalid record count
-   placeholder count

### Knowledge

-   document count
-   source count
-   current-version coverage
-   stale document count
-   provenance validation

### Enka

-   reachability
-   cache state
-   last successful fetch
-   last error
-   rate-limit status

### Gemini

-   configured/not configured
-   last request
-   request latency
-   error rate

### RAG

-   retrieval latency
-   evidence count
-   source diversity
-   version match
-   grounding status

### Release-Gate & Version Completeness (Core Design Principle)

The System Health tab houses the **Version-Complete Release Gate**.
- **Principle: Truthful Dashboard > Green Dashboard**: The System Health / Release Gate must represent actual system readiness. Do NOT optimize for "make the dashboard green"; optimize for "make the dashboard truthful".
- **Deterministic & Explainable**: Every completeness percentage, denominator, and blocker count must be derived from deterministic, explainable rules.
- **True Incompleteness vs. Classification Errors**: If something is genuinely incomplete, it must remain incomplete. If something is incorrectly classified as incomplete, the underlying classification/data logic must be fixed in Phase 18, never artificially bypassed.
- **Actionable Explainability**: For any incomplete gate, the UI must explain:
  - What is missing
  - Why it is missing
  - Whether it is actually required for the active game version
  - Which source/version established the requirement
  - What action is needed to resolve it

### Development-Only Classification & Production "Settings / App Status" Replacement

> [!IMPORTANT]
> **DEVELOPMENT-ONLY / INTERNAL INTERFACE MANDATE**:
> The System Health tab and its diagnostic cards are intended **ONLY for development, debugging, verification, and internal testing**.
> 
> The following information must **NEVER** be exposed to normal end users in the production release UI:
> - Raw health diagnostics and internal API status details
> - Backend server timestamps and internal environment variables
> - Internal dataset sync state and internal cache filepaths
> - Internal source registry, tier rankings, and authority hierarchy
> - Internal provenance labels, document counts, and pipeline states
> - Release-gate completeness percentages, blocker breakdowns, and developer test triggers
> - Raw JSON debug payloads and internal error stack traces
> 
> **Production Release Strategy (Option B — Consumer Settings / About)**:
> In production (`DEBUG=false`), the 5th tab MUST NOT display an engineering dashboard. It must be replaced with a clean consumer-facing **Settings / About / App Status** interface:
> 1. **GENERAL**: Theme/appearance toggle, compact vs comfortable display density, default landing tab selector, animation speed, and reduced-motion accessibility preference.
> 2. **ACCOUNT**: Connected UID management, manual "Refresh Showcase" button, last sync timestamp, and "Clear / Disconnect UID" option.
> 3. **AI PREFERENCES**: Response detail level (concise vs detailed), explanation verbosity, confirmation dialogs for intensive recalculations, and "Reset Chat Preferences".
> 4. **GAME CONTEXT**: Current game version badge in clean consumer formatting (e.g., `Genshin Impact v7.0 Ready`), server/region selector, and resin cap preferences.
> 5. **PRIVACY & DATA**: Clear summary of what data is stored locally (cached showcase & GOOD inventory), "Clear Cached Artifacts", and "Reset Local Storage".
> 6. **ABOUT**: GenshinIQ version, build notes, and minimal required legal/attribution disclosures.
> 
> **Core Principle**: *"Useful to the player" $\neq$ "Useful to the developer."* The production UI must never look like an engineering diagnostic tool.

The System Health tab (in development mode) helps the developer answer:

> "Can I trust what GenshinIQ is currently telling users?"

------------------------------------------------------------------------

# 4. Core Architectural Principles

## Principle 1 --- Structured data beats LLM memory

Exact game facts must come from structured data whenever possible.

Examples:

-   base stats
-   talent scaling
-   weapon stats
-   artifact bonuses
-   material requirements
-   character elements
-   weapon types

Gemini should explain these facts, not invent them.

------------------------------------------------------------------------

## Principle 2 --- Deterministic calculations beat LLM arithmetic

If a value can be calculated reliably in code, calculate it in code.

Examples:

-   artifact CV
-   stat totals
-   upgrade deltas
-   material totals
-   farming requirements
-   damage formulas
-   ER calculations
-   comparison scores

Gemini should explain the calculation.

------------------------------------------------------------------------

## Principle 3 --- Source hierarchy matters

Not every source has equal authority.

Suggested hierarchy:

``` text
TIER 1
Official HoYoverse information

TIER 2
Curated theorycrafting
KQM Guides / KQM TCL

TIER 3
Maintained structured game data
Project Amber / Ambr
genshin.dev / genshin-db or equivalent
Genshin Optimizer extracted data where appropriate

TIER 4
Statistical resources
Akasha and similar resources

TIER 5
Community sources
Forums / Reddit / community discussions
```

A source's tier should affect how the answer is worded and how conflicts
are resolved.

------------------------------------------------------------------------

## Principle 4 --- Version is a first-class property

Every current-sensitive fact should be associated with a game version
where possible.

Do not infer:

> "highest version found in local files = current live version"

Instead maintain a validated current-version state.

------------------------------------------------------------------------

## Principle 5 --- Account data, global game knowledge, and inventory instances remain separate

These are fundamentally different domains:

``` text
CANONICAL GAME DATA
What is universally true about Genshin Impact?
(Base stats, growth curves, materials, weapon definitions, artifact set rules)

ACCOUNT INVENTORY DATA (GOOD / Inventory Kamera)
What does this specific user actually own across their whole account?
(All owned characters, weapons, artifacts, inventory materials, lock states)

PUBLIC SHOWCASE DATA (Enka.Network)
What builds does this user currently expose on their in-game public showcase?
(Up to 8–12 showcase characters and their currently equipped gear)

MANUAL USER DATA
What custom targets, priorities, notes, or overrides has the user specified?

KNOWLEDGE & THEORYCRAFTING
What vetted guidance, rotations, mechanics, and guides exist?
```

Chat and planning services can combine them, but the underlying data
models must remain strictly separate.

### Critical Rule on Inventory Instances vs. Canonical Records

**Do not confuse duplicate inventory instances with duplicate canonical data.**

For example, a user's GOOD export may legitimately contain multiple copies of the same weapon:

``` text
Canonical database:
  Rust ID = "weapon_rust" (exactly one canonical entry with base stats & curves)
        |
        v
Account inventory:
  Rust instance #1 (Lv. 90, R5, equipped on Yoimiya)
  Rust instance #2 (Lv. 1, R1, unequipped, locked)
  Rust instance #3 (Lv. 1, R1, unequipped, unlocked)
```

Multiple weapon or artifact records sharing the same underlying item identity in an account inventory are valid, intentional, and expected. They must **never** be treated as canonical database corruption or duplicate-ID violations.

------------------------------------------------------------------------

## Principle 6 --- Missing data must never become fake data

Never replace unknown data with plausible-looking numbers.

Bad:

``` text
unknown base ATK -> 250
unknown element -> Pyro
unknown artifact roll count -> 1
```

Correct:

``` text
unknown -> null/unavailable/quarantined
```

or fail the dataset build when the field is required.

------------------------------------------------------------------------

# 5. Chat Philosophy --- Important Product Change

## 5.1 Do not make "I don't have enough information" the normal user experience

For a public application, a technical RAG failure should not be exposed
as the user's problem.

The user asks:

> "What's the best weapon for my character?"

They expect GenshinIQ to help.

Therefore the system should use a **knowledge escalation strategy**.

------------------------------------------------------------------------

## 5.2 Knowledge escalation

``` text
Question
   |
   v
Canonical structured data
   |
   v
Curated knowledge
   |
   v
Official sources
   |
   v
KQM / TCL
   |
   v
Approved secondary structured sources
   |
   v
Statistical sources
   |
   v
AI synthesis / inference
   |
   v
Best useful answer
```

The exact ordering can vary by question.

For example, exact weapon stats should prioritize structured data, while
a build recommendation should prioritize theorycrafting and
account-specific calculations.

------------------------------------------------------------------------

## 5.3 Three answer confidence classes

### A. Verified

Strong evidence directly supports the claim.

Examples:

-   exact base stat
-   exact talent scaling
-   official patch change

UI label:

**Verified**

------------------------------------------------------------------------

### B. Calculated / Theorycrafted

The result is derived from data and/or accepted theorycrafting.

Examples:

-   recommended weapon for the user's build
-   artifact stat priority
-   ER target
-   team recommendation

UI label:

**Calculated** or **Theorycrafting**

------------------------------------------------------------------------

### C. AI Analysis / Inference

The model is synthesizing available evidence where the conclusion is not
directly stated by a source.

UI label:

**AI Analysis**

The assistant should explain the basis and avoid presenting inference as
an official fact.

------------------------------------------------------------------------

## 5.4 Genuine knowledge gaps

If no useful answer can be established, the system should still avoid
silently hallucinating.

But the public-facing response should be helpful.

Preferred pattern:

> "I couldn't verify that specific interaction from the sources
> currently available. I don't want to present a guess as a confirmed
> mechanic. I can still give you the most likely explanation based on
> the available game data and theorycrafting."

Internally, the system records:

``` text
Knowledge Gap
- question
- missing topic
- missing source type
- attempted retrievals
- version
- date
```

The developer can then add knowledge.

This turns missing information into an engineering task rather than a
dead end for users.

------------------------------------------------------------------------

# 6. Do Not Fine-Tune Gemini as the Primary Knowledge Strategy

Do not try to solve changing Genshin knowledge by "training the AI
more."

Genshin changes too frequently.

Fine-tuning would become stale.

Instead:

``` text
Gemini
+
current structured data
+
current knowledge
+
current theorycrafting
+
calculators
+
account tools
```

The model remains the reasoning/explanation layer.

The knowledge system remains updateable independently.

------------------------------------------------------------------------

# 7. External Source Strategy

The following sources should be evaluated and integrated according to
their role, not all scraped indiscriminately.

## 7.1 Genshin Track

Primary UX reference for:

-   My Account progression presentation
-   character tracking UX
-   farming planner UX
-   tracked character requirements
-   guide organization
-   daily farming and domain schedule presentation

URL:

https://genshintrack.com/dashboard

Genshin Track explicitly focuses on telling users what to farm today and
what tracked characters still require. It also states that its guides
are maintained manually each patch.

GenshinIQ should learn from its information architecture and interaction
patterns, not copy the implementation. Genshin Track is a design reference,
NOT a runtime dependency.

------------------------------------------------------------------------

## 7.2 Official HoYoverse / HoYoLAB

Use for:

-   patch notes
-   official system changes
-   official character announcements
-   official mechanic descriptions
-   official version information

This is the highest-priority source for official facts.

------------------------------------------------------------------------

## 7.3 KQM Guides

Use for:

-   character builds
-   weapon recommendations
-   artifact recommendations
-   team recommendations
-   rotations
-   practical theorycrafting

URL:

https://keqingmains.com/

KQM currently publishes Version 7.0 material and continues updating
guides, including current character guides.

------------------------------------------------------------------------

## 7.4 KQM Theorycrafting Library (TCL)

Use for:

-   advanced mechanics
-   gauge theory
-   ICD
-   frame data
-   enemy mechanics
-   evidence-backed theorycrafting
-   niche interactions

URL:

https://library.keqingmains.com/

The TCL states that submitted information is vetted by KQM
Theorycrafting Editors and that pages have corresponding evidence
resources.

This should be one of GenshinIQ's highest-value theorycrafting sources.

------------------------------------------------------------------------

## 7.5 Project Amber / Ambr

Use as a maintained structured reference/cross-check for:

-   characters
-   weapons
-   stats
-   talents
-   materials
-   item progression

URL:

https://ambr.top/

It is especially useful for cross-checking structured records.

------------------------------------------------------------------------

## 7.6 genshin.dev / genshin-db ecosystem

Use as a structured data provider candidate.

The genshin.dev API provides static structured game data and exposes
entity endpoints.

URL:

https://github.com/genshindev/api

Current API:

https://genshin.jmp.blue/

Do not blindly treat it as authoritative. Treat it as a structured
provider and validate important data.

------------------------------------------------------------------------

## 7.7 Genshin Optimizer (frzyc)

Primary technical and functional reference for:

-   stat calculation architecture
-   combat formulas and stat scaling curves
-   build representation and comparison
-   artifact inventory data structures
-   artifact optimization algorithms and pruning
-   optimization targets and constraints
-   GOOD import/export interoperability

URL:

https://frzyc.github.io/genshin-optimizer/#/

Repository:

https://github.com/frzyc/genshin-optimizer

**Role and Boundaries**:
- Genshin Optimizer is a **reference project**, NOT a runtime dependency.
- GenshinIQ must implement its own backend calculation and optimization services in Python.
- Do NOT copy numerical game values from Genshin Optimizer without verifying their provenance and current version against canonical data sources.
- Gemini should explain calculated results, but deterministic arithmetic must be performed by code.

------------------------------------------------------------------------

## 7.7A GenshinOptimizer.com

Secondary UX and reference implementation for:

-   GOOD import workflow
-   simple artifact optimization UX
-   local-first inventory handling

URL:

https://www.genshinoptimizer.com/

This is an architectural reference, NOT a runtime dependency.

------------------------------------------------------------------------

## 7.7B GOOD / Inventory Kamera (Account Inventory Format)

Account inventory interchange format, NOT a canonical game data source
or knowledge source.

Inventory Kamera can produce GOOD v3 exports containing:

-   characters
-   weapons
-   artifacts
-   materials

**Crucial Boundaries**:
- GOOD data represents the user's personal inventory and must remain strictly separate from canonical game data.
- Multiple weapon or artifact instances with the same underlying item identity are legitimate account inventory items and must never be treated as canonical database duplicates.

------------------------------------------------------------------------

## 7.8 gcsim

Use for future team simulation.

URL:

https://docs.gcsim.app/

gcsim is designed for Genshin team DPS/combat simulation and reports
damage distribution, energy regeneration, reaction counts and related
metrics.

It should be introduced only after the core data layer is reliable.

------------------------------------------------------------------------

## 7.9 Akasha

Use as a statistical source for:

-   build benchmarking
-   percentile context
-   leaderboard-style comparisons
-   artifact/build distributions

Do not treat statistical rankings as universal truth.

------------------------------------------------------------------------

## 7.10 Genshin Center

Use as a reference for:

-   ascension planning
-   material planning
-   domain schedules
-   calculators
-   planning UX

URL:

https://genshin-center.com/

Do not make it the primary character tracker because Genshin Track is
now the chosen reference for that product area.

------------------------------------------------------------------------

# 8. PHASE 0 --- Full Baseline and Safety Lock

## Objective

Establish a reproducible baseline before modifying implementation.

## Tasks

1.  Freeze current behavior.
2.  Record current commit/version.
3.  Record current dataset hashes.
4.  Record test results.
5.  Record API endpoints.
6.  Record frontend screenshots.
7.  Record current external providers.
8.  Identify all data-generation scripts.
9.  Identify all generated datasets.
10. Identify all runtime caches.
11. Verify `.env` handling.
12. Rotate any credential that may have been exposed outside the local
    environment.

## Required deliverables

Create:

``` text
docs/audit/
    BASELINE.md
    DATA_SOURCES.md
    RUNTIME_BEHAVIOR.md
    KNOWN_ISSUES.md
```

## Acceptance

The baseline can be reproduced by another developer.

------------------------------------------------------------------------

# 9. PHASE 1 --- Canonical Data Pipeline Rebuild

## Objective

Make the structured game-data layer trustworthy.

This is the highest priority phase.

## 9.1 Remove fabricated data

Delete all estimation/default-generation behavior for required canonical
fields.

Examples:

-   fake character base stats
-   rarity-derived weapon base ATK
-   fake ascension stats
-   unknown element -\> Pyro
-   unknown weapon type -\> Sword
-   placeholder IDs derived from Python hash

## 9.2 Deterministic IDs

Never use Python's randomized `hash()` for persistent IDs.

Use:

-   provider IDs where available
-   canonical stable IDs
-   deterministic normalized-name hashing only as a last-resort internal
    mechanism

Prefer actual provider IDs.

## 9.3 One ingestion pipeline

Consolidate competing scripts into a clear pipeline.

Suggested structure:

``` text
scripts/
    sync_game_data.py
    sync_knowledge.py
    validate_game_data.py
    validate_knowledge.py
    build_manifest.py
```

Optional orchestrator:

``` text
scripts/sync_all.py
```

## 9.4 Raw -\> normalized -\> validated -\> published

``` text
External source
      |
      v
data/raw/
      |
      v
Normalizer
      |
      v
Normalized objects
      |
      v
Schema validation
      |
      v
Integrity validation
      |
      v
Cross-source validation
      |
      v
data/processed/
```

Never manually patch generated JSON as the normal workflow.

## 9.5 Integrity rules

Fail the build when:

-   duplicate IDs exist
-   duplicate canonical names exist
-   required fields are missing
-   placeholder values are detected
-   unknown enum values appear
-   invalid relationships exist
-   source metadata is missing
-   version metadata is missing for current-sensitive data

## 9.6 Coverage requirements

Minimum canonical entities:

-   characters
-   weapons
-   artifact sets
-   materials
-   talents
-   constellations

Recommended expansion:

-   enemies
-   domains
-   reactions
-   mechanics
-   regions
-   farming schedules

## Acceptance

A clean data rebuild produces:

-   zero placeholder required values
-   zero duplicate IDs
-   deterministic output
-   complete provenance
-   current-version coverage
-   validation report

------------------------------------------------------------------------

# 10. PHASE 2 --- Current Version and Update System

## Objective

Stop treating a hard-coded local version as the current live game
version.

## Tasks

1.  Introduce a `GameVersion` model.
2.  Store version metadata in datasets.
3.  Maintain a current-version record.
4.  Validate current-version sources.
5.  Track previous versions.
6.  Detect stale documents.
7.  Expose version status in System Health.
8.  Update the data pipeline for each patch.

## Version-aware data model

Example:

``` text
Entity
- id
- name
- game_version_introduced
- game_version_updated
- source
- source_url
- retrieved_at
- content_hash
```

## Version-aware retrieval

A query asking about current mechanics should prioritize:

``` text
current version
>
recent compatible version
>
older version
```

and never silently use an obsolete source as current.

## Acceptance

The UI and API show the validated current version.

The knowledge base clearly distinguishes current and stale documents.

------------------------------------------------------------------------

# 11. PHASE 3 --- Provenance and Source Registry

## Objective

Make every important answer traceable.

## Source registry

Create a source registry:

``` text
Source
- source_id
- name
- tier
- type
- base_url
- trust_level
- supported_topics
- update_frequency
```

## Document metadata

Every knowledge item should contain:

``` text
document_id
title
source_id
source_url
canonical_url
source_type
authority_tier
topic
entities
game_version
published_at
updated_at
retrieved_at
content_hash
```

## Important distinction

Do not confuse:

``` text
where data was fetched from
```

with:

``` text
where the user should verify it
```

and:

``` text
how authoritative it is
```

These are separate metadata fields.

## Acceptance

No document can enter the production knowledge base without provenance.

------------------------------------------------------------------------

# 12. PHASE 4 --- Knowledge Base Rebuild

## Objective

Replace the stale/incomplete knowledge library with a current curated
library.

## Initial source set

### Official

-   patch notes
-   official announcements
-   official system/character information

### KQM

-   character guides
-   build guides
-   team guides

### KQM TCL

-   mechanics
-   evidence
-   niche interactions
-   frame/gauge/ICD information

### Structured providers

-   game records
-   item records
-   progression records

## Ingestion rules

Do not scrape the whole internet.

Every source must be:

1.  approved
2.  classified
3.  version-tagged
4.  normalized
5.  validated
6.  indexed

## Chunking

Documents should be split into useful semantic chunks.

Example:

``` text
Character
  -> Overview
  -> Talents
  -> Passive
  -> Constellations
  -> Weapons
  -> Artifacts
  -> Teams
  -> Rotation
```

This is better than injecting an entire long document.

------------------------------------------------------------------------

# 13. PHASE 5 --- Retrieval Architecture

## Objective

Make retrieval precise enough for real Genshin questions.

## Stage 1

Keep the current simple retrieval system while rebuilding data.

## Stage 2

Add:

-   metadata filtering
-   version filtering
-   source-tier weighting
-   entity filtering
-   topic filtering
-   freshness weighting

## Stage 3

If testing proves necessary, add hybrid retrieval:

``` text
BM25 / sparse search
        +
dense embeddings
        +
reranking
```

Do not add a vector database merely because it sounds scalable.

Start locally and only introduce heavier infrastructure if benchmark
results justify it.

## Retrieval output

Every retrieved item should include:

``` text
source
URL
content
score
version
source_type
entity
topic
```

------------------------------------------------------------------------

# 14. PHASE 6 --- ACCOUNT DATA & INVENTORY

## Objective

Build a proper account-data layer. The account model must distinguish between:
1. Canonical game data
2. Public Enka showcase data
3. Full account inventory data
4. Manual user data

## Account Data Sources

### Enka.Network
Use for:
- public showcase characters
- equipped builds
- currently exposed account information

Do not represent Enka showcase as the user's complete inventory.

### GOOD / Inventory Kamera
Support GOOD v3 account imports. GOOD should be treated as the preferred rich local inventory source.
Support:
- characters (level, ascension, constellation, talent levels)
- weapons (level, ascension, refinement, lock state, location)
- artifacts (set, slot, level, rarity, main stat, substats, lock state, location)
- materials (inventory item counts)
- equipped relationships (which character holds which weapon/artifact)
- refinement levels (R1–R5)
- constellation levels (C0–C6)
- talent levels (auto, skill, burst)
- artifact main stats
- artifact substats (key, value, roll count)
- artifact levels (+0 to +20)
- lock state (locked/unlocked)
- multiple inventory instances (multiple copies of the same weapon or artifact set/slot)

Store the raw imported GOOD file for reproducibility and auditing (`data/raw/accounts/`).
Normalize it into internal account models (`backend/models/account.py`).
The normalized account inventory must not modify canonical game data.

## Account Source Model

Every account datum should retain its origin where practical:
- `GOOD`
- `Enka`
- `Manual`

When sources disagree, do not silently overwrite information. Apply explicit source precedence and record the conflict:
``` text
Precedence: Manual Overrides > GOOD Inventory Import > Enka Showcase Snapshot
```

## My Account UI Structure

"My Account" should eventually provide:
- Account Overview
- Characters
- Weapons
- Artifacts
- Materials
- Teams
- Progress
- Inventory Sources
- Build Optimizer
- Artifact Optimizer
- Farming Planner
- Upgrade Planner

Use **Genshin Track** as the primary UX reference for progression/farming and **Genshin Optimizer** as the primary functional reference for inventory and optimization. Do not copy either site's implementation directly.

## Acceptance

1. User can import a GOOD v3 JSON file and view their complete inventory separate from the Enka showcase.
2. Multiple copies of weapons and artifacts are preserved as separate inventory instances without canonical deduplication.
3. Every account record indicates its origin source (GOOD, Enka, or Manual).
4. No canonical game data is mutated or overwritten by account data ingestion.

------------------------------------------------------------------------

# 15. PHASE 7 --- DETERMINISTIC BUILD & STAT ENGINE

## Objective

Implement a deterministic calculation layer. Do not ask Gemini to perform calculations that can be performed reliably by code.

## Calculation Capabilities

The engine should eventually support:
- base character stats (Lv. 1–90) using canonical character growth curves
- level and ascension stat multipliers
- weapon base stats and secondary scaling curves across all refinement levels (R1–R5)
- weapon refinement passives and stat effects
- artifact main stats by slot, rarity, and level (+0 to +20)
- artifact substat roll aggregation
- artifact set bonuses (2-piece and 4-piece activation conditions)
- character talent level scaling ratios (Lv. 1–10/13)
- constellation stat and scaling effects where applicable
- character, weapon, and artifact conditional effects (e.g. stack mechanics, HP thresholds)
- elemental resonance buffs (Pyro, Hydro, Cryo, Anemo, Geo, Electro, Dendro)
- team buffs (e.g. Bennett burst ATK buff, Noblesse 4pc, Tenacity 4pc, Viridescent Venerer shred)
- stat aggregation (total HP, total ATK, total DEF, CRIT Rate, CRIT DMG, ER, EM, Elemental/Physical DMG Bonuses)
- derived combat stats and damage formula components (base damage, crit multiplier, reaction multiplier, enemy defense/resistance factors)
- energy recharge requirements where deterministic
- build comparison (side-by-side delta analysis between candidate weapons, artifacts, or sets)

## Architectural Role Separation

- Use **Genshin Optimizer** as the primary architectural and functional reference for the calculation/optimization domain.
- Use **official/structured game data** as the actual source of game values.
- Do NOT copy numerical values from Genshin Optimizer without verifying their provenance and current version against canonical data sources.
- **Gemini may explain the calculated result, but Gemini must not be the source of truth for deterministic arithmetic.**

## Workflow Example

For:

> "Is my Arlecchino build good?"

System computes deterministically:

``` text
Account Build (from GOOD / Enka)
    |
    +-- Weapon (White Tassel R5 Lv.90 -> Base ATK + CRIT Rate + Normal ATK bonus)
    +-- Artifacts (Gladiator 4pc -> Main stats, Substat rolls, 35% Normal ATK DMG)
    +-- Talents (Lv. 10 Normal Attack scaling)
    +-- Calculated Stats (Total ATK: 2150, CRIT: 74.2% / 168.4%, ER: 118%)
    |
    v
Build Analysis Engine
    |
    +-- Strengths (high CRIT ratio, 4pc set active)
    +-- Weaknesses (low ER if bursting frequently, suboptimal Goblet substats)
    +-- Benchmarks (comparison against KQM recommended stat benchmarks)
    +-- Upgrade Priorities (upgrade Goblet first, farm talent books)
    |
    v
Gemini Explanation Layer
    |
    +-- Formulates clear, grounded, natural-language advice citing computed numbers
```

## Acceptance

1. Same account build input deterministically produces the exact same calculated stats.
2. Calculation output matches in-game stat screens and verified formulas within floating-point tolerance.
3. Gemini receives pre-calculated stat blocks and comparison deltas in prompt context rather than performing arithmetic in LLM generation tokens.

------------------------------------------------------------------------

# 16. PHASE 8 --- Chat Intelligence and Knowledge Escalation

## Objective

Make Chat helpful without sacrificing trust.

## Query classification

Use a richer classification than only:

``` text
general / account
```

Recommended:

``` text
FACT
MECHANIC
BUILD
ACCOUNT_BUILD
WEAPON_COMPARE
ARTIFACT_COMPARE
TEAM_BUILD
FARMING
ABYSS
VERSION
PLANNING
CALCULATION
UNKNOWN
```

Queries can have multiple intents.

Example:

> "What's the best weapon for my Arlecchino?"

``` text
ACCOUNT_BUILD
+
WEAPON_COMPARE
```

## Tool planning

The router chooses tools.

Example:

``` text
ACCOUNT_BUILD
    -> account lookup
    -> canonical character
    -> weapon database
    -> KQM
    -> calculation
    -> Gemini
```

## Answer assembly

Gemini receives:

-   structured facts
-   account facts
-   retrieved evidence
-   calculation results
-   source metadata

It should not need to invent missing exact values.

------------------------------------------------------------------------

# 17. PHASE 9 --- Best-Effort Answering Policy

## Objective

Implement the revised product philosophy.

### Rule

> **Always try to help. Never fabricate certainty.**

## Example

User:

> "What's the best weapon for Odette?"

Possible evidence:

-   current structured weapon data
-   KQM guide
-   account stats
-   optimizer calculations

Answer normally.

------------------------------------------------------------------------

If KQM has no guide but structured data and related theorycrafting
exist:

Answer using the best available evidence and label it as
analysis/theorycrafting.

------------------------------------------------------------------------

If the interaction is extremely obscure:

Give the best-supported explanation, clearly marking uncertainty.

------------------------------------------------------------------------

Only when the system cannot establish a meaningful answer should it say
that verification is currently unavailable.

The message should be written for a normal user, not for a developer.

------------------------------------------------------------------------

# 18. PHASE 10 --- Citation and Grounding System

## Objective

Make citations meaningful rather than decorative.

## Citation & Grounding Architecture (Internal vs Production)

> [!IMPORTANT]
> **PRODUCTION-CLEAN GROUNDING INVARIANT**:
> Grounding and citations must be strictly validated **internally**, but must **NEVER** turn user-facing answers into cluttered citation or external-source dashboards.
> - **Internal Engine**: Rigorously tracks dataset references, account snapshot hashes, calculation equations, and knowledge package IDs.
> - **Development Mode (`DEBUG=true`)**: May display debug pills (e.g. `[Account Enka]`, `[Canonical DB]`, `[Calculated Engine]`) for developer auditing.
> - **Production Mode (`DEBUG=false`)**: Presents clean outcomes, natural explanations, and account-grounded cards.
>   - **NEVER** expose external source names (`KQM`, `TCL`, `Genshin Optimizer`, `Wiki`, `Reddit`).
>   - **NEVER** display internal source tiers (`Tier 1`, `Tier 2`, `Tier 5`).
>   - Present recommendations cleanly as GenshinIQ's grounded analysis:
>     - *"Based on your currently equipped weapons..."*
>     - *"Calculated for your team composition..."*
>     - *"Your Arlecchino currently has 71.4% CRIT Rate..."*


## Claim support

Internally represent:

``` text
Claim
Evidence
Evidence type
Source
Version
Confidence
```

This enables future automated grounding validation.

------------------------------------------------------------------------

# 19. PHASE 11 --- Characters & Data Tab Rebuild

## Objective

Make the global encyclopedia trustworthy, highly scannable, visually rich, and deeply integrated with user account personalization.

> [!IMPORTANT]
> **MANDATORY BEST-IN-CLASS UX / UI REQUIREMENTS (DO NOT IMPLEMENT NOW)**:
> Phase 11 MUST strictly implement the design principles, visual asset pipeline, and anti-text-wall standards defined in [Section 2B](#2b-mandatory-best-in-class-genshin-ux--ui-architecture--design-system).
> The character, weapon, and artifact views MUST NOT be a series of text blocks or raw database dumps. They must adopt the visual density, iconography, and structured card layouts proven by Genshin Track and Genshin Wiki.

## 10-Section Character Page Architecture (Mandatory)

The Character detail view MUST be rebuilt around this structured, high-density 10-section layout:

1. **Character Header**:
   - Splash art hero banner / high-res portrait icon
   - Name, in-game title, 4★ / 5★ rarity indicator
   - Element icon (inline SVG) with elemental color gradient
   - Weapon-type icon (inline SVG) and region badge
   - Current release version badge (`v7.0`) and source links
2. **Quick Summary**:
   - Concise role summary (1–2 sentences)
   - Visual strength tags (e.g., `Off-field Pyro`, `Snapshotting`)
   - Visual caveat tags (e.g., `High 80 ER Cost`)
3. **Your Character (Personalized Account Card)**:
   - Owned vs. Unowned indicator
   - Level & Ascension (`Lv. 90/90`)
   - Unlocked Constellation (`C6` badge)
   - Currently equipped weapon & refinement
   - Talent levels (`1 / 11 / 13`)
   - Quick action triggers: `[✨ Ask AI to Review Build]`, `[⚡ Optimize Artifacts]`, `[🌾 Farming Plan]`
4. **Base Stats**:
   - Visual stat cards: Base HP, Base ATK, Base DEF, Ascension Stat
   - Level selector / slider (`Lv. 1` to `Lv. 90`)
5. **Talents**:
   - Dedicated visual card per talent (Normal Attack, Elemental Skill, Elemental Burst, Passives)
   - Scannable key scaling numbers (DMG%, CD, Energy Cost)
   - Expandable drawer for complete multi-paragraph mechanical details
   - Visual talent leveling priority badge: `Burst > Skill >> Normal Attack`
6. **Constellations**:
   - Compact C1–C6 icon grid
   - Visual highlight for owned constellations
   - Major milestone indicators (e.g., `★ C4: +40% Duration (Major Spike)`)
   - Expandable descriptions in drawer
7. **Build (Weapons & Artifacts)**:
   - Recommended weapons with icons, refinement notes, and `BIS` / `F2P` / `Alternative` badges
   - Recommended artifact sets with set icons and 2pc / 4pc summary tags
   - Main stat priorities: Sands, Goblet, Circlet
   - Substat priority pill badges: `ER (to threshold) > CRIT Rate = CRIT DMG > ATK% > EM`
   - Scannable target stat benchmark cards (ER%, CRIT, ATK)
8. **Teams**:
   - 4-slot visual composition cards with portraits, elemental frame, and role tags
   - Archetype badges (`National`, `Vaporize`, `Mono-Pyro`)
   - Owned vs unowned visual indicators on teammates
   - Scannable rotation sequence chips
9. **Farming**:
   - Visual material grid with item icons, required vs owned counts, and net deficit
   - Boss material, local specialty, talent books, common mob drops, and weekly boss drops
   - Daily domain schedule banner showing today's availability
10. **AI Analysis**:
    - Grounded, account-aware synthesis bridging game data with user's specific account
    - Concrete, prioritized next steps

> [!NOTE]
> **Architecture & State Demarcation Rule**:
> The exact visual styling can evolve, but the information architecture **MUST** preserve these 10 responsibilities.
> Account-specific sections (Section 3: Your Character / Account State) must clearly distinguish the user's actual character state from generic canonical information, preventing confusion between global database facts and owned roster data.

## Weapon Page Architecture

``` text
Weapon Detail View
- Visual Header: High-res weapon icon, rarity background (3★/4★/5★), weapon type SVG
- Core Stats Card: Base ATK (Lv. 1 - Lv. 90), Secondary Stat (Type & Value)
- Passive Effect Card: Passive name, scaling table across Refinements R1 - R5
- Ascension Materials Grid: Item icons, required quantities, domain schedule
- Recommended Characters: Portrait avatars of characters with synergy tags (e.g., "Top F2P", "BIS")
- Provenance & Version: Version added, source reference, canonical data link
```

## Artifact Set Page Architecture

``` text
Artifact Set Detail View
- Visual Header: Set name, rarity range, slot piece icons (Flower, Feather, Sands, Goblet, Circlet)
- Set Bonuses: 2-piece effect card with highlighted stat boosts, 4-piece effect card with condition triggers
- Domain Source: Domain icon, location, schedule, resin efficiency indicator
- Recommended Characters: Portrait avatars of top beneficiaries with build synergy tags
- Canonical Source & Version: Release version, update timestamp, source link
```

## Data Integrity & Guardrails

- Never display placeholder numbers or fabricated stats.
- If a field is genuinely unavailable: display `Data unavailable` with clear explanation, never a fake or hallucinated value.
- All numbers must be derived deterministically from canonical versioned datasets.

## Phase 11 Visual Acceptance Criteria

In accordance with [Section 2B.9](#2b9-universal-ui-acceptance-criteria-14-point-inspection-gate), Phase 11 MUST satisfy:
1. **Immediate Scannability**: Character roles, elements, base stats, and recommended gear are scannable in under 5 seconds.
2. **Zero Walls of Text**: Raw paragraph descriptions are moved to expandable drawers; primary view uses cards and badges.
3. **Rich Visual Assets**: Character portraits/splash, elemental SVGs, weapon-type SVGs, and material icons render crisply.
4. **Visual Prioritization**: Key builds, ascension stats, and major constellation milestones are prominently highlighted.
5. **Clear Hierarchy**: 10-section structure is visually demarcated with consistent spacing and glassmorphic card boundaries.
6. **Account Distinction**: Owned status, equipped weapon, and talent levels are visually distinguished on "Your Character" card.
7. **No Runtime Dependencies**: All layouts, icons, and data render locally without calling external reference sites.
8. **Visual Inspection Passed**: Validated through browser capture and manual UX verification against best-in-class standards.

------------------------------------------------------------------------

# 20. PHASE 12 --- Guides Tab Rebuild

## Objective

Turn Guides into a curated, scannable knowledge center that bridges theorycrafting with personal account builds.

> [!IMPORTANT]
> **MANDATORY BEST-IN-CLASS UX / UI REQUIREMENTS (DO NOT IMPLEMENT NOW)**:
> Phase 12 MUST strictly implement the design principles from [Section 2B](#2b-mandatory-best-in-class-genshin-ux--ui-architecture--design-system).
> Character build guides MUST NOT be long, unbroken text articles. They must adopt the scannable, visual layout patterns proven by Genshin Track and KeqingMains (KQM), with weapon ranking cards, artifact priority grids, team synergy cards, and expandable theorycrafting drawers.

## Filter Architecture

- All
- Character Guides
- Combat Mechanics
- Theorycrafting & Rotations
- Patch Notes & System Changes
- Farming & Domain Schedules
- Team Compositions
- Spiral Abyss & Endgame

## Source Badges & Provenance

Every guide and build card must prominently display its source hierarchy badge:
- `OFFICIAL` (Patch notes, in-game notices, official archives)
- `KQM` (KeqingMains comprehensive written guides)
- `TCL` (Theorycrafting Library evidence projects)
- `STRUCTURED DATA` (Calculated directly from canonical game tables)
- `STATISTICAL` (Empirical Spiral Abyss usage and artifact distributions)
- `COMMUNITY` (Peer-reviewed community guides)

## Version & Freshness Badges

- `v7.0 CURRENT` (Verified for active version)
- `v6.8` (Older version guide)
- `STALE (Requires Review)` (Flags guides predating major mechanic/character updates)

## Scannable Build Guide Architecture (Mandatory)

Future Character Build Guides MUST present the following structured, visual components:

1. **Ranked Weapon Priority Cards**:
   - Ranked cards: `1. Staff of Homa (BIS)`, `2. The Catch (Top F2P)`, `3. Favonius Lance (Comfort / ER)`
   - Weapon icons, rarity backgrounds, refinement indicators (`R1` vs `R5`)
   - `BIS` / Best-in-Slot labels where mathematically justified, plus clear `F2P` recommendations
   - Relative performance percentage tags (e.g., `100% (Baseline)`, `94.2%`, `88.5%`)
   - Brief 1-sentence mechanical condition (e.g., "Assumes <50% HP threshold")
2. **Artifact Set Cards & Stat Callouts**:
   - Ranked 4pc and 2pc set cards with visual set icons and set bonus summaries
   - Main-stat callouts with clear badges for Sands, Goblet, Circlet
   - Substat priority pill hierarchy: `ER (to threshold) > CRIT Rate / DMG > ATK%`
   - Specific ER breakpoint benchmarks table based on team composition (e.g., `Solo Pyro: 220% ER`, `With Bennett: 180% ER`, `With Raiden: 160% ER`)
   - Side-by-side build comparison view with clear recommendation hierarchy
3. **Talent Leveling Priority Card**:
   - Visual sequence badge: `Burst (Lv. 9+) > Skill (Lv. 8+) >> Normal Attack (Lv. 1)`
   - Crown recommendation indicator
4. **Team Synergy Cards**:
   - 4-character visual cards with role badges (`Main DPS`, `Sub DPS`, `Enabler`, `Buffer`)
   - Rotation sequence timeline chips
5. **Personalization Callout ("Recommended Weapon" vs "What You Currently Own")**:
   - The key differentiator: Compare recommended gear directly against user's owned inventory
   - Rather than providing only generic advice, visibly present:
     - **Recommended Weapon**: `Staff of Homa (R1, Lv. 90)`
     - **What You Currently Own**: `The Catch (R5, Lv. 90)` or `Dragon's Bane (R3, Lv. 80)`
   - Highlight whether the user owns the `BIS` or `Top F2P` weapon, current level/refinement, and equipping suggestions
   - Action button: `[✨ Ask AI to Adapt Guide to My Roster]`
6. **Expandable Theorycrafting Notes**:
   - Collapsible accordion drawers for in-depth ICD mechanics, energy generation math, and calculation assumptions

## Phase 12 Visual Acceptance Criteria

In accordance with [Section 2B.9](#2b9-universal-ui-acceptance-criteria-14-point-inspection-gate), Phase 12 MUST satisfy:
1. **Immediate Scannability**: Build priorities, weapon rankings, and artifact stats are instantly readable without scrolling past walls of text.
2. **Zero Walls of Text**: Exhaustive theorycrafting rationale is organized into collapsible drawers.
3. **Visual Weapon & Artifact Rankings**: Weapons and artifacts render visual icons, rarity styling, and priority badges (`BIS`, `F2P`).
4. **Clear ER Breakpoints**: Energy requirements are displayed in a clean comparative table rather than buried in paragraphs.
5. **Personalized Grounding**: Visual callouts indicate which recommended items the user currently owns.
6. **Source & Freshness Transparency**: Source badges (`KQM`, `OFFICIAL`) and version tags (`v7.0`) are immediately visible on every guide.
7. **Visual Inspection Passed**: Verified via browser interaction and visual inspection against top Genshin reference guides.

------------------------------------------------------------------------

# 21. PHASE 13 --- Farming and Character Tracking

## Objective

Build a genuinely useful, high-density personal progression system inspired by Genshin Track.

> [!IMPORTANT]
> **MANDATORY BEST-IN-CLASS UX / UI REQUIREMENTS (DO NOT IMPLEMENT NOW)**:
> Phase 13 MUST strictly follow the design system defined in [Section 2B](#2b-mandatory-best-in-class-genshin-ux--ui-architecture--design-system).
> Use **Genshin Track** as the primary UX reference for:
> - Tracked character cards with progression sliders
> - High-density material requirement grids
> - Daily domain schedule cards with domain icons and day-of-week badges
> - Owned vs required vs missing deficit visualization
> - Actionable farming priorities
> Do NOT display farming plans as long text paragraphs or markdown bullets.

## Desired Workflow

``` text
My Account (Enka / GOOD Inventory)
           |
           v
Tracked Characters (Target Levels / Talents / Weapons)
           |
           v
Canonical Material Aggregator (Ascension + Talent Costs)
           |
           v
Net Deficit Engine (Required - Owned Inventory)
           |
           v
Today's Domain Schedule & Boss Rotation
           |
           v
Visual Daily Farming Action Plan (Resin Prioritization)
```

## Mandatory Visual Components

1. **Tracked Character Carousel / Cards**:
   - Character portrait avatar, current level -> target level (e.g., `Lv. 80 -> Lv. 90`)
   - Current talent levels -> target talent levels (e.g., `1/8/8 -> 1/9/10`)
   - Progress bar indicating total progression completion percentage
2. **Material Requirement & Deficit Grid**:
   - Visual cards grouping materials by category:
     - Boss Materials (e.g., Evergloom Ring)
     - Local Specialties (e.g., Mourning Flower)
     - Talent Books (e.g., Order series)
     - Common Enemy Drops (e.g., Transoceanic Pearl series)
     - Weekly Boss Drops (e.g., Worldspan Fern)
     - Gemstones (Sliver / Fragment / Chunk / Gemstone)
   - Every material card MUST show:
     - High-resolution material icon
     - Rarity color frame
     - Quantity fraction: `[Owned] / [Required]`
     - Color-coded deficit badge: green checkmark if complete, bold amber/red badge if missing (e.g., `Missing: 14`)
     - Crafting conversion indicator (if lower-tier materials can be crafted into higher-tier)
3. **Daily Domain Schedule Dashboard**:
   - Today's active domains with domain icons, location labels, and daily drops
   - Filter chips by day of the week: `Mon / Thu`, `Tue / Fri`, `Wed / Sat`, `Sun (All)`
   - Highlighted badges for tracked characters who need today's domain drops
4. **Resin-Efficient Daily Action Plan**:
   - Prioritized visual recommendations for spending daily resin (e.g., `1. Farm 3x Weekly Bosses (Half Resin)`, `2. Farm Steeple of Ignorance (Talent Books for Xiangling)`, `3. Spend remaining on Weapon Materials`)
   - Estimated days to completion based on 160 or 180 daily resin budget

## Example UI Representation & Deficit Structure

Instead of: *"You need 14 more Guide to Order and 6 Philosophies of Order for Odette..."*
The UI MUST present high-density visual cards with clear next-action recommendations:
- **Character Progression Sliders**: Level and talent progression sliders (`Lv. 80 -> Lv. 90`, `1/8/8 -> 1/9/10`)
- **Material Requirement Card**:
  - Category: `Talent Books`
  - Material Icon: `Philosophies of Order`
  - **Owned**: `12`
  - **Required**: `36`
  - **Missing**: `24` (Bold amber deficit indicator with crafting conversion option)
- **Schedule Card**: `Steeple of Ignorance (Active Today: Wednesday)` with active-day filter
- **Action Button**: `[Add to Today's Farming Queue]`, `[Mark Farmed]`, `[View Domain Details]`

*The user must be able to understand their farming state and exact deficits at a glance.*

## Phase 13 Visual Acceptance Criteria

In accordance with [Section 2B.9](#2b9-universal-ui-acceptance-criteria-14-point-inspection-gate), Phase 13 MUST satisfy:
1. **Immediate Scannability**: Daily farming priorities and missing items are visible at a glance.
2. **Zero Walls of Text**: Farming summaries use compact progress cards, badge counters, and schedule timelines.
3. **Visual Deficit Tracking**: Every required material shows an icon, owned vs needed counts, and a clear deficit indicator.
4. **Domain Schedule Visualization**: Today's active domains are visually distinct from inactive ones.
5. **Account Grounding**: Material counts are derived directly from user's imported GOOD inventory.
6. **Visual Inspection Passed**: Verified via browser capture and UX inspection benchmarked against Genshin Track.

------------------------------------------------------------------------

# 22. PHASE 14 --- Team Building

## Objective

Turn "Ask Teams" into an actual account-aware team composition engine with rich visual presentations.

> [!IMPORTANT]
> **MANDATORY BEST-IN-CLASS UX / UI REQUIREMENTS (DO NOT IMPLEMENT NOW)**:
> Phase 14 MUST strictly follow the design system defined in [Section 2B](#2b-mandatory-best-in-class-genshin-ux--ui-architecture--design-system).
> Team recommendations MUST NOT be rendered as unformatted text paragraphs or generic bullet lists.
> Teams must be presented visually using 4-slot character portrait cards, elemental frames, role badges (`Main DPS`, `Sub DPS`, `Support`, `Sustain`), synergy indicators, rotation sequence diagrams, and owned-vs-unowned inventory flags.

## Inputs

- User's actual roster (Enka / GOOD account data)
- Current character levels, ascensions, constellations
- Equipped and available weapons and artifacts
- Role classifications (Main DPS, Off-Field Sub-DPS, Elemental Buffer, Shielder, Healer)
- Current-version combat mechanics & elemental reaction rules
- Theorycrafting synergy databases (KQM / TCL)
- Optional Spiral Abyss / endgame floor context

## Mandatory Visual Team Presentation

Every recommended team composition MUST be rendered visually rather than as raw text:

1. **4-Slot Character Composition Card**:
   - High-resolution character portraits with elemental color-gradient borders and element indicators
   - Character name and rarity indicator (4★ / 5★)
   - Role badge: `Main DPS`, `Sub DPS`, `Support`, `Sustain`
   - User ownership & character progression state:
     - **Owned**: `Owned: Lv. 90 C2` (green check badge, active level and constellation)
     - **Unowned**: `Unowned (Substitute Available)` (distinct amber outline with substitute recommendation)
2. **Team Archetype & Synergy Chips**:
   - Archetype badge (e.g., `Vaporize`, `Aggravate`, `Hyperbloom`, `Freeze`, `Mono-Pyro`)
   - Elemental Resonance active badges (e.g., `Pyro Resonance: +25% ATK`, `Hydro Resonance: +25% HP`)
   - Key synergy bullets: 2–3 scannable chips explaining why the team works (e.g., `Xiangling snapshots Bennett Q`, `Double Hydro battery for Furina`)
3. **Interactive Visual Rotation Sequence**:
   - Visual sequence chips representing combat flow:
     $$\mathbf{Q \longrightarrow E \longrightarrow CA \longrightarrow Swap \longrightarrow Q}$$
   - Color-coded action tags: `Q (Burst)`, `E (Skill)`, `CA (Charged Attack)`, `Swap (Switch Character)`
   - Step-by-step sequence example: `1. Zhongli Hold E` -> `2. Xingqiu Q > E` -> `3. Swap Hu Tao` -> `4. Hu Tao E > N2CD`
4. **Energy Recharge (ER) Requirements Matrix**:
   - Compact table showing exact ER thresholds required per character under this specific team battery setup
5. **Alternative Character Substitutions**:
   - Visual substitute recommendation slots for unowned characters with one-click swap and synergy delta indicator
6. **Expandable Detailed Mechanics Drawer**:
   - In-depth mechanics explanations, rotation nuances, funneling instructions, and defensive considerations collapsed in an accordion drawer

## Phase 14 Visual Acceptance Criteria

In accordance with [Section 2B.9](#2b9-universal-ui-acceptance-criteria-14-point-inspection-gate), Phase 14 MUST satisfy:
1. **Immediate Scannability**: 4-slot team members, roles, archetype, and resonance are clear at a glance.
2. **Zero Walls of Text**: Team guides rely on visual cards, rotation chips, and stat badges rather than long paragraphs.
3. **Visual Account Grounding**: Characters the user owns are immediately distinguished from unowned recommendations.
4. **Actionable Substitutions**: Unowned slots offer visual alternatives directly matched against user inventory.
5. **Clear Visual Rotation**: Rotation steps are represented as sequenced visual chips.
6. **Visual Inspection Passed**: Verified via browser capture and UI review against top community team builders.

------------------------------------------------------------------------

# 23. PHASE 15 --- ARTIFACT OPTIMIZATION

## Objective

Build a deterministic artifact optimizer using the user's actual owned inventory, paired with a high-density, visual comparison UI inspired by Genshin Optimizer.

> [!IMPORTANT]
> **MANDATORY BEST-IN-CLASS UX / UI REQUIREMENTS (DO NOT IMPLEMENT NOW)**:
> Phase 15 MUST strictly implement the design principles defined in [Section 2B](#2b-mandatory-best-in-class-genshin-ux--ui-architecture--design-system).
> Optimization outputs MUST NOT be delivered as text dumps or unformatted lists.
> The UI must reproduce the proven inventory-oriented UX patterns from **Genshin Optimizer**:
> - Visual artifact cards displaying slot icons, set icons, +20 levels, main stats, and substats
> - Side-by-side visual comparison cards (Equipped vs Optimized Build)
> - Stat delta badges with green/red visual indicators (`+18.2% CRIT DMG`, `-50 ATK`)
> - High-density filter and target controls with instant reactivity

## Input

- Normalized GOOD inventory (all owned artifacts with set, slot, level, rarity, main stat, substats, lock state, current location)
- Canonical character data
- Canonical weapon data
- Artifact set data (2-piece and 4-piece bonuses)
- Character build target (role, weapon, talent priorities)
- Optimization objective

## Optimization Objectives

Support optimization objectives such as:
- **Maximize selected stat**: e.g., maximize Elemental Mastery, maximize total HP, maximize Energy Recharge
- **Maximize damage-related objective**: e.g., average skill damage, burst damage, crit-weighted expected output
- **Satisfy minimum ER threshold**: e.g., require ER $\ge$ 160% before optimizing for offensive stats
- **Satisfy main-stat requirements**: e.g., Sands = ATK% or EM, Goblet = Pyro DMG%, Circlet = CRIT Rate / CRIT DMG
- **Set bonus constraints**: e.g., enforce 4pc Crimson Witch of Flames, or allow 2pc/2pc combinations
- **Character-specific stat benchmarks**: e.g., 70%+ CRIT Rate, 140%+ CRIT DMG, 120%+ ER
- **Build comparison**: side-by-side comparison of current equipped build vs candidate optimized builds

## Optimizer Requirements

The optimizer must:
1. Read actual artifacts owned by the user from the normalized GOOD account inventory.
2. Respect artifact slot constraints (Flower of Life, Plume of Death, Sands of Eon, Goblet of Eonothem, Circlet of Logos).
3. Respect 5-piece and set bonus rules (maximum 5 equipped artifacts; allows 4pc set + 1 off-piece, or 2pc + 2pc + 1 off-piece, or 2pc + 3 rainbow pieces).
4. Respect equipped and available inventory (with user toggles to include or exclude artifacts currently equipped on other characters).
5. Calculate resulting stats deterministically using the Phase 7 stat engine.
6. Rank valid builds by the target objective.
7. Explain why the recommended build is better (highlighting stat deltas, effective rolls, and CV).
8. Identify which specific artifacts should be replaced on the character.
9. Show trade-offs between candidate builds (e.g., "+18.2% CRIT DMG at the cost of -12.4% ER").

## Reference Projects & Non-Dependency

- Use **Genshin Optimizer (frzyc)** as the primary technical and UX reference for optimization concepts, combinatorial pruning, objective formulas, and visual comparison layouts.
- Use **GenshinOptimizer.com** as a secondary reference for a simpler, intuitive GOOD -> optimization workflow.
- Do NOT make either website a runtime dependency. GenshinIQ must implement its own local optimizer service in Python.

## Mandatory Visual Optimizer UI Components

The UI must adopt an **inventory/optimizer-oriented UX**:

1. **Artifact Inventory Grids & Reactive Filters**:
   - Visual inventory grid displaying all owned pieces with slot icons, set icons, +20 levels, main stats, and substats
   - Reactive filter chips and controls:
     - **Slot filters**: Flower, Plume, Sands, Goblet, Circlet
     - **Set filters**: Single or multi-select artifact sets
     - **Main-stat filters**: ATK%, HP%, DEF%, EM, ER%, Elemental DMG%, CRIT Rate, CRIT DMG
     - **Substat filters**: Filter by required substat presence (e.g. CRIT Rate $\ge$ 10%)
     - Instant filter reactivity without full page reloads
2. **Side-by-Side Equipped vs Candidate Comparison**:
   - High-density comparative stat table with green (`+`) and red (`-`) delta pills
   - Clear stat delta visualization:
     ``` text
     Equipped
     CRIT DMG: 180.2%

     Candidate
     CRIT DMG: 198.4%

     Delta:
     +18.2% CRIT DMG
     ```
   - Clear display of CV (Crit Value), Total ATK, Total HP, ER%, and EM trade-offs
3. **Slot-by-Slot Replacement Instructions (Which Piece & Why)**:
   - 5-piece visual equipment slots (Flower, Feather, Sands, Goblet, Circlet)
   - Highlight whether each slot is retained or swapped
   - For swapped pieces: show "Equip from: [Character / Inventory]" badge
   - **Explainability**: The user should understand exactly **WHICH** artifact should be replaced and **WHY** (e.g. "Replacing Sands gains +18.2% CRIT DMG while maintaining 160% ER threshold").
4. **Target & Constraint Filter Bar**:
   - Compact toggle chips for: Set bonuses, Main stat locks, Min ER slider, Exclude equipped pieces
5. **Actionable Re-Equipping Summary**:
   - Scannable 3-step in-game re-equipping instructions without multi-paragraph prose

## Workflow

``` text
Normalized GOOD Inventory
           |
           v
Character Target + Optimization Objective
           |
           v
Combinatorial Pruning & Candidate Generation
           |
           v
Deterministic Stat Calculation & Ranking
           |
           v
Side-by-Side Visual Comparison (Equipped vs Optimized)
           |
           v
Actionable In-Game Re-Equipping Instructions + AI Synthesis
```

## Phase 15 Visual Acceptance Criteria

In accordance with [Section 2B.9](#2b9-universal-ui-acceptance-criteria-14-point-inspection-gate), Phase 15 MUST satisfy:
1. **Immediate Scannability**: Stat improvements, swapped pieces, and set bonus changes are readable in under 5 seconds.
2. **Zero Walls of Text**: Optimization results are presented via side-by-side comparison cards and delta pills, not paragraphs.
3. **Visual Piece Identification**: Every recommended artifact displays slot icon, set icon, +20 level badge, and substat breakdown.
4. **Visual Delta Callouts**: Positive and negative stat trade-offs are clearly color-coded (`+18.2% CRIT DMG` green, `-12.4% ER` amber).
5. **Deterministic Integrity**: Ranking matches local Python calculation without relying on external web APIs.
6. **Visual Inspection Passed**: Verified via browser capture and UX inspection benchmarked against Genshin Optimizer.

------------------------------------------------------------------------

# 24. PHASE 16 --- gcsim / Combat Simulation

## Objective

Add simulation only after deterministic data is trustworthy.

Potential questions:

> "Which team does more damage?"

> "Is this rotation better?"

> "Is Weapon A better than Weapon B for this team?"

Workflow:

``` text
Account
+
Team
+
Stats
+
Rotation
+
Enemy assumptions
      |
      v
Simulation
      |
      v
Metrics
      |
      v
Gemini explanation
```

Always disclose simulation assumptions.

------------------------------------------------------------------------

# 25. PHASE 17 --- Abyss / Current Content

## Objective

Make team recommendations current rather than generic.

Future inputs:

-   current Spiral Abyss enemies
-   chamber conditions
-   blessings
-   enemy resistances
-   account roster
-   team simulations

Output:

> Best available teams for your account for this Abyss cycle.

This should be version/date-bound.

------------------------------------------------------------------------

# 26. PHASE 18 --- System Health and Developer Observability

## Objective

Make data quality visible and enforce deterministic, truthful release readiness.

## 26.1 System Health & Release-Gate Discrepancy Remediation (Phase 8 Hard Gate)

> [!IMPORTANT]
> **OBSERVED ISSUE & REMEDIATION MANDATE (DO NOT FIX NOW)**:
> The System Health page has displayed a blocked state:
> - `Version-Complete Release Gate (Phase 8 Hard Gate): PHASE 8 BLOCKED`
> - `Overall Completeness: INCOMPLETE`
> - `Character Knowledge: INCOMPLETE (95% — 90/95)`
> - Active Blocker: `Character expert guide coverage incomplete: 90/95`
> 
> This discrepancy MUST be investigated and formally resolved during Phase 18 remediation.
> **DO NOT fix this now**. The active work in progress must not be interrupted or refactored prematurely.

### Core Release-Gate Design Principle: Truthful > Green

The System Health / Release Gate must represent **actual system readiness**.
- **Do NOT optimize for "make the dashboard green"**.
- **Optimize for "make the dashboard truthful"**.
- Every completeness percentage, ratio, and blocker count must be derived from **deterministic, explainable rules**.
- If something is genuinely incomplete, it must **remain incomplete** until canonical data or curated evidence is supplied.
- If something is incorrectly classified as incomplete, fix the underlying classification or registry synchronization logic during Phase 18.
- **Do NOT simply change "90/95" to "95/95" to make the UI green**. The underlying data and coverage calculation must be demonstrably correct.

### Mandatory 10-Point Investigation Requirements for Phase 18

When Phase 18 is implemented, the investigation must determine and document:
1. **Denominator Derivation**: Why the release gate expects 95 character knowledge entries.
2. **Coverage Count**: Why only 90 are currently considered covered.
3. **Exact Missing Entities**: Which exact 5 characters are missing (e.g., Natlan characters like Xilonen, Chasca, Ororon, Lan Yan, Yumemizuki Mizuki).
4. **Release Status & Requirement**: Whether those 5 characters are actually released in the active game version (`v7.0` / current patch) and therefore strictly required, or if they represent unreleased/upcoming content.
5. **False Positive Gaps**: Whether any characters are incorrectly counted as missing due to name slug mismatches, casing differences, or file naming anomalies.
6. **Exclusion of Unreleased Content**: Whether unreleased characters are correctly excluded from mandatory completeness requirements.
7. **Canonical Registry Alignment**: Whether the denominator (95) is derived dynamically from the canonical current-version character registry (`version_service` / canonical database) rather than an arbitrary hardcoded constant.
8. **Version & Source Parity**: Whether the knowledge coverage calculation and the actual canonical character dataset are using the same version, source manifest, and filtering criteria.
9. **Metadata Freshness**: Whether the System Health page is reporting stale or inconsistent knowledge metadata (e.g. cached disk stats vs live index).
10. **Hard-Gate Classification Granularity**: Whether the hard-gate logic correctly distinguishes:
    - **Required Current Content**: Core characters released in active version requiring full guides.
    - **Optional Content**: Supplementary variants or traveler elements.
    - **Unreleased Content**: Characters known in data but not yet playable/released in active version.
    - **NOT_APPLICABLE Content**: Entities exempt from standard guide structures.
    - **Stale Content**: Guides that exist but predate major mechanic changes.
    - **Genuinely Missing Content**: Released characters with zero guide documentation.

### Final Release Gate Behavioral Requirements

The final implementation must **NOT** produce a false `Phase 8 BLOCKED` state because of inconsistent counting, misaligned versions, or stale metadata.
The release gate must be **deterministic and explainable**.
When Phase 18 is complete, the System Health page must clearly show:
- **What is missing**: Exact entity names and missing doc categories.
- **Why it is missing**: Whether knowledge was never authored, failed validation, or is stale.
- **Whether it is actually required**: Released vs unreleased / optional status.
- **Which source/version established the requirement**: Canonical version registry anchor.
- **What action is needed to resolve it**: Clear operational guidance (e.g., "Add curated guide to data/knowledge/characters/ or update unreleased filter").

## Required health checks

``` text
Game version
Dataset validation
Knowledge freshness
Source availability
Enka availability
Gemini availability
RAG latency
Citation health
Duplicate records
Placeholder records
Knowledge gaps
Release-gate blockers breakdown
```

## Knowledge gap queue

Example:

``` text
Knowledge Gap #102

Question:
Does X interact with Y?

Current evidence:
3 related sources

Problem:
No source directly confirms the interaction.

Suggested action:
Review TCL / official patch notes.
```

This is how GenshinIQ continuously improves.

## 26.2 Production Settings vs. Development Diagnostics Architecture

> [!IMPORTANT]
> **DEVELOPER DASHBOARD CONFINEMENT MANDATE**:
> In Phase 18, the application must be equipped with an automated environment gate separating Developer Observability from Consumer UI:
> - When `DEBUG=true` (local dev environment): The **System Health** tab remains accessible for internal telemetry, source registry inspection, version release-gate evaluation, and knowledge gap queues.
> - When `DEBUG=false` (production release build): The 5th tab is automatically transformed into the clean, consumer-oriented **Settings / App Status** interface (Option B).
> 
> ### Required Production Settings Architecture:
> 1. **General Preferences**:
>    - UI Theme / Appearance (Celestial Dark default, Obsidian OLED)
>    - Display Density (Comfortable vs Compact)
>    - Default Landing Tab selector (Chat, Characters, Guides, Farming, Teams)
>    - Animations & Reduced Motion toggle
> 2. **Account Management**:
>    - Connected UID display & nickname
>    - Manual "Sync Enka Showcase" trigger
>    - Last Sync time indicator (e.g. "Synced 15 minutes ago")
>    - "Clear / Disconnect UID" button
> 3. **AI Reasoning Preferences**:
>    - Response Detail Level (Punchy / Scannable vs In-Depth Theorycrafting)
>    - Trade-off Explanation toggle (show/hide rotation nuance notes)
>    - Re-calculation Confirmation dialog toggle
>    - Reset AI Chat Preferences
> 4. **Game & Version Information**:
>    - Clean consumer version status: `Genshin Impact v7.0 Ready`
>    - Server Region indicator (NA / EU / Asia / SAR)
>    - Daily Domain & Resin reset countdown timer
> 5. **Privacy & Data Security**:
>    - Transparent summary: "GenshinIQ stores your imported character builds and inventory locally on your device. Account credentials or passwords are never requested or stored."
>    - "Clear Local Artifact Inventory"
>    - "Reset All Local Data"
> 6. **About & Legal Disclosures**:
>    - GenshinIQ application version (`v1.0.0`)
>    - Open-source credits and minimal non-cluttering legal/trademark attribution for HoYoverse/Genshin Impact assets.
> 
> **Release Invariant**: Normal end users must **NEVER** see raw health metrics, database counts, source tier registries, provenance badges, release gates, or internal error dumps.

------------------------------------------------------------------------

# 27. PHASE 19 --- Security and Public-Release Hardening

## Backend

Review:

-   CORS
-   UID validation
-   path traversal
-   request size
-   rate limits
-   timeout handling
-   external API failures
-   secrets
-   error leakage

## Frontend

Review:

-   Markdown rendering
-   citation rendering
-   HTML sanitization
-   untrusted source content
-   URL handling

## Privacy

Document:

-   what account data is collected
-   what is stored
-   cache retention
-   whether data is sent to Gemini
-   external providers
-   deletion behavior

Do not store more personal data than necessary.

------------------------------------------------------------------------

# 28. PHASE 20 --- Testing and Evaluation

## Unit tests

Test:

-   models
-   providers
-   normalization
-   calculations
-   versioning
-   provenance
-   validation

## Integration tests

Test:

``` text
Enka -> normalized account
Game source -> canonical DB
Knowledge source -> KB
Query -> retrieval
Chat -> Gemini
```

## End-to-end tests

Test every tab.

------------------------------------------------------------------------

# 29. Permanent GenshinIQ AI Benchmark

Maintain at least 50 benchmark questions after the initial rebuild.

Categories:

### 1. Exact facts

10

### 2. Mechanics

10

### 3. Build recommendations

10

### 4. Account questions

10

### 5. Teams/planning

5

### 6. Version-sensitive questions

5

### 7. Difficult/obscure questions

5

### 8. Knowledge-gap questions

5

For each:

``` text
question
expected behavior
required sources
retrieved sources
answer
correctness
unsupported claims
citation quality
version correctness
confidence class
```

------------------------------------------------------------------------

# 30. Acceptance Criteria for Chat

A Chat response is considered good when:

1.  It answers the actual question.
2.  It uses account data when the question is account-specific.
3.  Exact facts come from structured data where possible.
4.  Recommendations use appropriate theorycrafting evidence.
5.  Calculations are deterministic.
6.  Version-sensitive information is current.
7.  Citations identify the relevant source.
8.  Uncertainty is communicated naturally.
9.  The model does not invent exact game values.
10. The user receives a useful answer even when the best evidence is
    incomplete.

------------------------------------------------------------------------

# 31. Documentation Synchronization

The project currently has multiple documents describing overlapping
implementation status.

After the rebuild, maintain:

``` text
README.md
ARCHITECTURE.md
IMPLEMENTATION_DETAILS.md
NEXT_VERSION_ROADMAP.md
CHANGELOG.md
AGENTS.md
docs/DATA_SOURCES.md
docs/KNOWLEDGE_POLICY.md
docs/RELEASE_CHECKLIST.md
```

Do not claim:

``` text
28/28 tests
v5.4 current
all phases complete
```

unless those statements are generated/verified from the actual project.

------------------------------------------------------------------------

# 32. Release Process

Every release should follow:

``` text
1. Sync external data
2. Validate datasets
3. Validate provenance
4. Validate versions
5. Rebuild knowledge index
6. Run unit tests
7. Run integration tests
8. Run AI benchmark
9. Run frontend E2E
10. Inspect System Health
11. Review changelog
12. Tag release
```

------------------------------------------------------------------------

# 33. Phase Completion Rule

Every phase must follow:

``` text
INSPECT
  ↓
PLAN
  ↓
IMPLEMENT
  ↓
RUN
  ↓
TEST
  ↓
VERIFY REAL OUTPUT (Automated + Visual for UI)
  ↓
FIX
  ↓
RETEST
  ↓
DOCUMENT
```

Do not declare a phase complete merely because code exists.

### Mandatory Visual Inspection Gate for UI Phases (Phases 11–15)

For all user interface phases (Phase 11: Characters & Data, Phase 12: Guides & Builds, Phase 13: Farming & Progression, Phase 14: Teams, Phase 15: Artifact Optimization), phase sign-off **REQUIRES MANDATORY VISUAL INSPECTION**.

A UI phase **MUST NOT** be considered complete merely because:
- The page renders without crashing (HTTP 200)
- The backend API endpoints return valid JSON
- The automated unit/integration test suite (`pytest`) passes
- Python tests pass
- The browser console reports zero JavaScript errors

These are necessary technical prerequisites, but they are **NOT SUFFICIENT** for phase completion.

### Mandatory UI Acceptance Verification Workflow (14-Point Inspection Gate)

During the `VERIFY REAL OUTPUT` stage of every UI phase:
1. **Live Browser Capture**: The agent/developer must load the live page in the browser and capture visual inspection snapshots of all key workflows.
2. **14-Point Criteria Audit**: The UI must be explicitly evaluated against all 14 criteria:
   - [ ] 1. **Automated tests pass**: All unit and integration test suites pass without regressions.
   - [ ] 2. **Backend/API validation passes**: All backend models, schemas, and contract validations succeed.
   - [ ] 3. **No relevant browser console errors**: Browser console is clean of runtime errors or unhandled exceptions.
   - [ ] 4. **Live browser inspection**: Live browser inspection performed with visual capture artifacts.
   - [ ] 5. **Visual comparison against the planned UX architecture**: Card layouts, headers, and tabs strictly match the planned structure.
   - [ ] 6. **Verification of information hierarchy**: Headings, badges, and card boundaries are scannable and logically ordered.
   - [ ] 7. **Verification of responsive layout**: Layout adapts gracefully to varying desktop and mobile viewports.
   - [ ] 8. **Verification of visual asset rendering**: Character portraits, splash banners, element SVGs, weapon-type SVGs, and material icons render crisply with zero missing/broken assets.
   - [ ] 9. **Verification of account personalization**: Account stats, owned vs unowned badges, and inventory comparisons are prominently grounded.
   - [ ] 10. **Verification of loading/empty/error states**: Skeletons, zero-state notices, and fail-closed error boundaries render properly.
   - [ ] 11. **Verification of filters and interactions**: Tabs, search boxes, filters, and drawers respond instantly to user interaction.
   - [ ] 12. **Verification of comparison workflows**: Side-by-side comparisons, stat deltas, and replacement callouts are visually explicit.
   - [ ] 13. **Verification that the UI is not a text wall**: Dense information is conveyed through cards, tables, badges, and drawers rather than prose blocks.
   - [ ] 14. **Verification that the UI resembles a polished production Genshin application**: Matches benchmarks set by Genshin Track and Genshin Optimizer rather than looking like an internal developer prototype.
3. **Remediation Before Documentation**: Any UI surface failing these criteria must be fixed and visually re-tested before the phase can be documented and declared complete.

### Mandatory Production UI Release Gate (Pre-Release Cleanliness Audit)

> [!IMPORTANT]
> **HARD RELEASE GATE — ZERO ENGINEERING LEAKAGE IN PRODUCTION**:
> Before any public or production release (`DEBUG=false`), the agent/developer MUST inspect EVERY user-facing tab and screen against the following 16-point checklist:
> - [ ] 1. **No developer diagnostics**: System Health diagnostics, latency stats, and cache paths are completely excluded.
> - [ ] 2. **No internal source registry**: The source hierarchy, source URLs, and tier definitions are hidden from consumer views.
> - [ ] 3. **No external source names**: No mentions of `"KeqingMains"`, `"KQM"`, `"TCL"`, `"Genshin Optimizer"`, `"Genshin Wiki"`, or community forums on build cards.
> - [ ] 4. **No internal provenance labels**: No internal source IDs, hash markers, or provenance stamps visible in user views.
> - [ ] 5. **No raw JSON / debug dumps**: Zero inspectable raw payload dumps or unformatted database strings.
> - [ ] 6. **No pipeline terminology**: Zero internal jargon (e.g. `BM25 index`, `semantic chunker`, `canonical sync`).
> - [ ] 7. **No developer-only controls**: Test buttons, cache purgers, and mock simulation injection buttons are absent.
> - [ ] 8. **Clean Chat**: Chat responses provide direct answers, visual cards, and actionable advice without router debug pills.
> - [ ] 9. **Clean Character pages**: 10-section layout renders clean game data, account progression, and AI advice with zero source clutter.
> - [ ] 10. **Clean Guides**: Ranked weapons, ER tables, and artifact cards render recommendation hierarchy without citation dashboards.
> - [ ] 11. **Clean Teams**: 4-slot visual composition and rotation sequence chips without pipeline provenance tags.
> - [ ] 12. **Clean Farming**: Material cards display Owned / Required / Deficit and domain schedules without source file labels.
> - [ ] 13. **Clean Artifact Optimizer**: Equipped vs candidate comparisons display stat delta badges without candidate-generation metadata.
> - [ ] 14. **Clean Account pages**: Showcase and inventory render with clean game assets and personal progression markers.
> - [ ] 15. **Consumer Settings & About**: Tab 5 provides genuine user preferences (Theme, UID, AI detail, Privacy summary, App version).
> - [ ] 16. **Finished Product Feel**: The entire application feels like a polished, dedicated consumer Genshin application rather than an internal engineering dashboard.

> [!NOTE]
> **FINAL CORE PRINCIPLE**:
> GenshinIQ should use the best proven ideas from the Genshin ecosystem without becoming a clone.
> - **Internally**: Highly structured, provenance-aware, validated, source-aware, deterministic, and auditable.
> - **Externally**: Clean, visual, personalized, actionable, and professional.
> The user should experience GenshinIQ as a polished personal Genshin assistant — **not as a window into our data pipeline**.
> 
> Future implementation MUST follow this UX/UI architecture and release-gate strategy. These requirements are binding and must not be omitted when the corresponding phases are implemented.

------------------------------------------------------------------------

# 34. Recommended Implementation Order

The practical order is:

``` text
PHASE 0
Baseline + safety
        ↓
PHASE 1
Canonical data pipeline
        ↓
PHASE 2
Version/update system
        ↓
PHASE 3
Provenance/source registry
        ↓
PHASE 4
Knowledge rebuild
        ↓
PHASE 5
Retrieval
        ↓
PHASE 6
Account data
        ↓
PHASE 7
Deterministic build engine
        ↓
PHASE 8
Chat/tool routing
        ↓
PHASE 9
Best-effort knowledge escalation
        ↓
PHASE 10
Grounding/citations
        ↓
PHASE 11
Characters & Data
        ↓
PHASE 12
Guides
        ↓
PHASE 13
Farming/tracking
        ↓
PHASE 14
Teams
        ↓
PHASE 15
Artifact optimization
        ↓
PHASE 16
Simulation
        ↓
PHASE 17
Abyss/current content
        ↓
PHASE 18
System Health
        ↓
PHASE 19
Security/public hardening
        ↓
PHASE 20
Final evaluation/release
```

------------------------------------------------------------------------

# 35. What Should NOT Be Done

Do not:

-   blindly rewrite the whole application
-   introduce microservices
-   add Kubernetes
-   add LangGraph just for appearance
-   build multiple autonomous agents without a demonstrated need
-   add a large vector database before retrieval testing
-   scrape the entire internet
-   treat Reddit as authoritative
-   train/fine-tune Gemini as the main solution to current Genshin data
-   put game logic in the frontend
-   fabricate missing values
-   silently use stale game data
-   call a public Enka showcase the complete account
-   claim an answer is verified when it is only an inference

------------------------------------------------------------------------

# 36. Final Product Architecture

The target architecture is:

``` text
                                  GENSHINIQ
                                      │
    ┌─────────────────────────────────┼─────────────────────────────────┐
    │                                 │                                 │
GAME DATA                       ACCOUNT DATA                        KNOWLEDGE
    │                                 │                                 │
Official HoYoverse              GOOD / Inventory Kamera             KQM Guides / TCL
Project Amber / Ambr            Enka.Network (Showcase)             Official Patch Notes
genshin-db / AnimeGameData      Manual User Data                    Statistical / Community
    │                                 │                                 │
    └─────────────────────────────────┼─────────────────────────────────┘
                                      │
                           NORMALIZED DOMAIN MODEL
                                      │
             ┌────────────────────────┼────────────────────────┐
             │                        │                        │
        STAT ENGINE              BUILD ENGINE            KNOWLEDGE / RAG
             │                        │                        │
             ├────────────────────────┼────────────────────────┤
             │                        │                        │
     ARTIFACT OPTIMIZER          TEAM BUILDER           FARMING PLANNER
             │                        │                        │
             └────────────────────────┼────────────────────────┘
                                      │
                                    GEMINI
                           (Explanation & Reasoning)
                                      │
                                      v
                             ANSWER QUALITY LAYER
                          (Citations & Grounding)
                                      │
                                      v
                                  CHAT / UI
```

### Reference Projects & Non-Dependency Boundaries

``` text
Genshin Track
    ↓
Primary UX / product reference for My Account, character progression, and farming planner

Genshin Optimizer (frzyc)
    ↓
Primary technical/functional reference for stats, formulas, inventory, and optimization

GenshinOptimizer.com
    ↓
Secondary reference for GOOD import workflows and simple artifact optimization UX

* None of the reference projects are required at runtime.
* GenshinIQ implements its own backend services and maintains its own canonical game datasets.
```

------------------------------------------------------------------------

# 37. Final Definition of a Successful GenshinIQ

GenshinIQ is successful when a user can ask:

> "Is my Arlecchino build good?"

and the application can actually:

1.  identify the user's Arlecchino from available account data;
2.  inspect the actual weapon;
3.  inspect the actual artifacts;
4.  inspect talents and constellation;
5.  calculate relevant stats;
6.  retrieve current theorycrafting;
7.  retrieve current game mechanics;
8.  consider the user's team;
9.  calculate meaningful upgrade priorities;
10. explain the result naturally;
11. distinguish fact, calculation and recommendation;
12. cite the relevant evidence;
13. remain current across patches.

The same system should work for:

> "What should I farm today?"

> "Which weapon should I use?"

> "Build me two Abyss teams from my account."

> "Why does this reaction work this way?"

> "Is this artifact an upgrade?"

> "What changed this patch?"

> "What should I build next?"

------------------------------------------------------------------------

# 38. Final Strategic Goal

The ultimate objective is not:

> "Make Gemini know more Genshin facts."

It is:

> **Build a continuously updated Genshin knowledge and computation
> system that allows Gemini to reason over trustworthy data and explain
> the result naturally.**

That distinction is the foundation of the public-quality version of
GenshinIQ.

The five-tab UI remains the product shell.

The real product underneath it is:

``` text
CURRENT DATA
+
TRUSTED KNOWLEDGE
+
PERSONAL ACCOUNT
+
DETERMINISTIC COMPUTATION
+
AI REASONING
+
SOURCE TRANSPARENCY
```

That is the architecture that should be implemented phase-by-phase.
