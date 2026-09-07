# GenshinIQ — Personal Genshin Impact AI Assistant

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![Tests Passing](https://img.shields.io/badge/tests-28%2F28%20passing-brightgreen.svg)]()
[![Gemini Grounded](https://img.shields.io/badge/Gemini-Grounded%20RAG-8E44AD.svg)]()

**GenshinIQ** is a personal Genshin Impact AI assistant that combines public **Enka.Network showcase data**, **canonical structured game data**, **curated KeqingMains (KQM) theorycrafting**, and **Google Gemini** to provide accurate, source-grounded answers and reason over your actual in-game builds.

> **Core Philosophy**: Structured Data > LLM Memory. The assistant is designed to **fail closed**: when available account data or curated sources are insufficient, it states clearly that information is missing rather than guessing.

---

## 🌟 Key Features

### 1. Live Account Showcase Import (Enka.Network)
- **Zero-Credential Ingestion**: Simply enter your Genshin UID (default: `817739968`) to inspect public showcase builds.
- **In-Game Profile Picture**: Automatically extracts and renders your active in-game profile avatar (e.g. Yelan).
- **Combat Attribute Engine**: Normalizes Enka `fightPropMap` into standard stats: Max HP, ATK, DEF, CRIT Rate/DMG, Energy Recharge, Elemental Mastery, and Elemental DMG Bonuses.
- **Weapons & Artifact Substats**: Complete weapon details (level, refinement, base ATK, substats) and 5-slot artifact sets with roll counts and 2-pc/4-pc active bonuses.
- **Built-in TTL Caching**: Respects Enka rate limits with automatic disk caching and a 1-click **Bypass Cache** option.

### 2. Grounded Gemini RAG Chatbot
- **Account-Aware Intelligence**: Ask *"Review my Skirk build"* or *"Is my Arlecchino build good?"* and the assistant evaluates your actual equipped weapon, CRIT ratios (e.g. 73.8% / 225.0%), ER thresholds, and talent levels.
- **Dynamic Game Version Context**: Context is grounded with the active real-world date and game version to prevent temporal hallucination.
- **Source Citations**: Every recommendation includes expandable citations linking to authoritative sources (KQM guides, patch notes, or account data).
- **Fail-Closed Guardrails**: Strict system instructions prevent inventing stats or extrapolating characters not in your showcase.

### 3. Canonical Structured Game Database
- **4 Comprehensive Datasets**: Characters, Weapons, Artifact Sets, and Materials across all 6 released nations (Mondstadt through Natlan).
- **$O(1)$ In-Memory Indexing**: Fast filtering by element, weapon type, rarity, and cross-entity keyword search.
- **Visual Explorer**: Cards featuring 48px character portraits, glowing rarity borders (5-star gold, 4-star purple), and elemental badges.

### 4. Curated Theorycrafting Knowledge Base
- **KeqingMains Guides**: Full-length theorycrafting articles with crowning priorities, team comps, and rotation mechanics.
- **Mechanics References**: Deep-dives on Elemental Gauge Theory, Internal Cooldown (ICD), Bond of Life, and Natlan Nightsoul's Blessing.
- **Source Credibility Hierarchy**: All documents tagged as `AUTHORITATIVE`, `THEORYCRAFTING`, or `STATISTICAL`.

### 5. Interactive UI & Flagship Features
- **Dark Celestial Glassmorphism**: Tailored HSL palette (`#0a0d14`), blurred glass containers, and Google Fonts Outfit typography.
- **Today's Domain Rotation & Farming Planner**: Detects today's day of the week, displays farmable talent books across all nations, and highlights characters from your showcase who can be farmed today.
- **Zero Dead Placeholders**:
  - `✨ Ask AI to Review Build`: Direct bridge on character hero banner to chat assistant.
  - `📖 Theorycrafting Guide`: Direct bridge to character-specific guide advice.
  - `[Ask Teams]`: Spiral Abyss badge shortcut for Floor 12 team recommendations.
  - `⚡ Optimize Artifacts`: Header action button on Equipped Artifacts.
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

**28/28 tests passing** covering Enka normalization, game data lookups, knowledge search, intent classification, and RAG context generation.

---

## 📁 Project Structure

```text
GenshinIQ/
├── backend/
│   ├── api/             # FastAPI REST endpoints (/health, /account, /data, /knowledge, /chat)
│   ├── models/          # Pydantic schemas (account, game data, knowledge, chat)
│   ├── providers/       # Enka.Network client, fightProp normalizer, canonical DB
│   ├── services/        # Business logic (account, game data, knowledge, RAG, Gemini)
│   └── tests/           # 28-case automated pytest suite
├── frontend/
│   ├── index.html       # HTML5 single-page application structure
│   ├── style.css        # Dark Celestial glassmorphic design system
│   └── app.js           # Frontend application controller & asset pipeline
├── data/
│   ├── raw/showcases/   # Cached Enka showcase JSON fixtures
│   ├── processed/       # Canonical game data (characters, weapons, artifacts, materials)
│   └── knowledge/       # Curated KQM theorycrafting guides and mechanics notes
├── docs/
│   ├── ARCHITECTURE.md          # Multi-tier architecture documentation
│   ├── IMPLEMENTATION_DETAILS.md # Deep technical breakdown of all phases
│   └── SETUP_GUIDE.md           # Step-by-step setup and troubleshooting guide
├── scripts/             # Development, testing, and data maintenance scripts
├── CHANGELOG.md         # Release history and version updates
├── requirements.txt     # Python project dependencies
├── AGENTS.md            # Agent coding instructions & rules
└── README.md            # Project overview & documentation
```

---

## 🔒 Privacy & Data Ethics

- **Public Data Only**: Only public Enka.Network showcase data is requested. No miHoYo/HoYoverse account login or credentials are ever required.
- **Local Credentials**: Your `.env` file containing `GEMINI_API_KEY` is git-ignored and never committed.
- **Fair Use**: Intended as a personal assistant and theorycrafting companion. Game assets and names belong to Cognosphere / HoYoverse.
