# GenshinIQ Architecture Documentation

## 1. System Overview

GenshinIQ combines live in-game showcase data, structured canonical game data, authoritative community theorycrafting, and Google Gemini LLMs to create an account-grounded personal Genshin Impact assistant.

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Frontend Presentation Layer                         │
│   - Vanilla HTML5 / CSS3 / JavaScript                                      │
│   - Dark Celestial Glassmorphism Theme                                      │
│   - Enka CDN Asset Pipeline + Resilient Inline Vector Elemental Glyphs      │
│   - Account Showcase Carousel & Splash Art Hero Banners                     │
│   - Today's Domain Rotation & Farming Planner                               │
│   - Direct Action Bridging ("Ask AI to Review Build", "Theorycrafting Guide")│
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
                                       │ Context Assembly
                            ┌──────────▼──────────┐
                            │     RAG Service     │
                            │ - Intent Classifier │
                            │ - Dynamic Patch Date│
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

## 2. Component Breakdown

### 2.1 Backend Core (FastAPI)
- **`backend.main`**: FastAPI application entry point with CORS middleware, router registration, and static frontend hosting.
- **`backend.config`**: Pydantic Settings loading environment configurations from `.env`.
- **`backend.api.routes`**: Clean RESTful endpoints organizing health diagnostics, account showcases, canonical game data, a provenance manifest, curated knowledge, and chat assistant.

### 2.2 Account Integration (`AccountService` & `EnkaClient`)
- **Public Showcase Ingestion**: Connects to Enka.Network API to retrieve public player data without requiring game credentials or private tokens.
- **Profile Avatar Resolution**: Maps `profilePicture.avatarId` to canonical characters and CDN avatar icons.
- **Combat Attribute Normalizer**: Converts raw Enka `fightPropMap` keys into standard Genshin stats (HP, ATK, DEF, CRIT Rate/DMG, ER, EM, Elemental DMG Bonuses).
- **TTL Disk Caching**: Stores retrieved payloads under `data/runtime/showcases/{uid}.json` with a 300-second TTL to respect rate limits.

### 2.3 Game Data Service (`GameDataService`)
- **Canonical Datasets**: Fast in-memory dictionary indices for Characters, Weapons, Artifact Sets, and Materials.
- **Provenance Snapshot**: Emits a live manifest that summarizes dataset hashes, counts, and source/version state.
- **Filtering & Search**: Multi-attribute filtering (element, weapon type, rarity) and cross-entity keyword search.

### 2.4 Knowledge Service (`KnowledgeService`)
- **Curated Guides & Mechanics**: JSON-packaged Markdown articles from KeqingMains, official HoYoverse patch notes, and elemental mechanics references.
- **Source Credibility Hierarchy**:
  1. `AUTHORITATIVE` (Official game patch notes, descriptions, rules)
  2. `THEORYCRAFTING` (KQM guides, frame data, crowning priorities)
  3. `STATISTICAL` (Spiral Abyss usage rates, popular comps)

### 2.5 Retrieval-Augmented Generation (`RAGService` & `GeminiService`)
- **Intent Classifier**: Automatically routes user prompts into `account` or `general` workflows.
- **Dynamic Context Injection**: Injects current real-world date and active Genshin version to prevent temporal hallucination.
- **Grounded System Prompt**: Enforces strict instructions to rely only on provided facts, use exact account numbers, cite sources, and fail closed when data is missing.

---

## 3. Data Integrity & Fail-Closed Guardrails

1. **Structured Data > LLM Memory**: No base stats, scalings, or user build numbers are generated from LLM parametric memory. All numeric values originate from canonical datasets or Enka normalizer output.
2. **Fail-Closed Fallback**: If an account does not have a requested character displayed in their showcase, the model will not invent placeholder builds.
3. **Deterministic Math**: Artifact Crit Value (CV) and total stat sums are computed in Python rather than through LLM arithmetic.

---

## 4. Game Version Architecture & Knowledge Freshness Lifecycle

