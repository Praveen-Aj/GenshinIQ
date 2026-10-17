# GenshinIQ — Data Sources & Version Provenance Registry

## 1. Overview & Forensic Provenance

This document establishes the authoritative provenance, acquisition methodology, validation status, and content truth of all datasets in **GenshinIQ**.

Under the **Phase 10.6 Data Truth Charter**:
1. A passing test suite is **not** proof that GenshinIQ contains complete/current Genshin Impact data.
2. Local metadata cannot declare a dataset "current" merely because a file or folder exists.
3. If an upstream data source is unavailable or unverified, the system must report **UNVERIFIED / BLOCKED** rather than fabricating records or relabeling older datasets.

---

## 2. Data Sources Registry

| Source Identifier | Upstream Provider | Content Domain | Authority Tier | Verification Method | Status in Repo |
|---|---|---|---|---|---|
| `src_animegamedata` | [AnimeGameData (DimbreathBot)](https://github.com/DimbreathBot/AnimeGameData) | Characters, Weapons, Artifacts, Materials, Curves, Domains, Quests | PRIMARY DATAMINED | SHA-256 commit hash verification + Content Fingerprinting | Verified for v5.4; Unverified simulated v7.0 |
| `src_enka_network` | [Enka.Network](https://enka.network/) | Live player showcase, equipped artifacts, combat attributes, profile avatar | PRIMARY LIVE API | In-game showcase live fetch + FightProp translation | LIVE VERIFIED (UID `817739968`) |
| `src_keqingmains` | [KeqingMains (KQM)](https://keqingmains.com/) | Character build theorycrafting, talent priority, team comps, rotations | THEORYCRAFTING | Markdown documents with frontmatter & source tags | VERIFIED (10 extended guides) |
| `src_hoyoverse_patch_notes` | HoYoverse Official Notices | Patch notes, maintenance notices, version release dates | AUTHORITATIVE | Regex extraction of version announcements | VERIFIED (Patch 7.0 notes) |
| `src_genshin_optimizer` | Genshin Optimizer (GOOD v3) | Account inventory JSON exports | SECONDARY USER IMPORT | JSON schema validation + canonical entity resolution | VERIFIED (GOOD v3 parser) |

---

## 3. Version Dataset Verification Matrix

### Version 5.4 (Canonical Verified Baseline)
- **Source**: AnimeGameData + Hakushin/Enka mapping tables.
- **Acquisition**: Direct acquisition of canonical release game structures.
- **Normalization**: Normalized into 7 canonical structured files (`characters.json`, `weapons.json`, `artifacts.json`, `materials.json`, `avatar_curves.json`, `weapon_curves.json`, `artifact_levels.json`).
- **Content Fingerprint**: `fc1d93f32fe7abba1a4334810fabdabac96897dd227e8b924aa9c562743a91ef`.
- **Validation Status**: `PASSED` (numerical golden benchmarks, monotonic curve progressions, schema checks).
- **Verification Status**: `VERIFIED_STRUCTURED`.

### Version 7.0 (Simulated / Unverified Relabeled Dataset)
- **Audit Finding**: In the local repository, `data/processed/game_data/versions/7.0/` contains 121 characters, weapons, artifacts, and materials identical in numerical attributes and curves to version 5.4.
- **Content Fingerprint**: `fc1d93f32fe7abba1a4334810fabdabac96897dd227e8b924aa9c562743a91ef` (100% identical to v5.4).
- **Anti-Relabeling Detection**: Uniform `check_dataset_relabeling()` detects that 7.0 is a relabeled copy of 5.4.
- **Truth Determination**: **UNVERIFIED_RELABELED**.
- **Promotion Gate Decision**: Promotion to production release state is **BLOCKED** until genuinely acquired datamined ExcelBinOutput records for Version 7.0 are ingested.

---

## 4. Anti-Relabeling & Content Fingerprinting Specification

Dataset identity is content-aware, not label-aware.

```
Deterministic Entity Cleaner (Removes volatile timestamps, version fields, file hashes)
    ↓
Deterministic Canonical JSON Ordering (Sorted by Entity ID / Key)
    ↓
SHA-256 Cumulative Content Fingerprint
```

When candidate version $V_{target}$ is evaluated against prior version $V_{older}$ where $V_{older} < V_{target}$:
$$\text{If } \text{Fingerprint}(V_{target}) == \text{Fingerprint}(V_{older}) \implies \text{RELABELING DETECTED} \implies \text{GATE FAILS CLOSED}$$

---

## 5. Release Gate Single Source of Truth Lifecycle

```
EXPECTED (Formal Coverage Contract: data/canonical/version_coverage/{ver}.json)
    ↓
ACQUIRED (Raw ExcelBinOutput or Upstream API Fetch with Commit SHA)
    ↓
NORMALIZED (Canonical JSON Entities with Uniform Schema)
    ↓
VALIDATED (Numerical Benchmarks, Monotonic Curves, Golden Character Stats)
    ↓
CONTENT IDENTIFIED (Distinct Content Fingerprint vs All Earlier Versions)
    ↓
COMPLETE (Characters, Weapons, Artifacts, Materials, Knowledge, Domains >= Expected)
    ↓
PROMOTABLE (All Required Domain Gates Pass 100%)
    ↓
PROMOTED (Atomic Update to active_version.json and Runtime Mirrors)
```
