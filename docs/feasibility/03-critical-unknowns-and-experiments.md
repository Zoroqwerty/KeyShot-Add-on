# 3. Critical Unknowns Requiring Experiments

These experiments make up **Phase 1 (technical spike)**. Each one names the question, why it
matters, a procedure, what to measure, a pass criterion, and what to do if it fails.

The code fragments are **sketches built only from documented 2023.2 function names. They have
not been run.** Their purpose is to make each experiment concrete. They are not product code.

## Ranking

| ID | Question | Blocks | Severity if it fails |
|---|---|---|---|
| **E0** | What does the target version's API actually contain? | Everything | Critical |
| **E1** | Can a script create light-host geometry without side effects? | MVP | **Critical: product premise** |
| **E2** | Can a script create, assign and parameterize light materials? | MVP | **Critical: product premise** |
| **E3** | Do transforms and our placement maths behave as predicted? | MVP | Critical |
| E6 | Are delete, undo and save safe and predictable? | MVP | High (trust) |
| E7 | Can environment and render settings be changed non-destructively? | MVP | High (trust) |
| E13 | Can generated lights be re-identified after save, reload and user edits? | MVP | High |
| E14 | Are Lux / Lumen units scale-correct with mm scenes? | MVP quality | High |
| E10 | Is the scripted UI usable (dialogs, callbacks, browser dialog)? | MVP UX | Medium |
| E12 | Does offline, stdlib-only install work on clean Windows and macOS machines? | Release | High |
| E4 | How much does a preview render cost, and can we read its pixels? | Optimization | High for Phase 5 |
| E5 | Can we segment stones, metal and background in a preview? | Optimization | Medium |
| E8 | Do visibility flags behave the same on CPU and GPU, including inside gems? | Quality | Medium |
| E9 | How much of "bad diamonds" is render settings rather than lights? | Scope of claims | Medium |
| E11 | Is scene export plus offline mesh parsing practical for analysis? | Phase 4 only | Low for MVP |

---

## E0 — API inventory in the target version

**Why.** The baseline here is the 2023.2 docstrings. The documentation has known mismatches
with the installed module, and versions drift.

**Procedure.** In each target version (proposed: 2025.3 and 2026.2, on Windows and macOS),
run in the Scripting Console:

```python
# SKETCH — untested
import lux, luxmath, sys, json
inv = {
    "ks_version": lux.getKeyShotVersion(),
    "ks_display": lux.getKeyShotDisplayVersion(),
    "python": sys.version,
    "lux": sorted(n for n in dir(lux) if not n.startswith("_")),
    "SceneNode": sorted(n for n in dir(lux.SceneNode) if not n.startswith("_")),
    "MaterialGraph": sorted(n for n in dir(lux.MaterialGraph) if not n.startswith("_")),
    "Env": sorted(n for n in dir(lux.Env) if not n.startswith("_")),
    "ImageStyle": sorted(n for n in dir(lux.ImageStyle) if not n.startswith("_")),
    "RenderOptions": sorted(n for n in dir(lux.RenderOptions) if not n.startswith("_")),
    "shader_types": {n: getattr(lux, n) for n in dir(lux) if n.startswith("SHADER_TYPE_")},
    "lighting_presets": lux.getLightingPresets(),
}
json.dump(inv, open("<scratch>/jle_inventory.json", "w"), indent=1, default=str)
```

Also save the full `help(lux)` text, and test that `zlib`, `json`, `struct`, `os`,
`tempfile` and `subprocess` import.

**Measure.** A diff against the 2023.2 inventory. Look specifically for:

- a planar-light shader constant;
- any geometry, primitive or light creation call;
- light-layer, HDRI-pin or undo-group calls;
- `getBrowserDialog`;
- an exposure setting on `ImageStyle`.

**Pass.** Every function listed in the MVP path of doc 02 is present.

**If it fails.** Rework the creation path around whatever *is* present. If a newer version
adds a direct light-creation API, use it there and keep E1/E2 as the fallback for older
versions.

## E1 — Light-host geometry via OBJ import

**Why.** There is no documented primitive-creation call (G1).

**Procedure.**

1. Open a reference jewelry scene: a ring with stones, a saved camera, a custom environment,
   and some unsaved camera changes. Record a full state snapshot: tree dump, camera,
   environment name and parameters, lighting preset, scene info, the list of model sets, and
   `isSceneChanged`.
