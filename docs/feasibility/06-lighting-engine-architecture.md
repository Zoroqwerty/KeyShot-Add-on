# 6. Lighting-Engine Architecture

This section also covers the brief's §8, **Light and scene management** (§6.8–6.9), because
its state model is part of the architecture.

## 6.1 Design principles

1. **Lights are native.** Every generated light is ordinary KeyShot geometry with a KeyShot
   light material. The tool has no hidden runtime, so the scene renders identically without
   the tool installed.
2. **Camera-relative, scale-invariant presets.** Presets are written in angles (direction
   relative to the camera and target), *angular* sizes and *radiance* ratios. They are never
   written as coordinates. See [04](04-jewelry-optics.md) §4.5.
3. **Deterministic first.** The same inputs always produce the same rig. Optimization is an
   optional layer that only adjusts a small, declared set of parameters.
4. **One door to KeyShot.** Only the `KeyShotAdapter` imports `lux`. Everything else is pure
   Python and can be tested outside KeyShot with a mock adapter.
5. **Never touch what we did not create.** The adapter refuses writes to non-JLE nodes and
   materials. Scene-wide changes (environment, render preset) go through an explicit
   snapshot-and-restore path and require user consent.
6. **Explain every light.** Each light stores its role, its target, and the rule that placed
   it, shown in the UI as e.g. "Sparkle 3: 35° off-axis at 10 o'clock, 4° wide, targets hero
   stone".

## 6.2 Components

```
┌──────────────────────────── UI (getInputDialog → getBrowserDialog) ───────────────────────────┐
│ preset picker · analysis summary & tagging · rig list (solo/mute/reset) · diagnostics report │
└───────────────────────────────────────────────┬───────────────────────────────────────────────┘
                                                │ commands
                                     ┌──────────▼──────────┐
                                     │    Orchestrator     │  transactions, apply-plans, consent
                                     └──┬───────┬───────┬──┘
              ┌─────────────────────────┘       │       └─────────────────────────┐
   ┌──────────▼──────────┐        ┌─────────────▼────────────┐       ┌─────────────▼────────────┐
   │ A. Scene Analysis    │        │ B. Rig Generation        │       │ C. Optimization          │
   │ tiers T0–T4 (doc 05) │──────▶ │ preset → RigSpec         │──────▶│ render → metrics →       │
   │ → SceneModel         │SceneM. │ placement maths, checks  │RigSpec│ bounded parameter search │
   └──────────┬──────────┘        └─────────────┬────────────┘       └─────────────┬────────────┘
              │                                 │ RigSpec                          │ RenderRequest
              │                     ┌───────────▼────────────┐                     │
              │                     │ Realizer (apply-plan)  │                     │
              │                     └───────────┬────────────┘                     │
   ┌──────────▼─────────────────────────────────▼──────────────────────────────────▼──────────┐
   │ KeyShotAdapter (only module importing lux): capability probe · read scene · create hosts · │
   │ assign/param light materials · transforms · env clone · render preview · guards          │
   └──────────┬────────────────────────────────────────────────────────────────────────────────┘
              │
   ┌──────────▼──────────┐   ┌──────────────────────┐   ┌──────────────────────┐
   │ State Store (JSON)   │   │ Preset Library (JSON)│   │ Diagnostics/Metrics  │
   │ generated/applied/   │   │ archetypes, modules, │   │ PNG decode (stdlib), │
   │ overrides/locks      │   │ profiles, versions   │   │ masks, metrics       │
   └──────────────────────┘   └──────────────────────┘   └──────────────────────┘
```

## 6.3 Interfaces between the subsystems (data contracts)

All contracts are plain, JSON-serializable records with a `schema_version`. Lengths are in
**scene units**, and `units_per_meter` is recorded. Angles are in degrees. The types below
are illustrative schemas, not code.

