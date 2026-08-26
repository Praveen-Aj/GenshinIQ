# GenshinIQ Project & Development Rules

These instructions and rules govern all AI assistance, development workflows, and feature implementations in the **GenshinIQ** repository.

---

## 🎯 Primary Objective

Build a personal Genshin Impact AI assistant (**GenshinIQ**) that delivers accurate, source-grounded answers and reasons over the player's actual Genshin account and build data.

- **Primary User UID**: `817739968` (praveen)
- **Architecture Philosophy**: Structured data > LLM memory. Deterministic calculations > LLM arithmetic.

---

## 🛠️ Environment & Interpreter Configuration

- **Virtual Environment**: Always use the project-local `.venv` virtual environment located at `.venv/`.
- **Interpreter Path (Windows)**: `.venv\Scripts\python.exe`
- **Package Manager**: `venv + pip` (managed via [requirements.txt](file:///c:/Users/Praveen/Downloads/Python%20Scripts/GenshinIQ/requirements.txt)).
- **Never install packages globally.**

---

## 📋 Phase-by-Phase Development Rule

1. **Never implement everything at once.**
2. Follow strict sequential phases:
   - **Phase 0**: Project Foundation & Web App Core *(Completed & Verified ✅)*
   - **Phase 1**: Enka Account Showcase Import & Normalization *(Completed & Verified ✅)*
   - **Phase 2**: Structured Genshin Data Provider & Explorer *(Completed & Verified ✅)*
   - **Phase 3**: Curated Knowledge Base (KQM theorycrafting, patch notes, source classification)
   - **Phase 4**: Gemini RAG & Anti-Hallucination Retrieval
   - **Phase 5**: Account-Grounded Chatbot
   - **Phase 6**: Accuracy Benchmark Test Suite (20–30 test cases)
   - **Phase 7**: Grounding Validation & Fail-Closed Guardrails
   - **Phase 8**: Full Web UI Polish
3. For **EVERY** phase:
   - Plan -> Implement -> Run -> Automated Pytest -> End-to-End Browser/API Test -> Document Walkthrough.

---

## 📚 Source Hierarchy & Truth Rules

1. **AUTHORITATIVE**: Official HoYoverse data, in-game stats, talent scaling, patch notes.
2. **THEORYCRAFTING**: KeqingMains (KQM), Theorycrafting Library (TCL).
3. **STATISTICAL**: Aggregated showcase and usage data (Akasha, YShelper).
4. **COMMUNITY**: General forum discussions (lowest confidence).

Never present community opinions as authoritative mechanics. If evidence is insufficient, fail closed: *"Insufficient reliable evidence found to answer confidently."*
