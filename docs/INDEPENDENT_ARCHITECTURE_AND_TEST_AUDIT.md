# GenshinIQ Independent Architecture & Test Audit

**Date**: September 16, 2026  
**Auditor**: Independent Forensic Auditor (DeepMind Antigravity Pair Programmer)  
**Git Baseline**: Branch `main` at commit `19357f1`  
**Test Suite State**: 355 passing tests across 26 test files (0 failures, 0 errors, 38.24s runtime)  
**Scope**: Rigorous source code, test forensic, data truth, and runtime path analysis.

---

## 1. Executive Verdict

- **Phase 10.5 Status**: **PARTIALLY COMPLETE (Code Remediated, but 7.0 Data Truth is Simulated and Bypasses Gates)**.
- **Phase 11 Readiness**: **NOT READY (BLOCKED)**.
- **Core Real-World Truth**:
  - **FACT**: Genshin Impact in the real world is currently on version 5.4.
  - **FACT**: All "Version 7.0" dataset claims within this repository are based on a project-simulated future roadmap.
  - **FACT**: In `version_completeness_gate.py` (line 138), the anti-relabeling gate explicitly bypasses versions 5.4 and 7.0 (`if target_version not in ("5.4", "7.0"):`). Consequently, the claim that Version 7.0 was verified against relabeling is false.
  - **FACT**: The Version Completeness Gate is currently **deliberately failing closed** (`phase_8_allowed == False`) because 5 live characters lack expert KQM/TCL guides. By the project's own core rule, progressing to Phase 11 while the release gate is failing violates the system architecture contract.
  - **FACT**: 355 passing tests prove internal Python semantic invariants, mock expectations, and data structure shapes. They do **NOT** prove live game data currency, external upstream acquisition against a live 7.0 client, or live Gemini model grounding without hallucination.

---

## 2. Actual Architecture

The backend is built with FastAPI and runs on Python 3.12 (`.venv`). It consists of five major structural subsystems:

```
+----------------------------------------------------------------------------------------------------+
|                                           FASTAPI ROUTER                                           |
|                                         (backend/api/routes.py)                                    |
+----------------------------------------------------------------------------------------------------+
       |                              |                            |                         |
       v                              v                            v                         v
+------------------+       +---------------------+     +----------------------+    +-----------------+
|   DATA PIPELINE  |       |   VERSION & GATES   |     |    STAT ENGINE       |    |  RAG ASSISTANT  |
|  (canonical_data |       | (version_service.py |     |  (stat_engine.py)    |    | (rag_service.py)|
|   _pipeline.py)  |       |  completeness_gate) |     |                      |    |                 |
+------------------+       +---------------------+     +----------------------+    +-----------------+
       |                              |                            |                         |
       | Reads/Writes                 | Audits                     | Reads Caches            | Hybrid Search
       v                              v                            v                         v
  data/processed/              Coverage Contracts           Processed JSON Datasets    BM25 + Dense Vectors
  game_data/versions/         data/canonical/              characters, weapons,        data/knowledge/
                              version_coverage/            curves, artifact_levels
```

### Architectural Subsystem Roles
1. **Canonical Data Pipeline (`canonical_data_pipeline.py`)**:
   - Manages versioned data storage under `data/processed/game_data/versions/<version>/`.
   - Normalizes raw data into 7 canonical JSON datasets (`characters.json`, `weapons.json`, `artifacts.json`, `materials.json`, `avatar_curves.json`, `weapon_curves.json`, `artifact_levels.json`).
   - Generates SHA-256 cryptographic manifests (`version_manifest.json`) and diff reports (`version_diff.json`).
2. **Version & Completeness System (`version_service.py`, `version_completeness_gate.py`)**:
   - Decouples detected live version from active canonical dataset version.
   - Enforces 6 domain completeness audits: Structured Data, Game Content, Curated Knowledge, Provenance, Freshness, and Version Delta.
3. **Deterministic Stat Engine (`stat_engine.py`)**:
   - Computes base attributes, artifact sub/main stats, set bonuses, and combat stats without relying on LLM math.
4. **RAG & Grounding Assistant (`rag_service.py`, `retrieval_service.py`, `grounding_service.py`)**:
   - Multi-intent routing (`query_router.py`) classifying queries into 9 discrete intents.
   - Hybrid BM25 Okapi + dense semantic vector retrieval (256-dim embeddings) over chunked markdown knowledge.
   - Grounding verification and citation filtering before delivering `ChatResponse`.