2. Write a temporary OBJ containing three named unit rectangles (`o JLE_probe_01` … `03`),
   with explicit `vn` normals and no `mtllib`.
3. Import it with explicit options:

   ```python
   # SKETCH — untested
   opts = lux.getImportOptions()
   opts.update({"import_type": 0, "center_geometry": False, "snap_to_ground": False,
                "adjust_camera_look_at": False, "adjust_environment": False,
                "separate_parts": True, "merge_objects": False, "merge_groups": False,
                "retain_materials": False})
   # also test: geometry_units (scene-unit factor), up_vector (0..5), model_set_import_to
   before = {n.getID() for n in lux.getSceneTree().find("")}
   ok = lux.importFile(obj_path, showOpts=False, dontAsk=True, opts=opts)
   new = [n for n in lux.getSceneTree().find("") if n.getID() not in before]
   ```

4. Snapshot again and diff.
5. Repeat with: the jewelry selected and unselected; scene units of mm and m; a scene with
   several model sets; the GUI vs headless.
6. Also test `duplicate()` of an imported host as an alternative to importing more.

**Measure.**

- Which nodes appeared (group, model, objects) and with what names and world transforms.
- Any change to the camera, environment, materials, units or model-set activation.
- Whether a default material was created and what it was named.
- How many undo steps were added.
- Import time.

**Pass.**

- Each OBJ object becomes a separate, addressable object node, inside a single group.
- The camera, environment, units and existing materials are unchanged.
- The world transform matches the OBJ coordinates within 1e-6 × scene size, after a known
  unit or up-axis mapping.

**If it fails.**

- (a) Try `duplicate()` of a host created once by the user through *Edit › Add Geometry*, with
  the tool guiding them.
- (b) Ship a template `.bip` / `.ksp` and test whether it can be *imported into* (not opened
  over) the current scene.
- (c) As a last resort, adopt a "bring-your-own-lights" mode: the user adds N planes once, and
  the tool configures and positions them.

If none of these work without user-visible side effects, the native-light premise fails; see
[14](14-final-recommendation.md).

## E2 — Light-material creation, assignment and parameters

**Why.** There is no documented light-material constructor (G2), and the light parameters
are undocumented (G3).

**Procedure.**

- **Route (a), graph rebuild:** `createSceneMaterial("JLE_probe")` →
  `g = getMaterialGraph("JLE_probe")` → `r = g.getRoot()`; record `r.getType()` and
  `r.getParameters()` → `n = g.newNode(lux.SHADER_TYPE_MESH_LIGHT)` → try to connect `n`
  where the surface shader goes (inspect `r.getInputEdges()`) → apply the material to a probe
  host and see whether it emits light.
- **Route (b), shipped package:** build `JLE_Lights.kmp` *in the GUI* containing "JLE Area
  Light", plus "JLE Planar Light" where the version supports it, and "JLE Black Flag" (a
  black diffuse material) → `importMaterials(kmp, folder="JLE")` →
  `node.setMaterial("JLE Area Light", link=False)` → `node.getMaterial()` returns the
  duplicate's name → `getMaterialGraph(dup).getRoot().getParameters()`.
- For each light type, dump every parameter: `getName`, `getDisplayName`, `getType`,
  `getValue`. Then try `setValue` on power, units, colour, the camera / reflection / shadow
  visibility flags, and front/back emission.
- Check the per-light independence of `link=False`: change one light and confirm the others do
  not change.

**Measure.**

- Which route works.
- The full parameter schema per light type, per version.
- Whether units can be set by script.
- Whether colour accepts linear or sRGB values. Calibrate by rendering a white Lambertian card
  under a light of known colour.

**Pass.** At least one route produces N independent, editable area lights whose power,
colour and visibility flags can be set and read back by script.

**If it fails.**

- If parameters cannot be set, ship one material variant per intensity / colour step. This is
  coarse and a poor fit with the product goal.
- If no light material can be applied at all, the native-light premise fails.

## E3 — Transform semantics and placement-maths validation

**Why.** The engine puts reflections where it predicts they will appear. Conventions (Y-up,
row vectors, Euler order, horizontal vs vertical FOV, the meaning of `absolute=True`) must be
pinned down.

**Procedure.**

