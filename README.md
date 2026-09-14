# GenshinIQ — Personal Genshin Impact AI Assistant

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![Tests Passing](https://img.shields.io/badge/tests-342%2F342%20passing-brightgreen.svg)]()
[![Gemini Grounded](https://img.shields.io/badge/Gemini-Grounded%20RAG-8E44AD.svg)]()

**GenshinIQ** is a personal Genshin Impact AI assistant that combines public **Enka.Network showcase data**, a **GOOD v3 account import**, **canonical structured game data**, **curated KeqingMains (KQM) theorycrafting**, a **hybrid BM25 + dense retrieval engine**, and **Google Gemini** to provide accurate, source-grounded answers and reason over your actual in-game builds.

> **Core Philosophy**: Structured Data > LLM Memory. The assistant is designed to **fail closed**: when available account data or curated sources are insufficient, it states clearly that information is missing rather than guessing.

---

## 🌟 Key Features

### 1. Live Account Showcase Import (Enka.Network)
- **Zero-Credential Ingestion**: Simply enter your Genshin UID (default: `817739968`) to inspect public showcase builds.
- **In-Game Profile Picture**: Automatically extracts and renders your active in-game profile avatar (e.g. Yelan).
- **Combat Attribute Engine**: Normalizes Enka `fightPropMap` into standard stats: Max HP, ATK, DEF, CRIT Rate/DMG, Energy Recharge, Elemental Mastery, and Elemental DMG Bonuses.
- **Weapons & Artifact Substats**: Complete weapon details (level, refinement, base ATK, substats) and 5-slot artifact sets with roll counts and 2-pc/4-pc active bonuses.
- **Built-in TTL Caching**: Respects Enka rate limits with automatic disk caching and a 1-click **Bypass Cache** option.

### 2. Full Account Import (GOOD v3)
- **Complete Inventory**: Import your full character roster, all weapons, all artifacts, and all materials from any GOOD v3 compatible scanner (e.g. Genshin Optimizer).
- **Canonical Entity Resolution**: Scanner keys are resolved to canonical game database records via exact, alias, and legacy matching.
- **Idempotent & Deterministic**: Re-importing the same file produces identical results with zero duplicate instances.
- **Diff Engine**: Compare snapshots to track progression (characters gained, weapons leveled, artifacts upgraded).

### 3. Deterministic Build & Stat Engine
- **Pure Mathematical Layer**: Character combat attributes (HP, ATK, DEF, CRIT, ER, EM, DMG%) are calculated entirely in Python — no AI-generated values.
- **Full Aggregation Pipeline**: Character base stats + Weapon base ATK + Ascension stats + Artifact main/substats + Set bonuses, resolved through canonical level curves.
- **Build Snapshots & Comparisons**: Reproducible build snapshots with deterministic delta ($\Delta$) computation between builds.
- **Audit Breakdown**: Every stat can be traced to its contributing source (character base, weapon, artifact piece, set bonus).

### 4. Grounded Gemini RAG Chatbot
- **Account-Aware Intelligence**: Ask *"Review my Skirk build"* or *"Is my Arlecchino build good?"* and the assistant evaluates your actual equipped weapon, CRIT ratios, ER thresholds, and talent levels.
- **Hybrid Retrieval**: Combines BM25 Okapi lexical search with local subword dense vector similarity for robust evidence retrieval.
- **Dynamic Game Version Context**: Context is grounded with the active real-world date and game version to prevent temporal hallucination.
- **Source Citations with Grounding**: Every recommendation includes expandable citations linking to authoritative sources, with grounding transparency badges (Fully Grounded / Partially Grounded / Ungrounded).
- **Fail-Closed Guardrails**: Strict system instructions prevent inventing stats or extrapolating characters not in your showcase.

### 5. Canonical Structured Game Database
- **4 Comprehensive Datasets**: Characters, Weapons, Artifact Sets, and Materials across all 6 released nations (Mondstadt through Natlan).
- **$O(1)$ In-Memory Indexing**: Fast filtering by element, weapon type, rarity, and cross-entity keyword search.
- **Visual Explorer**: Cards featuring 48px character portraits, glowing rarity borders (5-star gold, 4-star purple), and elemental badges.
- **Versioned Data Pipeline**: Immutable versioned storage with fail-closed validation gates and deterministic rollback.

### 6. Curated Theorycrafting Knowledge Base
- **KeqingMains Guides**: Full-length theorycrafting articles with crowning priorities, team comps, and rotation mechanics.
- **Mechanics References**: Deep-dives on Elemental Gauge Theory, Internal Cooldown (ICD), Bond of Life, and Natlan Nightsoul's Blessing.
- **Source Credibility Hierarchy**: All documents tagged as `AUTHORITATIVE`, `THEORYCRAFTING`, or `STATISTICAL`.
- **Knowledge Escalation**: Multi-tier escalation service with freshness tracking, version-aware revalidation, and knowledge contracts.

### 7. Interactive UI & Flagship Features
- **Dark Celestial Glassmorphism**: Tailored HSL palette (`#0a0d14`), blurred glass containers, and Google Fonts Outfit typography.
- **Today's Domain Rotation & Farming Planner**: Detects today's day of the week, displays farmable talent books across all nations, and highlights characters from your showcase who can be farmed today.
- **Zero Dead Placeholders**:
  - `✨ Ask AI to Review Build`: Direct bridge on character hero banner to chat assistant.
  - `📖 Theorycrafting Guide`: Direct bridge to character-specific guide advice.
  - `[Ask Teams]`: Spiral Abyss badge shortcut for Floor 12 team recommendations.
  - `⚡ Optimize Artifacts`: Header action button on Equipped Artifacts.
- **Grounding Transparency**: Inline grounding status badges and expandable citation drawers on AI responses.
- **Resilient Asset Pipeline**: Enka CDN image resolution with inline vector SVG elemental badges to eliminate 404 broken images.

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.12+
- Git

### 2. Installation
```powershell
# Clone repository
git clone https://github.com/Praveen-Aj/GenshinIQ.git
cd GenshinIQ

# Create & activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
Copy-Item .env.example .env
```

### 3. Configure API Key
Open `.env` and set your Google Gemini API key:
```ini
GEMINI_API_KEY=your_gemini_api_key_here
USER_UID=817739968
```

If you are switching into a production-style launch, keep `DEBUG` boolean (`true`/`false`) and change `APP_ENV` instead, for example `APP_ENV=release`.

### 4. Run Development Server
```powershell
.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.

Interactive Swagger API documentation is available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

---

## 🧪 Automated Testing

Run the full pytest suite:
```powershell
.venv\Scripts\pytest backend/tests -v
```

Run with coverage:
```powershell
.venv\Scripts\python.exe -m coverage run -m pytest backend/tests -v
.venv\Scripts\python.exe -m coverage report -m
```

The automated test suite covers **342 test cases** spanning Enka normalization, game data lookups, knowledge search, intent classification, provenance, RAG context generation, canonical data pipeline integrity, GOOD v3 account import, stat engine calculations, source registry, knowledge contracts, version discovery, retrieval evaluation, query routing, and citation grounding.

---

## 📁 Project Structure

```text
GenshinIQ/
├── backend/
│   ├── adapters/        # External data source adapters
│   ├── api/             # FastAPI REST endpoints (/health, /account, /data, /knowledge, /chat, /build)
│   ├── llm/             # LLM integration layer
│   ├── models/          # Pydantic schemas (account, game data, knowledge, chat, grounding, stat engine)
│   ├── providers/       # Enka.Network client, fightProp normalizer, canonical DB
│   ├── rag/             # RAG pipeline modules
│   ├── services/        # Business logic (account, game data, knowledge, RAG, Gemini, stat engine, retrieval, grounding)
│   └── tests/           # 342-case automated pytest suite (26 test modules)
├── frontend/
│   ├── index.html       # HTML5 single-page application structure
│   ├── style.css        # Dark Celestial glassmorphic design system
│   └── app.js           # Frontend application controller & asset pipeline
├── data/
│   ├── canonical/       # Source registry, knowledge contracts, version coverage
│   ├── raw/showcases/   # Cached Enka showcase JSON fixtures
│   ├── processed/       # Canonical game data (characters, weapons, artifacts, materials) with versioned storage
│   └── knowledge/       # Curated KQM theorycrafting guides, mechanics notes, wiki summaries
├── docs/
│   ├── ARCHITECTURE.md          # Multi-tier architecture documentation
│   ├── IMPLEMENTATION_DETAILS.md # Deep technical breakdown of all phases
│   ├── NEXT_VERSION_ROADMAP.md  # Next release plan
│   ├── SETUP_GUIDE.md           # Step-by-step setup and troubleshooting guide
│   └── audit/                   # Data sources audit & pipeline assessment
├── scripts/             # Development, testing, data maintenance, and version management scripts
├── CHANGELOG.md         # Release history and version updates
├── requirements.txt     # Python project dependencies
├── AGENTS.md            # Agent coding instructions & rules
└── README.md            # Project overview & documentation
```

---

## 🔒 Privacy & Data Ethics

- **Public Data Only**: Only public Enka.Network showcase data is requested. No miHoYo/HoYoverse account login or credentials are ever required.
- **Local Credentials**: Your `.env` file containing `GEMINI_API_KEY` is git-ignored and never committed.
- **GOOD Exports Stay Local**: Imported GOOD v3 files are stored locally in `data/runtime/account/` and are git-ignored.
- **Fair Use**: Intended as a personal assistant and theorycrafting companion. Game assets and names belong to Cognosphere / HoYoverse.