### 4.1 Explicit Version Concepts
GenshinIQ explicitly decouples four distinct version concepts to avoid future-maintenance drift:
1. **Actual Current Game Version (`current_version`)**: The live patch currently released by HoYoverse (e.g. `7.0`). Represented in `data/canonical/game_versions.json` with `is_released=true` and `is_current=true`. Exactly one release in the registry can have `is_current=true`.
2. **Latest Known Version (`latest_known_version`)**: The highest version verified through an approved source in the canonical registry.
3. **Project Target Version (`project_target_version`)**: The active development anchor (e.g. `7.0`) ensuring that data schemas, tests, and baselines remain deterministic even if runtime sync is offline.
4. **Document Content Version (`game_version`) & Affected Scope (`affected_systems`)**: The patch version against which a knowledge document was authored, accompanied by its dependency scope (e.g. `character:Bennett`, `artifact:HarmonicWhimsy`, `mechanics:BaseATKBuff`).

### 4.2 Decoupled Discovery Lifecycle: DISCOVER → VERIFY → PROMOTE
The automated update pipeline consists of three separate, strictly gated operations:

```text
┌─────────────────────────┐
│       1. DISCOVER       │  Queries Tier 1 HoYoverse official news / version endpoint.
│                         │  Returns candidate: version, patch name, release_date, is_released.
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│       2. VERIFY         │  Strictly validates candidate legitimacy:
│                         │  - is_released == True (rejects upcoming/pre-installation previews)
│                         │  - valid semantic version (rejects invalid jumps e.g. 7.0 -> 7.2)
│                         │  - backed by approved source authority (src_hoyoverse_patch_notes)
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│       3. PROMOTE        │  Atomically updates canonical registry (data/canonical/game_versions.json):
│                         │  - Previous current version: is_current = false
│                         │  - New version: is_current = true, is_released = true
│                         │  - Preserves 100% of historical patch records (53 patches)
│                         │  - Logs patch changes in patch_changes.json
│                         │  - Rebuilds data manifest
└─────────────────────────┘
```

### 4.3 Authoritative Source Hierarchy
GenshinIQ never scrapes Reddit, community forums, social media, blogs, or wikis for version authority:
1. **Official HoYoverse Sources (Tier 1)**: `https://genshin.hoyoverse.com/en/news` (source `src_hoyoverse_patch_notes`).
2. **Approved Structured Data Providers (Tier 3 Fallback)**: Verified canonical registries.
3. **Cached Offline State**: If the network or official endpoints are unreachable, GenshinIQ retains the last verified version and sets `discovery_status = "CACHED_OFFLINE"` without failing closed or assuming valid documents are stale.

### 4.4 Automated Discovery via CLI & Scheduling
To discover updates without manual code edits or JSON editing:
```bash
python scripts/update_game_version.py --check
```
- **Discovery Behavior**:
  - Contacts approved official source.
  - If official source reports `v7.0` (already current): Reports `Verification: PASS`, `Update required: NO`, retains `v7.0`.
  - If official source reports `v7.1` (live released): Validates release evidence, automatically promotes `v7.1` to current, unsets `v7.0` current flag, logs audit output, and rebuilds manifest.
  - If official source reports `v7.2` (upcoming/preview): Verification fails (`REJECTED_UNRELEASED`), does not promote.
  - If source fails: Safely falls back to last verified canonical version with `discovery_status = "CACHED_OFFLINE"`.
- **Scheduled Execution**: Can be safely invoked by Windows Task Scheduler, cron, CI, or application startup.

### 4.5 Change-Aware Freshness Semantics (Why Old Knowledge is Not Blindly Stale)
A newer game version does **not** blindly invalidate older knowledge. Freshness is calculated semantically:
- **`CURRENT`**: Authored for the current version (`v7.0`) or explicitly verified for it.
- **`RECENT_COMPATIBLE`**: Authored for an earlier version (e.g. `v7.0` when the game is `v7.1`), where no intervening patch modified any of the document's `affected_systems` (e.g., Bennett's Base ATK scaling is unchanged in 7.1, so the 7.0 guide remains fully compatible).
- **`STALE`**: An intervening patch explicitly modified one or more of the document's `affected_systems` (e.g., an artifact set rework or character kit adjustment).
- **`HISTORICAL`**: Archival documentation accurate for its era but superseded.
- **`UNKNOWN`**: Insufficient metadata to evaluate compatibility.

### 4.6 Knowledge Revalidation Workflow
Version discovery and knowledge ingestion are strictly decoupled:
1. **New Patch Detected**: Only the version registry and patch change log are updated.
2. **Identification of Affected Knowledge**: `VersionService.get_patch_changes(from_version, to_version)` checks which documents have `affected_systems` intersecting with patch modifications.
3. **Selective Revalidation**: Only flagged documents are scheduled for theorycrafting review or re-ingestion, avoiding full knowledge base wipes.