1. Use a test scene: a polished metal sphere of known radius at a known position, a camera
   with known FOV, and a black environment.
2. For five target surface points, compute the mirror direction
   (doc 06, §"Reflection placement").
3. Place a small area light along each mirror direction at distance D.
4. Render at 800×800 and find the brightest blob centroid.
5. Compare it with the predicted projection of the target point.

Also test:

- `applyTransform` relative vs absolute on a node nested under a transformed group;
- `getTransform(world=True)` round-trip;
- `rotateAroundAxis` direction (right-handed?);
- whether `getCameraFieldOfView` is horizontal or vertical for a non-square aspect ratio.

**Pass.** The highlight centroid is within 2% of the image width of the prediction, for all
points and for two aspect ratios.

**If it fails.** Fix the conventions (this is cheap). Fail only if transforms are not
reproducible.

## E4 — Preview cost and pixel access

**Procedure.** On the benchmark scenes (doc 12), run `renderImage` at:

- 256, 384 and 512 px;
- max samples 16, 32, 64 and 128, and max time 2, 5 and 10 s;
- CPU and GPU (where present);
- with and without the Jewelry lighting preset and caustics.

Time the wall clock, including file write and the pure-Python PNG decode (stdlib `zlib`).
Repeat each configuration 5 times to measure metric variance (see E5 / doc 08). Test
`lux.screenshot()` as a near-free preview and characterise its convergence. Check whether
`renderImage` blocks the GUI and whether the user can cancel.

**Pass for Phase 5 viability.** A preview whose key metrics have a coefficient of variation
of 5% or less costs ≤ 20 s on the reference hardware. This is a *proposed* threshold: it makes
a 10-iteration single-view optimization take about 3–4 minutes.

**If it fails.** Optimization becomes "diagnose once, suggest fixes" (lint), not a loop.

## E5 — Segmentation masks

**Procedure.**

1. Render the clown pass alongside the beauty pass. Check that the colours are constant per
   material across renders and versions.
2. Map colours to materials by projecting each component's bounding box (we know the camera)
   and taking the dominant clown colour inside it.
3. Compare against ground-truth masks: render with temporary flat materials *in a copy of the
   scene only*.
4. Also evaluate the zero-render option: projected bounding-box or ellipse masks.

**Pass.** Stone-mask IoU ≥ 0.8 for the hero stone and ≥ 0.6 for pavé clusters.

## E6 — Delete, undo and save safety

**Procedure.**

- **Deletion:** delete the probe lights, save, reload, and inspect for remnants
  (`getDeleted`).
- **Material deletion:** call `deleteMaterial` on (i) a scene-only probe material and (ii) a
  library material in a *disposable* library folder. Determine whether the library is
  touched.
- **Undo:** after a full rig generation, press undo repeatedly and record what reverts. Repeat
  with `setUndoEnabled(False)` during generation.
- **Save:** `saveFile(path)` to a different path, then check whether the window title and the
  scene's path changed.

**Pass.** We can fully remove a rig and leave **no** trace in the scene or library, and we
know exactly how undo behaves.

**If it fails.** Avoid the call that misbehaves (for example, never call `deleteMaterial`;
leave orphan materials and tell the user); document the behaviour.

## E7 — Non-destructive environment, render settings and camera

**Procedure.**

- **Environment:** `newEnvironment("JLE_probe", activate=True, clone=True)`, edit it, then
  `setActiveEnvironment(original)`. Diff the original environment's parameters; they must be
  bit-identical.
- **Render settings:** snapshot `getLightingPreset()` and `getRenderOptions().getDict()`,
  switch to "Jewelry", then restore.
- **Camera:** switch cameras for multi-view and back, with an *unsaved* active camera. The
  unsaved changes must survive.
- **Render options:** pass a modified `opts` to `renderImage` and confirm the scene's own
  render options are unchanged.

**Pass.** All restorations are exact.

## E8 — Visibility flags on CPU vs GPU and inside gems

**Procedure.** Area light behind the camera, with each combination of camera / reflection /
shadow visibility flags. Observe it on chrome metal, in the diamond's *refraction*, and on the
ground, in CPU and GPU modes. (A community report says flags behaved differently on GPU.)

**Pass.** The flag behaviour is documented in a table; the engine uses only consistent
combinations.

## E9 — What lighting cannot fix (gem rendering sanity)

