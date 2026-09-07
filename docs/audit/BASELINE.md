# GenshinIQ — Phase 0 Baseline Audit

**Audit Date:** 2026-09-07  
**Commit:** `26c41ac` (branch `main`)  
**Environment:** Python 3.12.10 (win32) in `.venv`  
**Server Framework:** FastAPI 0.110.0 on Uvicorn 0.28.0  

---

## 1. System & Environment Baseline

- **App Name:** GenshinIQ
- **App Version:** 0.3.0
- **App Environment:** `development`
- **Host / Port:** `127.0.0.1:8000`
- **Debug Flag:** `True` (with alias support for `release` / `development`)
- **Default UID:** `817739968`
- **Enka API Base URL:** `https://enka.network/api`
- **Enka Cache TTL:** 300 seconds (5 minutes)
- **Gemini Model:** `gemini-2.5-flash` via Google Generative Language API (`v1beta`)

---

## 2. Test Suite & Coverage Baseline

**Command:** `.venv\Scripts\pytest.exe backend/tests -v --cov=backend`

### Results:
- **Total Tests:** 34
- **Passed:** 34 (100%)
- **Failed:** 0
- **Warnings:** 1 (Starlette deprecation regarding TestClient / httpx)
- **Total Statements:** 1,614
- **Statements Missed:** 155
- **Coverage:** 90%

### Test Distribution by Module:
- `backend/tests/test_enka_import.py`: 6 tests (100% module coverage)
- `backend/tests/test_game_data.py`: 7 tests (100% module coverage)
- `backend/tests/test_health.py`: 3 tests (100% module coverage)
- `backend/tests/test_knowledge_base.py`: 7 tests (100% module coverage)
- `backend/tests/test_provenance.py`: 2 tests (100% module coverage)
- `backend/tests/test_rag.py`: 6 tests (100% module coverage)
- `backend/tests/test_settings.py`: 3 tests (100% module coverage)

---

## 3. Dataset Integrity & Hashes Baseline

### Canonical Structured Game Data (`data/processed/game_data/`)

| File Name | Size (Bytes) | Record Count | SHA-256 Digest |
| :--- | :--- | :--- | :--- |
| `artifacts.json` | 17,502 | 50 | `1227f7168adef95ccafe7c58f2f55db21fc4815048d5dc41704ae92eda300e35` |
| `characters.json` | 330,215 | 89 | `5557a459f140abf83ef6d3a03ee3c30ca51d2bc935bf1b1eba0c70e3c188f6a6` |
| `materials.json` | 1,723 | 6 | `7300261983c3fc66ba199c793a2d4f8bb4400eea3497417a31c33b1690e9e4cf` |
| `weapons.json` | 115,015 | 184 | `4830c7ea2981c8a55057b13ccf795da44c63605a7a1d793a0c72dafa843ff4ba` |

### Curated Knowledge Base (`data/knowledge/`)
- **Total JSON Documents:** 163
- **Aggregate Content SHA-256:** `40163de2f4d872c5ba1daa6148b73208973f41e24d644239368b59e81ef3edec`
- **Breakdown by Topic:**
  - Character Guides / References: 102
  - Artifact Set References: 52
  - Game Mechanics: 8
  - Patch Notes: 1 (`official_patch_5_0_nightsoul_notes.json`)

### Account Raw & Runtime Caches (`data/raw/showcases/` and `data/runtime/showcases/`)

| Cache File | Size (Bytes) | Location | SHA-256 Digest |
| :--- | :--- | :--- | :--- |
| `700000000.json` | 7,302 | `data/raw/showcases/` | `a383db108b33d1e08bf639548c08c6a6176b2d50846f5a3adfb0973d1d9de3ba` |
| `817739968.json` | 130,649 | `data/raw/showcases/` | `a527623d80b2de872c441dd3fd54a0f050357cb0115a3f3ce6151969994cf07a` |
| `700000000.json` | 7,302 | `data/runtime/showcases/` | `d6d236c971b9292c368c008b397b094862e737fca0041efb0d27b980806b231a` |
| `817739968.json` | 130,589 | `data/runtime/showcases/` | `d32e3f87f2fd955a95014277e7401ac36ea218eff71f2320bf33be8be9aeee51` |

---

## 4. API Surface Baseline

| Method | Route | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | System health, version, timestamp, configuration |
| `GET` | `/api/account/{uid}` | Player showcase retrieval with TTL cache |
| `POST` | `/api/account/{uid}/refresh` | Cache bypass showcase fetch |
| `GET` | `/api/account/{uid}/characters` | Normalized list of showcase character builds |
| `GET` | `/api/account/{uid}/character/{character_ident}` | Detailed character build lookup by name or ID |
| `GET` | `/api/data/characters` | Filterable canonical character catalog |
| `GET` | `/api/data/characters/{name_or_id}` | Detailed canonical character record |
| `GET` | `/api/data/weapons` | Filterable canonical weapon catalog |
| `GET` | `/api/data/weapons/{name_or_id}` | Detailed canonical weapon record |
| `GET` | `/api/data/artifacts` | Canonical artifact set catalog |
| `GET` | `/api/data/artifacts/{name_or_id}` | Detailed canonical artifact set bonuses & pieces |
| `GET` | `/api/data/materials` | Canonical materials list |
| `GET` | `/api/data/search` | Cross-entity keyword search across game data |
| `GET` | `/api/data/manifest` | Data provenance and checksum manifest |
| `GET` | `/api/knowledge/documents` | Filterable knowledge articles list |
| `GET` | `/api/knowledge/documents/{doc_id}` | Specific knowledge article content |
| `GET` | `/api/knowledge/search` | Typo-tolerant keyword search across knowledge |
| `POST` | `/api/chat` | Grounded chat generation with citations |
