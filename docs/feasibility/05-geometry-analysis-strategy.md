# 5. Geometry-Analysis Strategy

## 5.1 Goal and non-goals

**Goal.** Produce a `SceneModel` (schema in [06](06-lighting-engine-architecture.md)) that
lets the rig generator answer four questions:

- Where is the piece, and how big is it?
- Where is the hero stone (if any), and roughly which way does it face?
- Where are the secondary stones and pavé clusters?
- Where is the metal, and what kind is it?

Every answer carries a **confidence and a reason**, and **the user can override everything**.

**Non-goals for the MVP.** Facet-level reconstruction, automatic cut classification, automatic
defect repair, and any modification of the user's geometry or materials.

## 5.2 What the API gives us (from [02](02-keyshot-api-capability-matrix.md))

| Available [E1] | Not available [E4] |
|---|---|
| Scene tree (groups, objects, model sets), node names and paths | Vertices, normals, triangles, UVs |
| World and local axis-aligned bounding boxes and centres | Oriented bounding boxes, curvature, thickness |
| Node transforms (world and local) | Ray casting or occlusion queries |
| Material per node; shader type and parameters via the Material Graph | Per-face materials inside one object |
| Selection state (what the user selected in KeyShot) | Picking a 3D point on the surface |
| Scene units; triangle and object counts (scene-wide) | Per-object triangle count (not documented) |
| CAD metadata per node (`getMetadata`, 2026.1+) | — |
| Camera(s) | — |

**Optional offline path [E2/E3]:** `lux.exportFile` to OBJ/STL/glTF, then parse the file
outside KeyShot to get mesh data. This is gated by E11 and by the measured benefit (§5.9).

## 5.3 Pipeline (tiers, cheapest first)

```
T0  Scope          → which nodes are "the jewelry"         (user selection, default)
T1  Material pass  → stone / metal / other per object      (shader type + params)
T2  Name pass      → role hints from names/paths/metadata  (keyword dictionaries)
T3  Spatial pass   → hero stone, pavé clusters, band/head, (bounding-box relations)
                     jewelry type, up/table direction
T4  Confirm & tag  → user reviews, fixes, and tags         (UI; always available)
T5  Mesh pass      → (optional, Phase 4, gated)            (export + offline parse)
```

Each tier writes *evidence*, not final verdicts. A small rule-based combiner (§5.6) produces
roles with confidence. Ask the user only when confidence is low or when roles conflict.

### T0 — Scope

- **Default.** The nodes the user selected before launching (`root.getSelected()`).
- **If nothing is selected.** Offer "all visible objects", but exclude:
  - our own `JLE_` nodes;
  - cameras;
  - any node the user marked as "ignore" (props, ground plane, ring box, display stand).
- **Hidden** nodes (`isHidden`) are excluded by default.
- **Why selection-first.** Scenes often contain display props, multiple variants, or
  several pieces. Guessing scope is the most dangerous kind of misidentification.

### T1 — Material pass (strongest automatic signal)

For each object, get the material name → Material Graph → root shader type → key
parameters:

| Shader type (constant) | Class | Extra evidence |
|---|---|---|
| `lux_gem` | **stone** (high confidence) | IOR, Abbe, colour → species hint (diamond-like if IOR ≈ 2.4 and colourless) |
| `lux_glass_simple`, `lux_glass` (dielectric), `lux_liquid` | stone *candidate* (medium) | IOR > 1.7 raises confidence. Glass used as stone → flag "consider Gem material". |
| `lux_metal`, `lux_anisotropic`, `lux_brushed2`, `lux_brushed_solid` | **metal** | Colour → alloy (§5.5). Roughness → finish. |
| `lux_advanced`, `lux_generic`, `lux_general` | ambiguous | Metallic-like parameters → metal candidate. Transmission → stone candidate. |
| Multi-material / complex graph | resolve active sub-material | Walk the graph via `getMaterialNodes()` |
| Light materials | **exclude** (existing user lights) | Recorded as "existing lights" (see [06](06-lighting-engine-architecture.md) §6.9) |
| Others (plastic, diffuse, …) | **other** | Often an unassigned default material → "material missing" |

### T2 — Name pass

- Keyword dictionaries cover role and material words: diamond, stone, gem, brilliant,
  centre/center, main, side, accent, melee, pavé/pave, halo, prong, claw, head, basket,
  gallery, shank, band, bail, chain, link, clasp, bezel, setting, gold, platinum, silver,
  rose, yellow, white…
