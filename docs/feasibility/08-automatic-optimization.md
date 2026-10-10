# 8. Automatic Optimization Design

**Position.** Optimization is a *refinement layer* on top of a deterministic rig that is
already good. It is not the source of quality. It ships in two stages:

1. **Diagnostics ("lighting lint")**: one preview, metrics, plain-language findings and
   suggested fixes. Phase 3/4. Valuable on its own.
2. **Bounded optimizer**: a small number of preview renders with controlled parameter changes.
   Phase 5, gated by the cost and stability measurements from E4/E5.

## 8.1 Why image brightness is the wrong objective

Maximizing brightness drives the rig toward large, intense sources near the view axis. That:

- removes the dark facets that make up the pattern in GIA's sense, so diamonds look like
  glass or ice;
- kills fire, because large sources make the dispersed colours overlap and cancel;
- clips metal highlights to white, which destroys gold colour and form;
- flattens metal gradients, so shape becomes unreadable.

Good jewelry images instead need **bounded brightness plus structured contrast**: enough
light to read, darkness in the right places, highlights that stop short of clipping, and
colour in the mid-tones. **The objective is therefore a set of target *bands* per region,
with hard limits. Nothing is maximized.**

## 8.2 Preview pipeline

| Step | Choice | Evidence / note |
|---|---|---|
| Render call | `lux.renderImage(path, w, h, opts, format=PNG)` with `opts = lux.getRenderOptions()` modified in memory | [E1] call; [E3] that the scene's own settings are not altered (E7) |
| Size | 256–512 px long side (decided from E4 stability data); optional `setRegion` around the jewelry or the hero stone | [E1] |
| Budget | `setMaxSamplesRendering(n)` for repeatability, preferred over max time (time varies with machine load) | [E1] |
| Passes | Beauty plus **clown pass** (per-material colours) when masks are needed | [E1]; mapping [E3] (E5) |
| Decode | stdlib PNG decoder → linear-light floats for luminance; display values kept for clipping checks | [E2] |
| Cancellation | User cancel → `renderImage` returns False → the loop stops and keeps the best-so-far | [E1] |

## 8.3 Region masks

The metrics need *where* the stones, metal and background are. Options, in order of
preference:

1. **Clown pass mapped to materials.** For each component, project its world bounding box with
   the camera and take the dominant clown colour inside it. That colour is assigned to the
   component's material. Stones share a gem material, so this gives a "stones" mask. The hero
   mask is the intersection with the hero's projected box or ellipse. Cost: one extra pass
   per preview. Validated by E5.
2. **Projected bounding-box ellipses** (zero render cost). Usable for hero-stone metrics
   (round, oval) and a coarse metal and background split. Poor for pavé and thin metal.
3. **Cryptomatte** (2025.3+) for exact per-object IDs. This needs an EXR decoder; deferred.

**Background** = pixels outside the dilated union of jewelry masks. With an alpha output it is
exact.

## 8.4 Metrics

Notation:

- Y = linear luminance (Rec.709 weights).
- D = display-referred 8/16-bit values, normalized to [0, 1].
- "Region" ∈ {hero, stones, pavé, metal, background, silhouette band}.

| Metric | Definition | Reliability class |
|---|---|---|
| `clip_frac` | fraction of region pixels with max(D_R, D_G, D_B) ≥ 0.98 | **R1** objective, spec-like |
| `hotspot_max_area` | largest 8-connected clipped blob ÷ region area | **R1** |
| `crush_frac` | fraction with D_Y < 0.03 | **R1** |
| `bg_white_frac` | fraction of background pixels with min(D) ≥ 0.99 | **R1** (spec for packshot) |
| `exposure_median` | median Y of the jewelry region | **R1** (target band calibrated) |
| `dark_frac` / `bright_frac` (stones) | fraction with Y < τ_d / Y > τ_b; τ values calibrated per KeyShot version | **R2** reliable to compute; target from artist references |
| `contrast` (stones) | (P95 − P5) / (P95 + P5) of Y | **R2** |
| `sparkle_count` / `sparkle_density` | number of bright blobs (D_Y ≥ 0.95, area 1…A_max px), per 1,000 mask px | **R2**, resolution-dependent; noise-sensitive at low samples |
| `fire_frac` | fraction with D_Y > 0.5 and CIELAB chroma C\* > c_min | **R3** proxy; confounded with colour noise |
| `gradient_energy` (metal) | mean \|∇Y\| over unclipped metal pixels, normalized by mean Y | **R2** |
| `dynamic_range` (metal) | P95 − P5 of Y in metal | **R2** |
| `hue_band` (metal) | mean hue h_ab and chroma of metal mid-tones (0.2 < Y < 0.8) vs the alloy band | **R2** (bands calibrated) |
| `silhouette_contrast` | mean \|Y_in − Y_out\| across a 3–5 px boundary band | **R2** |
| `sparkle_uniformity` (pavé) | coefficient of variation of sparkle density over a 4×4 grid of the pavé mask | **R2** |
| `noise_est` | Immerkær-style fast noise estimate (Laplacian-kernel residual in low-gradient areas), or the difference between two seeds if available | **R3** |
| `render_time_s` | wall clock per preview | **R1** |

