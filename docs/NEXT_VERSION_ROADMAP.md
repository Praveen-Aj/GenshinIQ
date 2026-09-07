# GenshinIQ Next Version Roadmap

**Target release:** `v0.4.0`  
**Date:** Monday, September 7, 2026  
**Status:** Living roadmap for the next implementation cycle

## Goals

The next version should make GenshinIQ more trustworthy, more reproducible, and easier to extend. The main focus is to tighten evidence quality, harden the data pipeline, and make the build-review experience more deterministic.

## Roadmap

### 1. Integrity Sprint

Primary outcome: every answer should have a clear evidence chain.

Deliverables:

- Enforce evidence-only RAG for grounded responses.
- Add source and version metadata to curated documents and canonical datasets.
- Separate mutable runtime caches from committed fixtures.
- Make provenance visible in APIs and assistant responses where relevant.

Acceptance criteria:

- The assistant does not guess when local evidence is missing.
- Every surfaced recommendation can be traced back to a source or dataset version.
- Cache files and test fixtures are no longer mixed together.

### 2. Evaluation Sprint

Primary outcome: confidence in the assistant through repeatable checks.

Deliverables:

- Build a suite of 30-50 grounded questions covering account, general, and edge-case flows.
- Define expected citations and fail-closed behavior for each question.
- Run the suite in CI so regressions are caught automatically.

Acceptance criteria:

- Answers are checked for grounding, not just presence of text.
- Fail-closed behavior is verified whenever evidence is incomplete.
- CI can detect silent quality drift.

### 3. Deterministic Build-Review Engine

Primary outcome: compute the facts in Python before Gemini explains them.

Deliverables:

- Calculate artifact CV, stat targets, ER thresholds, and set bonuses in code.
- Produce upgrade priorities from reproducible logic.
- Keep Gemini in an explanatory role, not a calculation role.

Acceptance criteria:

- Build reviews are consistent across runs with the same inputs.
- The assistant explains computed results rather than inventing them.
- Recommendations are based on explicit formulas and thresholds.

### 4. Data Pipeline Hardening

Primary outcome: cleaner imports and more reliable datasets.

Deliverables:

- Make dataset imports reproducible and version-aware.
- Validate schemas for characters, weapons, artifacts, materials, and knowledge docs.
- Track freshness and source changes explicitly.
- Improve fixture generation and dataset regeneration workflow.

Acceptance criteria:

- Data updates can be reproduced from source inputs.
- Invalid or incomplete records fail validation early.
- Version drift is easy to spot.

### 5. UX and Security Pass

Primary outcome: safer rendering and clearer user flows.

Deliverables:

- Sanitize Markdown and citations before rendering them in the frontend.
- Harden API and frontend error handling.
- Review public-facing endpoints for restrictive defaults where needed.
- Remove any accidental trust in untrusted content.

Acceptance criteria:

- Untrusted content cannot inject arbitrary HTML into the UI.
- Error states are understandable and do not leak internals.
- Public endpoints are limited to the minimum behavior needed.

### 6. Release Engineering

Primary outcome: a release process that is easy to trust and repeat.

Deliverables:

- Add CI checks for lint, tests, coverage, and data validation.
- Prepare tagged release notes and GitHub metadata updates.
- Keep documentation synchronized with shipped behavior.
- Establish a repeatable checklist for future releases.

Acceptance criteria:

- A release can be verified from the CI pipeline alone.
- Documentation matches the actual runtime behavior.
- GitHub-facing metadata reflects the current version and scope.

## Suggested Sequence

1. Finish the integrity sprint first.
2. Use the integrity work to anchor the evaluation suite.
3. Build the deterministic review engine once the inputs are trustworthy.
4. Harden the data pipeline in parallel with the engine work.
5. Close with UX/security and release engineering.

## Risks To Watch

- Mixing runtime cache files with committed fixtures.
- Letting the LLM generate unsupported conclusions.
- Treating documentation as source of truth when code behavior has changed.
- Improving the UI without sanitizing untrusted rendering paths.

## Done Definition

The next version is ready when:

- Answers are grounded in evidence or explicitly fail closed.
- Test coverage includes both functional checks and quality checks.
- The build review flow is deterministic and explainable.
- The docs, release notes, and repo metadata all describe the same shipped behavior.