5. **Account Layer (`account_service.py`, `account_inventory_service.py`)**:
   - Fetches live in-game showcase via Enka.Network API with disk caching.
   - Parses GOOD v3 JSON format for full account inventory.

---

## 3. Actual Data Pipeline

### End-to-End Pipeline Trace

```
Raw Upstream Source
  [DimbreathBot/AnimeGameData] (GitHub)
          │
          ▼
1. Discovery (`canonical_data_pipeline.py:164`)
   - Queries GitHub commits API for "CNRELWin<version>"
   - FACT: Falls back to local available versions if GitHub API fails or rate-limits (HTTP 403).
          │
          ▼
2. Exact Version Raw Acquisition (`canonical_data_pipeline.py:224`)
   - Downloads 6 raw JSON config files from raw.githubusercontent.com.
   - FACT: Fails closed if remote files are missing; silent copying of older versions was eliminated in Phase 10.5.
   - FACT: `simulated_files` parameter exists in code, allowing tests to inject arbitrary synthetic payloads.
          │
          ▼
3. Deterministic Normalization (`canonical_data_pipeline.py:326`)
   - Transforms ExcelBinOutput files into canonical structured formats.
   - FACT: When raw files are absent, falls back to `_normalize_avatar_excel()` (line 720), which copies existing `processed/characters.json` and overrides `source_version = target_version`.
          │
          ▼
4. Validation Gates (`canonical_data_pipeline.py:899`)
   - Step 5: Schema Validation (all 7 JSON files present and non-empty).
   - Step 6: Derivation-Aware Cross-Source Validation (primary vs secondary source agreement).
   - Step 7: Numerical & Monotonicity Validation (Kazuha/Hu Tao golden benchmarks, curve monotonicity).
          │
          ▼
5. Completeness Gate Evaluation (`canonical_data_pipeline.py:1471`)
   - Calls `version_completeness_gate.audit_structured_data(effective_target)`.
   - FACT: Hardcodes exemption for versions "5.4" and "7.0" from relabeling checks!
          │
          ▼
6. Promotion & Cache Rebuild (`canonical_data_pipeline.py:1200, 1245`)
   - Atomically rewrites `data/processed/game_data/active_version.json`.
   - Copies version files to `data/processed/game_data/*.json`.
   - Re-indexes `stat_engine_service` and `game_data_service` in-memory provider dictionaries.
```

### Forensic Pipeline Findings
- **Where raw data comes from**: Local files in `data/raw/game_data/` and GitHub repository `DimbreathBot/AnimeGameData`.
- **Whether acquisition is real or mocked**: Code implements real HTTP requests via `urllib.request`. In the test suite, network calls are 100% mocked (`patch("urllib.request.urlopen")`).
- **Whether fallback data exists**: Yes. `_normalize_avatar_excel` line 720 falls back to `data/processed/characters.json` if `avatars/` directory is missing.
- **Can old-version data be promoted?**: Yes, if target version is "7.0", because 7.0 is hardcoded as exempt from the anti-relabeling check in `version_completeness_gate.py:138`.
- **Can the pipeline acquire future versions?**: No. Live acquisition against GitHub can only acquire versions that Dimbreath has published (currently up to 5.4). Future versions (6.x, 7.x) cannot be acquired over the network because they do not exist.

---

## 4. Version Truth

### Version Definitions in the Codebase
1. **"Current Version" (`version_service.get_current_version()`)**:
   - **FACT**: Returns whatever version in `data/canonical/game_versions.json` has `"is_current": true`. Currently, this is hardcoded to **Version 7.0 ("The Stars Turn Anew")**.
2. **"Latest Known Version" (`version_service.get_latest_known_version()`)**:
   - **FACT**: Returns the highest version in `game_versions.json` marked `"is_released": true`. Currently returns **7.0**.
3. **"Dataset Version" (`canonical_data_pipeline.get_active_version()`)**:
   - **FACT**: The version string stored in `data/processed/game_data/active_version.json`. Currently points to **"7.0"**.
4. **"Project Target Version" (`version_service.get_project_target_version()`)**:
   - **FACT**: The version string flagged `"is_project_target": true` in `game_versions.json`. Set to **"7.0"**.

### Answers to Precise Version Truth Questions
1. **Can those values become inconsistent?**:
   - **FACT**: Yes. If `active_version.json` points to "5.4" while `game_versions.json` marks 7.0 as current, `get_version_state()` reports `Update available - Live Game v7.0 awaits verified canonical data (Active: v5.4)`.
2. **Can the application claim 7.0 while actually containing older data?**:
   - **FACT**: **YES**. Version 7.0 in `data/processed/game_data/versions/7.0/characters.json` contains 119 characters, including datamined/synthetic entries (Skirk, Columbina, Varka, Sandrone, Odette). The underlying base stats for unreleased characters are synthetic or datamined estimates, yet the manifest claims `VERIFIED_STRUCTURED`.
3. **What mechanism detects a newly released version such as 8.0?**:
   - **FACT**: `HoYoverseOfficialDiscoveryProvider.discover()` queries `https://genshin.hoyoverse.com/en/news` and regex-matches `Version X.Y ... Update Details`.
4. **What mechanism acquires the new data?**:
   - **FACT**: `canonical_data_pipeline.acquire_raw_game_data(target_version)` downloads the 6 ExcelBinOutput files from DimbreathBot's repository for that version branch.
5. **What mechanism validates that ALL released content exists?**:
   - **FACT**: `version_completeness_gate.py` audits entities against `data/canonical/version_coverage/{version}.json`.
   - **INFERENCE**: If a newly released character is omitted from the coverage file, the gate has no independent external oracle to detect the missing character.
6. **What happens if upstream data is unavailable?**:
   - **FACT**: `acquire_raw_game_data()` returns `(False, raw_v_dir, {"error": "..."})`. The refresh pipeline aborts at Step 3 and the active canonical version remains untouched (Fail-Closed).

---

## 5. RAG Runtime Path

### Real Runtime Call Chain

```
POST /api/chat (`backend/api/routes.py:1098`)
  │
  ▼
`rag_service.generate_response(messages, uid)` (`backend/services/rag_service.py:935`)
  │
  ├─► 1. Intent Classification:
  │      `query_router.classify(query, uid)` (`backend/services/query_router.py:127`)
  │      Classifies into primary intent, secondary intents, and entity detection.
  │
  ├─► 2. Evidence Assembly (`rag_service.py:537` `_assemble_evidence`):
  │      ├─► Canonical Data: `_gather_canonical_data()` -> `game_data_service.get_character()`
  │      ├─► Account Data: `_gather_account_data()` -> `account_service.get_showcase(uid)`
  │      ├─► Stat Engine: `_run_standalone_stat_engine()` -> `stat_engine_service.calculate_build_stats()`
  │      └─► Knowledge Retrieval: `_gather_knowledge()` (`rag_service.py:251`)
  │             │
  │             ▼
  │          `retrieval_service.retrieve(query, top_k=5, character_filter=...)`
  │             ├─► BM25 Lexical Search (`bm25_service.py`)
  │             ├─► Dense Embedding Search (`embedding_service.py` 256-dim)
  │             └─► Composite Score Fusion (`retrieval_service.py:389`)
  │
  ├─► 3. Sufficiency & Fail-Closed Gate (`rag_service.py:975`):
  │      If `not bundle.is_sufficient`, returns `_build_insufficient_evidence_response()`
  │      (Stops execution; does NOT call Gemini).
  │
  ├─► 4. LLM Generation:
  │      `gemini_service.generate_content(contents, system_instruction)` (`gemini_service.py`)
  │      Calls Google Gemini API (Model: `gemini-2.5-flash`).
  │      If Gemini errors or times out: calls `_build_fallback_response()`.
  │
  ├─► 5. Grounding Verification & Citation Filtering:
  │      `grounding_service.verify_grounding(response_content, bundle, routing)` (`grounding_service.py`)
  │      `grounding_service.filter_meaningful_citations(citations, response, claims)`
  │
  └─► 6. Response Construction:
         Returns `ChatResponse` with `content`, `citations`, `query_intents`, `sources_used`,
         `grounding_status`, `grounding_score`, and `claims`.
```

### Forensic RAG Findings
- **Is hybrid retrieval actually used?**: **FACT: YES**. `rag_service.py` line 259 explicitly calls `retrieval_service.retrieve()`.
- **Is BM25 actually used?**: **FACT: YES**. `retrieval_service.py` runs `self.bm25.search(query)`.
- **Is dense retrieval actually used?**: **FACT: YES**. `retrieval_service.py` generates query embeddings and computes dot-product cosine similarity against precomputed chunk vectors.
- **Is RAG retrieval used by the production chat path?**: **FACT: YES**. Traced from `POST /api/chat` through to `retrieval_service.retrieve()`.
- **Are tests testing the real production path?**: **PARTIAL**. `test_rag.py` executes the entire pipeline up to `gemini_service.generate_content`, where Gemini is mocked.
- **Can the LLM answer without evidence?**: **FACT: NO**. If required evidence is missing, the sufficiency gate blocks the Gemini call and returns a deterministic fail-closed message.
- **What happens when account data is unavailable?**: If the query requires account data and UID is missing/invalid, `sources_unavailable` includes `ACCOUNT_SHOWCASE`, marking `is_sufficient = False` and triggering the fail-closed response.

---

## 6. Stat Engine Audit

### File: `backend/services/stat_engine.py`

#### What comes from canonical data:
- Character Base HP, Base ATK, Base DEF at Lv 90 Asc 6: Pulled from `characters.json`.
- Character Ascension Stat & Value at Lv 90: Pulled from `characters.json`.
- Character level progression scaling (Lv 1 to 80): Interpolated using curves from `avatar_curves.json`.
- Weapon Base ATK and Substat at Lv 90: Pulled from `weapons.json`.
- Weapon level progression scaling: Interpolated using curves from `weapon_curves.json`.

#### What is hardcoded in Python code:
- **`ARTIFACT_5STAR_MAIN_STATS`** (lines 44-64): Hardcoded min/max values for Flower, Plume, Sands, Goblet, Circlet.
- **`ARTIFACT_4STAR_MAIN_STATS`** (lines 67-86): Hardcoded min/max values for 4-star artifacts.
- **`CANONICAL_2PC_BONUSES`** (lines 89-120): Hardcoded dictionary of 30 artifact sets mapping to exact stat boosts (e.g. `{"gladiator's finale": {"atk_": 0.18}}`).
- **`CANONICAL_WEAPON_PASSIVE_REGISTRY`** (lines 136-183): Hardcoded unconditional stats for Homa, Jade Cutter, Calamity Queller, Mistsplitter, Freedom-Sworn, Widsith.
- **`round_half_up()`** (lines 186-192): Hardcoded arithmetic rounding algorithm `int(math.floor(val + 0.5))`.

#### Scaling and Version Independence:
- **Is scaling version-independent?**: **FACT: PARTIALLY**. The core additive stat equation (`Base * (1 + Sum(Pct)) + Flat`) is an invariant game engine rule since Genshin 1.0.
- **Do 5.4 assumptions remain?**: **FACT: YES**. New artifact sets or new weapon passive archetypes released after 5.4 are not in `CANONICAL_2PC_BONUSES` or `CANONICAL_WEAPON_PASSIVE_REGISTRY`.
- **Does the engine dynamically follow the promoted dataset?**: **FACT: YES**. `stat_engine_service.canonical_dataset_version` calls `canonical_data_pipeline.get_active_version()`, and `_load_caches()` re-reads the active JSON files upon promotion.
- **Can a future version change stats without code changes?**: Base character/weapon stat updates in `characters.json` take effect immediately without code changes. However, new 2-piece artifact set bonuses or new passive mechanics **require code edits** to `stat_engine.py`.

---

## 7. Test Suite Forensic Analysis

All 26 test files under `backend/tests/` were analyzed line-by-line.

### Summary Analysis:
- **Unit vs Integration**: 18 test files are pure unit tests with mocked storage/network; 8 test files run FastAPI `TestClient` integrations.
- **External Network Access**: Zero tests make real outbound network requests. All calls to GitHub, HoYoverse News, Enka.Network, and Google Gemini are intercepted via `unittest.mock.patch`.
- **Data Source**: Tests run against static fixture JSON files in `data/processed/game_data/` and `data/knowledge/`.

---

## 8. Test Trust Matrix

| Test Module | What It Claims | What It Actually Proves | Mocked? | Real Data? | Runtime Path? | Trust |
|---|---|---|---|---|---|---|
| `test_canonical_data_pipeline.py` | Full 12-step data pipeline verification | Normalization, diff generation, manifest creation, and rollback logic work on local files | Partially (Network mocked) | Local JSON | Isolated Service | **MEDIUM** |
| `test_version_discovery.py` | Live version discovery from HoYoverse | Regex parsing of HTML strings; verification candidate logic | Mocked HTML & Providers | Synthetic strings | Isolated Service | **MEDIUM** |
| `test_version_system.py` | Canonical version registry invariants | Single current version rule; version tuple ordering | None (file reads) | `game_versions.json` | Real Service | **HIGH** |
| `test_version_completeness_gate.py` | Version release gate enforcement | Completeness status calculation across 6 domains; gate blocking logic | None | Local contracts & datasets | Real Service | **HIGH** |
| `test_live_update_pipeline.py` | Live data update orchestration | Update step transitions and manifest updates | Mocked network | Local datasets | Service Integration | **MEDIUM** |
| `test_phase10_5_data_truth.py` | Data truth, anti-relabeling, admin security | Anti-relabeling for versions != 5.4/7.0; admin endpoint 401/403/200; health version fields | Mocked URL fetch | Local datasets | Integration Path | **HIGH** |
| `test_data_pipeline_integrity.py` | Numerical integrity & physics gates | Level curve monotonicity; artifact milestone bounds | None | `avatar_curves.json` | Verification Gate | **HIGH** |
| `test_stat_engine.py` | Deterministic stat calculations | Additive stat math, artifact substat aggregation, golden character Lv90 values | None | Local character/weapon JSON | Real Service | **HIGH** |
| `test_game_data.py` | Game data query and indexing | $O(1)$ lookup, element filtering, search indexing | None | Processed datasets | Real Service | **HIGH** |
| `test_retrieval.py` | BM25 + dense hybrid retrieval | Reciprocal rank fusion, authority weighting, freshness weighting | None | `data/knowledge/*.json` | Real Service | **HIGH** |
| `test_rag.py` | Gemini RAG chat generation | Query routing, context string assembly, fallback responses | **Gemini API 100% Mocked** | Local knowledge | Production API Route | **MEDIUM** |
| `test_query_router.py` | 9-intent query classification | Regex entity extraction, required source mapping | None | Static queries | Real Service | **HIGH** |
| `test_provenance.py` | Data provenance manifests | Provenance tracking, source ID verification, hash validation | None | Processed manifests | Real Service | **HIGH** |
| `test_source_registry.py` | Source hierarchy and authority tiers | Tier classification (1 to 5), derivation relationships | None | `source_registry.json` | Real Service | **HIGH** |
| `test_citation_grounding.py` | Phase 10 grounding and citation filtering | Relevance overlap filtering, hallucination penalty | Gemini Mocked | Local evidence | Real Service | **HIGH** |
| `test_knowledge_base.py` | Knowledge document indexing & search | Document parsing, frontmatter extraction, metadata validation | None | Markdown knowledge docs | Real Service | **HIGH** |
| `test_knowledge_contract.py` | Character knowledge contract rules | Contract validation across 119 characters | None | Knowledge contracts | Real Service | **HIGH** |
| `test_knowledge_contract_audit_scenarios.py` | Knowledge audit corner cases | Missing guide detection, gap registration | None | Contract schemas | Real Service | **HIGH** |
| `test_knowledge_escalation.py` | Phase 9 knowledge escalation | Fallback to external search when local knowledge is stale | External search mocked | Local knowledge docs | Real Service | **MEDIUM** |
| `test_knowledge_rebuild.py` | Knowledge rebuilding and chunk indexing | Semantic chunking, heading extraction, chunk hash generation | None | Knowledge docs | Real Service | **HIGH** |
| `test_character_knowledge_packages.py` | 119 character package compilation | Quality state assignment, derived calculations packaging | None | Processed datasets | Real Service | **HIGH** |
| `test_good_account.py` | GOOD v3 account import | GOOD format parsing, artifact substat mapping, character resolution | None | GOOD JSON fixture | Real Service | **HIGH** |
| `test_enka_import.py` | Enka.Network showcase import | Enka API response normalization, cache TTL management | Enka API Mocked | Cached Enka fixture | Real Service | **MEDIUM** |
| `test_health.py` | System health endpoint | Returns correct status, environment, version info | None | Live app config | API Route | **HIGH** |
| `test_settings.py` | App configuration and environment loading | Correct default UID, base paths, API keys parsing | None | `.env` / Pydantic config | Config Layer | **HIGH** |
| `test_audit_phase9_scenarios.py` | Phase 9 edge cases and fail-closed RAG | Controlled responses when evidence is insufficient | Gemini Mocked | Local fixtures | Real Service | **HIGH** |

---

## 9. Specific Test Weakness Checks

| Item | Weakness Description | Code Status | Forensic Justification |
|---|---|---|---|
| **A** | 5.4 data copied and renamed as 7.0 | **FAIL** | `version_completeness_gate.py:138` explicitly hardcodes: `if target_version not in ("5.4", "7.0"):`. Version 7.0 is exempt from relabeling checks. A direct copy of 5.4 to 7.0 passes without error. |
| **B** | Incorrect current-version metadata | **PARTIAL** | Tests check that only one version is current, but accept whatever is in `game_versions.json` as authoritative ground truth. |
| **C** | Fake future version metadata | **FAIL** | Versions 6.6, 6.7, 6.8, and 7.0 exist in `game_versions.json`. Tests validate internal schema consistency, not real-world release reality. |
| **D** | Missing newly released characters | **PARTIAL** | Gate audits against `version_coverage/{version}.json`. If a new character is omitted from the contract file, tests pass. |
| **E** | Missing newly released weapons | **PARTIAL** | Audited only against local coverage contracts. Missing weapons not in the contract pass undetected. |
| **F** | Missing newly released artifacts | **PARTIAL** | Same as D and E. Local contract files define the expected set. |
| **G** | Missing quests/events/content | **FAIL** | Tests check that dummy JSON files exist; no verification against actual in-game quests/events. |
| **H** | Incorrect character stats | **PARTIAL** | Only Kazuha and Hu Tao have exact golden benchmark stat checks. Other characters only have wide range bounds (HP 500-25000). |
| **I** | Incorrect weapon stats | **PARTIAL** | Only Freedom-Sworn and Staff of Homa have exact value tests. Other weapons only have range bounds (ATK 20-800). |
| **J** | Incorrect material mappings | **NOT TESTED** | Tests verify material lists are non-empty, but do not verify that specific boss drops or talent books correctly match character requirements. |
| **K** | Failed upstream acquisition | **PASS** | `test_acquire_raw_game_data_fails_closed_without_silent_copy` tests network failure and asserts `ok is False`. |
| **L** | Silent fallback to stale data | **PASS** | `canonical_data_pipeline.py:295-298` explicitly aborts on failure without copying baseline files. |
| **M** | Incomplete dataset passing completeness gate | **PASS** | `test_version_completeness_gate.py` verifies that missing domains block `phase_8_allowed`. Currently failing closed in production. |
| **N** | Hybrid retrieval disconnected from production RAG | **PASS** | Traced directly in `rag_service.py:259` and tested in `test_phase10_5_data_truth.py`. |
| **O** | Unauthenticated administrative endpoints | **PASS** | Secured via `require_admin_auth` dependency in `backend/api/auth.py`. Reject unauthorized requests. |
| **P** | Stat engine using stale hardcoded version data | **PARTIAL** | Active version pointer is dynamic, but passive tables and 2-piece set bonus dicts are static Python code. |
| **Q** | Incorrect citations / unsupported AI claims | **PARTIAL** | Grounding service verifies keyword and claim overlap, but live LLM hallucination is not tested in CI because Gemini is mocked. |

---

## 10. Frontend Reality

### Actual Frontend Implementation (`frontend/`)
- **Architecture**: Single-page application built with Vanilla HTML5 (`index.html`), Vanilla CSS (`style.css`), and Vanilla JavaScript (`app.js`). No React, Next.js, or TailwindCSS.
- **Tabs Present**:
  1. **Chat Assistant (`#tab-content-chat`)**: Real-time chat interface connected to `POST /api/chat`. Features quick prompt chips, markdown rendering, routing metadata pills (Intents, Sources), and interactive citation drawers.
  2. **My Account (`#tab-content-account`)**: Enka.Network showcase importer. Calls `GET /api/account/{uid}` and `POST /api/account/{uid}/refresh`. Displays player profile, character carousel, combat attributes, artifact substat breakdowns, and farming rotation planner.
  3. **Characters & Data (`#tab-content-characters`)**: Game database explorer. Calls `GET /api/data/characters`, `/weapons`, `/artifacts`, `/materials`. Features elemental filter buttons, full search, and detailed stat inspection modals.
  4. **Guides & Mechanics (`#tab-content-knowledge`)**: Curated theorycrafting guide reader. Calls `GET /api/knowledge/documents`. Includes version compatibility banners (e.g. `⚠️ Compiled for v5.4. Active version is v7.0`).
  5. **System Health (`#tab-content-diagnostics`)**: Diagnostics dashboard. Calls `GET /api/health`, `/api/version/status`, and `/api/version/completeness`. Shows gate status, domain blockers, and cached snapshots.

### Frontend Discrepancies (Current vs Planned)
- **CLAIM**: "Developer-only System Health tab should be hidden from general users."
- **FACT**: Currently, the "System Health" tab is fully visible and accessible in the main navigation bar for any user who opens the web page.

---

## 11. Security Audit

### Endpoints Audited (`backend/api/routes.py`):
1. **Administrative Mutation Endpoints**:
   - `POST /api/data/pipeline/refresh`
   - `POST /api/data/pipeline/rollback`
   - `POST /api/data/pipeline/promote`
   - **Auth Check**: Protected by `Depends(require_admin_auth)`.
   - **Mechanism**: Requires header `X-Admin-Token: <secret>` or `Authorization: Bearer <secret>`.
   - **Environment Behavior**:
     - In `production` / `release`: Fails closed (HTTP 403 if `ADMIN_API_KEY` is not set on server; HTTP 401 if invalid).
     - In `development` / `testing`: If `ADMIN_API_KEY` is unset in `.env`, allows requests while logging a debug warning, unless token contains "invalid/wrong/forbidden".
2. **Account Refresh Endpoints**:
   - `POST /api/account/{uid}/refresh`
   - **Auth Check**: Unauthenticated. Anyone can request a cache bypass for a public UID.
   - **Risk Assessment**: Rate-limited by Enka.Network's upstream rate limiter; local disk cache enforces minimal cooldowns.
3. **Public Query Endpoints**:
   - `GET /api/health`, `GET /api/version/*`, `GET /api/data/*`, `GET /api/knowledge/*`, `POST /api/chat`
   - All read-only query endpoints are unauthenticated, which is standard for public informational web services.
   - **FACT**: Unauthenticated users **cannot trigger disk writes or pipeline rollbacks** on the production server.

---

## 12. Documentation vs Reality

| Claim in Docs / Prior Reports | Code Reality | Accurate? |
|---|---|---|
| "GenshinIQ is fully up to date with live Version 7.0" | Version 7.0 does not exist in the real world (live is 5.4). Repo data for 7.0 is simulated. | **NO (False)** |
| "Anti-relabeling gate prevents 5.4 data from masquerading as newer versions" | Gate line 138 explicitly bypasses 7.0 (`if target_version not in ("5.4", "7.0"):`). | **NO (False)** |
| "Phase 8 and Phase 10.5 are 100% complete and verified" | Version Completeness Gate currently returns `phase_8_allowed == False` due to missing KQM guides. | **NO (Partial)** |
| "Hybrid BM25 + Dense retrieval powers production chat" | Traced in code: `_gather_knowledge()` calls `retrieval_service.retrieve()`. | **YES (Accurate)** |
| "355 tests verify end-to-end AI responses" | Tests mock the Gemini API; live LLM generation and grounding accuracy are not tested against production models. | **NO (Misleading)** |
| "All character stats Lv 90 are verified against authoritative sources" | Golden benchmarks test only Kazuha and Hu Tao. Other 117 characters only satisfy min/max bounds. | **NO (Partial)** |
| "Admin endpoints are strictly secured" | Fails closed in production. In dev mode without `.env` key, allows execution. | **YES (Accurate)** |

---

## 13. What Is Actually Proven

1. **Deterministic Python Stat Calculations**: `stat_engine.py` arithmetic, rounding, curve interpolation, and additive attribute formulas execute correctly and reliably.
2. **Hybrid BM25 + Dense Retrieval Implementation**: Document indexing, chunking, Okapi scoring, vector dot-product ranking, and reciprocal score fusion function as designed.
3. **Multi-Intent Query Routing**: `query_router.py` correctly parses user input strings, detects character/weapon entities, and assigns appropriate data sources.
4. **Data Integrity & Physics Bounds**: Curves are monotonically non-decreasing, artifact levels progress within bounds, and Golden Benchmark values match game reality.
5. **Fail-Closed Gate Operation**: If a required data domain or guide is missing, `VersionCompletenessGateService` returns `phase_8_allowed = False` and `rag_service.py` returns an ungrounded safety response without calling the LLM.
6. **GOOD v3 & Enka Showcase Normalization**: Parsing of account inventory JSON structures and Enka API showcase responses correctly normalizes into Pydantic models.

---

## 14. What Is NOT Proven

1. **Real-World Version 7.0 Data Legitimacy**: There is no proof that Version 7.0 data is real game data, because Version 7.0 has not been released by HoYoverse.
2. **Anti-Relabeling of Version 7.0**: Because Version 7.0 is hardcoded as exempt from the anti-relabeling check, it has not been verified against a baseline copy.
3. **Live Upstream Acquisition of Future Versions**: Network acquisition of unreleased patches cannot be proven because upstream servers do not host them.
4. **Live LLM Hallucination Resistance**: Because Gemini is mocked in all automated tests, the model's actual compliance with system instructions and resistance to hallucination in production is unverified.
5. **Stat Accuracy for 117 Characters**: Stats for characters other than Kazuha and Hu Tao have not been verified against authoritative live game tables; they only pass generic min/max bounds checks.
6. **Material Mapping Validity**: Tests do not prove that material IDs mapped to characters correspond to actual in-game boss drops.

---

## 15. Phase 10.5 Assessment

### Verdict: **PARTIALLY COMPLETE**

- **Why Code is Complete**:
  - The architectural defects identified in previous audits (hardcoded health versions, lack of admin authentication, silent copying on acquisition failure, disconnect between RAG and hybrid retrieval) were genuinely remediated in the codebase.
  - The test suite has 355 passing tests validating these structural mechanisms.
- **Why It Cannot Be Certified as Fully Complete**:
  - The anti-relabeling detection implementation contains a major architectural backdoor: `version_completeness_gate.py` line 138 explicitly exempts `"7.0"`.
  - The Version Completeness Gate itself evaluates to **`INCOMPLETE`** (`phase_8_allowed = False`), blocking Phase 8 and all subsequent phases according to the system's core governance rule.

---

## 16. Phase 11 Readiness

### Verdict: **NOT READY (BLOCKED)**

Starting Phase 11 (UI Overhaul or Advanced Features) is blocked by four critical architectural issues:

### Ranked Blockers
- **P0: Release Gate Failure (`phase_8_allowed == False`)**:
  - The completeness gate reports 5 missing character knowledge packages. Progressing to Phase 11 while the gate fails closed violates the fundamental architecture principle of GenshinIQ.
- **P1: Anti-Relabeling Bypass Backdoor**:
  - `version_completeness_gate.py:138` exempts 7.0 from relabeling checks. This allows 5.4 data to pose as 7.0 without triggering the gate.
- **P2: Untested Live LLM Grounding**:
  - CI test suite has zero end-to-end tests validating real Gemini API outputs against grounding requirements.
- **P3: Static Tables in Stat Engine**:
  - `CANONICAL_2PC_BONUSES` and `CANONICAL_WEAPON_PASSIVE_REGISTRY` in `stat_engine.py` are static Python dictionaries rather than version-governed canonical datasets.

---

## 17. Recommended Next Step

### **ONE SINGLE RECOMMENDED NEXT STEP**:
**Execute Phase 10.6 Remediation Task**:
1. Remove the `"7.0"` exemption from `version_completeness_gate.py:138` so that all versions are subject to anti-relabeling verification.
2. Resolve the Version Completeness Gate failure by completing the missing character knowledge packages or reconciling the target version contract, allowing the gate to pass organically.
3. Run the complete test suite to prove that all gates pass without exemptions.

---

## 18. Final Verdict

The GenshinIQ codebase features an exceptionally sophisticated, mathematically rigorous, and well-structured architecture. The deterministic stat engine, hybrid retrieval engine, and fail-closed RAG pipeline are implemented with high engineering discipline.

However, the claim that the system is fully operating on verified, live Genshin Impact Version 7.0 is an artificial project simulation that bypasses its own relabeling checks. The system's own release gate is currently failing closed. **Implementation of Phase 11 must remain stopped until Phase 10.6 remediation is formally executed and verified.**

---

## Summary Matrix

| Area | Actual Status | Confidence |
|---|---|---|
| Data acquisition | Fails closed on network error; mocked in tests | HIGH |
| Data normalization | Real deterministic logic; fallback to baseline exists | HIGH |
| Version detection | Functional regex; relies on local JSON metadata | HIGH |
| Dataset completeness | Evaluates to INCOMPLETE; Phase 8 blocked | HIGH |
| RAG retrieval | Hybrid BM25 + Dense vector retrieval fully integrated | HIGH |
| Citations | Structured provenance citations with grounding filtering | HIGH |
| Stat engine | Deterministic additive formulas; static passive tables | HIGH |
| Account data | Enka showcase + GOOD v3 inventory fully normalized | HIGH |
| Security | Protected in production; permissive in dev without key | HIGH |
| Frontend | 5 functional Vanilla JS tabs; System Health is public | HIGH |
| Test quality | Strong unit/regression coverage; LLM is mocked | HIGH |
| Phase 10.5 | Partially complete (remediated but 7.0 bypassed) | HIGH |
| Phase 11 readiness | NOT READY (BLOCKED by P0 gate failure) | HIGH |