---

## 5. Phase 5 — Production Hybrid Retrieval Architecture

### 5.1 Core Architectural Principle
> **Retrieval is an evidence-selection mechanism, NOT an authority mechanism.**
> Retrieval ranking selects, orders, and packages candidate evidence without altering its underlying canonical authority tier, truth status, or registered provenance.

```text
User Query
  │
  ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. Query Signals Extraction                                 │
│    - Normalization & tokenization                           │
│    - Entity detection: characters, weapons, artifacts       │
│    - Mode detection: mechanics, character, weapon, farming  │
│    - Historical intent detection                            │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
               ▼                              ▼
┌──────────────────────────────┐ ┌──────────────────────────────┐
│ 2a. BM25 Okapi Lexical Search│ │ 2b. Dense Vector Similarity  │
│   - Field boosts:            │ │   - Provider: LocalSubword   │
│     * Headings: 2.5x         │ │     dense-v1 (256-dim)       │
│     * Character: 2.0x        │ │   - Offline, unit-normalized │
│     * Topic: 1.5x, Body: 1.0x│ │   - Fast cosine sim (<5ms)   │
└──────────────┬───────────────┘ └──────────────┬───────────────┘
               │                                │
               └───────────────┬────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Score Normalization & Fusion                             │
│    - Min-max score scaling to [0.0, 1.0]                    │
│    - Base hybrid score = 0.50 * lexical + 0.50 * semantic   │
│    - Graceful degradation: VECTOR_DEGRADED / LEXICAL_DEGRADED│
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Provenance Validation & Filtering                        │
│    - Validates source_id against central source_registry    │
│    - Rejects unregistered sources & tampered tiers          │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Composite Reranking & Multipliers                        │
│    - Authority Tier: Tier 1 (1.20x) -> Tier 5 (0.90x)       │
│    - Freshness: Current (1.15x) -> Stale (0.65x)            │
│    - Historical Queries: Bypasses stale downweighting       │
│    - Entity Alignment: Matching (2.2x), Conflicting (0.20x) │
│    - Topic Match: Artifact/Weapon/Farming/Mechanics boosts  │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Deduplication & Diversity Filtering                      │
│    - Max 2 chunks per document (prevents guide monopoly)    │
│    - Near-duplicate suppression (token Jaccard > 0.85)      │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. EvidenceBundle Output                                    │
│    - Query, Signals, Ranked RetrievedEvidence items         │
│    - Full retained provenance (URLs, tiers, hashes)         │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Semantic Chunking
Documents are parsed into semantic chunks (`SemanticChunk`) along markdown `#`, `##`, and `###` heading boundaries:
- **Preserved Context**: Breadcrumb headings (e.g. `Kaedehara Kazuha Guide > Weapon Rankings`) are attached to each chunk.
- **Atomic Structures**: Markdown tables, math formulas (`$$...$$`), and bulleted lists are kept intact without midpoint fragmentation.
- **Consolidation**: Image-only headings or tiny sections (<15 words) are prepended to the subsequent section rather than emitted as useless fragments.
- **Inherited Provenance**: Every chunk inherits parent document metadata (`source_id`, `canonical_url`, `authority_tier`, `game_version`, `freshness_status`, `content_hash`).

### 5.3 Hybrid Search & Embedding Service
- **BM25 Okapi (`backend.services.bm25_service`)**:
  - Inverted index with field boosts: Headings (2.5x), Character (2.0x), Topic/Tags (1.5x), Body (1.0x).
  - Robertson-Spärck Jones IDF with length normalization ($k_1=1.5, b=0.75$).
  - Domain synonym expansion (`GENSHIN_DOMAIN_SYNONYMS`): Bridges acronyms like EM -> Elemental Mastery, ER -> Energy Recharge, BoL -> Bond of Life.
- **Local Subword Embedding (`backend.services.embedding_service`)**:
  - Model: `local-subword-dense-v1` (256 dimensions).
  - **Architectural Clarification**: This is an offline, deterministic **subword dense hashing projection** (MD5/signed polynomial hashing over character 3–5-grams, word tokens, and domain synonyms) with $L_2$ unit normalization. It is **NOT** a learned neural transformer model (such as BERT or Ada-002), but provides fast, 100% offline lexical-gap bridging and fuzzy character/term matching without external GPU or network dependencies.
  - Cosine similarity computed in microseconds.
  - Pluggable behind `EmbeddingProvider` protocol.

