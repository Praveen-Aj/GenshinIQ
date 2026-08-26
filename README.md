# GenshinIQ

GenshinIQ is a personal Genshin Impact assistant that combines public Enka.Network showcase data, local structured game data, curated theorycrafting sources, and Gemini to provide source-grounded answers about game mechanics and your displayed builds.

> The assistant is designed to fail closed: when the available account data and curated sources are insufficient, it should say so rather than guess.

## Current capabilities

- Imports a public Enka.Network showcase by UID and normalizes characters, weapons, artifacts, talents, and combat stats.
- Caches account results locally to respect Enka.Network rate limits.
- Serves searchable structured data for characters, weapons, artifact sets, and materials.
- Searches a curated local knowledge base containing selected KQM guides, mechanics notes, and official patch notes.
- Offers Gemini-backed chat with grounded sources and optional account-build context.
- Includes a lightweight web interface for showcase browsing, game data, knowledge search, and chat.

## Stack

- Python 3.12+, FastAPI, and Pydantic
- Vanilla HTML, CSS, and JavaScript
- Enka.Network public API for account showcases
- Gemini API for grounded response generation

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `GEMINI_API_KEY` in `.env` to enable chat, then run:

```powershell
.\.venv\Scripts\python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). Interactive API documentation is available at `/docs` when `DEBUG=true`.

## Tests

```powershell
.\.venv\Scripts\pytest backend/tests -v
```

The test suite covers health checks, Enka payload normalization, structured-data retrieval, knowledge retrieval, and RAG context assembly.

## Project layout

```text
backend/    FastAPI app, API routes, models, providers, services, and tests
frontend/   Static web interface
data/       Versioned game data, curated knowledge, and showcase fixtures
docs/       Architecture and setup documentation
scripts/    Development and data-maintenance utilities
```

## Status

The core account import, structured data, knowledge retrieval, and account-aware RAG flows are implemented. The bundled datasets are intentionally curated samples, not a complete or continuously updated copy of all Genshin Impact content. See [the architecture guide](docs/ARCHITECTURE.md) and [implementation plan](GenshinIQ%20%E2%80%94%20Antigravity%20Implementation%20Plan.md) for design goals and next phases.

## Privacy and data

Only public Enka.Network showcase data is requested. Your local `.env` file, including `GEMINI_API_KEY`, is excluded from Git. Avoid committing personal account exports if you do not want them in a public repository.
