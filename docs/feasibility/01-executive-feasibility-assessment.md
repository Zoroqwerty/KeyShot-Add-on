# 1. Executive Feasibility Assessment

## Verdict

**Conditionally feasible. Proceed only to a 2–3 week technical spike, not to product
development.**

The product rests on four claims. Their status is:

| Claim | Status | Confidence |
|---|---|---|
| A script can create editable physical KeyShot lights | **Plausible, unproven.** KeyShot has no documented "create light" or "create primitive" call. There is a credible workaround: import generated plane geometry, then apply a light material. | Medium |
| A script can understand enough of a jewelry scene to place lights well | **Partly.** Hierarchy, names, materials, world bounding boxes and the camera are documented as readable. Mesh data (vertices, normals, facets) is **not** exposed. | Medium-high for coarse analysis; low for facet-level analysis |
| Rule-based, camera-relative rigs can produce a professional *starting point* | **Plausible.** This follows from jewelry optics and studio practice, but has not been shown on real models. | Medium |
| The tool removes about 90% of an artist's lighting work | **Unknown. It is a hypothesis, not a result.** Doc [12](12-testing-and-benchmarking.md) defines how to measure it. | None yet |

**The commercial risk is larger than the technical risk.** Since 2025 KeyShot itself ships
several things that overlap with this product:

- a **Light Positioning tool** with a "Highlight" mode (click a point and the light moves to
  put a reflection there);
- **Planar lights** (softboxes with barndoors) and **Light Layers** (limit which parts a light
  affects);
- built-in **Lighting Presets**, including one called **Jewelry**;
- the long-standing **HDRI Editor with pins**;
- **AI Shots**, a generative restyle feature.

Cheap template scenes and HDRI kits also already exist. The product must therefore win on
things those tools do not do:

1. **Automatic, scale-invariant, camera-relative rigs**, generated in seconds.
2. **Consistency across a catalogue** of many similar pieces.
3. **Jewelry-specific diagnostics** of a render: stone contrast, highlight clipping, metal
   readability.
4. **Regeneration that never overwrites the artist's edits.**

Each of these must be proven by benchmark, not asserted.

## What is technically solid, per the documentation

- **Lights are ordinary scene objects.** In KeyShot a physical light is a *material applied to
  geometry* [E1]. Generated lights are therefore normal scene-tree parts. Artists can select,
  move (Move tool, Light Positioning tool), resize and re-parameterize them with the tools
  they already use, which fully meets the editability requirement.
- **Node control.** Scene nodes can be found, renamed, transformed with 4×4 matrices,
  hidden, locked, duplicated, deleted and assigned materials [E1, as of 2023.2].
- **Material inspection and editing.** Shader type and parameters can be read and written
  through the Material Graph API (since KeyShot 11) [E1]. This allows gem and metal materials
  to be identified (`lux_gem`, `lux_metal`, …) and light parameters to be set. The *names* of
  the light parameters are not documented [E3].
- **Camera.** The active camera's position, look-at, up vector, field of view and lens can be
  read and set. Cameras can be listed and switched [E1].
- **Rendering.** Rendering to file (PNG/EXR/TIFF) with time or sample limits, region
  rendering and many passes (clown, normals, depth, reflection, refraction, …) is
  documented [E1]. Cryptomatte was added in 2025.3 [E1].
- **User interface.** Native multi-field dialogs (`getInputDialog`, which can stay open with
  an Apply callback) and an HTML/JS dialog (`getBrowserDialog`) are documented [E1, 2023.2].
- **Offline operation.** Scripts run in KeyShot's embedded Python, so no network is needed for
  scripting [E2].

## What is missing or unproven, and could block the product