### 5.4 Index Lifecycle & Deterministic Re-Indexing
- **Storage Location**: `data/runtime/index/` (`chunks.json`, `vectors.json`, `embedding_meta.json`).
- **Model Change Invalidation**: If `meta["model_name"]` or `meta["dimension"]` changes, the index is automatically invalidated and cleared.
- **Incremental Indexing**: `scripts/rebuild_retrieval_index.py` inspects `content_hash` of each document. Unchanged documents are skipped in <1s.
- **CLI Commands**:
  ```bash
  # Force full purge and rebuild
  python scripts/rebuild_retrieval_index.py --force

  # Incremental update based on content hash
  python scripts/rebuild_retrieval_index.py --incremental
  ```

### 5.5 Ranking Formula & Balance
Composite ranking score formula:
$$\text{Score} = \text{BaseScore} \times \text{AuthMult} \times \text{FreshMult} \times \text{SignalMult}$$
1. **Base Score**:
   - **Hybrid (Both Matched)**: $(0.60 \cdot S_{\text{norm\_bm25}} + 0.40 \cdot S_{\text{norm\_vector}}) \times 1.15$ (reinforcing dual-signal candidates).
   - **Lexical Only**: $0.60 \cdot S_{\text{norm\_bm25}}$.
   - **Vector Only**: $0.40 \cdot S_{\text{norm\_vector}}$.
2. **Authority Multiplier**: Tier 1 (1.20x), Tier 2 (1.15x), Tier 3 (1.05x), Tier 4 (1.00x), Tier 5 (0.90x). Gentle influence that never overrides high relevance.
3. **Freshness Multiplier**: Current (1.15x), Recent Compatible (1.05x), Stale (0.75x).
4. **Historical Query Bypass**: If the query asks about historical versions (e.g., "1.0", "patch 5.0"), older versions are ranked neutrally (1.0x) rather than penalized.
5. **Entity & Topic Alignment Multiplier**:
   - Matching character receives $2.2\times$; conflicting character receives $0.20\times$ penalty.
   - For general mechanics queries with no character mentioned, universal mechanics documents receive $1.35\times$ while character-specific guide chunks receive $0.65\times$ isolation.
   - Specific topics (Artifacts, Weapons, Farming) receive $1.4\times$ boost on section-relevant keywords.

### 5.6 Graceful Degradation
- If vector index is unavailable or empty: Falls back to BM25, returns `retrieval_status = "VECTOR_DEGRADED"`.
- If lexical index is unavailable or empty: Falls back to vector, returns `retrieval_status = "LEXICAL_DEGRADED"`.
- If both fail: Returns empty bundle with `retrieval_status = "EMPTY"`.
- Fabricated evidence is never generated.

### 5.7 Evaluation Benchmark Results (32 Curated Queries)
Evaluation across 32 deterministic ground-truth Genshin Impact queries spanning Character Mechanics, Weapons, Artifacts, Game Mechanics, Domain Farming, Patch History, and Semantic Paraphrasing:

| Metric | BM25 Only | Dense Only (Subword Hash) | Hybrid (Fused) |
| :--- | :---: | :---: | :---: |
| **Precision@1** | **1.0000** (100.0%) | 0.8125 (81.3%) | **1.0000** (100.0%) |
| **Precision@3** | **0.8021** (80.2%) | 0.5833 (58.3%) | 0.7812 (78.1%) |
| **Precision@5** | **0.6375** (63.8%) | 0.4500 (45.0%) | 0.6000 (60.0%) |
| **Recall@5** | **1.0000** (100.0%) | 0.8906 (89.1%) | **1.0000** (100.0%) |
| **MRR** | **0.9844** | 0.7523 | **0.9844** |
| **nDCG@5** | 0.9723 | 0.8174 | **0.9725** |

---

## 6. Account Data Architecture (Phase 6 — GOOD v3 Ingestion & Normalization)