```text
SceneModel                           # output of A, input of B and C
  schema_version, scene_fingerprint, keyshot_version, units_per_meter
  scope_node_refs[]                  # NodeRef = {id, path_names[], name}
  jewelry: {bbox_min, bbox_max, center, radius_S, type, type_confidence}
  components[]: Component
  hero_stone_ref | null
  frames: {finger_axis?, up_dir?, table_normal?, *_confidence}
  cameras: {active: CameraState, selected_for_multiview[]: CameraState}
  environment: {name, brightness, background, ground_shadows, ...}   # snapshot
  render_settings: {lighting_preset, render_options_dict}             # snapshot
  existing_lights[]: NodeRef          # user lights already in scene
  warnings[]: {code, severity, message, evidence[]}

Component
  ref: NodeRef, role, role_confidence, evidence[]
  material: {name, shader_type, class: stone|metal|other|light|unknown,
             params: {ior?, abbe?, color_rgb?, roughness?}, alloy?, finish?}
  bbox_world, center_world, size_rel (to S), fingerprint
  cluster_id?                        # pavé cluster

CameraState
  name, position, look_at, up, fov_deg, fov_axis(h|v), lens_type, aspect, resolution

PresetSpec                           # from Preset Library
  id, version, archetype, display_name
  required: [hero_stone?|metal?|...], recommended_inputs[]
  modules[]: ModuleSpec              # see doc 07
  environment_profile: {background, brightness_rel, hdri?: none|neutral_gradient}
  render_profile?: {lighting_preset: "Jewelry"|null, min_ray_bounces?}
  objective: {metric targets with tolerances, weights}           # used by C and diagnostics
  tunables[]: {param_path, min, max, step}                       # what C may change

ModuleSpec
  id, role (key|sparkle|strip|rim|fill|flag|kicker), count_rule,
  target (hero|jewelry|metal_band|pave_cluster:k|...),
  placement: {mode: angular|reflection, alpha_deg, beta_deg[] | beta_rule,
              distance_k, aim: target|custom},
  shape: {type: rect|strip|disc, angular_w_deg, angular_h_deg, long_axis_rule},
  emission: {units: lux, radiance_rel, kelvin, two_sided: false},
  visibility: {camera: false, reflections: true, shadows: false}

LightSpec                            # output of B (one per light)
  light_key (stable: rig_id/module_id/index), role, target_ref
  type: area|planar|point|spot, material_template
  world: {position, normal, long_axis, width, height}
  emission: {units, value, kelvin, rgb_linear}
  visibility flags, rationale (human-readable), checks: {collision, frustum, occlusion}

RigSpec
  rig_id, preset_id, preset_version, scene_fingerprint, camera_name, lights[]: LightSpec
  environment_actions[], render_actions[]       # explicit, reversible
  generated_at, generator_version

RigInstance                          # output of Realizer
  rig_id, light_key → {node_ref, material_name}, group_ref, env_clone_name,
  applied_values (exact values written), applied_at

RenderRequest / RenderResult         # C ↔ Adapter
  camera_name, width, height, max_samples|max_time, passes[], region?, seed_note
  → image_path(s), elapsed_s, ok

MetricReport
  per_region: {hero, stones, metal, background}: {clip_frac, dark_frac, contrast,
             sparkle_count, chroma_bright_frac, gradient_energy, hue_stats, ...}
  global: {noise_est, render_time_s}, stability: {cv per metric (if repeated)}

OptimizationRequest / Result
  rig_id, camera_set, objective, tunables, budget {renders, seconds}, locks
  → best_rig_spec, history[], stop_reason, metric_reports[]
```

**Boundary rules**

- A never writes to the scene.
- B is a *pure function* `(SceneModel, PresetSpec, Overrides, Locks) → RigSpec`, with no
  KeyShot calls.
- C may only change the parameters listed in `tunables` that are not locked.
- Only the Realizer and the Adapter write to the scene, and only by executing an **apply plan**
  (a list of intended writes) that the Orchestrator has checked against locks and overrides.

## 6.4 Placement mathematics

**Notation.**

| Symbol | Meaning |
|---|---|
| *p* | Target point (hero centre, jewelry centre, or a cluster centre) |
| *c* | Camera position |
| *u_c* | Camera up vector |
| *S* | Bounding-sphere radius of the **whole** piece (for clearance) |

### 6.4.1 Camera-relative frame

