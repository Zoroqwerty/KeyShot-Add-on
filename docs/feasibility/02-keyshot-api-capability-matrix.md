# 2. Verified KeyShot API Capability Matrix

Evidence labels ([E1]–[E4]) and source caveats are defined in [README.md](README.md).

Notation:

- "2023.2 doc" means the official `help(lux)` docstrings for KeyShot 2023.2, read from a
  verbatim third-party transcription.
- "2024.1 ref", "2025.3 ref" and "2026.1 ref" mean search extracts of the official reference
  pages at `media.keyshot.com/scripting/...`.
- Spike IDs (E0–E14) refer to [03](03-critical-unknowns-and-experiments.md).

**Target version.** The research baseline is KeyShot 2023.2. The proposed MVP target is
KeyShot Studio **2025.3 and 2026.2**: the current release plus the last release of the
previous year. This is to be confirmed with customers (Action 1 in
[14](14-final-recommendation.md)). **Every row must be re-verified in the target version by
E0.**

---

## A. Script execution and extension mechanisms

| Operation | Mechanism | Evidence | Notes / risks | Spike |
|---|---|---|---|---|
| Run Python in the GUI | Scripting Console; scripts in the Scripts library folder (`lux.getKeyShotFolder(lux.FOLDER_SCRIPTS)`) | [E1] KS 11 manual, 2024 manual, 2023.2 doc | Documented ways to use scripting: live console, script library, command line | E0 |
| Python version | 3.8 (KS 10), 3.10 (KS 11), 3.11 (2023.x transcription header), 3.12 (KS 2024) | [E1] | 2025/2026 version not confirmed → [E3]. Affects any compiled dependency. | E0 |
| Headless (command-line) scripting | `keyshot -headless -script …` | [E1] 2024 manual | Docs: "Pro feature, KeyShot 9.3 or newer"; FlexLM features `keyshot2` (Pro), `keyshot_enterprise`, `keyshot_network_rendering`. GUI-only calls (dialogs, `screenshot`) are absent from the headless API. | — |
| Dockable panel / native plugin UI from Python | None documented | [E4] | The MVP must work with modal or "Apply"-style dialogs | E10 |
| C++ plugin SDK for in-app tools | No public SDK found for this purpose (`FOLDER_EXTERNAL_PLUGIN` exists, purpose undocumented) | [E4] | Do not plan on it | — |
| Use third-party Python packages | KeyShot can detect a locally installed Python of the *same* version and its modules (General Preferences toggle) | [E1] manual (old version text) + forum | Fragile for offline install → **design stdlib-only** | E12 |

## B. Creation of new scene geometry

| Operation | Mechanism | Evidence | Notes / risks | Spike |
|---|---|---|---|---|
| Create a primitive (plane, disc, sphere) | GUI: *Edit › Add Geometry*. **No `lux` function documented** (2023.2 doc; none surfaced in 2024–2026 extracts). | [E4] | The central gap | E0 |
| Import generated geometry | `lux.importFile(path, showOpts=False, dontAsk=True, opts=dict)`. Import options include `import_type` (0 = add to scene), `center_geometry`, `snap_to_ground`, `adjust_camera_look_at`, `adjust_environment`, `geometry_units`, `up_vector`, `separate_parts`, `merge_objects`, `merge_groups`, `model_set_import_to`, `retain_materials` | [E1] 2023.2 doc + official scripting example | Using this to create *light hosts* is [E2]. Side effects (new model set or group, unit conversion, material creation from MTL, camera or environment refit) → **[E3]** | **E1** |
| Duplicate an existing node | `SceneNode.duplicate(amount, linkMats)` | [E1] | Needs a template node to exist first (created via E1, or shipped in a template file) | E1 |
| Create a group to hold the rig | No group-creation call; `moveToGroup(group)` moves into an *existing* group | [E1]/[E4] | Workaround: one OBJ with N named objects → importer creates the group → [E3] | E1 |
| Load geometry plus lights from a template scene into the current scene | `importFile` / `openFile` / `openPackage` | [E3] | Whether `.bip`/`.ksp` *imports* (adds to scene) rather than *opens* (replaces the scene) is undocumented. `openFile` would replace the user's scene — **must not be used** on a working scene. | E1 |

## C. Creation of physical light sources

