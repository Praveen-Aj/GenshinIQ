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

## 3. Data Pipeline Target Architecture (Phase 1+)

To comply with the Remediation Plan:
1. Consolidate all ingestion into a single verified pipeline:
   - `scripts/sync_game_data.py`: Fetches raw data into `data/raw/`.
   - `scripts/validate_game_data.py`: Validates against strict Pydantic models with zero fabricated stats.
   - `scripts/build_manifest.py`: Builds deterministic checksums and records.
2. Eliminate Python's randomized `hash()`: All entities must possess canonical, provider-stable numeric IDs.
3. Remove all fabricated defaults: Missing data must be quarantined or fail validation rather than silently defaulted.
4. Integrate authoritative references (Ambr/Project Amber, KQM, KQM TCL, official patch notes).