### 6.1 Account Data vs Authoritative Knowledge Boundary
GOOD v3 is strictly treated as **user-specific account inventory state**, never authoritative game knowledge.
- **RAG & Knowledge Boundary**: GOOD records are strictly forbidden from being ingested into RAG documents, semantic chunks, embeddings, vector indexes, BM25 Okapi indexes, or the central source registry.
- **Data Flow**:
  ```text
  Raw GOOD v3 JSON
         ↓
  Schema & Boundary Validation
         ↓
  Canonical Entity & Alias Resolution
         ↓
  Normalized Account Snapshot (Instances with Deterministic IDs)
         ↓
  Account API Endpoints (GET /api/account/*)
         ↓
  (Downstream Phase 7+ stat/build engines consume this via API)
  ```

### 6.2 Raw vs Normalized Model Separation
1. **Raw Preservation**: The raw, un-mutated GOOD export is archived at `data/runtime/account/raw_good_snapshot.json` with an accompanying hash manifest (`snapshot_meta.json`).
2. **Normalized Derivation**: The canonical model is stored in `data/runtime/account/normalized_account_snapshot.json` containing:
   - `metadata`: Exporter, schema version, parser version, import timestamp, source file hash, and total counts.
   - `characters`: Owned characters normalized to canonical IDs, levels (1–90), ascension (0–6), constellations (0–6), and talent levels.
   - `weapons`: Unique instances with level, ascension, refinement (1–5), location, locked status, and deterministic `account_instance_id`.
   - `artifacts`: Unique instances with set ID, slot, rarity, level, main stat, substats, location, and deterministic `account_instance_id`.
   - `materials`: Inventory items with canonical material IDs and quantities.
   - `unresolved_records`: Explicit audit trail of unknown entities.

### 6.3 Canonical Identity Resolution
Entity resolution bridges scanner keys to canonical database records:
- **Characters**: Multi-word characters (`Kaedehara Kazuha`, `Raiden Shogun`, `Hu Tao`, `Kamisato Ayaka`, `Arataki Itto`, `Sangonomiya Kokomi`) resolve cleanly without word fragmentation.
- **Resolution Categories**: Every entity logs its status:
  - `EXACT_MATCH`: GOOD key directly matches canonical ID or canonical name.
  - `ALIAS_MATCH`: GOOD key resolved via canonical aliases table (e.g. `GladiatorsFinale` -> `Gladiator's Finale`).
  - `LEGACY_MATCH`: Resolved via legacy identifier mapping.
  - `UNRESOLVED`: Entity preserved in inventory with raw key and quantity, but explicitly flagged without synthetic fabrication.

