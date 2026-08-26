# GenshinIQ — Workspace Instructions & Rules

## Project Overview
GenshinIQ is a personal Genshin Impact AI assistant that combines:
1. **Live Enka.Network Account Integration** (Primary User UID: `817739968`)
2. **Canonical Game Database** (Characters, Weapons, Artifact Sets, Materials)
3. **Curated Knowledge Base** (KQM Theorycrafting, Official Patch Notes)
4. **Gemini RAG & Account-Grounded Chatbot**

## Python Virtual Environment
- **Python**: 3.12+ in `.venv`
- **Interpreter**: `.venv\Scripts\python.exe`
- **Package Manager**: `.venv\Scripts\pip.exe` with `requirements.txt`

## Running & Testing
- **Start Dev Server**: `.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload`
- **Run Pytest Suite**: `.venv\Scripts\pytest backend/tests -v`
- **Frontend URL**: `http://127.0.0.1:8000/`

## Key Architecture Principles
1. **Structured Data > LLM Memory**: Game stats, scalings, and account builds must come from canonical providers or Enka data, not hallucinated.
2. **Phase-by-Phase**: Follow the development phases strictly and test each phase before declaring it complete.
3. **Fail-Closed Guardrails**: If reliable evidence is missing, state clearly that information is insufficient.