**Procedure.** Use a reference round brilliant built procedurally with known proportions and
watertight geometry (doc 12). Render it with fixed lights while varying:

- ray bounces (e.g. 6, 12, 24, 48);
- the Gem material's Abbe number (0 vs about 55);
- IOR (1.5 "glass" vs 2.417);
- inverted normals;
- an open mesh;
- CPU vs GPU.

**Measure.** The stone metrics from doc 08.

**Use.** This separates *render-setting and model defects* from *lighting defects*, so that
diagnostics blame the right thing, and it calibrates the "minimum ray bounces" pre-flight
check.

## E10 — UI feasibility

**Procedure.**

- `getInputDialog` with an `apply=` callback that generates a rig. Does the scene update while
  the dialog stays open? Is the real-time view interactive?
- `getBrowserDialog`: presence, how data is passed both ways (`init`, `lux.yieldResult`),
  whether it is modal, and whether repeated yields are possible.
- Long operations: progress feedback and cancellation.

**Pass.** One of the dialogs supports a **generate → inspect → tweak → regenerate** loop
without restarting the script.

## E11 — Mesh export for optional analysis (Phase 4 gate)

**Procedure.**

- `exportFile(tmp.obj, lux.EXPORT_OBJ)` on scenes of 0.5M, 2M and 8M triangles. Measure the
  time, the file size, whether hidden nodes are included, and whether object names map back to
  scene nodes.
- Parse the file outside KeyShot. Try facet-normal clustering on the hero stone to recover the
  table normal and the cut family.

**Gate.** Proceed only if the doc 05 experiment shows a measurable placement benefit over the
bounding-box heuristic.

## E12 — Offline installation

**Procedure.**

- On clean Windows and macOS VMs with networking disabled, install the package (copied into
  the Scripts folder, or via an installer).
- Run all features.
- Repeat under a standard (non-admin) user account, and with common antivirus software.
- Verify there are no imports outside the standard library and no use of KeyShot's
  "local Python" preference.

**Pass.** Full function offline; the install and uninstall leave no stray files except the
documented library folder from E2 route (b).

## E13 — Re-identification stability

**Procedure.** Generate a rig, then:

- save, close and reopen;
- rename a light in the scene tree;
- duplicate a light;
- move a light into another group;
- reimport the jewelry with "update geometry" (`import_type=1`).

After each, check what `getID()`, node names and material names look like.

**Pass.** A documented identification strategy (ID → name prefix → material name →
transform-plus-size fingerprint) recovers ≥ 99% of lights across these events in tests.

## E14 — Units and scale invariance

**Procedure.**

- Apply the same preset (angular and Lux specification) to the same ring at scale ×0.5, ×1
  and ×2, and with the scene unit set to mm, cm and m. Use a copy of the scene, because
  `setSceneUnit` changes the scene.
- Compare renders with depth of field disabled.
- Repeat in Lumen mode.

**Pass.** The images match within the metric noise floor in Lux mode, which proves the
scale-invariance principle in KeyShot. A difference in Lumen mode is expected and confirms
the unit semantics.

---

## Non-technical unknowns (resolve in parallel)

| ID | Unknown | How to resolve |
|---|---|---|
| U1 | Which 2026 editions (Professional / Business / Enterprise) include scripting, the HDRI Editor and headless mode | Ask Luxion sales or partner support in writing |
| U2 | Whether the EULA allows selling third-party scripts and installing materials into the user library | Legal review; ask Luxion about partner programmes |
| U3 | How long an expert's lighting setup actually takes today, with their own templates | Time-and-motion study (doc 12) |
| U4 | Whether customers value "auto" more than "consistent across a catalogue" | 8–12 customer interviews (Action 9) |
| U5 | Whether Lightmap's HDR Light Studio still supports current KeyShot | Lightmap's compatibility chart or support |

## Spike exit criteria (Go / No-Go)

**Go to Phase 2 if all of the following hold:**

- E0 shows the MVP path functions present;
- E1 **and** E2 pass in at least one route;
- E3 passes;
- E6 and E7 show that a full, trace-free removal is possible (or that the known residue is
  acceptable and disclosed);
- U1 confirms scripting is available in the edition(s) the target customers own.

**Pivot** (see doc 14) if E1 or E2 fails in every route, or if U1 shows scripting is limited
to an edition few jewelry studios own.
