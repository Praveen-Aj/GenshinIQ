# GenshinIQ — Workspace Instructions & Rules

## Project Overview
**GenshinIQ** is a personal Genshin Impact AI assistant that combines:
1. **Live Enka.Network Account Integration** (Default UID: `817739968`)
   - Normalizes live character builds, weapons, artifact substats, combat attributes, and in-game showcase profile avatar.
   - Built-in TTL disk caching to respect Enka API rate limits.
2. **Canonical Game Database** (Characters, Weapons, Artifact Sets, Materials)
   - Structured, versioned JSON datasets with $O(1)$ fast memory indexing, filtering, and cross-entity global search.
3. **Curated Knowledge Base** (KeqingMains Guides, Game Mechanics, Official Patch Notes)
   - Markdown documents tagged with source hierarchy (`AUTHORITATIVE`, `THEORYCRAFTING`, `STATISTICAL`).
4. **Gemini RAG & Account-Grounded Chatbot**
   - RAG pipeline that classifies queries (`general` vs. `account`), injects relevant canonical context & account stats, and enforces fail-closed guardrails.
5. **Interactive Frontend Web Application**
   - Dark celestial glassmorphic UI with Enka CDN asset rendering, inline elemental SVGs, showcase carousel, splash art hero banners, daily domain farming rotation planner, and instant AI build review triggers.

---

## Python Virtual Environment & Tooling
- **Python**: 3.12+ located in `.venv`
- **Interpreter**: `.venv\Scripts\python.exe`
- **Package Manager**: `.venv\Scripts\pip.exe` with `requirements.txt`
- **Test Runner**: `.venv\Scripts\pytest.exe`

---

## Running & Testing Commands
- **Start Dev Server**: `.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload`
- **Run Pytest Suite**: `.venv\Scripts\pytest backend/tests -v`
- **Frontend URL**: `http://127.0.0.1:8000/`
- **API Documentation**: `http://127.0.0.1:8000/docs` (when `DEBUG=true`)

---

## Key Architecture Principles
1. **Structured Data > LLM Memory**: Game stats, scalings, and account builds must come from canonical providers or Enka data, never hallucinated.
2. **Fail-Closed Guardrails**: If reliable evidence is missing or an account build cannot be confirmed, the assistant must state clearly that information is insufficient rather than guessing.
3. **Zero Dead Placeholders**: All cards, badges, and showcase builds must provide actionable click-throughs directly bridging to the chat assistant (e.g. `✨ Ask AI to Review Build`, `📖 Theorycrafting Guide`, `[Ask Teams]`, `⚡ Optimize Artifacts`).
4. **Resilient Asset Pipeline**: Character assets resolve to Enka CDN with local and inline SVG fallbacks for elemental icons to eliminate 404 broken images.
