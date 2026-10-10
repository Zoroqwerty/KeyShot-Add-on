# 12. Testing and Benchmarking Plan

## 12.1 Benchmark dataset

### Base models (B01–B10)

| ID | Model | Purpose |
|---|---|---|
| B01 | Round-brilliant solitaire ring (4-prong, ~1 ct equivalent) | Reference case; stone and band |
| B02 | Emerald-cut ring | Step-cut behaviour; strips |
| B03 | Oval diamond ring | Bow-tie; elongated sparkle placement |
| B04 | Pavé engagement ring (pavé shoulders plus centre stone) | Pavé clusters plus hero |
| B05 | Yellow-gold ring (metal-dominant, polished, small accent stones) | Gold saturation, clipping |
| B06 | Rose-gold ring | Hue identity |
| B07 | White-gold ring (or platinum) | Neutral metal, flags |
| B08 | Multi-stone necklace (stations or graduated stones) | Multi-target cone; large spatial spread |
| B09 | Diamond bracelet (tennis or line) | Many repeated stones; link geometry; size |
| B10 | Complex piece with overlapping components (halo + split shank + gallery, or a cluster brooch) | Identification stress; occlusion |

### Reference stones

Procedurally built round, oval, princess and emerald stones with known proportions (e.g.
Tolkowsky-like round), watertight, correct normals. These serve as ground truth for optics
experiments (E9) and angular response maps. Building them avoids depending on unknown CAD
stone proportions.

### Variation axes

Each base model is varied along these axes; not all combinations are needed:

| Axis | Levels |
|---|---|
| **Dimensions** | Stone size: ~0.3 / 1 / 3 ct equivalents (B01, B03). Ring size: small and large. Export units: correct; ×1000 wrong (tests the scale warning). |
| **Geometry** | Band profile: comfort, knife-edge, flat. Setting: prong / bezel. Pavé density: low / high. Stones separate vs **merged** with metal (STL-style). Low-poly melee vs proper melee. |
| **Material assignment** | Correct (Gem shader, proper metal) / generic glass stones / unassigned (default material) / wrong alloy colour |
| **Naming** | Descriptive English / CAD-generic (`Object 123`, `Brep`) / non-English / misleading (a metal part named "diamond") |
| **Scene context** | Clean / with props (ring box, ground plane, stand) / existing HDRI pins and lights / multiple model sets |
| **Camera angles** | C1 face-up (camera along the table normal) · C2 hero three-quarter (~35° elevation) · C3 side profile · C4 low angle · C5 catalogue front (fixed template). Adapted for necklaces and bracelets (flat lay plus a three-quarter view). |

### Suites

| Suite | Content | Size |
|---|---|---|
| **Core** | 10 models × 5 cameras, clean variant | 50 cases |
| **Stress** | ~100 cases sampled across the variation axes, with emphasis on naming, material and merged-mesh variants | ~100 cases |
| **Catalogue** | One ring design in 3 alloys × 3 stone sizes × 2 settings | 18 SKUs; tests consistency |

### Ground-truth labels per model

Scope nodes, roles (hero, secondary, pavé, metal sub-roles), cut family, table normal, alloy,
finish, jewelry type. These allow the analysis tiers to be scored independently of lighting
quality.

### Sourcing and licensing

- In-house modelled pieces (preferred).
- Marketplace models whose licence explicitly allows benchmarking and publishing renders.
- Customer models under NDA, kept in a separate private suite.
- No model is used without a recorded licence.

## 12.2 Experimental conditions

| Code | Condition | Description |
|---|---|---|
| **D0** | Default | KeyShot default environment plus the "Jewelry" lighting preset; no lights. A naive baseline. |
| **D1** | Template | The best available licensed template scene or HDRI kit, applied with minimal fitting by an artist (≤ 2 min) |
| **D2** | Expert manual | Experienced jewelry visualization artists (≥ 3) use **their real workflow**: own templates, HDRI pins and the Light Positioning tool are allowed. They work until they would deliver to a client. |
| **T0** | Tool, raw | Tool output, no edits |
| **T1** | Tool + artist | The same artists start from T0 and edit until deliverable |

**Design rules**

- A within-artist design: each artist does D2 and T1 on *different but matched* cases.
- Latin-square assignment and counterbalanced order, to control learning effects.
- Identical render settings for final comparison images: resolution, samples, image style.
- Background is allowed to differ only as part of a preset's intent; comparisons are made
  within the same intent.
- Sessions are screen-recorded and time-stamped.

## 12.3 Measures

