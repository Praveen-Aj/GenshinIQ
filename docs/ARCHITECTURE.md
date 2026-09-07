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
- **`backend.api.routes`**: Clean RESTful endpoints organizing health diagnostics, account showcases, canonical game data, curated knowledge, and chat assistant.
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
