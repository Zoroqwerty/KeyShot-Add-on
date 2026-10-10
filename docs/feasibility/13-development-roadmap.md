# 13. Development Roadmap with Effort Estimates

## 13.1 Assumptions behind every estimate

- **Team.**
  - 1 senior Python developer with 3D-maths and rendering background at 1.0 FTE (estimates
    are in *developer person-weeks*, pw).
  - 1 experienced jewelry visualization artist: 0.2 FTE in Phases 1–2, 0.4–0.5 FTE in
    Phases 3–6.
  - A product owner for decisions and customer interviews; not counted.
- **Equipment.** KeyShot licences for the two target versions on Windows and macOS; one
  GPU-capable workstation; the benchmark models available by Phase 3.
- **Scope.** Estimates include unit and integration tests and developer documentation. They
  exclude marketing, sales, legal review, the customer-facing website and support.
- **Uncertainty.** The ranges reflect the [E3] unknowns. The upper end assumes one of the
  fallback routes from doc 03 is needed. Spike results can move Phase 2–6 estimates by
  ±30%; re-estimate at each gate.
- **Calendar.** About 4.3 pw per month at full effectiveness. Calendar time is longer because
  of artist review cycles and waiting for raters.

## 13.2 Phases

### Phase 1 — Technical spike

| Item | Content |
|---|---|
| **Deliverables** | E0–E14 results report (doc 03) for each target version and OS; throw-away probe scripts; API inventory diff vs 2023.2; a decision memo (Go / Pivot / Stop) with a chosen light-creation route; written answers from Luxion on edition and EULA (U1/U2); notes from 8–12 customer interviews (U3/U4, run in parallel by the product owner) |
| **Dependencies** | Licences and machines; a few test scenes |
| **Technical risks** | F-01 (no clean creation route); import side effects; undocumented parameter names; edition restrictions |
| **Acceptance** | The Go criteria in doc 03 ("Spike exit criteria") |
| **Effort** | **2–3 pw** developer; ~0.5 pw artist (building the KMP light materials and test scenes) |
| **Stop / change** | E1 and E2 fail in all routes → pivot (doc 14 §14.3). U1 shows scripting is limited to editions few target studios own → re-scope or stop. |

### Phase 2 — Basic lighting engine

| Item | Content |
|---|---|
| **Deliverables** | `KeyShotAdapter` with capability probe and allow-list guard; `SceneModel` analysis tiers T0–T4 (basic T3); placement maths and constraint checks; module-based generator; realizer (host creation, materials, parameters, transforms, group); environment clone; state store (G/A/O/L), sync, apply plans; regenerate / reset / remove; minimal UI (`getInputDialog`); one draft preset (Solitaire) to exercise the engine; CI unit tests; per-version integration tests |
| **Dependencies** | Phase 1 Go; E13 identification strategy; E10 UI findings |
| **Technical risks** | Sync tolerances (false overrides); edge-case import side effects; UI limits; transform conventions in nested groups |
| **Acceptance** | (1) Integration suite shows **zero non-JLE changes** on all Core scenes, both versions. (2) Regeneration with simulated edits preserves **100%** of overrides unless the user explicitly chooses otherwise. (3) Remove leaves no trace beyond the documented residue (E6). (4) Identical inputs give an identical RigSpec. |
| **Effort** | **5–7 pw** |
| **Stop / change** | If the dialog cannot support iterative work, reduce the UI to one-shot generate / remove plus a separate "sync and report" script |

### Phase 3 — Initial presets (archetype-first)

| Item | Content |
|---|---|
| **Deliverables** | Calibration of *E_ref* per version. Archetypes **S** (Solitaire Ring), **M** (White, Yellow, Rose profiles) and **E** (Packshot), calibrated with artist review cycles 1–2. **Diagnostics v1:** pre-flight material, render-setting and scale checks plus one-preview metrics, with clown-pass or bounding-box masks. Pilot study (doc 12 §12.6) on the Core suite against D0, D1 and D2. Then profiles: Diamond Brilliance, Pavé, Multi-Stone, Dark Luxury (K), Intricate (D), with review cycle 3. Calibrated metric bands per preset. |
| **Dependencies** | Phase 2; benchmark Core suite and labels; artist availability |
| **Technical risks** | Rules that look good on B01 fail on B08–B10 (F-07); flags need a black material; Lux calibration varies by version |
| **Acceptance (Phase 3 gate)** — proposed thresholds, to be confirmed before the pilot | (1) T0 preferred over D0 in ≥ 80% and over D1 in ≥ 60% of blind pairs. (2) T1 reaches "deliverable" faster than D2 in ≥ 2/3 of matched cases. (3) R1 specs (clipping, background) met in ≥ 90% of in-scope cases. (4) No hard failures. |
| **Effort** | **6–9 pw** developer; **4–6 pw** artist |
| **Stop / change** | If T0 is **not** preferred over templates (D1), the automatic-rig value proposition is in doubt. Reposition toward diagnostics plus catalogue consistency, or stop. |