| Operation | Mechanism | Evidence | Notes / risks | Spike |
|---|---|---|---|---|
| What a light *is* | A material applied to geometry. Types: Area Light (Diffuse), Point Light, IES, Spotlight, Emissive; **Planar Light** since 2025.1 | [E1] manuals 2024/2025 | Point lights replace the host part's geometry with a point at its centre. KeyShot support recommends hosting lights on separate primitives, never on product parts. | — |
| Shader type constants | `SHADER_TYPE_MESH_LIGHT='lux_mesh_light'`, `SHADER_TYPE_POINT_LIGHT='lux_point_light'`, `SHADER_TYPE_SPOTLIGHT='lux_spotlight'`, `SHADER_TYPE_IES_LIGHT='lux_ies_light'`, `SHADER_TYPE_EMISSIVE='lux_emissive'` | [E1] 2023.2 doc; `SHADER_TYPE_MESH_LIGHT` also in 2024.1 ref | That `lux_mesh_light` is the UI's "Area Light" is an inference → check with `ShaderNode.getType()` (returns the human name). **No planar-light constant was found** → [E4] | E0, E2 |
| Create a light material: route (a) | `lux.createSceneMaterial(name)` creates a *diffuse* material → `getMaterialGraph(name)` → `newNode(SHADER_TYPE_MESH_LIGHT)` → wire it as the material's surface | [E3] | `MaterialGraph` has `getRoot`, `newNode`, `newEdge`, `removeNode`, but **no `setRoot`**. Whether the root shader can be replaced is unknown. | **E2** |
| Create a light material: route (b) | Ship `JLE_Lights.kmp` → `lux.importMaterials(file, folder)` into the material library → `node.setMaterial("<library name>", link=False)` | [E2] | `setMaterial` by library name is shown in the official example (`node.setMaterial("Matte White")`). `importMaterials` **writes into the user's material library**; disclose this and clean it up on uninstall. | **E2** |
| Create a light material: route (c) | Apply one of KeyShot's bundled light materials by name | [E3] | Names vary by version and locale → fallback only | E2 |

## D. Assignment of light-source materials

| Operation | Mechanism | Evidence | Notes / risks | Spike |
|---|---|---|---|---|
| Apply a material to a node | `SceneNode.setMaterial(mat, link=False)`; `lux.setObjectMaterial(mat, obj, link)`; `lux.applyMaterialMapping(dict, link)` | [E1] | With `link=False` a duplicate is created. The duplicate's name is auto-generated → read it back with `node.getMaterial()` [E3]. A per-light unique material is required so each light can be edited independently. | E2 |
| Rename a material | Not documented in 2023.2 (`ShaderNode.setName` names a *node*, not the material) | [E4] | Identify lights by node name plus the stored material name instead | E2 |

## E. Light position and orientation

| Operation | Mechanism | Evidence | Notes / risks | Spike |
|---|---|---|---|---|
| Transform a node | `SceneNode.applyTransform(luxmath.Matrix, absolute=False)` | [E1] | "absolute=True" only for *object* nodes. The doc example shows absolute *translation*. Whether absolute replaces rotation and scale too → [E3] | **E3** |
| Build matrices | `luxmath.Matrix.makeIdentity/makeRotate/makeScale/makeTranslate`, `.rotateAroundAxis(axis, deg)`, `.setTransformation(scale, rotate, trans)`, `.getTransformation()`, `.invert()`, `.mul()`; `luxmath.Vector` with `cross`, `dot`, `normalize` | [E1] 2023.2 doc | `Matrix.dump()` shows translation in the 4th **row** (row-vector convention). Euler order of `rotate(vec)` is undocumented → [E3]. Prefer `rotateAroundAxis` or explicit basis matrices. | E3 |
| Read back a transform | `SceneNode.getTransform(world=…)`, `getCenter(world)`, `getBoundingBox(world)` | [E1] | Needed to detect artist edits | E3 |
| Aim / look-at helper for lights | None in the API; GUI has the Light Positioning tool (2025.1) | [E4] for scripting | Compute orientation ourselves | — |

## F. Light size, intensity, colour and other parameters

