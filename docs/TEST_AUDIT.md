# GenshinIQ Test Suite Audit

**Audit Date:** September 15, 2026
**Total Test Modules:** 26
**Total Automated Tests:** 355
**Test Suite Execution Status:** 355 Passed, 0 Failed, 0 Skipped (100% Pass Rate)
**Execution Runtime:** ~38.2 seconds (Python 3.12, Pytest 9.1.1)

---

## 1. Test Inventory

| Test Module | Tests | Type | Mocked? | Real Data? | Runtime Integration? |
| :--- | :---: | :--- | :---: | :---: | :---: |
| `test_audit_phase9_scenarios.py` | 9 | Unit / Integration | Partial (Simulated error states) | Yes | Yes |
| `test_canonical_data_pipeline.py` | 22 | Integration | Partial (Network/GitHub 403 fallback) | Yes | Yes |
| `test_character_knowledge_packages.py` | 16 | Integration | No | Yes | Yes |
| `test_citation_grounding.py` | 15 | Unit / Integration | Partial (Mocked Gemini responses) | Yes | Yes |
| `test_data_pipeline_integrity.py` | 8 | Integration | No | Yes | Yes |
| `test_enka_import.py` | 6 | API / Integration | Yes (Mocked Enka HTTP payloads) | No | Yes |
| `test_game_data.py` | 7 | Integration | No | Yes | Yes |
| `test_good_account.py` | 21 | API / Integration | No | Synthetic Fixtures | Yes |
| `test_health.py` | 3 | API / Integration | No | No | Yes |
| `test_knowledge_base.py` | 7 | Integration | No | Yes | Yes |
| `test_knowledge_contract.py` | 25 | Integration | No | Yes | Yes |
| `test_knowledge_contract_audit_scenarios.py` | 12 | Integration | No | Yes | Yes |
| `test_knowledge_escalation.py` | 19 | Unit / Integration | Partial (Simulated freshness deltas) | Yes | Yes |
| `test_knowledge_rebuild.py` | 8 | Integration | No | Yes | Yes |
| `test_live_update_pipeline.py` | 11 | Integration | No | Yes | Yes |
| `test_phase10_5_data_truth.py` | 13 | Integration | Partial (Upstream discovery fallback) | Yes | Yes |
| `test_provenance.py` | 2 | Integration | No | Yes | Yes |
| `test_query_router.py` | 22 | Integration | Partial (Mocked LLM classification) | Yes | Yes |
| `test_rag.py` | 6 | API / Integration | Yes (Mocked Gemini API client) | No | Yes |
| `test_retrieval.py` | 30 | Integration | No | Yes | Yes |
| `test_settings.py` | 3 | Integration | No | Yes | Yes |
| `test_source_registry.py` | 13 | Integration | No | Yes | Yes |
| `test_stat_engine.py` | 39 | Integration | No | Yes | Yes |
| `test_version_completeness_gate.py` | 9 | Integration | No | Yes | Yes |
| `test_version_discovery.py` | 9 | Unit | Yes (MockDiscoveryProvider) | No | No |
| `test_version_system.py` | 20 | Integration | No | Yes | Yes |
| **TOTAL** | **355** | | | | |

---

## 2. Coverage by Phase

- **Phase 0 & Foundation**: `test_health.py` (3), `test_settings.py` (3)
  - Covers environment configuration parsing, release mode toggles, and base health diagnostics.
- **Phase 1 (Enka Showcase Integration)**: `test_enka_import.py` (6)
  - Covers Enka payload parsing, combat attribute calculation from `fightPropMap`, TTL caching, and error handling.
- **Phase 2 (Canonical Game Data & Version Registry)**: `test_game_data.py` (7), `test_data_pipeline_integrity.py` (8), `test_version_system.py` (20)
  - Covers canonical entity lookups, $O(1)$ memory indexing, filter querying, 53-patch monotonic version ordering, and staleness distance calculations.
- **Phase 3 (Provenance & Source Authority)**: `test_source_registry.py` (13), `test_knowledge_base.py` (7)
  - Covers the 5-tier authority hierarchy, cryptographic SHA-256 content hashing, and rejection of mislabeled wiki tiers.
- **Phase 4 (Version Discovery & Knowledge Rebuild)**: `test_version_discovery.py` (9), `test_knowledge_rebuild.py` (8), `test_canonical_data_pipeline.py` (22)
  - Covers 12-step data pipeline, upstream AnimeGameData discovery, raw directory normalization, and rollback/promotion semantics.
- **Phase 5 (Hybrid Retrieval & RAG Routing)**: `test_retrieval.py` (30), `test_rag.py` (6)
  - Covers BM25 Okapi + dense 256-dim embedding retrieval, composite score reranking, authority weighting, and context assembly.