### Phase 4 — Jewelry analysis

| Item | Content |
|---|---|
| **Deliverables** | Improved T3 heuristics; name dictionaries built from real CAD exports; CAD-metadata use (2026.1+); oriented-box use where local frames exist; model memory; identification accuracy report vs ground truth; **angular response maps** for round, oval, princess and emerald (render sweep); E11 mesh-export experiment plus the §5.9 benefit test and a T5 decision |
| **Dependencies** | Phase 3 metrics; Stress suite; E4 timing (sweep cost) |
| **Technical risks** | CAD naming conventions vary widely; response-map sweep cost; mesh export of large scenes |
| **Acceptance** | Role accuracy ≥ 90% on cases with descriptive names and correct materials, ≥ 70% with generic names but correct materials; manual tagging needed in ≤ 30% of Stress cases; response maps integrated, with a measured effect on stone metrics |
| **Effort** | **3–5 pw**, plus **2 pw optional** if the T5 mesh path is justified |
| **Stop / change** | Mesh analysis shows no measurable benefit → do not build it (doc 05 §5.9) |

### Phase 5 — Automatic optimization

| Item | Content |
|---|---|
| **Deliverables** | Preview pipeline; metric-stability protocol results per scene class (doc 08 §8.9); expert controller (diagnose → act → verify); Mode A (single view) with time-boxed budgets per hardware tier; Mode B multi-view diagnostics, plus optimization if stable; before/after UI and accept / revert; optional ablation check |
| **Dependencies** | E4/E5 pass; calibrated bands (Phase 3); render-time table per tier |
| **Technical risks** | F-18/F-19 (cost, noise); metric "hacking" (score improves, image does not) |
| **Acceptance** | On the Core suite: in ≥ 50% of cases where R0 was out of band, the optimized rig improves S by > 2σ; blind preference for optimized vs R0 is **non-inferior** overall and superior in out-of-band cases; ≥ 90% of runs finish inside the time box; zero non-JLE scene changes |
| **Effort** | **4–7 pw** |
| **Stop / change** | Stability fails at affordable preview cost → ship diagnostics only. Optimized results not preferred → drop the optimizer. |

### Phase 6 — Production readiness

| Item | Content |
|---|---|
| **Deliverables** | Offline installer and uninstaller (Windows / macOS); offline licence mechanism; user documentation (incl. supported-case statement and limitations); tested-version matrix; integration suite on all supported versions; beta with 5–10 studios (6–10 weeks of calendar time, overlapping); the main validation study (doc 12) to support or reject the automation claims; bug fixing |
| **Dependencies** | Phases 2–3 (and 5 if included); beta partners; legal and EULA clearance (U2) |
| **Technical risks** | Install environments (F-17); a new KeyShot release during beta (F-06) |
| **Acceptance** | E12 passes on clean machines; zero open critical or high trust bugs (F-04/F-05/F-15 class); beta SUS ≥ 70 (proposal); a published claims statement backed by the doc 12 analysis |
| **Effort** | **4–6 pw** developer, plus artist support for the study |
| **Stop / change** | Beta shows edit loss or scene damage → stop the release until fixed; this is non-negotiable |

## 13.3 Totals

| Scope | Developer effort | Artist effort | Calendar (1 developer) |
|---|---|---|---|
| Spike only | 2–3 pw | ~0.5 pw | 3–4 weeks |
| MVP **without** optimizer (Phases 1–4 + 6) | **20–30 pw** | 6–9 pw | ~5–9 months |
| MVP **with** optimizer (Phases 1–6) | **24–37 pw** (+2 optional mesh path) | 8–12 pw | ~7–11 months |

A second developer would shorten the calendar, but not by half: the artist review cycles and
the validation study are serial bottlenecks.

## 13.4 Gate summary

```
Spike ──Go?──▶ Engine ──▶ Archetypes S/M/E ──Phase-3 gate (beats templates?)──▶ Profiles
                                                   │ no → reposition/stop
                                                   ▼
                                     Analysis (T5 only if proven) ──▶ Optimizer (only if stable)
                                                                          │ no → diagnostics only
                                                                          ▼
                                                               Production + validation study
```