```
v = normalize(c − p)            # toward the camera
r = normalize(u_c × v)          # screen-right
u = v × r                       # screen-up
```

### 6.4.2 Angular placement (the photographer's description)

Each light is described by:

- off-axis angle **α**: 0° = directly behind the camera, 90° = side-on, >90° = behind the
  subject;
- clock angle **β**: 0° = 12 o'clock / top of frame, 90° = 3 o'clock / right.

```
ω(α, β) = cos α · v + sin α · (cos β · u + sin β · r)     # unit direction from p to light
L       = p + D · ω,     D = k · S                         # light centre
n_L     = −ω (aim at p)  or  normalize(aim_point − L)      # emitter normal
w       = 2 D tan(θ_w / 2),   h = 2 D tan(θ_h / 2)         # size from angular size
t       = normalize(long_axis_ref − (long_axis_ref·n_L) n_L)   # strip long axis in light plane
```

Default distance factor: *k* = 5 (initial; tunable range 3–10).

- Small *k* gives more parallax: each stone sees the light from a different angle, which
  means more sparkle variety but less uniformity.
- Large *k* behaves like an environment.

*k* has no effect on specular highlight brightness (radiance) or size (angular size). It
changes **diffuse fall-off across the piece**: at *k* = 5 the near and far sides differ in
irradiance by about (5.5 / 4.5)² ≈ 1.5×. That is acceptable for fill light, and a reason not
to go below *k* ≈ 3.

### 6.4.3 Reflection placement (to put a highlight where we want it)

For a surface point *q* with unit normal *n*, seen from camera *c*:

```
o = normalize(c − q);  require n·o > 0                # point faces the camera
i = 2 (n·o) n − o                                     # mirror direction toward the light
L = q + D · i ;  n_L = −i                             # light centred on the mirror ray
```

This is the same principle as KeyShot's GUI "Highlight" mode (Light Positioning tool) and the
HDRI Editor's "Set highlight", here computed without a click.

**Where *q* and *n* come from without mesh access: analytic proxies.**

| Proxy | How it is built | What it gives |
|---|---|---|
| **Ring band** | Finger axis *a*, band centre *c_b*, outer radius *R_o* (half of the extent perpendicular to *a*), width *W* (extent along *a*) | Surface point at azimuth ψ around *a*: `q = c_b + R_o e(ψ)`, normal `n ≈ e(ψ)` (cylinder). For domed or comfort-fit profiles, `n` tilts toward ±*a* by γ ∈ [0, γ_max]; γ_max is a preset parameter (initial 40°). A strip whose long axis is parallel to the band's local tangent draws a continuous highlight line whose position is set by ψ. |
| **Plate / pendant face** | Normal = the thinnest bounding-box axis (or the local-frame axis) | Planar mirror placement |
| **Hero table** | Table normal *t_n* (doc 05, T3.6 / T3.7) | The "table flash" direction. Presets usually **avoid** placing large sources exactly on it (glare), and may place a small source near it on purpose. |

E3 validates the maths on a sphere with a known answer before any proxy is trusted.

### 6.4.4 Multi-target cones (multi-stone, pavé)

For targets *p_j*, with view vectors *v_j* and a shared light at *L*:

- the direction error at target *j* is about `angle(L − p_j, L − p_ref)`, roughly
  `|p_j − p_ref| / D`;
- sparkle modules for multi-stone pieces choose *k* so that this parallax stays below the
  module's angular tolerance (e.g. 5° → `D ≥ 11.5 · max|p_j − p_ref|`). Alternatively they
  **use** the parallax to spread sparkle across a pavé field by spreading β.

### 6.4.5 Constraint checks (all cheap, bounding-box level)

1. **Collision.** Light rectangle corners and centre must lie outside the jewelry bounding
   box inflated by 0.15 S. If not, push the light outward along ω.
2. **Frustum.** Project the light corners with `CameraState`. If any corner is in frame and
   camera-visibility is on, switch that light to camera-invisible (default) or move it.
3. **View-axis keep-out.** Keep α ≥ α_min (default 8°) for all large sources. This preserves
   the near-axis "obstruction" darkness that gives stones their pattern (doc 04 §4.3).