**Reliability classes**

- **R1:** objective, with a target set by specification. Safe to optimize against.
- **R2:** objective to compute, but *what value is good* must be calibrated against
  artist-approved references (doc 12). Safe only inside calibrated bands.
- **R3:** a proxy that noise or confounds can fool. Use only as a soft secondary term, and
  only when the stability test (§8.9) passes.
- **Subjective (human-only):** luxury feel, highlight *composition* (where on the piece the eye
  goes), shadow beauty, realism, brand fit, overall preference. These are measured only in
  blind evaluation (doc 12) and are never optimized automatically.

## 8.5 Objective

- **Hard constraints.** Any violation is an immediate reject.
  - Per-preset R1 limits, e.g. `metal.clip_frac ≤ 0.03`, packshot `bg_white_frac ≥ 0.995`.
  - No light inside the jewelry bounding box (geometry check).
  - Locked parameters unchanged.
- **Soft band penalties.** For each targeted metric *m* with band [lo, hi]:
  `pen_m = 0` inside the band, otherwise the normalized distance to the band.
- **Score:** `S = Σ w_m · pen_m` (lower is better), with weights from the preset's
  `objective`.
- **A score is only meaningful relative to its noise.** σ_S is estimated from repeat renders
  of the same rig (§8.9).

## 8.6 The loop: diagnose → act → verify

```
0. Pre-flight (no render): geometry checks; material checks (doc 04 §4.8);
   render-setting checks (ray bounces, caustics vs. preset). Report blockers first —
   do not optimize lights to compensate for a render-setting defect.
1. Generate the deterministic rig R0 (doc 06). best ← R0.
2. Render preview(s) of R0; compute metrics; estimate σ_S (repeat 2–3×, first run only).
3. Diagnose: list violated constraints and out-of-band metrics, ranked by w_m·pen_m.
4. Act: take the top 1–2 deficiencies; apply the mapped corrective action(s) (table below)
   to *tunable, unlocked* parameters, within bounds.
5. Render the candidate; compute metrics and S.
6. Keep if constraints hold and S_new < S_best − 2σ_S; else revert, and mark that action as
   tried for this deficiency (try the next mapped action next time).
7. Stop if any stopping condition (§8.8) holds; else go to 3.
8. Present: before/after previews, metric deltas, and the parameter diff. The user
   accepts (apply as new G with provenance "optimized") or reverts to R0.
```

**Deficiency → corrective-action map (expert controller; initial rules).** This is more
render-efficient than black-box search, because each render tests a hypothesis.

| Deficiency | First action | Second action | Guard |
|---|---|---|---|
| Metal clipping above the limit | Strip and key radiance × 0.8 | Widen strips × 1.3, keeping energy | Re-check stone brightness |
| Metal crushed (black) | Strip radiance × 1.25 | Re-target strips by reflection placement to the darkest metal sector (ψ shift ±15°) | Dark presets allow higher crush |
| Stones too dark (`dark_frac` > hi) | Sparkle radiance × 1.25 | Sparkle ring α − 5° (toward the axis, not below α_min) | Pre-flight confirms ray bounces OK |
| Stones washed out (`dark_frac` < lo) | Key size × 0.8 | Raise α_min by 3°, or darken the environment by 20% | Keep `bright_frac` ≥ lo |
| Low fire (Abbe > 0) | Sparkle size × 0.8 with radiance × 1.2 | Darken the environment by 20% | Only if `noise_est` is OK |
| Too few sparkles | Add a sparkle source at an unused high-response β (if under the cap) | Reduce sparkle size | Light cap |
| Background not white enough (packshot) | Raise environment / background brightness one step | Enable alpha-output suggestion | Re-check metal clip |
| Weak silhouette | Rim radiance × 1.3 | Rotate rim β ±20° | — |
| Exposure out of band | Global G × (target / median) clamped to [0.7, 1.4] | — | Always allowed unless G is locked |

