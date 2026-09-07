# GenshinIQ — Personal Genshin Impact AI Assistant

Build a personal Genshin Impact AI assistant called **GenshinIQ**.

## PRIMARY OBJECTIVE

The product is NOT primarily a Genshin database or showcase website.

The primary objective is:

> A Genshin-specific AI chatbot that gives accurate, current, source-grounded answers and can reason over my actual Genshin account/build data.

The system must be substantially more useful for Genshin questions than asking a generic AI without access to my account and curated Genshin sources.

---

## IMPLEMENTATION & VERIFICATION STATUS (ALL PHASES COMPLETE)

| Phase | Description | Status | Verification & Test Coverage |
|---|---|---|---|
| **Phase 0** | **Project Foundation** | **COMPLETED** | FastAPI app, Pydantic settings, health check endpoint (`/api/health`), tests pass. |
| **Phase 1** | **Account Showcase Integration** | **COMPLETED** | Live Enka.Network parser, TTL disk caching, FightProp map normalization, UID `817739968` live verified. |
| **Phase 2** | **Canonical Structured Game Data** | **COMPLETED** | 4 canonical datasets (Characters, Weapons, Artifacts, Materials), $O(1)$ in-memory lookups, filters, global search. |
| **Phase 3** | **Curated Knowledge Base** | **COMPLETED** | KQM Theorycrafting guides, elemental gauge mechanics, Natlan Nightsoul mechanics, official patch notes, source hierarchy. |
| **Phase 4** | **Grounded Chat Assistant (RAG)** | **COMPLETED** | Intent classification, canonical knowledge retrieval, Gemini API integration, dynamic game version grounding, 30s timeout resilience. |
| **Phase 5** | **Account-Grounded Recommendations** | **COMPLETED** | Account build injection into RAG context, build quality review, weapon/artifact comparisons, crowning priority. |
| **UI Overhaul** | **Interactive Web Application** | **COMPLETED** | Dark Celestial glassmorphic UI, Enka CDN assets, inline SVGs, Today's Domain Rotation planner, zero dead placeholders. |

- **Automated Test Suite**: **28/28 tests passing** (`.venv\Scripts\pytest backend/tests -v`).
- **Live E2E Verification**: Verified across all 5 navigation tabs via browser subagents at `http://127.0.0.1:8000/`.

---

# DEVELOPMENT RULE

**Do not implement everything at once.**

Work phase-by-phase.

For EVERY phase:

1. Inspect the existing implementation.
2. Plan the change.
3. Implement it.
4. Run the application.
5. Run automated tests.
6. Perform realistic end-to-end tests.
7. Inspect the actual output/results.
8. Compare the result against the requirements below.
9. Fix any issues found.
10. Run the tests again.
11. Only declare the phase complete after the implementation actually works.

Do NOT simply say "implemented successfully" without testing it.

If something cannot be tested, explicitly state why.

---

# IMPORTANT CONSTRAINTS

Do not prematurely introduce:

- complex microservices
- Kubernetes
- Qdrant
- LangGraph
- multiple agents
- complex frontend frameworks
- damage simulators
- community scraping
- large-scale infrastructure

Use the simplest architecture that satisfies the current phase.

The architecture must remain extensible so these can be added later.

---

# PHASE 0 — PROJECT FOUNDATION

Create a clean repository structure.

Recommended initial architecture:

```text
genshiniq/
├── backend/
│   ├── api/
│   ├── services/
│   ├── models/
│   ├── providers/
│   ├── rag/
│   ├── llm/
│   └── tests/
│
├── frontend/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── knowledge/
│
├── scripts/
├── tests/
├── docs/
├── .env.example
└── README.md
```

Choose appropriate technologies, but keep them simple.

Prefer:

- Python backend
- FastAPI
- simple web frontend
- Gemini API initially
- SQLite initially unless there is a demonstrated reason for PostgreSQL
- Git
- pytest

Do not add infrastructure merely for future scalability.

### Phase 0 test

Confirm:

- backend starts
- frontend starts
- health endpoint works
- frontend can communicate with backend
- environment configuration works
- automated test suite runs

Do not proceed until this works.

