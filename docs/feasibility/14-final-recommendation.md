# 14. Final Technical Recommendation

## 14.1 Recommendation

**Do not start product development yet. Fund a 2–3 week technical spike (Phase 1) and, in
parallel, a short market validation.** Continue only if the spike exit criteria in doc 03
are met.

**Why this is worth a spike:**

- KeyShot's model, *light = material on geometry*, means generated lights are fully native
  and editable. That meets the most important product requirement without any custom
  runtime.
- The documented API covers the needed reads (tree, bounds, materials, camera) and writes
  (import, material assignment, material-graph parameters, transforms, environment clones,
  render to file), at least as of 2023.2.
- Jewelry optics supports a **camera-relative, angular, radiance-based** rule system that is
  scale-invariant and explainable. That is a credible core for a strong MVP *without* ML or
  expensive optimization.

**Why it is not yet a "go":**

- The two operations everything depends on, **creating light geometry** and **creating
  configurable light materials**, have *no direct documented API*. They rely on workarounds
  (OBJ import; shipped KMP or material-graph rebuild) that must be proven free of side
  effects.
- Since 2025, KeyShot ships manual tools that already make experts fast: Light Positioning
  "Highlight" mode, planar lights, HDRI pins. The product must beat *those*, not an empty
  scene.
- Whether scripting is available in the editions customers own (2026 Professional / Business /
  Enterprise) is not yet confirmed.

## 14.2 Architecture and policy decisions to adopt now

1. **Deterministic, rule-based generator** in camera-relative angular coordinates;
   **Lux-unit area lights**; scale invariance as a tested property (E14).
2. **Coarse analysis** (materials > spatial > names) with **manual tagging always
   available**. Mesh analysis only if a benefit is measured.
3. **One KeyShot adapter, an allow-list write guard, and environment clones.** Never modify
   user geometry, materials or environments without explicit, reversible consent.
4. **State model G/A/O/L with apply plans.** Regeneration never silently overwrites edits.
5. **Diagnostics in the MVP; optimizer after the MVP**, gated by measured preview cost and
   metric stability.
6. **Ten presets delivered as five archetypes.** Validate three (S, M, E) with artists before
   writing the rest.
7. **Standard library only**; offline install and licence; publish a tested-version matrix.
8. **Claims discipline.** Do not market "90% automation" until doc 12's pre-registered study
   supports it, and then only for the categories it covers.
9. **Positioning hypothesis:** consistency at catalogue volume, plus jewelry-specific
   diagnostics, plus edit-safe automation. Validate it in interviews before Phase 3.

## 14.3 If the spike fails: legitimate pivots

| Pivot | When | How it works | Trade-off |
|---|---|---|---|
| **P1 — Template-first workflow** | E1 and/or E2 fail for *existing* scenes | The tool starts from a **shipped template scene** that already contains JLE light hosts with light materials. It imports the user's jewelry into it (`importFile`, documented), then only *positions and parameterizes* existing lights (transforms and material graph). No geometry or light-material creation is needed. | Works for new shots, not for retrofitting existing scenes; the template must match the KeyShot version |
| **P2 — "Bring your own lights" configurator** | Creation fails, but parameters and transforms work | The user adds N planes once (*Edit › Add Geometry*); the tool tags, configures and positions them | One manual step per scene |
| **P3 — Diagnostics-only product** ("render doctor") | Light control works poorly, or rigs do not beat templates | Pre-flight material, render-setting and scale checks; one-preview metrics; plain-language fixes | Smaller value; minimal API risk; complements every other workflow |
| **P4 — Generated environment (HDR) add-on** | Physical lights are impossible, or as an extra | Synthesize an equirectangular HDR (Radiance RGBE, stdlib) with camera-relative softboxes, and set it via `Env.setLightingEnvironment` | Fails the brief's "physical, editable lights" requirement; pins not editable as pins. **Only as an optional extra.** |
| **P5 — Luxion partnership / API request** | Any API gap | Ask for `createPrimitive` / `createLight`, HDRI-pin and Light-Layer scripting; discuss partner distribution | Depends on Luxion's roadmap |

## 14.4 The first ten actions, in priority order

| # | Action | Output | Owner (suggested) | Effort |
|---|---|---|---|---|
| **1** | **Confirm target versions and editions.** Ask Luxion in writing which 2026 editions include scripting, headless mode and the HDRI Editor, and whether third-party commercial scripts and library-material installs are allowed. Buy or obtain licences for the two target versions on Windows and macOS. | Written answers (U1, U2); licences | Product owner | Days (calendar) |
| **2** | **Run E0, the API inventory**, in each target version: `dir`/`help` dumps, `SHADER_TYPE_*` list, Python version and stdlib check. Diff it against the 2023.2 baseline used in this report. | `jle_inventory_<ver>.json`; diff report; updated doc 02 | Developer | 1–2 days |
| **3** | **Run E1, light-host geometry.** Multi-object OBJ import with explicit options; full before/after scene-state diff; `duplicate()` alternative; P1 template-import check. | Pass/fail per route; side-effect list | Developer | 2–3 days |
| **4** | **Run E2, light materials and parameters.** Material-graph rebuild vs shipped KMP vs bundled library lights; dump the full parameter schema for area, point, spot and planar lights; verify units, colour space and visibility flags are scriptable. | Chosen creation route; parameter schema per version | Developer + artist (builds the KMP) | 3–4 days |
| **5** | **Run E3 and E14, maths and units.** Sphere highlight-placement test (≤ 2% error); transform conventions; Lux scale-invariance test. | Validated conventions; scale-invariance evidence | Developer | 2–3 days |
| **6** | **Run E6, E7 and E13, safety and identity.** Delete, undo and save semantics; environment clone and restore; render-option isolation; ID stability across save and reload. | Safety playbook (which calls are allowed); identification strategy | Developer | 2–3 days |
| **7** | **Run E4, E5 and E10, preview and UI feasibility.** Preview timing per resolution and samples on available hardware; stdlib PNG decode; clown-pass mapping; dialog iteration loop and browser dialog. | Timing table; mask method decision; UI decision | Developer | 3–4 days |
| **8** | **Write the Go / Pivot / Stop memo.** Apply the doc 03 exit criteria and choose the creation route or pivot (§14.3). Re-estimate Phases 2–6. | Decision memo | Developer + product owner | 1 day |
| **9** | **Interview 8–12 target users** (jewelry visualization artists, e-commerce studios, manufacturers' render teams): time per lighting setup today, use of templates, HDRI pins and the Light Positioning tool, catalogue volumes, willingness to pay, edition owned. | Interview synthesis; validated or rejected positioning (U3, U4) | Product owner | 2–3 weeks (parallel) |
| **10** | **Assemble benchmark v0 and the expert baseline.** Ten base models with licences and ground-truth labels, five cameras each (Core suite). Have 2 artists produce timed D2 rigs on 6 cases each, for the pilot. | Core suite plus labels; baseline times and rigs | Artist + product owner | 2–3 weeks (parallel) |

Actions 1, 9 and 10 run in parallel with the developer's spike (2–8). The Phase 2 decision is
taken when all ten are complete.
