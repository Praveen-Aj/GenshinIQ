# Phase 12–20 Remediation Log

**Log Date:** October 19, 2026  
**Repository:** https://github.com/Praveen-Aj/GenshinIQ  
**Target Scope:** Phases 12–20 Implementation & Integration  

---

## Remediation Entry 1: Hardcoded Curated Characters List Discrepancy

- **Defect:**
  `GuideService._curated_chars` and `EncyclopediaService.curated_characters` contained hardcoded sets of 15 character names.
  The two sets were inconsistent: `guide_service.py` contained `"ganyu"` (which has only a wiki reference guide, no KQM guide), but omitted `"citlali"` (which has `kqm_citlali_guide.json`). `encyclopedia_service.py` included `"citlali"` but omitted `"ganyu"`.
  Furthermore, characters outside this hardcoded list were automatically classified as `GENERIC_FALLBACK`, ignoring available knowledge documents.
- **Root Cause:**
  Static hardcoded sets were used during early Phase 11 development instead of dynamically scanning the `data/knowledge` directory for authoritative `kqm_*_guide.json` files.
- **Files Changed:**
  - `backend/services/encyclopedia_service.py`
  - `backend/services/guide_service.py`
- **Correction:**
  - Added dynamic method `get_curated_characters()` to `EncyclopediaService` that discovers all characters with `kqm_*_guide.json` documents in `data/knowledge` and caches the set.
  - Initialized `GuideService._curated_chars = encyclopedia_service.get_curated_characters()`, keeping both services synchronized.
  - Added fallback defaults to ensure core theorycrafting characters are preserved if the directory is momentarily inaccessible.
- **Regression Test:**
  `backend/tests/test_guides_rebuild.py::test_dynamic_curated_characters_discovery`
- **Verification Result:**
  **PASSED**. Curated characters count dynamically resolved to 15, Citlali correctly included, and both services report identical sets.

---

## Remediation Entry 2: Character Guide Detail Placeholder Talents and Constellations

- **Defect:**
  The 15-section character guide detail endpoint returned generic placeholder talents (`"Normal Attack"`, `"Elemental Skill"`, `"Elemental Burst"`) and generic placeholder constellation descriptions (`"C1: Initial Upgrade"`, `"C2: Key Spike"`) for all non-curated characters (such as Kamisato Ayaka, Diluc, Xiao, Cyno), even though real deterministic talents and constellations exist in canonical character packages.
- **Root Cause:**
  `GuideService.get_character_guide` previously constructed a static dictionary for `talents_breakdown` and `constellations_summary` without querying `CharacterKnowledgePackage`.
- **Files Changed:**
  - `backend/services/guide_service.py`
- **Correction:**
  - Integrated `CharacterKnowledgePackage` retrieval via `character_knowledge_service.get_character_package(char.name)`.
  - Extracted deterministic combat talent names (e.g. `"Kamisato Art: Kabuki"`, `"Kamisato Art: Hyouka"`, `"Kamisato Art: Soumetsu"`) and constellation names/descriptions (e.g. `"Snowswept Sakura"`, `"Blizzard Blade Seki no To"`).
  - Cleaned Hoyoverse XML color formatting tags (`<color=...>`) from descriptions.
  - Updated provenance note to reflect canonical game reference status when full package data is present.
- **Regression Test:**
  `backend/tests/test_guides_rebuild.py::test_character_guide_deterministic_talents_and_constellations`
- **Verification Result:**
  **PASSED**. Detail endpoint for Kamisato Ayaka returned real talent names and constellation names.

---

## Remediation Entry 3: Frontend Guide Card Gold Badge Class Mismatch

- **Defect:**
  In `frontend/app.js`, guide card badge styling checked `item.guide_type === 'CURATED_THEORYCRAFTING'`, whereas `guide_service.py` outputs `item.guide_type = 'CURATED_CHARACTER_GUIDE'`. As a result, curated character cards fell back to `badge-secondary` rather than glowing gold.
- **Root Cause:**
  Typographical naming difference between frontend CSS class selector logic and backend response model enum.
- **Files Changed:**
  - `frontend/app.js`
- **Correction:**
  - Updated line 2334 of `frontend/app.js` to:
    `if (item.guide_type === 'CURATED_THEORYCRAFTING' || item.guide_type === 'CURATED_CHARACTER_GUIDE' || item.guide_type === 'CURATED_WEAPON_GUIDE')`
- **Regression Test:**
  Manual inspection via browser smoke test (`browser_subagent`).
- **Verification Result:**
  **PASSED**. Character cards for curated characters now render with proper gold badge formatting.

---

## Remediation Entry 4: Missing Local Files in Remote GitHub Repository

- **Defect:**
  Independent GitHub inspection found that service files (`abyss_service.py`, `team_service.py`, `simulation_service.py`, `artifact_optimizer_service.py`, `progression_service.py`, `observability_service.py`, `security.py`) and test suites (`test_50_scenario_benchmark.py`, `test_abyss_service.py`, etc.) were absent on remote `main`.
- **Root Cause:**
  Previous development work was completed locally in the working directory but had not been staged, committed, or pushed to GitHub.
- **Files Changed:**
  - 8 backend services/modules
  - 9 backend test suites
  - Documentation and audit logs
- **Correction:**
  - Audited all untracked files in the local working tree.
  - Verified and enhanced unit and integration tests.
  - Staged and prepared changes for Git commit with accurate documentation.
- **Regression Test:**
  Two-pass full repository regression run (`.venv\Scripts\pytest backend/tests`).
- **Verification Result:**
  **PASSED**. 491/491 tests pass cleanly across all 37 test modules.

---

## Remediation Entry 5: Outdated Test Badge and Suite Count in README

- **Defect:**
  `README.md` advertised an obsolete test count (`371/371 passing` across 26 test modules).
- **Root Cause:**
  Documentation was not updated after Phases 12–20 test modules were added.
- **Files Changed:**
  - `README.md`
  - `docs/audit/MASTER_EXECUTION_CHECKLIST.md`
- **Correction:**
  - Updated `README.md` test badge to `491/491 passing`.
  - Updated test suite documentation to reflect 491 test cases across 37 test modules.
- **Regression Test:**
  Verified README against final pytest run output.
- **Verification Result:**
  **PASSED**. README matches actual final test metrics.