---

# PHASE 1 — ENKA ACCOUNT IMPORT

Implement Enka account integration first.

The user should be able to provide their Genshin UID.

Retrieve the publicly available showcase/build information through Enka.

Normalize the data internally.

At minimum capture:

### Character

- character ID
- name
- level
- ascension
- constellation
- talent levels

### Weapon

- weapon ID
- level
- refinement
- relevant stats

### Artifacts

For each artifact:

- slot
- set
- level
- rarity
- main stat
- substats
- values

### Account

Capture whatever relevant public account information Enka actually provides.

Do not invent fields that aren't available.

Implement caching according to Enka's documented TTL/rate-limit behavior.

Do not enumerate or mass-query UIDs.

Only retrieve a UID explicitly provided by the user.

### Phase 1 tests

Create tests using mocked Enka responses.

Verify:

- JSON parsing
- character parsing
- weapon parsing
- artifact parsing
- substat parsing
- malformed response handling
- cache behavior
- API errors
- HTTP 429 handling

Then perform a real test using my supplied UID.

Display the imported data in a simple debug/account page.

**Before finishing Phase 1, visually and functionally verify that the imported data matches the source data.**

---

# PHASE 2 — STRUCTURED GENSHIN DATA

Add a reliable structured Genshin data provider.

Initially investigate/use an appropriate source such as:

- genshin-db
- equivalent maintained structured data

Do not duplicate the entire Genshin database unnecessarily.

Support at minimum:

- characters
- weapons
- artifacts
- talents
- constellations
- materials
- relevant stats/mechanics

Create a normalized internal interface so the rest of the application does not depend directly on one external provider.

Example concept:

```text
CharacterProvider
WeaponProvider
ArtifactProvider
MaterialProvider
```

### Phase 2 tests

Ask the backend for known characters/weapons/artifacts and verify:

- names
- IDs
- stats
- talents
- localization where supported

Compare selected records against the source.

Do not proceed until the structured data is demonstrably correct.

---

# PHASE 3 — KNOWLEDGE BASE

Create the initial curated knowledge base.

Start small.

Use:

1. KQM/TCL
2. Official Genshin patch information
3. Selected Genshin Wiki information
4. Structured game data

Do NOT ingest the entire internet.

Every knowledge document must retain metadata such as:

```text
source
source_url
source_type
character
topic
game_version
published_at
updated_at
```

Classify sources:

```text
AUTHORITATIVE
THEORYCRAFTING
STATISTICAL
COMMUNITY
```

Do not treat community discussion as equivalent to authoritative game data.

---

# PHASE 4 — GEMINI RAG

Use Gemini API initially.

First determine whether Gemini's native File Search/RAG capability is sufficient for the initial knowledge base.

Do NOT immediately build a custom vector database.

The retrieval system should return:

- relevant source
- source URL
- relevant content
- metadata

The model must be instructed:

> Answer only from the supplied evidence and structured data. Do not invent game mechanics, statistics, or recommendations.

If evidence is insufficient:

> "I don't have enough reliable information to answer that."

Do not force an answer.

Every factual/recommendation answer should provide citations/sources.

---

# PHASE 5 — ACCOUNT-GROUNDED CHAT

Now connect:

```text
USER
 ↓
CHAT API
 ↓
QUERY UNDERSTANDING
 ↓
 ┌────────────────────────────┐
 │ Structured Genshin data    │
 │ Knowledge retrieval        │
 │ User's Enka account        │
 └────────────────────────────┘
 ↓
GEMINI
 ↓
GROUNDED ANSWER
 ↓
CITATIONS
```

The chatbot must understand when a question requires personal account data.

Example:

> "Is my Arlecchino build good?"

It should NOT answer generically.

It should:

1. Find my Arlecchino.
2. Read actual weapon/artifacts/stats.
3. Retrieve relevant KQM/game knowledge.
4. Evaluate the build.
5. Explain the reasoning.
6. Cite the knowledge sources.

---

# PHASE 6 — ACCURACY TEST SUITE

Create a permanent benchmark.

At minimum 20–30 questions covering:

### Basic facts

- character mechanics
- weapon effects
- artifact effects