4. **Coarse occlusion.** Test the segment *L* → *p* against the bounding boxes of other
   in-scope components, excluding the target's own head. If it intersects, rotate β in ±10°
   steps up to ±40°. If still blocked, keep the light and flag `occlusion: possible`.
   Prong-level occlusion is handled statistically: several sparkle sources at different β.
5. **Ground.** If the environment has ground shadows enabled and the piece is snapped to the
   ground, keep lights above the ground plane (α and β limited accordingly). The behaviour of
   lights below KeyShot's ground is [E3].

## 6.5 Data-driven priors: angular response maps

Experiment (Phase 3, reused in Phase 4):

1. For each cut family at standard proportions, render the stone face-up lit by **one** small
   source.
2. Sweep that source over a camera-relative grid of α (0°–90° in 5° steps) and β (0°–360° in
   15° steps).
3. Record the stone region's mean luminance, bright fraction and chroma (fire proxy).

The resulting tables say *which directions a given cut actually turns into return light and
fire, for this KeyShot version's gem shader*. Sparkle modules then sample β and α from
high-response bands instead of from folklore.

These are lookup tables, not a model, so this is not ML. The cost is offline and one-off.
Grid size × render time per cell is measured in E4 before the sweep resolution is decided.

## 6.6 Intensity and colour

- **Units.** All generated area and planar lights use **Lux** (emittance per area), so
  appearance stays constant when lights are resized or the piece is rescaled (doc 04 §4.5;
  verified by E14). Artists can switch any light to Lumen or Watt; the tool records it as an
  override.
- **Radiance ratios, not absolute numbers.** Each module carries `radiance_rel`. The rig
  value is `E_v = G × E_ref × radiance_rel`, where:
  - *G* is a global exposure scalar (the main tunable);
  - *E_ref* is a per-KeyShot-version reference emittance. *E_ref* is calibrated once during
    Phase 3: the Lux value at which a source reflected in a neutral polished metal renders at
    about 80% display white under KeyShot's default image style.

  Because image-style exposure is not scriptable in 2023.2 [E4], *G* absorbs scene-specific
  exposure differences. The diagnostics layer flags extreme *G*.
- **Initial ratio conventions** (hypotheses to calibrate with artists):

  | Module | Ratio |
  |---|---|
  | key | 1.0 |
  | sparkle | 1.5–3.0 (small, so total energy stays low) |
  | strip | 0.6–0.9 |
  | rim | 0.8–2.0 (dark presets higher) |
  | fill | 0.1–0.25 |
  | flag | 0 (black card) |

- **Colour.** Presets specify a **Kelvin** value. The engine converts Kelvin → CIE xy
  (Planckian locus approximation) → linear Rec.709 RGB, normalized to unit luminance. E2
  determines whether KeyShot's light colour parameter expects linear or sRGB values.
  Commercial presets default to a neutral 5000–6500 K; tinted lights are allowed only in
  explicitly stylistic presets.

## 6.7 How many lights

- Presets declare modules with `count_rule`, e.g. `sparkle: 4 for round, 6 for elongated,
  +2 per extra stone cluster, cap 8`.
- Global cap in the MVP: **≤ 10 lights per rig**, typically 4–7.
- **Every light needs a role and a measurable contribution.** After the first preview, an
  optional *ablation check* mutes each light in turn (hide/show; one render per light, so
  costly; Phase 5 only). It proposes removing any light whose absence changes all region
  metrics by less than the noise floor.
- **More lights is not better.** Each light adds highlights that compete for attention, more
  noise to converge (more light sampling), and more for the artist to manage.

## 6.8 Light and scene management (brief §8)

### State layers

| Layer | Meaning | Where it lives |
|---|---|---|
| **G — Generated** | The `RigSpec` the engine computed: every parameter, plus provenance (preset and version, `SceneModel` fingerprint, camera snapshot) | State store |
| **A — Applied** | The exact values written to KeyShot at the last apply, plus node refs, the group ref and material names | State store |
| **O — Overrides** | Per light, per parameter: the artist's value, when it was detected, and the override mode (§ below) | State store, derived on sync |
| **L — Locks** | Explicit per-light or per-parameter flags: "never change". Overrides imply a soft lock. | State store |
| **E — Evaluated** | What is in KeyShot now: the truth. By construction E = A ⊕ O. | KeyShot scene |

