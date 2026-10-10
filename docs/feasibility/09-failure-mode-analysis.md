# 9. Failure-Mode Analysis

## Scales

**Probability** (before mitigation):

| Code | Meaning |
|---|---|
| H | Likely |
| M | Plausible |
| L | Unlikely |
| ? | Unknown until the spike |

**Severity:**

| Level | Meaning |
|---|---|
| **Critical** | Invalidates the product or destroys user trust |
| **High** | Makes outputs unusable for common cases |
| **Medium** | Degrades quality or needs manual work |
| **Low** | Cosmetic |

**"Blocks MVP"** means the MVP cannot ship until there is an acceptable answer.

## 9.1 Priority ranking (by potential to invalidate the product)

| Rank | ID | Failure | Why it ranks here |
|---|---|---|---|
| 1 | F-01 | No clean programmatic way to create light geometry or light materials | No product without it |
| 2 | F-02 | Generated rigs are not better or faster than artists' existing workflow | No market without it |
| 3 | F-03 | Scripting unavailable or restricted in the editions customers own, or EULA limits | No market without it |
| 4 | F-04 | Accidental changes to existing scenes | One incident destroys trust |
| 5 | F-05 | Loss of manual edits on regeneration | Breaks the core promise |
| 6 | F-06 | API limitations or version incompatibility | Support cost; can strand customers |
| 7 | F-07 | Preset performance varies wildly between models | Undercuts the "90%" claim |
| 8 | F-13 | Poor lighting from alternate camera angles | Common complaint; inherent physics |
| 9 | F-10/F-11/F-12 | Flat diamonds, dark facets, unnatural gems | Most visible quality failures; often not the lighting's fault |
| 10 | F-08/F-09 | Wrong component identification; missing material information | Common with real CAD; manual fallback exists |

## 9.2 Detailed analysis

### Product-invalidating

| ID | Failure | Root cause | Prob. | Sev. | Detection | Prevention | Recovery | Blocks MVP |
|---|---|---|---|---|---|---|---|---|
| F-01 | Lights cannot be created cleanly | No documented geometry or light-material constructor; import has side effects; library route fails | ? | Critical | Spike E1/E2 | Test three creation routes; capability probe at runtime | Pivot options (doc 14): "bring your own lights" configurator; template-scene workflow; HDR-image generator | **Yes** |
| F-02 | No real value over existing tools | KeyShot Light Positioning (2025.1), HDRI pins, built-in presets and templates are already fast for experts | M | Critical | Artist time studies and blind tests (doc 12); interviews (U3/U4) | Focus on automation **plus** consistency, diagnostics and override-safe regeneration; target catalogue workflows | Narrow positioning (e.g. e-commerce batch consistency), or stop | **Yes** (gate at Phase 3) |
| F-03 | Edition or licensing restriction | Scripting documented as a "Pro feature"; 2026 edition mapping unknown; EULA unknown | ? | Critical | Ask Luxion (U1/U2) | Confirm before Phase 2 | Re-scope the market or the distribution model | **Yes** |

### Trust-critical

| ID | Failure | Root cause | Prob. | Sev. | Detection | Prevention | Recovery | Blocks MVP |
|---|---|---|---|---|---|---|---|---|
| F-04 | Accidental changes to existing scenes | Import options refit the camera or environment; editing the user's environment; `deleteMaterial` touching the library; `saveFile` re-targeting the scene; camera switches losing unsaved camera edits | M | Critical | Before/after scene snapshot diff in every integration test; runtime post-condition checks | Adapter allow-list (writes only to JLE refs); environment *clone*; consented, snapshotted scene actions; never call `deleteMaterial` or `saveFile` on user items; explicit import options | Revert-last-operation from the apply plan; restore snapshots; documented manual recovery | **Yes** |
| F-05 | Loss of manual edits | Naive regeneration overwrites; overrides not detected (tolerances, renamed lights) | M | Critical | Sync diff before every write; tests that simulate artist edits | G / A / O / L state model; apply plans; "Keep my edits" default; rig-relative override storage | Keep the old rig hidden ("generate as new"); state backups | **Yes** |
| F-14 | Lost or mismatched sidecar state | `.bip` moved without its sidecar; unsaved scene | H | Medium | Rig nodes found without state | Backup store; reconstruct A from the scene; name tags | Treat all values as artist-owned; continue | No |
| F-15 | Light re-identification fails | Node IDs change on reload; users rename or duplicate lights | M | High | E13; sync finds unmatched nodes | Layered identification (ID → name tag → material name → fingerprint) | Ask the user to confirm the matches | Yes (needs E13 answer) |