### 6.4 Inventory Instance Invariants (Weapons & Artifacts)
1. **Multiple Weapon Copies**: Multiple copies of identical weapons (e.g. 16 copies of Dragon's Bane) are legitimate inventory instances. Each copy receives a stable, deterministic instance ID (`weapon_good_{id}`) preserving independent level, refinement, lock status, and equipped location.
2. **Individual Artifact Identity**: Two identical artifacts (e.g. identical set, slot, main stat, and substats) remain distinct inventory objects (`artifact_good_{id}`). Artifacts are never merged or deduplicated away.

### 6.5 GOOD vs Enka Responsibilities
- **GOOD v3**: Primary source of truth for full player inventory (all 50 owned characters, all 239 weapons, all 320 artifacts, all 591 materials).
- **Enka.Network**: Public showcase profile provider (equipped 8-character showcase, public avatar, live fightProp combat attributes, and adventure rank).

### 6.6 Import Idempotency & Deterministic Diffing
- **Idempotent Ingestion**: Re-importing the identical GOOD file produces an identical snapshot hash, identical instance IDs, and zero duplicate instances.
- **Deterministic Diffing (`compute_diff`)**: Compares two snapshots and emits precise diff records:
  - `characters_added`, `characters_removed`, `characters_modified` (level, constellation, talent shifts)
  - `weapons_added`, `weapons_removed`
  - `artifacts_added`, `artifacts_removed`
  - `materials_changed` (`old`, `new`, `delta`)

### 6.7 Security & Input Sanitization
- **Strict Size Bounds**: Payloads capped at 10 MB.
- **Fail-Closed Range Validation**: Levels (1–90), ascension (0–6), constellations (0–6), talents (1–15), refinements (1–5), artifact levels (0–20), material quantities (≥ 0) strictly validated. Impossible values are rejected with HTTP 422.
- **No Path Traversal**: Filesystem storage paths are sandboxed within `data/runtime/account/`; no client input paths or internal filesystem paths are exposed via the API.

---

## 7. Deterministic Build & Stat Engine Architecture (Phase 7)

### 7.1 Pure Deterministic Mathematical Layer
Phase 7 provides an auditable, reproducible calculation pipeline for character builds and combat attributes. It enforces strict mathematical invariants:
- **No AI-Generated Values**: Zero stats or scalings are generated from LLM memory or parameter estimations.
- **Fail-Closed Incomplete Model**: Computations report `CalculationStatus.COMPLETE`, `PARTIAL`, `UNSUPPORTED`, or `INVALID` with explicit missing-field warnings.
- **Zero In-Combat Assumptions**: Passives requiring conditional combat triggers (e.g. stack building, hit counters, enemy HP thresholds) are not falsely baked into the static stat sheet.

### 7.2 Stat Hierarchy & Aggregation Pipeline
Combat attributes are resolved through a layered pipeline:
```text
Character Base Stats (Lv, Asc) + Weapon Base ATK (Lv, Asc)
                            ↓
                     Total Base ATK
                            ↓
────────────────────────────────────────────────────────────────────────
[Percentage Modifiers]
  + Character Ascension Stat (HP%, ATK%, DEF%, CRIT%, ER%, DMG%...)
  + Weapon Secondary Stat (if percentage)
  + Static Weapon Passives (e.g. Staff of Homa +20% HP)
  + Artifact Main Stats (HP%, ATK%, DEF%, ER%, CR%, CD%, DMG%...)
  + Artifact Substats (HP%, ATK%, DEF%, ER%, CR%, CD%...)
  + Active 2-Piece Artifact Set Bonuses (e.g. 2pc Gladiator +18% ATK)
────────────────────────────────────────────────────────────────────────
[Flat Additions]
  + Artifact Flower Main Stat (+Flat HP)
  + Artifact Plume Main Stat (+Flat ATK)
  + Artifact Substats (Flat HP, Flat ATK, Flat DEF, Flat EM)
  + Weapon Secondary Stat (if flat, e.g. EM)
  + Character Ascension Stat (if flat, e.g. EM)
────────────────────────────────────────────────────────────────────────
[Derived Combat Attributes]
  Final HP  = (Character Base HP) * (1 + Sum HP%) + (Sum Flat HP)
  Final ATK = (Character Base ATK + Weapon Base ATK) * (1 + Sum ATK%) + (Sum Flat ATK)
  Final DEF = (Character Base DEF) * (1 + Sum DEF%) + (Sum Flat DEF)
  Final CRIT Rate = 0.05 + Sum CRIT Rate%
  Final CRIT DMG  = 0.50 + Sum CRIT DMG%
  Final ER        = 1.00 + Sum ER%
  Final EM        = 0.00 + Sum EM
  Crit Value (CV) = 2 * (Artifact CRIT Rate%) + (Artifact CRIT DMG%)
```

### 7.3 Character & Weapon Stat Resolution
- **Characters**: Levels 1–90 and Ascension Phases 0–6 resolved from `data/processed/game_data/characters.json` and raw promote definitions (`data/raw/game_data/avatars/`). Ascension special stats unlock at Phase 2 (Lv40+) and scale through Phase 6 (Lv80+).
- **Weapons**: Base ATK and secondary stats scale across levels 1–90. Refinement levels 1–5 scale static passives where supported.
- **Artifacts**: Main stats follow canonical 5-star / 4-star progression curves. Substats are preserved from exact account instances without roll loss.

### 7.4 Build Snapshot & Comparison Primitives
- **Reproducible Snapshots (`CharacterBuildSnapshot`)**: Combines character identity, equipped weapon, equipped artifacts, calculated combat stats, and full auditable breakdown. Identical inputs guarantee byte-identical outputs.
- **Build Comparison (`BuildComparison`)**: Deterministic delta ($\Delta$) computation between Build A and Build B, producing exact attribute deltas ($\Delta \text{ATK}$, $\Delta \text{HP}$, $\Delta \text{CRIT}$, $\Delta \text{CV}$) without optimization or heuristics.

### 7.5 REST API Surface
- `GET /api/build/{character_id}`: Full build snapshot for owned or canonical character.
- `GET /api/build/{character_id}/stats`: Derived combat attribute sheet.
- `GET /api/build/{character_id}/breakdown`: Auditable mathematical contribution breakdown.
- `POST /api/build/calculate`: Ad-hoc build calculation for arbitrary character/weapon/artifact gear.
- `POST /api/build/compare`: Deterministic delta comparison between two builds.



