# Phase 12 — Guides & Knowledge Library Data Coverage & Forensic Audit

**Audit Date:** October 19, 2026  
**Status:** COMPLETE & VERIFIED  
**Governing Plan:** `GenshinIQ_Final_Implementation_Remediation_Plan.md` — Phase 12

---

## 1. Executive Summary

Phase 12 rebuilds the GenshinIQ Guides experience from a raw markdown document browser into a **structured, visual knowledge library**.

All 439 game entities and topics are accessible via `/api/guides` and rendered into the glassmorphic dual-pane interface:
- **Total Guides:** 439
  - **Characters:** 121 (15 Hand-Curated Theorycrafting Guides + 106 Archetype Baselines)
  - **Weapons:** 246 (100% deterministic curve evaluation via `encyclopedia_service.get_weapon_scaling`)
  - **Artifact Sets:** 63 sets (2-piece and 4-piece set bonuses, domain schedules, notable character users)
  - **Team Archetypes:** 4 curated compositions (National, Hyperbloom, Vape/Overload, Aggravate) with rotation timelines
  - **Game Mechanics:** 4 deep-dive guides (Elemental Reactions, Energy Recharge/ICD, Damage Formula, Poise/Shield Break)
  - **Daily Farming Rotations:** All 6 regions (Mondstadt, Liyue, Inazuma, Sumeru, Fontaine, Natlan)

---

## 2. Forensic Taxonomy & Invariant Enforcement

1. **Fail-Closed Fallback Integrity (`never_masquerade_fallback`):**
   - Hand-curated character guides display badge: `✨ Curated Theorycrafting` (`guide_type: CURATED_CHARACTER_GUIDE`).
   - Algorithmic fallback characters display badge: `ℹ️ Archetype Baseline` (`guide_type: GENERIC_FALLBACK`).
   - Baselines clearly state that recommendations are derived from canonical element and stat scalings, never claiming human verification.

2. **Consumer Sanitization (`zero_source_leakage`):**
   - Zero internal database keys (`src_*`), scraper identifiers, community scrapers, or internal confidence scores are leaked to the API or UI.
   - Provenance is verified backend-internal.

3. **Deterministic Weapon & Artifact Curves:**
   - Weapons calculate exact Base ATK and secondary stat values at Lv 1 and Lv 90 using Hoyoverse curve formulas.
   - R1 vs R5 refinement passives are mathematically evaluated.

4. **Actionable Contextual Bridges:**
   - Every guide card features 1-click AI action buttons (e.g. `✨ Review My Build`, `✨ Who Should Equip This?`, `✨ Compare Weapons`, `✨ Find Best Teams`) that pre-fill and trigger queries in the Chat tab with user account context.

---

## 3. Verification Evidence

- Backend Test Suite: `backend/tests/test_guides_rebuild.py` — **13 passed, 0 failed**.
- Endpoints Verified:
  - `GET /api/guides/summary` (200 OK)
  - `GET /api/guides?category=...&element=...&weapon_type=...&q=...` (200 OK)
  - `GET /api/guides/character/{name}` (200 OK)
  - `GET /api/guides/weapon/{name}` (200 OK)
  - `GET /api/guides/artifact/{name}` (200 OK)
  - `GET /api/guides/teams/{slug}` (200 OK)
  - `GET /api/guides/mechanics/{slug}` (200 OK)
  - `GET /api/guides/farming` (200 OK)