### Sync

On every tool action, *before* any write:

1. Read E for all rig lights: transform, size from scale, material parameters, visibility,
   hidden state.
2. Diff E against A with tolerances: position 1e-4 S, angle 0.1°, relative emission 0.5%.
3. Record differences in O. Also detect deleted, duplicated, renamed and foreign-moved lights
   (identification strategy in E13).

### Regeneration (never silent)

1. Sync. Compute the new G′ from the current scene, camera and preset.
2. Build an **apply plan**: per light, per parameter, `old A → new G′`, marked:
   - **free:** no override;
   - **overridden:** O exists;
   - **locked:** L set.
3. If any overridden or locked entries would change, show a dialog with a per-light summary:
   - **Keep my edits** (default). Apply G′ to free parameters only. Overridden parameters keep
     the artist's values. Conflicts are listed where G′ moved a lot, e.g. "key light: you
     moved it; the new camera suggests 25° higher".
   - **Replace selected edits**: per-light checkboxes.
   - **Generate as a new rig**: the old rig is hidden, not deleted.
   - **Cancel.**
4. Execute the plan; store G′ and A′. O keeps only the parameters that are still overridden.

### Override modes for transforms

An artist who moved a light may have meant "this world position" or "this position relative
to the camera". The override is stored in both forms: world coordinates, and rig-relative
(α, β, D). On regeneration for a **different camera**, the default is *rig-relative*,
because it keeps the artist's intent ("I raised the key light"). The world option is one
click away.

### Other operations

| Operation | Implementation |
|---|---|
| Select a light | `SceneNode.select()` from the rig list; the KeyShot Move tool / Light Positioning tool then works natively |
| Move, rotate, resize, change intensity | Native KeyShot tools; detected as overrides on next sync |
| Solo / mute | `hide()` / `show()` on rig nodes only; the original hidden states are recorded and restored |
| Naming | Nodes: `JLE·<rigId>·<role>·<nn>` (e.g. `JLE·7Q2K·sparkle·03`). Group: `JLE Rig 7Q2K — Solitaire Ring`. Materials: whatever KeyShot assigns on duplication (recorded in A); renaming materials has no documented API. |
| Reset one light | Apply G for that light; clear its O and L (with confirm) |
| Reset rig | Apply G for all; clear O (confirm, with count of edits lost) |
| Save configuration | Export RigSpec + O as a `.jlerig.json` "look" file: preset plus artist tweaks in rig-relative form. It can be applied to other pieces, which is the **catalogue-consistency feature**. |
| Load configuration | Import a look file → regenerate for the current piece and camera |
| Remove rig | Delete rig nodes. Re-activate the user's original environment; optionally remove the JLE environment clone. Restore the render snapshot if we changed it. Leave or delete our materials according to E6. Then verify by scanning for `JLE·<rigId>` remnants. |
| Undo | KeyShot's own undo is left enabled (behaviour from E6). The tool offers its own **"Revert last operation"**, built from the apply plan's old values. There is no transactional undo in the API [E4]. |

### Storage

- **Primary:** a sidecar `<scene file>.jle.json` next to the `.bip`, using atomic writes
  (temp file + `os.replace`), a schema version and a checksum.
- **Backup:** `<KeyShot config root>/JewelryLightEngine/state/<scene-hash>/<rig_id>.json`,
  with the last N versions.
- **Unsaved scenes** (no path yet): use the backup store only. On next launch, reconcile by
  scanning the tree for `JLE·` nodes and matching rig IDs.
- **If the sidecar is lost** (e.g. the `.bip` was sent alone): the rig still renders. The tool
  can **reconstruct A** from the scene (names, transforms, parameters) and treat it as
  "generated values unknown, all values are artist-owned". Nothing breaks; only the
  generated/override distinction is lost.

