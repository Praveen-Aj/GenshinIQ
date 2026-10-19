# GenshinIQ — Master End-to-End Execution Checklist

**Initiated:** October 19, 2026  
**Governing Documents:**
- `GenshinIQ_Final_Implementation_Remediation_Plan.md`
- `NEXT_VERSION_ROADMAP.md`
- User End-to-End Completion Mandate

---

## Baseline Verification (Pre-Execution)
- [x] Initial Working Tree Audit: Clean Git working tree (commit `f82bc74`).
- [x] Initial Test Suite Run: **381 passed, 0 failed, 1 warning** in 53s across 29 test files.
- [x] Server Health: Running on `http://127.0.0.1:8000/`.
- [x] Release Gate Status: Current-Data Blocker remains strictly **OPEN / PARKED** (`phase_8_allowed = False`).

---

## Phase Execution Checklist

### Phase 12 — Guides Tab Rebuild (Visual Knowledge Library)
- [x] Domain Service (`guide_service.py`): Summary, search, multi-category filters, character, weapon, artifact, team, mechanics, farming endpoints.
- [x] Fix Weapon Scaling: Connected `get_weapon_guide` to `encyclopedia_service.get_weapon_scaling` (exact Lv 1/90 Base ATK and R1 vs R5 scaling).
- [x] Frontend Rebuild (`index.html` & `app.js`): Rebuilt `#tab-content-knowledge` with structured visual cards, element/weapon/rarity chips, owned-only toggle, detail views (no text walls, zero source ID leakage).
- [x] Contextual AI Action Buttons: Bridge guide context to Chat tab (`askAssistant`).
- [x] Tests (`test_guides_rebuild.py`): Unit & integration tests for all guide endpoints, search, filtering, and sanitization (13/13 passing; 394/394 full suite passing).
- [x] Documentation: Created `docs/audit/PHASE_12_DATA_COVERAGE.md`.

### Phase 13 — Farming and Progression Planner
- [x] Service Layer (`backend/services/progression_service.py`): Personal progression tracking, ascension & talent level calculations, inventory-aware shortfall analysis, resin requirements.
- [x] API Endpoints (`/api/progression/*`): Target character progression, missing materials breakdown, domain schedule recommendation.
- [x] Frontend Integration: Personal progression planner & farming calculator in UI.
- [x] Automated Tests (`test_progression_service.py`): Progression math, inventory shortfall, resin estimations.
- [x] Verification & Evidence.

### Phase 14 — Team Building Engine
- [x] Service Layer (`backend/services/team_service.py`): Team recommendations, synergy matrices, elemental resonance, role compatibility, rotation flow generation.
- [x] API Endpoints (`/api/teams/*`): Team builder recommendations based on account inventory or canonical pool.
- [x] Frontend Integration: Team composition workbench, synergy badges, rotation timeline chips, AI bridge.
- [x] Automated Tests (`test_team_service.py`): Synergy scoring, resonance calculation, invalid team handling.
- [x] Verification & Evidence.


### Phase 15 — Artifact Optimization Engine
- [x] Service Layer (`backend/services/artifact_optimizer_service.py`): Deterministic artifact evaluator, roll value (RV), crit value (CV), set bonus balancing, custom stat weight scoring, candidate build generator from account bag.
- [x] API Endpoints (`/api/optimizer/*`): Optimize character build, compare candidate loadouts, explain stat deltas.
- [x] Frontend Integration: Artifact optimizer panel with stat sliders, candidate gear comparison pills, equip recommendation.
- [x] Automated Tests (`test_artifact_optimizer.py`): Math validation, constraint checks, account inventory integration.
- [x] Verification & Evidence.

### Phase 16 — Combat Simulation (gcsim Integration & Rotation Modeling)
- [x] Service Layer (`backend/services/simulation_service.py`): gcsim configuration generator, rotation parser, local execution or fallback deterministic model, DPS metrics calculation.
- [x] API Endpoints (`/api/simulation/*`): Run simulation, retrieve rotation breakdown and DPS graph data.
- [x] Frontend Integration: Simulation tab/modal with DPS curves, rotation timeline, assumptions explanation.
- [x] Automated Tests (`test_simulation_service.py`): Input generator, error handling, parser validation.
- [x] Verification & Evidence.

### Phase 17 — Spiral Abyss & Endgame Tracker
- [x] Service Layer (`backend/services/abyss_service.py`): Floor 12 chamber lineups, enemy resistances, ley line disorders, verified team recommendations.
- [x] API Endpoints (`/api/abyss/*`): Floor 12 data, lineup tracker, team recommendations grounded in account roster.
- [x] Frontend Integration: Visual Abyss tracker cards with monster lineup icons and tailored counter-teams.
- [x] Automated Tests (`test_abyss_service.py`): Lineup queries, freshness indicators, fallback handling.
- [x] Verification & Evidence.

### Phase 18 — System Health & Developer Observability
- [x] Service Layer (`backend/services/observability_service.py`): Diagnostics telemetry, retrieval index metrics, dataset checksums, pipeline run history, error counters.
- [x] API Endpoints (`/api/diagnostics/detailed`): Comprehensive system health telemetry without leaking credentials or PII.
- [x] Frontend Integration: Diagnostics dashboard in System Health tab with real-time telemetry and SHA-256 signatures.
- [x] Automated Tests (`test_observability_service.py`): Telemetry generation, error state reporting, zero credential leakage (4/4 passing).
- [x] Verification & Evidence.

### Phase 19 — Security & Public Hardening
- [x] Security Audit & Hardening:
  - Input validation and parameter constraints on all API routes (`validate_identifier`, query lengths, Chat schema bounds).
  - Path traversal checks on file lookups (`knowledge_service.py`, `version_service.py`, routes).
  - XSS sanitization in markdown parsers (`parseMarkdownToHtml` in `frontend/app.js`).
  - Rate limiting and payload size middleware (`backend/security.py`).
  - Defense-in-depth security HTTP headers (`X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy`).
- [x] Automated Tests (`test_security_hardening.py`): Malformed inputs, traversal attacks, injection safety, headers (12/12 passing).
- [x] Verification & Evidence.

### Phase 20 — 50-Scenario Benchmark, Evaluation & Release Gate
- [x] Grounding Benchmark Suite (`backend/tests/test_50_scenario_benchmark.py`): 50 realistic queries covering account builds, mechanics, farming, teams, edge cases, fail-closed tests (50/50 passing).
- [x] Release Gate Evaluation: Audit Version 7.0 game data status, verify `phase_8_allowed == False` invariant, ensure fail-closed integrity.
- [x] Two-Pass Final Verification:
  - Pass 1: Full regression run across all tests (491/491 passing, 0 failed, 1 warning in 52.02s).
  - Pass 2: Clean restart, re-run full test suite (491/491 passing in 52.29s), re-run benchmark (50/50), browser end-to-end smoke verification via `browser_subagent`.
- [x] Final Evidence-Based Report (`docs/audit/FINAL_RELEASE_REPORT.md` Sections A through G).