- **Phase 6 (GOOD v3 Account Import)**: `test_good_account.py` (21)
  - Covers full JSON inventory ingestion, canonical entity resolution (exact, alias, legacy), multi-copy weapons, and snapshot diffing.
- **Phase 7 (Deterministic Stat Engine)**: `test_stat_engine.py` (39)
  - Covers level 1 to 90 character curves, weapon base scalings, artifact substat arithmetic, exact `round_half_up` integer rounding, and build comparisons.
- **Phase 8 (Knowledge Contracts & Release Gate)**: `test_version_completeness_gate.py` (9), `test_query_router.py` (22)
  - Covers multi-domain completeness auditing, forbidden placeholder rejection, fail-closed Phase 8 blocking, and dual-track query routing.
- **Phase 9 (Source Provenance & Audit Scenarios)**: `test_provenance.py` (2), `test_audit_phase9_scenarios.py` (9), `test_knowledge_escalation.py` (19)
  - Covers provenance manifest endpoints, best-effort knowledge escalation, and contract derivation graphs.
- **Phase 10 (Citation Assembly & Grounding Transparency)**: `test_citation_grounding.py` (15), `test_live_update_pipeline.py` (11)
  - Covers 4-tier citation building, grounding status classification, and live update orchestrator state machine.
- **Phase 10.5 (Data Truth & Pipeline Remediation)**: `test_phase10_5_data_truth.py` (13), `test_character_knowledge_packages.py` (16), `test_knowledge_contract.py` (25), `test_knowledge_contract_audit_scenarios.py` (12)
  - Covers audit remediation: dynamic coverage contracts, anti-relabeling detection, admin secret bearer token security, and zero-hallucination gap cataloging.

---

## 3. Important Testing Gaps

An objective audit requires distinguishing between what the test suite **proves** vs what it **simulates or assumes**. The following 8 gaps are explicitly documented:

### 1. Actual Version 7.0 Data Truth
- **Reality**: In the real world, Genshin Impact is currently at version 5.4. Version 7.0 ("The Stars Turn Anew") is a project-simulated future release used to validate the architectural version-advancement pipeline.
- **Test Reality**: While `test_version_system.py` and `test_stat_engine.py` verify that the codebase handles 7.0 as a decoupled canonical version, the test suite does not (and cannot) prove that 7.0 game assets represent actual future HoYoverse binaries. Datasets for 7.0 are derived from local structured files, not a live future game client.

### 2. Stale-Data & Relabeling Detection
- **Coverage**: `test_phase10_5_data_truth.py` and `version_completeness_gate.py` detect if `characters.json` is a byte-identical copy of baseline 5.4 with only `game_version_updated` changed.
- **Gap**: If an upstream provider introduces subtle stat changes or unannounced balance adjustments between patches without incrementing character counts, the tests only catch differences if golden regression benchmarks (e.g. Kazuha, Hu Tao) are tripped. Unmonitored 4-star characters could silently pass if structural types match.

### 3. Real Upstream Network Acquisition
- **Coverage**: `canonical_data_pipeline.py` includes HTTP client logic to fetch repository tree commits from Dimbreath/AnimeGameData on GitHub.
- **Gap**: In automated testing (`test_canonical_data_pipeline.py`, `test_phase10_5_data_truth.py`), GitHub API calls are intercepted with fallback mock SHA/commit headers to avoid CI failure due to GitHub unauthenticated IP rate limits (HTTP 403). The actual end-to-end network socket download over the public internet is therefore not exercised in every automated run.

### 4. Real Normalization vs Pre-Normalized Files
- **Coverage**: `canonical_data_pipeline._normalize_avatars_dir` parses raw avatar JSON files from `data/raw/game_data/avatars/`.
- **Gap**: The raw avatar JSON files stored locally are already in AnimeGameData export format. The tests do not prove raw extraction from encrypted Hoyo game client binary assets (`.pck` or Unity AssetBundles); they rely on Dimbreath's datamined JSON schema.

### 5. Completeness Gate Fail-Closed Correctness
- **Coverage**: `test_version_completeness_gate.py` verifies that Phase 8 is blocked (`phase_8_allowed == False`) because live knowledge coverage has 5 missing character guides (Xilonen, Chasca, Ororon, Lan Yan, Yumemizuki Mizuki).
- **Reality Check**: The gate correctly fails closed in the current test environment. However, the simulation test (`test_simulated_complete_state_allows_phase_8`) only verifies that Phase 8 would unblock if mock complete packages were injected; it does not generate actual full KQM theorycrafting guides for the 5 missing characters.

### 6. Hybrid Retrieval Runtime Wiring & LLM Grounding
- **Coverage**: `test_retrieval.py` thoroughly benchmarks the hybrid BM25 + dense embedding retrieval ranker against `retrieval_eval_dataset.py`.
- **Gap**: In `test_rag.py` and `test_citation_grounding.py`, calls to `google.generativeai` (Gemini API) are mocked with deterministic text strings. The test suite does not evaluate live Gemini 2.5 Flash API token generation, latency, or real-world prompt drift across network calls.

