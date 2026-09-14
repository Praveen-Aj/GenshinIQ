# GenshinIQ — Data Sources & Pipeline Assessment

**Audit Date:** 2026-09-07  
**Status:** Audit & Remediation Plan (Phase 0)

---

## 1. External Data Providers & Integrations

The project currently touches or references the following external providers:

### 1. Enka.Network API
- **Base URL:** `https://enka.network/api`
- **Asset CDN:** `https://enka.network/ui/`
- **Role:** Player showcase retrieval (`/uid/{uid}`) for characters, levels, weapons, artifact substats, combat attributes, and player avatar profile.
- **Client Implementation:** `backend/providers/enka_client.py`
- **Caching Layer:** `backend/services/cache_service.py` (`data/runtime/showcases/{uid}.json`, default TTL 300s).
- **Audit Findings:** 
  - Works reliably for available showcase avatars.
  - Mixes "account" semantics with "showcase" semantics (only characters in the active in-game showcase are visible).
  - Unsafe defaults in fallback stat parsing (`crit_rate=0.05`, `crit_dmg=0.50`, `energy_recharge=1.00`, `fetter_level=10`, `rolls=1`).

### 2. Google Gemini API
- **Endpoint:** `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent`
- **Client Implementation:** `backend/services/gemini_service.py`
- **Role:** Synthesizing chat responses and explaining theorycrafting/build advice.
- **Audit Findings:**
  - Connects properly via direct HTTP REST calls using `httpx`.
  - API key currently resides in local `.env` and must be kept protected.
  - Fallback logic triggers when the model is busy, returning local knowledge citations or showcase summaries.

### 3. Community API (`genshin.jmp.blue`)
- **Role:** Used as the source for `scripts/repopulate_game_data.py` and `scripts/fetch_knowledge_from_api.py`.
- **Audit Findings:**
  - Provides static JSON dumps of characters, weapons, and artifact sets.
  - Incomplete / uncurated stats: lacks exact Level 90 scalings and ascension stats for new characters.
  - The script filled missing stats with fabricated placeholders (`base_atk=250.0`, `base_hp=11000.0`, `ascension_stat="CRIT Rate" 19.2%`).
  - Led to corrupt/duplicate IDs and arbitrary rarity fallbacks.

### 4. KeqingMains (KQM) Guides
- **URL:** `https://keqingmains.com/`
- **Role:** Tier 2 curated theorycrafting for character guides (e.g. Arlecchino, Furina, Neuvillette, Kazuha, Mavuika, Skirk, Citlali).
- **Audit Findings:** High quality, but manually copied into isolated JSON files; lacks automated ingestion, validation, or version synchronizer.

### 5. Genshin Impact Community Wiki (Fandom)
- **Role:** Used in `scripts/fetch_knowledge_from_api.py` to create 94 `wiki_*.json` documents.
- **Audit Findings:**
  - Misclassified as `AUTHORITATIVE` in `metadata.source_type`. Fandom wikis are Tier 5 Community sources, not official Tier 1.

---

## 2. Competing Ingestion Scripts Inventory

The audit revealed multiple uncoordinated data-generation scripts in `scripts/`:

1. `scripts/expand_game_data.py`:
   - Hardcoded Python lists (`NEW_CHARACTERS`, `NEW_WEAPONS`, `NEW_ARTIFACT_SETS`).
   - Appends entries into `data/processed/game_data/`.
   - Introduced ID collisions (e.g., Kazuha vs. Ayaka on ID `10000047`, Staff of Homa vs. Calamity Queller on ID `13501`).

2. `scripts/repopulate_game_data.py`:
   - Fetches from `genshin.jmp.blue`.
   - Generates non-deterministic IDs: `10000200 + hash(name) % 1000`.
   - Fabricates base stats (`base_hp=11000.0`, `base_atk=250.0`, `base_def=700.0`).
   - Fabricates weapon base attacks based on rarity tiers (e.g. 5★ = 608.0, 4★ = 510.0).
   - Defaults unknown element to `"Pyro"` and unknown weapon type to `"Sword"`.

3. `scripts/fetch_knowledge_from_api.py`:
   - Scrapes character and artifact summaries from `genshin.jmp.blue` into `data/knowledge/`.
   - Generates markdown files tagged with `source_type: AUTHORITATIVE` despite coming from community scrapers.

4. `scripts/add_icons_to_data.py`:
   - Ad-hoc script patching `icon` keys onto existing JSON items.

5. `scripts/import_account.py`:
   - CLI utility to fetch and save showcase to `data/raw/showcases/`.

---

## 3. Implemented Canonical Data Refresh & Acquisition Architecture

The data pipeline has been restructured to adhere strictly to the verified multi-source hierarchy and version decoupling model:

### Verified Source Roles & Derivation Relationships
| Source ID | Name | Role | Derivation Relationship | Authority Level |
|---|---|---|---|---|
| `src_hoyoverse_official` | HoYoverse Official | Official announcements, patch notes, dates, mechanics | `OFFICIAL` | Highest for official statements |
| `src_animegamedata` | Dimbreath / AnimeGameData | Primary raw structured game-data (curves, stats, talents) | `PRIMARY_ORIGINAL` | Primary canonical game data |
| `src_project_amber` | Project Amber / Ambr | Secondary structured / cross-validation | `AGGREGATOR` | High (Secondary validation) |
| `src_genshin_db` | genshin-db | Secondary normalized package | `DERIVED_FROM` (`src_animegamedata`) | Corroboration only (`DERIVED_AGREEMENT`) |
| `src_genshindev_api` | genshin.dev API | Community aggregator / fallback | `AGGREGATOR` | Fallback recovery |
| `src_honey_hunter` | Honey Hunter World | Human-readable sanity check & discovery | `REFERENCE` | Non-authoritative reference |
| `src_genshin_optimizer` | Genshin Optimizer | Technical reference (formulas & mechanics) | `REFERENCE` | Non-runtime technical reference |
| `src_enka_network` | Enka.Network API | Player showcase retrieval | Account Data | Strictly account-data |
| `src_good_standard` | Genshin Open Object Description | Account export schema | Account Data | Strictly account-data |

### Architecture Principles Implemented
1. **No Naive Majority Voting**: Agreement between `src_animegamedata` and `src_genshin_db` is formally tracked as `DERIVED_AGREEMENT` (corroboration), never as independent confirmation.
2. **Decoupled Version Model**:
   - `detected_game_version`: Live game version detected from official announcements/patch notes.
   - `latest_known_game_version`: Highest known game version from authoritative sources.
   - `latest_available_dataset_version`: Highest version available in upstream repositories.
   - `latest_verified_dataset_version`: Highest version having passed all validation gates.
   - `active_canonical_dataset_version`: Version currently used by StatEngine and runtime services (`5.4`).
   - `project_target_version`: Version currently targeted by the application (`7.0`).
3. **Immutable Versioned Storage**:
   - Raw data: `data/raw/game_data/versions/<version>/` with `raw_manifest.json`.
   - Processed data: `data/processed/game_data/versions/<version>/` with `version_manifest.json`.
   - Active canonical pointer: `data/processed/game_data/active_version.json`.
4. **Fail-Closed Gate & Rollback**:
   - Discrepancies on critical numerical fields generate `CONFLICT` and block canonical promotion.
   - Any validation failure leaves the active canonical version pointer untouched.
   - The system supports instantaneous deterministic rollback to any verified historical dataset version.