| Operation | Mechanism | Evidence | Notes / risks | Spike |
|---|---|---|---|---|
| Size | Scale the host geometry (`applyTransform`) | [E1] mechanism | For area lights, size changes intensity semantics: **Lumen** keeps total flux constant; **Lux** keeps emittance per m² constant, so a bigger light emits more (manual 2024/2025). Prefer Lux for reflection-driven lights (see doc 06). | E3 |
| Power, units, colour | `getMaterialGraph(m).getRoot().getParameters()`, then `ShaderParameter.setValue()`. Colour accepts an RGB tuple in [0,1] or a colour name. | [E1] mechanism; **parameter names [E3]** | Units (Watt/Lumen/Lux) are a UI option; whether the unit is a scriptable parameter → [E3]. `ColorParameter.setKelvin` exists for *scene colours* (2500–9500 K); for light materials, convert Kelvin to RGB ourselves. | **E2** |
| Visibility flags | UI: Visible to Camera, Visible in Reflections, Visible in Shadows, front/back emission (area light) | [E1] manual (UI). Scriptability [E3]. | A community report says area lights stayed visible in reflections or refractions on GPU even with the flag off → test CPU vs GPU | E2, E8 |
| Planar light barndoors | UI (2025.1) | [E1] UI; scripting [E4] | Not required for the MVP | E2 |
| Light Layers (light linking) | UI (2025.2), maximum 5 layers | [E1] UI; scripting [E4] | Would allow "stone-only" and "metal-only" lights. Defer. | E0 |

## G. Scene geometry, hierarchy, transforms and bounds

| Operation | Mechanism | Evidence | Notes / risks | Spike |
|---|---|---|---|---|
| Traverse the tree | `lux.getSceneTree()`, `SceneNode.getChildren/getParent/getPath/find(name, mat, types, depth)`, `getKind`, `isGroup/isObject/isModelSet/isCamera`, `lux.dumpTree()` (JSON) | [E1] 2023.2; `getSceneTree` in 2026.1 ref | Good basis for analysis | E0 |
| Bounds and centres | `getBoundingBox(world=True)` → (min, max), `getCenter(world=True)` | [E1] | Axis-aligned in world or local space. No oriented bounding boxes. | E3 |
| Selection | `isSelected`, `getSelected` (recursive), `select/deselect` | [E1] | Lets the user select the jewelry in KeyShot before running the tool | E10 |
| Scene statistics and units | `lux.getSceneInfo()` (unit/meter scale, triangle, object and nurbs counts, sizes); `setSceneUnit` | [E1] | Read-only use. **Never change units.** | E0 |
| Node and CAD metadata | `SceneNode.getMetadata()` (new in 2026.1, CAD metadata as a dict); `lux.getMetaData()` (scene XMP, read) | [E1] 2026.1 ref / blog | Useful when CAD exports carry layer or attribute tags. Content varies by source CAD → [E3] | E0 |
| **Mesh data** (vertices, normals, triangles, facets) | **None** | **[E4]** | Workaround: `lux.exportFile(path, lux.EXPORT_OBJ / STL / GLTF / USD)` exports the *scene*, then parse it outside KeyShot. Selection-only export is not documented → [E3]. | E11 |

## H. Identification and inspection of assigned materials

| Operation | Mechanism | Evidence | Notes / risks | Spike |
|---|---|---|---|---|
| Material of a node or object | `SceneNode.getMaterial()`, `lux.getObjectMaterial(id)`, `lux.getMaterialMapping()`, `lux.getSceneMaterials()` | [E1] | — | E0 |
| Material type | `getMaterialGraph(name).getRoot().getType()` → e.g. `lux_gem`, `lux_metal`, `lux_glass`, `lux_glass_simple`, `lux_dielectric`… | [E1] mechanism; constants in 2023.2 doc | Multi-materials and complex graphs (mix nodes, textures) need graph walking | E2 |
| Gem and metal parameters (IOR, Abbe/dispersion, colour, roughness) | `ShaderNode.getParameters()` / `getParameter(name).getValue()` | [E1] mechanism; names [E3] | Material-graph node IDs change when the file is edited (forum) → always look nodes up by type or name | E2 |

## I. Camera access