- Matching is case-insensitive and tolerant of accents. A short list of common non-English
  equivalents is included (DE, FR, IT, ES at first; extend from field data).
- **Non-informative name detection.** Names like `Object 123`, `Brep`, `Mesh`, `Layer 01`,
  `Default`, `Body1`, or pure numbers give no evidence, and their weight drops to zero.
- **CAD metadata (2026.1+).** If `getMetadata()` returns layer or attribute fields, run the
  same dictionaries over them. The content depends on the source CAD and must be sampled
  from real files (Rhino, MatrixGold, RhinoGold, JewelCAD) before any rule is written.

### T3 — Spatial pass (bounding boxes)

Let *S* be the jewelry's bounding-sphere radius (half the world bounding-box diagonal). All
thresholds are **relative to S or to stone sizes**, never absolute, except for the
plausibility check.

1. **Scale plausibility.** Compare bounding-box dimensions with plausible jewelry sizes:
   rings about 15–35 mm, pendants and earrings about 5–60 mm, bracelets about 50–80 mm,
   necklaces about 100–600 mm. A model that is 1000× off triggers a warning (likely a unit
   error). **Never auto-rescale.**
2. **Hero stone.** Take the stone with the largest bounding-box volume. If the top two are
   within 20% of each other, it is *ambiguous*: suggest the multi-stone preset or ask the
   user. The threshold is an initial guess, to be calibrated.
3. **Secondary stones vs pavé.** Stones under about 0.3 × the hero's size are "small". If there
   are 8 or more small stones with similar sizes (size coefficient of variation < 0.3), group
   them into **pavé clusters** by single-linkage on centre distance, with a threshold of about
   2.5 × the median small-stone size. Other stones are "secondary". All thresholds are initial
   values for calibration.
4. **Metal roles.** The metal object whose bounding box contains or is nearest to the hero
   centre is the **head/setting**. The largest remaining metal object is the **band/shank**
   (rings) or the **body**.
5. **Jewelry type.** Sort the overall bounding-box extents d1 ≥ d2 ≥ d3 and combine them with
   the plausibility ranges and part statistics:
   - **ring:** the band has d1 ≈ d2 > d3, and stones sit at one end of an axis;
   - **pendant:** d3 ≪ d2, and there is a bail-like small metal part at the top;
   - **earring pair:** two similar clusters separated along one axis;
   - **bracelet:** d1 ≈ d2 at 50–80 mm;
   - **necklace / chain:** a large extent with many repeated small metal parts.

   Always show the guessed type to the user as a one-click confirmation.
6. **Ring frame and stone "up" (table-normal heuristic).**
   - For rings, take the band's smallest extent axis as the **finger axis** *a*.
   - Up direction: `u = normalize(c_hero − c_band)`, projected perpendicular to *a*.
   - For a solitaire, *u* is a usable estimate of the **table normal**.
   - Confidence is reduced for east-west, bypass, toi-et-moi, eternity and cluster designs, and
     whenever the stones are spread symmetrically.
7. **Oriented boxes when available.** Where a stone object carries its own rotation (block
   instances, gem objects exported with local frames), use `getBoundingBox(world=False)` and
   `getTransform(world=True)` to get an oriented box. The thinnest local axis gives a strong
   table-normal estimate. *Whether CAD exports preserve this is [E3]; sample real files.*
8. **Duplicate and overlap warnings.** Two stone objects with near-identical bounding boxes
   (centre distance < 2% of stone size, size ratio 0.98–1.02) are likely duplicates. This
   produces muddy stones, so warn.

### T4 — Confirm and tag (always available)

- **Summary screen.** Shows the detected jewelry type, the hero stone, counts of secondary
  stones and pavé clusters, the metal alloy guess, and warnings. Each item shows a confidence
  icon and its reason, e.g. "material `Diamond 01` is a Gem shader (IOR 2.42)".
- **Tagging workflow.** Without a picking API, tagging uses KeyShot's own selection:
  1. The user selects parts in the scene tree or the viewport.
  2. In the tool dialog they press **"Tag selection as …"** with one of: Hero stone /
     Secondary stones / Pavé / Metal: band / Metal: head / Metal: other / Ignore.
  3. The tool re-reads the selection (`getSelected`).

  This works with `getInputDialog`'s Apply callback, if E10 confirms it.
- **Merged-mesh fallback.** If stones and metal are one object, stone-targeted modules switch
  to "jewelry-level" targets. The user can still give the **stone direction**: "stone faces
  camera / up / custom", where custom means "use the current camera direction". The tool
  warns that gem-specific quality is limited by the model.