| Measure | Definition | How |
|---|---|---|
| **Time to usable result** | (a) "usable starting point": the artist rates ≥ 4/5 on "I would refine this rather than start over"; (b) "deliverable": the artist would send it to a client | Timer plus self-report, cross-checked against recordings |
| **Number of manual adjustments** | One adjustment = changes to one parameter of one object, merging changes within 10 s | Tool's override log (doc 06 §6.8) plus coded recordings for non-light edits |
| **Render time** | Final-render wall clock at fixed samples, **and** time to reach a fixed noise level (`noise_est`) | Automated |
| **Failure rate** | *Hard:* crash, scene modification outside JLE (snapshot diff), wrong role not flagged. *Soft:* panel rates "unacceptable", or the artist starts over. | Automated plus panel |
| **Facet readability** | Stone `dark_frac`, `bright_frac`, `contrast`, `sparkle_count` in band (R2) **plus** blind ratings of stone crops | Metrics plus panel |
| **Highlight clipping** | `clip_frac`, `hotspot_max_area` per region (R1) | Metrics |
| **Metal readability** | `gradient_energy`, `dynamic_range`, `crush_frac`, `hue_band` (R2) plus blind ratings | Metrics plus panel |
| **Repeatability** | (i) Determinism: the same input gives identical RigSpec (exact). (ii) Across models in a category: distribution of band violations. (iii) Across repeated renders: σ per metric. (iv) Catalogue: variance across SKUs. | Automated |
| **User satisfaction** | System Usability Scale (SUS), task-specific Likert items, a structured interview | Questionnaire |
| **Identification accuracy** | Role accuracy, hero precision and recall, alloy accuracy vs labels; fraction of cases needing manual tagging | Automated against ground truth |

## 12.4 Blind visual evaluation

- **Format.** Pairwise two-alternative forced choice (2AFC): "Which image would you rather
  publish for this product?" Plus per-image attribute ratings on stone life, metal form and
  overall.
- **Raters.** Jewelry visualization artists, product photographers and merchandisers. Aim for
  ≥ 15 raters; the exact number comes from a power analysis after a pilot (§12.6). Raters must
  not know which condition produced which image.
- **Randomization.** Random order and sides. Include repeated pairs as consistency checks, and
  attention checks.
- **Analysis.** Bradley–Terry scores per condition; non-inferiority tests (below); inter-rater
  agreement with Krippendorff's α. Results are reported per category (ring, earrings,
  pendant, bracelet, necklace) and per preset.

## 12.5 Validating the "≈90% automation" goal

The goal is treated as a **pre-registered hypothesis** with operational definitions.

1. **Primary (time-based) automation ratio, per case:**
   `r = 1 − t(T1 → deliverable) / t(D2 → deliverable)`, the same artist on matched cases.
   The claim "≈90%" is supported for a category if:
   - **median r ≥ 0.9** with a 95% CI lower bound ≥ 0.85; **and**
   - **quality non-inferiority:** T1 is not less preferred than D2 by more than 10 percentage
     points in blind 2AFC (one-sided test); **and**
   - the hard-failure rate is ≤ 2%.
2. **Secondary:**
   - *first-pass acceptance:* the fraction of cases where **T0** (no edits) is rated
     deliverable;
   - *edit fraction:* the fraction of generated parameters unchanged in the final rig.

   Report these, but never headline them. The edit fraction can look high even when the few
   edited parameters took most of the time.
3. **Honest baseline.** D2 includes the artists' own templates and KeyShot's 2025+ tools. A
   comparison against "lighting from an empty scene" would inflate r and is not allowed as the
   primary result.
4. **Reporting.** Full distributions per category; all failures listed; no exclusion of
   "hard" models after the fact. Models that are out of scope by the published
   supported-case statement are reported separately.
5. **Expectation (stated, not assumed).** r near 0.9 is most plausible for **repeat
   catalogue work** (the same camera template, similar SKUs). It is least plausible for
   one-off hero images. A claim may end up valid only for some categories. That is an
   acceptable outcome.

## 12.6 Sample-size approach

Run a **pilot** first (2 artists × 6 cases per condition) to estimate the variance of r and of
preference rates. Then size the main study for:

- the CI width on median r (bootstrap);
- the non-inferiority power on 2AFC (e.g. 80% power at a 10-point margin).

No sample size is asserted before the pilot.

## 12.7 Automated test suites (engineering)

| Suite | What | When |
|---|---|---|
| Unit | Vector maths, placement, constraint checks, state diffing and apply plans, PNG decoder, metrics (pure Python, mock adapter) | Every commit (CI, CPython) |
| Integration (per KeyShot version) | Generate, sync, regenerate-with-simulated-edits, remove, on Core scenes. **Scene snapshot diff must show zero non-JLE changes.** Idempotency (generate twice = same rig). | Every release candidate; every new KeyShot release |
| Golden metrics | Core suite renders; metrics compared with stored bands, **not pixel equality** (renderer noise and version changes) | Per release |
| Install | Clean offline VMs (Windows / macOS), standard user, install → use → uninstall | Per release |
| Performance | Generation time; preview time per tier (E4 protocol) | Per release |