| Operation | Mechanism | Evidence | Notes / risks | Spike |
|---|---|---|---|---|
| Read the active camera | `getCamera`, `getCameraPosition/LookAt/Up/Direction/Distance/FieldOfView/FocalLength/Lens`, `getSphericalCamera` | [E1] | `getCameraLens` gives the lens type (perspective, orthographic, shift, panorama) | E3 |
| List and switch cameras | `getCameras`, `setCamera(name)`, `newCamera`, `saveCamera`, `removeCamera`, `isCameraUnsaved` | [E1] | Switching for multi-view evaluation must restore the original camera **and** must not save an unsaved camera without consent | E7 |
| Camera nodes in the tree | `NODE_TYPE_CAMERA` | [E1] | — | — |

## J. Lighting and render settings

| Operation | Mechanism | Evidence | Notes / risks | Spike |
|---|---|---|---|---|
| Lighting presets (render-quality presets, including **"Jewelry"**) | `lux.getLightingPreset()`, `getLightingPresets()`, `setLightingPreset(name)` | [E1] 2023.2; 2025.3 ref | The Jewelry preset = Interior preset + ground illumination + more ray bounces + caustics (manual). This is a *scene-wide* change → snapshot and restore. | E7 |
| Environment | `getActiveEnvironment()` → `Env.get/setBrightness, Rotation, Size, Height, LightingEnvironment(path), BackgroundColor, Backplate, GroundShadows, GroundReflections, FlattenGround`; `newEnvironment(name, activate, clone)`, `setActiveEnvironment`, `removeEnvironment` | [E1] | **Non-destructive pattern:** clone into a new environment rather than editing the user's | E7 |
| HDRI Editor pins | None in the API | **[E4]** | Pins are stored in the scene (manual) but cannot be scripted | — |
| Render options | `getRenderOptions()` → `RenderOptions.setMaxTimeRendering / setMaxSamplesRendering / setAdvancedRendering / setRayBounces / setCausticsQuality / setGlobalIllumination / setRegion / setThreads / setOutput*Pass …`; `setRenderEngine(PRODUCT / INTERIOR / *_GPU)` | [E1] | Passing an `opts` object to `renderImage` is expected not to change the scene's stored settings → [E3] | E4 |
| Image style (exposure, tone) | `getActiveImageStyle()` (kind, bloom, denoise, curve, vignette…) | [E1] | No exposure value in 2023.2's `ImageStyle` → [E4]. Matters for calibrating intensities. | E0 |

## K. Preview rendering and image data