### 7. Administrative Endpoint Authentication
- **Coverage**: `test_phase10_5_data_truth.py` tests that `/api/data/pipeline/refresh` rejects requests without `ADMIN_API_KEY` (401/403) and accepts valid tokens.
- **Gap**: Read-only endpoints (`/api/data/*`, `/api/knowledge/*`, `/api/health`) are intentionally unauthenticated. Only mutation endpoints (`/refresh`, `/rollback`) require admin authorization.

### 8. Stat Engine Version Independence
- **Coverage**: `test_stat_engine.py` verifies character level 1–90 scalings and artifact arithmetic against canonical curves.
- **Gap**: The mathematical formulas (e.g. `base_hp = init_hp * curve + promote_hp`) are static game engine invariants. While the stat engine queries `get_canonical_dataset_version()` dynamically, it does not maintain separate historical curve formulas for deprecated legacy mechanics (e.g. pre-1.6 Elemental Mastery reaction scaling formulas).

---

## 4. Test Trust Assessment

To provide independent reviewers with an honest, uninflated appraisal of test fidelity:

### HIGH TRUST (Verifies Genuine Deterministic Runtime Logic)
- **`test_stat_engine.py` (39 tests)**: High trust. Pure deterministic math tested across 100+ breakpoints, golden stat baselines (Kazuha, Hu Tao, Freedom-Sworn, Homa), and exact round-half-up integer display matching in-game numbers.
- **`test_good_account.py` (21 tests)**: High trust. Validates complex account JSON normalization, exact/alias/legacy key resolution, and artifact duplicate prevention without mocks.
- **`test_version_system.py` (20 tests)**: High trust. Exercises the full 53-patch version registry monotonically from 1.0 to 7.0, calculating patch distance and staleness states.
- **`test_retrieval.py` (30 tests)**: High trust. Executes actual BM25 Okapi lexical indexing and local subword vector similarity ranking against a real evaluation dataset without network mocking.
- **`test_source_registry.py` (13 tests)**: High trust. Directly verifies SHA-256 content hashes of production markdown and JSON documents against the registry.
- **`test_version_completeness_gate.py` (9 tests)**: High trust. Real multi-domain audit across characters, weapons, game content, and knowledge gaps; correctly enforces fail-closed state.
- **`test_character_knowledge_packages.py` (16 tests)**: High trust. Verifies contract compilation and zero-hallucination gap cataloging across canonical character datasets.

### MEDIUM TRUST (Partially Mocked / Environmental Fallbacks)
- **`test_canonical_data_pipeline.py` (22 tests)**: Medium trust. Pipeline normalization, schema validation, and rollback mechanics are genuine; however, GitHub upstream discovery is mocked/fallback-driven to bypass rate limiting.
- **`test_phase10_5_data_truth.py` (13 tests)**: Medium trust. Verifies anti-relabeling and admin auth, but uses synthetic secondary sources for cross-source conflict testing.
- **`test_query_router.py` (22 tests)**: Medium trust. Router regex and heuristic intent classification paths are genuine; LLM semantic classifier fallback is mocked.
- **`test_citation_grounding.py` (15 tests)**: Medium trust. Citation extraction logic and grounding score formulas are genuine; LLM generation inputs are synthetic.
- **`test_knowledge_escalation.py` (19 tests)**: Medium trust. Escalation rules are exercised against real and simulated version delta documents.

### LOW TRUST (Primarily Unit Mocks / Metadata Checks)
- **`test_enka_import.py` (6 tests)**: Low trust for network; Medium trust for parsing. Enka.Network HTTP client is completely mocked with static JSON fixtures. Does not test live network connection to Enka servers or handle live Enka rate limits.
- **`test_rag.py` (6 tests)**: Low trust for generation. Gemini LLM API client is mocked. Does not evaluate actual model generation quality or anti-hallucination guardrails against live Gemini models.
- **`test_version_discovery.py` (9 tests)**: Low trust. Uses `MockDiscoveryProvider` to simulate upstream version discovery scenarios rather than connecting to live HoYoverse announcement APIs.

---

## 5. Audit Conclusion & Readiness Assessment

- **Current State**: The repository possesses a rigorous, deterministic, 355-test automated verification suite covering data pipelines, stat calculations, retrieval ranking, version delta tracking, and release completeness gates.
- **Phase 11 Readiness**: **NOT RECOMMENDED TO PROCEED TO PHASE 11 (UI REDESIGN) UNTIL AUDIT FINDINGS ARE OFFICIALLY RATIFIED.** The completeness release gate is currently **deliberately failing closed** (`phase_8_allowed == False`), which is the exact intended behavior required by architectural guardrails.