| # | Gap | Why it matters | Workaround | Evidence |
|---|---|---|---|---|
| G1 | No documented API to **create geometry** (a plane for an area light) | There is nothing to attach a light to | Write a small OBJ file and import it with `lux.importFile` and safe import options; or duplicate a template node | [E2]/[E3] |
| G2 | No documented API to **create a light material** directly | There is no light without one | (a) Ship a `.kmp` package of light materials, load it with `lux.importMaterials`, apply it by name. (b) Rebuild a scene material's graph with `newNode(SHADER_TYPE_MESH_LIGHT)` | [E3] |
| G3 | **Light-shader parameter names** (power, units, colour, visibility flags) are not documented | Intensity and colour cannot be set reliably | Enumerate them with `ShaderNode.getParameters()` in each target version | [E3] |
| G4 | **No mesh access** (vertices, normals, facets) | Cut type, table orientation, pavé layout and occlusion cannot be read directly | Bounding-box and material heuristics, user tagging, and optionally `lux.exportFile` to OBJ/STL followed by offline parsing | [E4] → [E2] |
| G5 | **No transactional undo** (only `setUndoEnabled`) | One "Generate" may leave many undo steps, or none | The tool keeps its own journal and offers "Remove rig" / "Revert" | [E4] |
| G6 | **HDRI Editor pins, Light Layers and the Light Positioning tool have no documented scripting API** | The most common KeyShot jewelry workflow (HDRI and pins) cannot be automated directly | Use geometric area lights; optionally generate an HDR image (deferred) | [E4] |
| G7 | **Edition and licensing**: scripting was a *Pro* feature up to KeyShot 11 (and in the 2024 headless docs). The 2026 editions are Professional, Business and Enterprise. KeyShot's pricing page says all Studio features are in every plan, which suggests scripting is in all three, but no source says so explicitly. | The addressable market depends on which editions run scripts; older non-Pro perpetual licences cannot | Confirm with Luxion | [E2] |
| G8 | **API drift** between versions; Python moved from 3.10 (KS 11, manual) to 3.11 (2023.x, per the transcribed docs) to 3.12 (KS 2024, manual) | Version support costs | Probe capabilities at runtime; publish a tested-version matrix | [E1] for KS 11 / 2024, [E3] impact |

**Kill criterion.** If neither G1 nor G2 can be solved without visible side effects on the
user's scene (camera moved, environment refit, materials renamed, unit rescale), the "native
editable lights" premise fails. The fallback options are listed in
[14](14-final-recommendation.md).

## Physics constraints that limit what any lighting tool can do

- **Gem appearance is decided mainly by geometry, material and render settings, not by
  lights.** Wrong IOR, missing dispersion, open or inverted gem meshes, poor cut proportions
  in CAD stone libraries, and too few ray bounces all produce dark or glassy stones that no
  light rig can repair. The tool must *detect and report* these problems rather than try to
  "light around" them (see [04](04-jewelry-optics.md) and [09](09-failure-mode-analysis.md)).
- **Brightness is not brilliance.** GIA's cut-grading research replaced "brilliance" with
  *brightness*, and grades it together with *fire* and *scintillation*, where scintillation
  includes the contrast pattern. Pushing brightness up washes out contrast and fire.
- **Mirror-like metal and diamond facets show you the light sources themselves.** In
  reflection, a highlight's brightness depends on the source's *radiance* and its size on the
  source's *angular size*, not on its distance. That means presets can be written in angular
  and radiance terms and scale to any piece size. This is the central design idea of the
  engine ([06](06-lighting-engine-architecture.md)).
- **Lighting depends on the camera.** A rig tuned for a face-up view will usually be weaker
  from a profile view. Multi-view robustness is a trade-off to manage, not a bug to fix.

## Recommended architecture

- A **deterministic, rule-based rig generator** working in camera-relative angular
  coordinates, driven by scale-invariant presets.
- **Coarse scene analysis**: hierarchy, names, materials, bounding boxes and the camera, with
  **manual tagging as the guaranteed fallback**.
- A thin **KeyShot adapter**, the only module that touches `lux`, with runtime capability
  probing.
- A **state store** that keeps generated parameters, artist overrides and the evaluated rig
  separate.
- **Image-based evaluation added in stages**: first as a diagnostic "lint" report, then as a
  bounded optimizer with a small budget.
- **No machine learning in the first versions.** There is no training data, no differentiable
  renderer, and no evidence that ML beats rules here.

**Ten presets:** build the engine around **five archetypes** and express the ten requested
presets as parameter profiles of those archetypes ([07](07-preset-specifications.md),
[11](11-mvp-scope.md)). Validate three archetypes with artists before writing the other
seven profiles.

## Effort (assumptions in [13](13-development-roadmap.md))

| Scope | Person-weeks | Calendar (1 senior developer plus a part-time jewelry artist) |
|---|---|---|
| Spike | 2–3 | 3–4 weeks |
| MVP without automatic optimization | about 20–30 | about 5–9 months |
| MVP with bounded optimization and production hardening | about 24–37 (+2 optional) | about 7–11 months |

These are planning estimates with stated assumptions, not commitments.
