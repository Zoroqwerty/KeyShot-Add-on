# Jewelry Light Engine for KeyShot — Technical Feasibility Report

Status: **Research deliverable (pre-implementation).** No production code exists or should
be written until the Phase 1 spike (see [03](03-critical-unknowns-and-experiments.md)) has
resolved the blocking unknowns.

Date of research: 2026-10-10. Latest KeyShot release identified: **KeyShot Studio 2026.2**
(June 2026).

## Deliverables (in the requested order)

| # | Deliverable | File |
|---|---|---|
| 1 | Executive feasibility assessment | [01-executive-feasibility-assessment.md](01-executive-feasibility-assessment.md) |
| 2 | Verified KeyShot API capability matrix | [02-keyshot-api-capability-matrix.md](02-keyshot-api-capability-matrix.md) |
| 3 | Critical unknowns requiring experiments | [03-critical-unknowns-and-experiments.md](03-critical-unknowns-and-experiments.md) |
| 4 | Jewelry optics research summary | [04-jewelry-optics.md](04-jewelry-optics.md) |
| 5 | Geometry-analysis strategy | [05-geometry-analysis-strategy.md](05-geometry-analysis-strategy.md) |
| 6 | Lighting-engine architecture | [06-lighting-engine-architecture.md](06-lighting-engine-architecture.md) |
| 7 | Specifications for the ten presets | [07-preset-specifications.md](07-preset-specifications.md) |
| 8 | Automatic optimization design | [08-automatic-optimization.md](08-automatic-optimization.md) |
| 9 | Failure-mode analysis | [09-failure-mode-analysis.md](09-failure-mode-analysis.md) |
| 10 | Competitive analysis | [10-competitive-analysis.md](10-competitive-analysis.md) |
| 11 | MVP scope and exclusions | [11-mvp-scope.md](11-mvp-scope.md) |
| 12 | Testing and benchmarking plan | [12-testing-and-benchmarking.md](12-testing-and-benchmarking.md) |
| 13 | Development roadmap with effort estimates | [13-development-roadmap.md](13-development-roadmap.md) |
| 14 | Final technical recommendation + first ten actions | [14-final-recommendation.md](14-final-recommendation.md) |
| — | Sources and evidence log | [sources.md](sources.md) |

## Evidence classification used throughout

Every claim about KeyShot capabilities carries one of these labels:

| Label | Meaning |
|---|---|
| **[E1] Confirmed** | Stated in official KeyShot documentation: the official manual, or the official `lux` / `luxmath` docstrings. |
| **[E2] Suggested** | Follows from documented capabilities, but the specific combination or behavior is not documented. |
| **[E3] Needs PoC** | Can only be settled by running an experiment in the target KeyShot version. |
| **[E4] Unsupported / unknown** | No documented mechanism was found; treat as unavailable until proven otherwise. |

"Confirmed" means *documented*. It does not mean *works in every version*. KeyShot users have
reported that the online documentation does not always match the installed module (see
[sources.md](sources.md), forum thread on `setBrightness`). For that reason, every [E1] item
is re-checked in the target version by experiment E0 before it is relied on.

## How the evidence was gathered, and its limits

Read this before trusting any table in this report.

1. **Direct access to keyshot.com was blocked** from the research environment by its network
   policy. The hosts that could not be reached were `media.keyshot.com`,
   `manuals.keyshot.com`, `community.keyshot.com` and `www.keyshot.com`. The official pages
   were therefore read through search-engine extracts (titles, URLs and quoted passages), not
   fetched in full.
2. **The most complete function inventory used is the KeyShot 2023.2 `help(lux)` /
   `help(luxmath)` output.** It was read from a third-party verbatim transcription
   (GitHub `donaldtuttle/Unofficial_KeyShot_Python`). This text is Luxion's own docstrings,
   but it describes 2023.2, not 2025.x or 2026.x.
3. Search extracts of the **official 2024.1, 2025.3 and 2026.1 `lux` reference pages**
   confirmed that several key items are still present in those versions (for example
   `SHADER_TYPE_MESH_LIGHT`, `getSceneTree`, `isUndoEnabled` / `setUndoEnabled`,
   `MaterialGraph.newNode`, and the node-level `getMetadata` added in 2026.1). No extract
   gave a complete 2026.x function list.
4. Nothing was executed inside KeyShot. **No benchmark numbers in this report are
   measurements.** Where a cost matters, the report gives a way to measure it instead of a
   number.

Consequence: experiment **E0 (API inventory in the target version)** is the first action in
the roadmap. Its output replaces the 2023.2 baseline used here.