### Build questions

- artifact recommendations
- stat priorities
- weapon choices

### Account questions

- "Is my X build good?"
- "What should I upgrade?"
- "Which character should I build?"

### Team questions

- best team from available characters
- team alternatives
- rotation questions

### Version-sensitive questions

- recent character changes
- patch changes

### Insufficient-evidence questions

Questions where the system should explicitly refuse to make an unsupported claim.

For each test define the expected behavior/result.

Track:

```text
question
retrieved_sources
answer
expected_answer
correct/incorrect
unsupported_claims
citation_quality
```

---

# PHASE 7 — GROUNDING VALIDATION

Implement validation only after the basic RAG works.

The system should detect:

- unsupported factual claims
- missing citations
- outdated sources
- contradictions
- insufficient retrieval evidence

Implement a fail-closed behavior.

Example:

```text
Insufficient reliable evidence was found to answer this confidently.
```

is preferable to an invented answer.

---

# PHASE 8 — SIMPLE UI

Only after the backend works.

Build a clean minimal UI containing:

```text
GenshinIQ

[ Chat ]

[ My Account ]

[ Characters ]
```

The chat is the primary interface.

For account-specific responses, show relevant character/build information when useful.

Do NOT spend time reproducing the complete Enka/Akasha/Seelie UI.

Use existing appropriate Genshin assets/data sources where legally and technically appropriate.

---

# LATER PHASES — DO NOT IMPLEMENT YET

Keep these as future extension points:

### Akasha

- percentile
- leaderboard
- build benchmarking

### Genshin Optimizer / deterministic calculations

- damage
- stat comparison
- artifact optimization

### gcsim

- team simulation
- rotation verification

### Community sources

- Reddit
- forums
- community discussions
- current meta

### Advanced RAG

Only introduce:

- hybrid BM25/dense retrieval
- reranking
- vector DB
- advanced agents

if testing proves Gemini File Search is insufficient.

---

# CRITICAL DESIGN PRINCIPLES

### 1. Structured data beats LLM memory

For exact game facts, retrieve structured data rather than relying on model knowledge.

### 2. Deterministic calculations beat LLM arithmetic

When calculations are eventually implemented, use deterministic tools.

### 3. Source hierarchy matters

Do not treat:

```text
Official data
KQM
Akasha statistics
Reddit opinion
```

as equivalent evidence.

### 4. Version matters

Genshin changes continuously.

Avoid using obsolete information when answering current-version questions.

### 5. Account data must remain separate

Clearly distinguish:

```text
GAME KNOWLEDGE
vs
MY ACCOUNT DATA
```

### 6. Never fabricate certainty

If evidence is insufficient, say so.

---

# FINAL ACCEPTANCE TEST

Before declaring the project ready for Phase 1 MVP, actually run the application and demonstrate these scenarios:

### Test 1

Ask:

> "What is my current roster/build information?"

Expected: answer uses actual Enka data.

### Test 2

Ask:

> "Is my Arlecchino build good?"

Expected: answer references my actual Arlecchino data and relevant knowledge sources.

### Test 3

Ask a factual Genshin question.

Expected: answer comes from the structured/knowledge sources and includes citations.

### Test 4

Ask a question requiring information that is NOT in the knowledge base.

Expected: the system does NOT hallucinate.

### Test 5

Ask a version-sensitive question.

Expected: current-version information is preferred and old information is not incorrectly presented as current.

### Test 6

Break/disconnect an external data source.

Expected: graceful error handling rather than fabricated data.

---

# COMPLETION RULE

Do NOT finish after writing code.

Before declaring a phase complete:

**IMPLEMENT → RUN → TEST → VERIFY OUTPUT → FIX → RETEST → REPORT**

At the end of each phase, provide:

1. What was implemented.
2. Files/components changed.
3. Tests performed.
4. Test results.
5. Any failures/limitations.
6. Evidence that the result matches the requirements.
7. What should be done next.

If a test fails, fix it before moving forward unless the failure is an external dependency that cannot reasonably be resolved.

Start with **Phase 0 only**.

Do not implement Phase 1 until Phase 0 has been tested and confirmed working.