- **Cut family.** A dropdown (Round / Oval / Pear / Marquise / Princess / Emerald-Asscher /
  Cushion / Other). Default Round, or remembered from the last tag.

## 5.4 Role taxonomy

`hero_stone`, `secondary_stone`, `pave_cluster` (a group of stones), `metal_band`,
`metal_head`, `metal_other`, `chain_links`, `detail_region`, `other_in_scope`, `ignored`,
`existing_light`.

Prongs are usually part of the head object. **Prongs are not a separate role in the MVP**,
because without mesh access we cannot locate them reliably.

## 5.5 Metal alloy and finish from material data

- Convert the metal base colour (from the `lux_metal` colour parameter, or its preset name)
  to CIELAB and LCh.
- Classify:
  - **white metals:** chroma below a threshold;
  - **yellow gold:** hue in a yellow band;
  - **rose gold:** a redder hue band.
- Calibrate the bands on KeyShot's own library metals per version, and on customer
  materials. The thresholds are **not** assumed here.
- Material-name keywords (e.g. "18k yellow", "rose", "platinum", "rhodium") override colour
  when present.
- **Finish:** roughness parameter → polished / satin. Brushed shaders → brushed.

## 5.6 Combining evidence

Use a transparent scoring combiner, not ML:

1. Each piece of evidence adds a signed weight to each candidate role.
2. Material evidence is weighted above spatial evidence, which is weighted above name
   evidence.
3. Normalize the scores to a confidence value in [0, 1].
4. A role is accepted automatically at confidence ≥ 0.8 (initial). Between 0.5 and 0.8 it is
   proposed and highlighted for review. Below 0.5 it is left unassigned and the user is asked.
5. Every decision stores its evidence list, so the UI can say *why*.

The weights are hand-set, then tuned on the labelled benchmark (doc 12). This is the
cheapest form of "learning", it remains inspectable, and it does not need a training
pipeline.

## 5.7 Storing assignments for reuse

- **Per scene:** the sidecar JSON (doc 06 §6.8) holds role tags keyed by a **component
  fingerprint**, not by node ID alone, because IDs may change (E13).
- **Fingerprint** = (scene-tree path names, object name, material name at tagging time, world
  bounding-box size rounded to 1% of S, centre in jewelry-normalized coordinates).
  Matching uses the best weighted agreement, so renames or material swaps alone do not break
  it.
- **Per model across scenes ("model memory"):** a user-level store keyed by the imported
  source file name plus a geometry signature (sorted part bounding-box sizes). It reuses tags
  when the same CAD model is re-imported or used in colour variants. This is very valuable for
  catalogue work. It is opt-in, and the store is local and offline.

## 5.8 Possible through the API vs needs extra geometry processing

| Analysis | Supported API | Extra processing (mesh export) |
|---|---|---|
| Scope, roles from materials and names | ✔ | — |
| Hero stone and sizes (separate parts) | ✔ | — |
| Pavé clusters (separate parts) | ✔ | — |
| Jewelry type (coarse) | ✔ | Better with hole and topology detection |
| Table normal | ◐ heuristic; ✔ if local frames exist | ✔ facet-normal clustering (largest planar facet) |
| Cut family | ✘ | ✔ facet count, symmetry, outline shape |
| Stones inside merged meshes | ✘ | ✔ connected components plus planarity |
| Prong locations and occlusion | ✘ | ✔ but costly (needs proximity queries) |
| Metal surface normals for highlight targeting | ◐ analytic proxies (doc 06) | ✔ sampled normals |
| Mesh defects (normals, holes, duplicates) | ◐ duplicates only | ✔ |

## 5.9 Avoiding expensive analysis without proven benefit

Mesh export plus parsing (T5) costs export time for large pavé scenes (E11 measures it),
disk I/O and code complexity. **It is built only if a controlled experiment shows benefit.**

1. **Experiment.** On the benchmark (doc 12), generate rigs using:
   - (a) the T3 heuristic table normal and a user-chosen cut;
   - (b) the ground-truth table normal and cut, from the benchmark labels.
2. **Compare** stone metrics (doc 08) and run a blind pairwise preference test.
3. **Decision.** If (b) does not beat (a) by more than the metric noise floor, *and* raters show
   no significant preference, do not build T5.

The same rule applies to prong-occlusion modelling. In the MVP, occlusion is handled
statistically: several sparkle sources at different azimuths ensure that no single blocked
direction blacks out the stone.