### Platform and operations

| ID | Failure | Root cause | Prob. | Sev. | Detection | Prevention | Recovery | Blocks MVP |
|---|---|---|---|---|---|---|---|---|
| F-06 | API limitations or version incompatibility | Functions renamed or moved (documented mismatch precedent); Python version changes; new light types without API | M | High | E0 inventory diff per release; CI integration tests per supported version | Capability probing; feature flags; a narrow, explicitly tested-version matrix | Disable affected features with a clear message; hotfix | Yes (for the supported versions) |
| F-16 | Missing dependencies | Third-party packages unavailable in the embedded Python | L (by design) | High | Import check at startup | **stdlib-only** policy enforced by a CI import linter | — | Yes (policy) |
| F-17 | Offline installation failures | Network-dependent installer; permissions; antivirus; wrong Scripts folder; macOS quarantine | M | High | E12 on clean VMs | Copy-in install via `getKeyShotFolder(FOLDER_SCRIPTS)` path discovery; signed installer; offline licence file | Manual install guide; uninstall script | Yes |
| F-18 | Excessive render times (previews) | Dispersion, caustics, many small lights, high-resolution previews, CPU-only machines | H | Medium | Measure `render_time_s`; time-box | Region renders; small previews; sample-capped; tier-based budgets (doc 08) | Fall back to diagnostics-only; user-adjustable budget | No (optimizer is not in MVP) |
| F-19 | Unstable preview measurements | Monte-Carlo noise; dispersion colour noise; denoiser variability | H | High (for optimizer) | Repeat-render σ protocol (doc 08 §8.9) | Sample-based previews; R3 metrics as soft terms only; acceptance requires > 2σ | Disable the optimizer per scene class; keep R0 | No (MVP), Yes for Phase 5 |
| F-20 | UI blocks or freezes KeyShot | Long synchronous operations in the dialog callback | M | Medium | E10 | Short operations per click; progress messages; render calls cancellable | Cancel; restore state | No |
| F-21 | GPU/CPU behaviour differences | Visibility flags reportedly differ on GPU; feature gaps (dispersion, caustics) | M | Medium | E8/E9 on both engines | Engine-specific settings; documented limitations | Warn per engine | No |
| F-22 | Light Layers / planar lights unscriptable | Not in the documented API | H | Low | E0 | Use area lights; planar optional | — | No |

### Analysis and identification

| ID | Failure | Root cause | Prob. | Sev. | Detection | Prevention | Recovery | Blocks MVP |
|---|---|---|---|---|---|---|---|---|
| F-08 | Incorrect component identification | Generic names; merged meshes; unassigned materials; props in scope | H | High | Confidence scores; summary screen; diagnostics (e.g. "hero stone not in frame") | Selection-first scope; material-first evidence; conservative thresholds; ask below 0.5 | Manual tagging (always available); model memory | No (manual fallback exists) |
| F-09 | Missing material information | Default or plastic materials on stones; generic glass; no alloy colour | H | High | Shader-type and parameter checks | Ask the user for the stone and metal roles and alloy; suggest (never apply) gem materials | Lighting proceeds by role; diagnostics explain the limits | No |
| F-23 | Wrong scale or units | CAD exported in wrong units | M | Medium | Bounding-box plausibility check | Warn; never rescale | User fixes the units | No |

### Optical and quality