| Operation | Mechanism | Evidence | Notes / risks | Spike |
|---|---|---|---|---|
| Render a preview | `lux.renderImage(path, width, height, opts, format)` | [E1] | The GUI shows a render output window; whether the call blocks and how long it takes per preview → [E3]. Cancellation returns False (doc). | **E4** |
| Pixel access | No in-memory buffer; read the written file | [E2] | PNG can be decoded with stdlib `zlib`. EXR (Cryptomatte) needs a decoder → keep the MVP on PNG / 8–16-bit TIFF | E4 |
| Segmentation masks | Clown pass (`setOutputClownPass`, coloured **per material** per KeyShot's own tip); render layers; Cryptomatte (2025.3+) | [E1] | Mapping clown colours to material names → [E3]. Render layers would require changing the user's layer assignments → avoid. | E5 |
| Real-time snapshot | `lux.screenshot()` returns the path of a real-time view capture | [E1] | Convergence state at capture time unknown → [E3]. Possibly a very cheap preview. | E4 |
| Region render | `RenderOptions.setRegion((x0,y0,x1,y1))` | [E1] | Render just the hero stone for stone metrics | E4 |

## L. User interface

| Operation | Mechanism | Evidence | Notes / risks | Spike |
|---|---|---|---|---|
| Native form dialog | `lux.getInputDialog(title, desc, values, id, apply)` with text, int, double, item, check, file, folder and label fields; `id` persists values; `apply` callback keeps the dialog open | [E1] 2023.2 doc; 2026 manual page | Enough for the MVP UI. Whether `apply` callbacks may modify the scene while the dialog is open → [E3] | **E10** |
| HTML/JS dialog | `lux.getBrowserDialog(url, html, result, init)`; JavaScript calls `lux.yieldResult(obj)` | [E1] 2023.2 doc | Not surfaced in newer extracts → [E3] that it is still present. Richer UI (light list, sliders). | E10 |
| Messages, files | `getMessageBox`, `getInputFile/Folder/Text/Int/Double/Item` | [E1] | — | — |

## M. Saving, restoring and deleting generated rigs

| Operation | Mechanism | Evidence | Notes / risks | Spike |
|---|---|---|---|---|
| Delete nodes | `SceneNode.delete()`; `undelete()`, `getDeleted()` and `isDeleted()` exist | [E1] | Deletion looks *soft* (nodes are recoverable). Whether deleted nodes persist in the saved `.bip` → [E3] | E6 |
| Delete materials | `lux.deleteMaterial(name)` — "Deletes material from KeyShot context", with a note about loading resource libraries | [E1] text; **semantics [E3]** | **Danger:** it may delete from the *library*, not the scene. Never call it on names we did not create. | **E6** |
| Persist rig state inside the scene | No `setMetaData`; node or material metadata is not writable (2023.2) | [E4] | Store state in a **sidecar JSON** and tag lights by node name | E6 |
| Save the scene | `lux.saveFile(path)`, `savePackage` | [E1] | Whether `saveFile(path)` re-targets the open scene to the new path (a "Save As" side effect) → [E3]. Do not auto-save the user's scene. | E6 |
| Save configurations | Python `json` to disk | [E2] | stdlib only | — |

## N. Undo, recovery and preserving existing scene state

| Operation | Mechanism | Evidence | Notes / risks | Spike |
|---|---|---|---|---|
| Undo control | `lux.isUndoEnabled()`, `lux.setUndoEnabled(bool)` ("re-enabled when a script context is destroyed") | [E1] 2023.2; 2024.1 ref | **No undo grouping or transactions** → [E4]. What a script generation leaves on the undo stack → [E3] | **E6** |
| Detect scene changes | `lux.isSceneChanged()` | [E1] | Prompt the user to save before generating | — |
| Snapshot and restore settings | Read and record environment, lighting preset, render options (`getDict()`), active camera; restore on removal | [E2] | `RenderOptions(dict=…)` round-trip is documented | E7 |

## O. Offline execution and external dependencies

| Item | Finding | Evidence |
|---|---|---|
| Scripting needs a network | No: embedded interpreter, local API | [E2] |
| KeyShot licence activation and AI features | Outside our control. AI Shots is described as running on-device. KeyShot Cloud (2026.2) is online. | [E1] for the AI-runs-on-device statement |
| Our dependencies | **Design for the Python standard library only** inside KeyShot. Optional analysis helpers can be a bundled external executable launched via `subprocess` [E3]. | [E2] |
| Our own licence enforcement | Must work offline (signed licence file); no phone-home | Design decision |

## P. Licensing restrictions and edition differences

| Item | Finding | Evidence |
|---|---|---|
| Scripting edition | "Scripting (Pro feature)" (KeyShot 11 manual); headless "Pro feature, 9.3 or newer" (2024 manual) | [E1] for those versions |
| 2026 editions | KeyShot Studio **Professional / Business / Enterprise**; rental only, from **$1,299/year** (2026.2 coverage) | [E2] (reseller and press) |
| Which 2026 editions include scripting and the HDRI Editor | Not found | **[E3] — ask Luxion** |
| Redistribution of commercial scripts; EULA limits on add-ons | Not found | **[E4] — legal review** |
| KeyShot Viewer / Web / Cloud running scripts | Not found | [E4] — out of scope |

## Q. Compatibility across versions

| Item | Finding | Evidence |
|---|---|---|
| API is versioned per release | Separate reference pages per version (6.x … 2026.1) | [E1] |
| Docs vs installed module mismatches | Forum: `setBrightness` documented for root `lux` but lives on `lux.Env` | [E1] (forum report) |
| Lighting features added recently | Planar lights and Light Positioning tool (2025.1), Light Layers (2025.2), Cryptomatte / OpenPBR / custom pivot (2025.3), node `getMetadata` and headless `renderAnimation` (2026.1), faster script execution and Apple-Silicon GPU (2026.2) | [E1] release notes and blogs |
| Scene files across versions | Newer `.bip` files generally do not open in older KeyShot (common behaviour; not verified here) | [E3] |
| **Strategy** | Runtime capability probing (`hasattr`, try/except around optional calls), a published tested-version matrix, and an E0 inventory diff on every new KeyShot release | — |

---

## Minimum viable implementation path (based on documented functions only)

1. **Packaging.** A pure-Python package in the KeyShot Scripts folder (stdlib only),
   launched from the script library.
2. **UI.** `getInputDialog` with an `id` for persistence, plus an Apply callback; upgrade to
   `getBrowserDialog` if E10 passes.
3. **Analysis.** `getSceneTree` → selected nodes → materials (shader type via Material Graph)
   → world bounding boxes → camera state.
4. **Light creation.** Write one OBJ containing *N* named unit rectangles →
   `importFile(opts={import_type:0, center_geometry:False, snap_to_ground:False,
   adjust_camera_look_at:False, adjust_environment:False, separate_parts:True,
   merge_objects:False, …})` → find the new nodes by diffing the tree before and after →
   `setMaterial(<JLE light material>, link=False)` → set parameters via the Material Graph →
   `applyTransform`.
5. **Environment.** `newEnvironment("JLE_<rig>", activate=True, clone=True)`, then adjust it.
   The user's environment is never edited.
6. **State.** A sidecar JSON next to the scene plus a backup in the KeyShot config folder;
   lights identified by a node-name prefix plus stored material names.
7. **Removal.** Delete our nodes, re-activate the original environment, and restore the
   snapshotted lighting preset and render options.

Every step above depends on at least one [E3] item. **E1, E2 and E3 must pass before Phase 2
starts.**

## Appendix: 2023.2 functions relevant to this product (verbatim names)

- **Scene:** `getSceneTree`, `dumpTree`, `getSceneInfo`, `getObjects`, `getMaterialMapping`,
  `applyMaterialMapping`, `getObjectMaterial`, `setObjectMaterial`, `getSceneMaterials`,
  `importFile`, `getImportOptions`, `exportFile`, `saveFile`, `savePackage`,
  `isSceneChanged`, `hasContents`.
- **SceneNode:** `applyTransform`, `getTransform`, `getBoundingBox`, `getCenter`,
  `getChildren`, `getParent`, `getPath`, `find`, `getKind`, `getID`, `getName`, `setName`,
  `getMaterial`, `setMaterial`, `duplicate`, `delete`, `undelete`, `hide`, `show`, `lock`,
  `unlock`, `select`, `deselect`, `isSelected`, `getSelected`, `moveToGroup`,
  `getRenderLayer`, `setRenderLayer`, `snapToGround`, `centerAndFit`; plus `getMetadata`
  (2026.1).
- **Materials:** `createSceneMaterial`, `getMaterialGraph` (`getRoot`, `getNodes`,
  `getNodesFromType`, `newNode`, `newEdge`, `removeNode`, `removeEdge`), `ShaderNode`
  (`getType`, `getParameters`, `getParameter`, `getInputEdges`), `ShaderParameter`
  (`getName`, `getType`, `getValue`, `setValue`, `isPure`), `importMaterials`,
  `loadMaterials`, `saveMaterial`, `saveMaterialPackage`, `deleteMaterial`,
  `getLibraryMaterials`.
- **Camera:** `getCamera`, `getCameras`, `setCamera`, `newCamera`, `saveCamera`,
  `removeCamera`, `get/setCameraPosition`, `LookAt`, `Up`, `Direction`, `Distance`,
  `FieldOfView`, `FocalLength`, `getCameraLens`, `get/setSphericalCamera`,
  `setStandardView`.
- **Environment, lighting, render:** `getActiveEnvironment` (`Env.*`), `newEnvironment`,
  `setActiveEnvironment`, `removeEnvironment`, `getEnvironments`, `get/setLightingPreset`,
  `getLightingPresets`, `getRenderOptions` (`RenderOptions.*`), `get/setRenderEngine`,
  `renderImage`, `screenshot`, `getActiveImageStyle`.
- **UI and system:** `getInputDialog`, `getBrowserDialog`, `getMessageBox`, `getInputFile`,
  `getKeyShotVersion`, `getKeyShotDisplayVersion`, `getKeyShotFolder`, `isHeadless`,
  `getOS`, `getSystemInfo`, `isUndoEnabled`, `setUndoEnabled`, `sync`.
- **luxmath:** `Matrix` (`makeIdentity`, `makeRotate`, `makeScale`, `makeTranslate`,
  `rotateAroundAxis`, `setTransformation`, `getTransformation`, `mul`, `invert`, `val`) and
  `Vector` (`cross`, `dot`, `normalize`, `len`, `getOrthogonalBasis`).