Black-box search (e.g. compass/pattern search over 3–6 continuous tunables) is an optional
Phase 5b fallback when the controller stalls. It uses the same accept/reject rule and budget.

## 8.7 Mode A — single-view optimization

- **Input:** the active camera (or a named camera), the preset objective, a budget
  (default proposal: **≤ 12 renders or ≤ T minutes**, with T chosen by the user, e.g. 2, 5
  or 10).
- Uses region renders around the jewelry where possible.
- **Output:** the optimized rig for that camera.

## 8.8 Mode B — multi-view optimization

- **Input:** a camera set (e.g. front, three-quarter, side, top, low-angle). The rig is shared
  in world space.
- **Per-view scores** S_v. **Aggregate** = max_v S_v (robust), with mean_v S_v as a
  tie-breaker. Hard constraints apply per view.
- **Action choice** targets the worst view's top deficiency. An action is accepted only if it
  improves the aggregate and violates no constraint in any view.
- **Cost control:**
  - evaluate the candidate on the worst view first;
  - only if it improves there, render the other views ("screen-then-verify");
  - a smaller preview size is allowed for secondary views.
- **Inherent limit.** Camera-dependent optics (doc 04 §4.3) mean one world-fixed rig
  *cannot* be optimal for opposite views. When the aggregate stalls with a large spread
  between views, recommend **per-shot rigs**: a separate rig per camera, switched through
  KeyShot **Studios** and **model sets** (`Studio.setModelSets`, `setCamera`) [E2]. This is
  deferred beyond the MVP.

## 8.9 Metric stability protocol (prerequisite for any optimization)

1. For each benchmark scene and candidate preview setting, render the same rig *n* = 5 times.
2. Compute per-metric σ, and σ_S.
3. Choose the cheapest preview setting where:
   - R1/R2 metrics have a coefficient of variation ≤ 5% (proposal);
   - σ_S is less than the smallest action effect you need to detect, measured by applying
     each corrective action once and recording |ΔS|.
4. If no affordable setting satisfies this, **disable the optimizer** for that scene class.
   Ship diagnostics only.

## 8.10 Stopping conditions and fallback

Stop when **any** of the following holds:

| Condition | Outcome |
|---|---|
| All hard constraints met **and** all banded metrics in band | Success |
| Render budget or time box exhausted | Budget |
| 3 consecutive rejected candidates | Stalled |
| The same tunable oscillates (+/−/+) | Oscillation |
| σ_S grows above the median accepted improvement | Unstable measurements |
| User cancel, or `renderImage` returns False | Cancelled |
| A pre-flight blocker appears mid-run (e.g. the user changed materials) | Aborted |

**Fallback rules**

- The deterministic R0 is always kept.
- The final proposal is `best` only if it beats R0 by more than 2σ_S. Otherwise R0 is
  recommended unchanged, to avoid chasing noise.
- Every candidate rig applied during the loop uses only JLE lights and the JLE environment
  clone. On cancel or abort, the Orchestrator restores the pre-run applied state A.

## 8.11 Cost estimation (method, not numbers)

No evidence-based timing exists yet. The model is:

```
T_opt ≈ Σ_iterations Σ_views ( t_render(res, samples, engine, scene) + t_io + t_decode + t_metrics )
        + t_apply·iterations  [+ repeats for σ estimation]
```

**Benchmark (E4).**

- Hardware tiers: an 8-core laptop CPU; a 16–32-core workstation CPU; an NVIDIA RTX-class
  GPU; Apple Silicon GPU (2026.2+).
- Scenes: the doc 12 benchmark scenes.
- Settings: 3 preview resolutions × 4 sample counts.
- Measure each term separately. Report the median and the 90th percentile.
- From these, derive **default budgets per tier**, so that Mode A finishes inside the
  user-selected time box with ≥ 90% probability.
- Publish the measured table with the product. Never quote expected optimization times
  without it.