| ID | Failure | Root cause | Prob. | Sev. | Detection | Prevention | Recovery | Blocks MVP |
|---|---|---|---|---|---|---|---|---|
| F-10 | Flat-looking diamonds (washed out, low contrast) | Large sources near the view axis; bright environment; no near-axis darkness | M | High | Stone `dark_frac` below band; `contrast` low | α_min keep-out; dark environment profile; small sparkle sources | Controller: shrink key, darken environment | No |
| F-11 | Dark facets / black stones | **Usually** too few ray bounces, inverted normals, an open mesh, wrong IOR or CAD proportions; less often too little light in high-response directions | H | High | Pre-flight render-setting and material checks; E9 calibration; `dark_frac` high | Offer the Jewelry render preset (consented); response-map sparkle placement | Diagnostics name the likely cause; do not crank up lights to compensate | No |
| F-12 | Unnatural gemstone appearance (glassy, over-sparkly, rainbow noise, "CG" look) | Wrong material values; excessive dispersion (low Abbe); too many tiny lights; too few samples | M | High | `fire_frac` vs band; noise estimate; human review | Abbe sanity range; sparkle cap; sample guidance | Reduce sparkle count; warn about materials | No |
| F-24 | Incorrect diamond geometry | CAD stone library proportions; low-poly melee; duplicates | H | Medium | Duplicate-bounding-box check; mesh checks only in Phase 4 | Diagnostics text; benchmark includes such models | Explain; the user fixes the CAD | No |
| F-25 | Incorrect refractive properties | IOR or dispersion misconfigured | M | High | Read gem parameters | Warn with recommended values (doc 04) | User updates the material | No |
| F-26 | Lights intersecting the jewelry | Small *k*; odd bounding boxes (necklaces); user moved the piece after generation | M | Medium | Bounding-box collision check at generation **and** sync | Push-out rule; minimum *k*; re-check on regeneration | Auto-fix offered | No |
| F-27 | Lights obstructed by prongs or other parts | Prongs inside the head bounding box; no mesh occlusion test | H | Medium | Stone region dark in a sector; coarse bounding-box ray test | Distributed sparkle β; avoid single-source dependence | Controller rotates β; artist adjusts | No |
| F-28 | Excessive reflections (cluttered "window" highlights) | Too many lights; rectangle edges on polished metal | M | Medium | `hotspot` and highlight blob count on metal; human review | Light caps; soft-edged strips; fewer, larger metal sources | Ablation check (Phase 5); mute lights | No |
| F-29 | Overexposed gold | Radiance too high; broad bright environment | H | High | `metal.clip_frac`; hue / chroma shift | Gold profiles (lower radiance, wider strips) | Controller reduces radiance | No |
| F-30 | Unwanted colour contamination | Tinted lights; coloured environment or backplate reflected; gold lighting stones yellow; neutral metal picking up warm fill | M | Medium | Background and metal a\*/b\* drift; stone chroma when not dispersive | Neutral Kelvin defaults; neutral environment clone | Neutralize the Kelvin of the offending module | No |
| F-13 | Poor lighting from alternate camera angles | Camera-dependent optics; world-fixed rig | H | Medium | Multi-view diagnostics (render several cameras) | Camera-relative regeneration per shot; multi-view mode B; per-shot rigs (later) | Regenerate per camera; Studios + model sets workflow | No |
| F-07 | Preset performance varies between models | Unusual designs outside the rules (bypass, cluster, chains, mixed metals); identification errors | H | High | Benchmark distribution, not mean; per-category failure rates | Archetypes with fallbacks; refuse or warn conditions; tagging | Collect failures → rule updates; honest documentation of supported cases | No (but defines the "supported cases" list) |

## 9.3 What the analysis implies

1. **The three "Critical, unknown" items (F-01, F-02, F-03) are resolved by spike results,
   artist studies and a Luxion conversation, not by engineering.** Do these first.
2. **The trust items (F-04, F-05, F-15) are engineering problems with known solutions.**
   Their cost is in tests: snapshot-diff integration tests on every supported version.
3. **Most visible quality failures are not lighting failures.** The pre-flight diagnostics
   (materials, render settings, scale) are as important as the rig generator to how users
   perceive quality.
4. **Camera dependence is physics.** The product should present it as a workflow (regenerate
   per shot, multi-view check), not hide it.
