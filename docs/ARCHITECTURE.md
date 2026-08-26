# GenshinIQ Architecture Documentation

## Core System Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                 Frontend (HTML5 / Vanilla CSS / JS)         │
│  - Dark Celestial Theme                                     │
│  - Showcase Viewer (UID 817739968)                          │
│  - Game Data Database Explorer                              │
│  - Chat Assistant (Gemini Grounded)                         │
└──────────────────────────────┬──────────────────────────────┘
                               │ REST / JSON (HTTP)
┌──────────────────────────────▼──────────────────────────────┐
│                    FastAPI Backend Router                   │
│  - /api/health                                              │
│  - /api/account/{uid}                                       │
│  - /api/data/{characters, weapons, artifacts, search}       │
│  - /api/knowledge/{documents, search}                       │
└──────┬───────────────────────┬───────────────────────┬──────┘
       │                       │                       │
┌──────▼──────────────┐ ┌──────▼──────────────┐ ┌──────▼──────────────┐
│   Account Service   │ │   Game Data Service │ │  Knowledge Service  │
│  - Enka Client      │ │  - Structured JSON  │ │  - Curated KQM / TCL│
│  - FightProp Normal │ │    Datasets         │ │  - Patch Notes Docs │
│  - TTL Disk Cache   │ │  - O(1) Index Maps  │ │  - Source Tagging   │
└─────────────────────┘ └─────────────────────┘ └─────────────────────┘
```

## Data Principles
1. **Deterministic Calculations**: Player stats, damage formulas, and character scalings are computed directly via structured schemas rather than asking an LLM to perform mental arithmetic.
2. **Strict Source Hierarchy**: Official in-game mechanics (`AUTHORITATIVE`) > Theorycrafting (`THEORYCRAFTING`) > Aggregated usage (`STATISTICAL`) > Community forum discussion (`COMMUNITY`).
3. **Fail-Closed Retrieval**: If grounding evidence is missing, the assistant declares lack of verified data rather than guessing.