### Never modify user geometry or materials

- The adapter keeps an **allow-list of node and material refs created by this tool** (from A).
  Write calls on anything else raise an error inside the tool. This includes `setMaterial`,
  `applyTransform`, `hide`/`show`, `delete` and `setName`.
- Scene-wide writes (environment, lighting preset, render options) are a separate, consented
  "scene actions" channel with a snapshot and restore.
- Analysis uses only read calls. The optional mesh export (Phase 4) writes only to a temp
  file.

## 6.9 Interaction with the user's existing lighting

Scenes often already contain an HDRI, pins and some lights.

- Existing light materials are found by shader type during analysis and listed. The rig is
  **additive** by default.
- **"Preview without existing lights"** temporarily hides them. This changes user nodes, so it
  needs consent, and their state is recorded and restored when the preview ends.
- **The environment.** The preset's environment profile is applied to a **clone**
  (`newEnvironment(name, activate=True, clone=True)`). HDRI pins in the user's environment are
  preserved in the original. Whether the clone also carries the pins is [E3]; it is useful
  either way.
- The tool never deletes user lights.

## 6.10 Comparison of approaches

| Approach | What it means here | Strengths | Weaknesses | Verdict |
|---|---|---|---|---|
| **Deterministic rules** | Presets as camera-relative modules (§6.4.2) | Instant, explainable, repeatable, scale-invariant, easy for artists to predict | No awareness of the specific piece beyond frames and targets | **Core of the MVP** |
| **Geometric heuristics** | Role targeting, reflection placement on proxies, collision and occlusion checks, response-map priors | Adapts to each piece at near-zero cost | Proxies are approximate; no prong-level knowledge | **MVP (bounding box + proxies)**; mesh-based only if gated |
| **Numerical optimization on cheap proxies** | Optimize analytic coverage, e.g. "highlight stripe spans 60% of the band arc", without rendering | Fast | The proxy objective may not track the real image | Phase 4, small and optional |
| **Image-based evaluation** | Preview render → metrics (doc 08) | Measures what the customer sees; catches defects | Render cost, noise, metric validity | **Phase 3 as diagnostics, Phase 5 as bounded optimizer** |
| **Black-box optimization over renders** | Pattern search or CMA-ES over tunables | General | Many renders; noisy; may find "metric hacks" | Phase 5 only, with a tiny budget and an expert-rule controller first |
| **Machine learning** | Learn a placement policy or aesthetic critic | Could encode taste if data existed | **No dataset, no labels, no differentiable renderer, opaque behaviour** | **Not justified.** Revisit only after collecting many artist-approved rigs and pairwise ratings, and then as a *ranking* model, not a generator. |

**Can rules alone give a strong MVP?** Very likely yes for the **starting-point** claim. Most
commercial jewelry lighting follows reusable, camera-relative patterns: overhead key, strip
gradients, sparkle sources, rims, flags. The open question is not *whether* rules work, but
*how often* they need more than minor edits. Doc 12 measures exactly that.

## 6.11 Packaging and technology

- **Pure Python, standard library only**, targeting the oldest Python in the supported
  KeyShot range (3.11 or 3.12; decided by E0). No NumPy or Pillow inside KeyShot.
- **Image decoding:** a small stdlib PNG decoder (`zlib` + `struct`) for 8- and 16-bit RGB(A).
  EXR (Cryptomatte) is deferred.
- **Layout (proposed):**

  ```
  Scripts/Jewelry Light Engine.py    # launcher
  jle/adapter/keyshot.py             # only lux user
  jle/adapter/mock.py                # tests
  jle/core/{model, vecmath, analysis, presets, generator, realizer, state}.py
  jle/eval/{png, masks, metrics, optimizer}.py
  jle/ui/{dialogs, browser/}.py
  jle/presets/*.json
  jle/assets/JLE_Lights.kmp          # if route (b) of E2 is chosen
  ```

- **Tests:** unit tests for the maths and state logic run in CI with CPython and the mock
  adapter. Integration tests run in KeyShot via a headless or console test script on each
  supported version (doc 12).
