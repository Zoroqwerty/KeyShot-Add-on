# Sources and Evidence Log

**Access method legend.**

| Code | Meaning |
|---|---|
| **R** | Read in full (cloned or fetched) |
| **S** | Seen as a search-engine extract only. The host was blocked from the research environment, or the page was not fetched. |

Search extracts are paraphrases plus short quotes produced by the search tool. Treat every
**S** item as pointing to the right page, and re-read it before quoting it externally.

## KeyShot scripting API

| Source | Access | Used for |
|---|---|---|
| GitHub `donaldtuttle/Unofficial_KeyShot_Python`: `lux/KeyShot_lux_API.md`, `luxmath/KeyShot_luxmath_API.md`, `lux_headless/KeyShot_headless_lux_API.md`, `Scripts/*.txt` — https://github.com/donaldtuttle/Unofficial_KeyShot_Python | **R** | Verbatim KeyShot **2023.2** `help(lux)` / `help(luxmath)` docstrings (Python 3.11 header); official example texts (import, scene nodes, material graph, transforms, render, camera, cancelling). Third-party transcription of official text. |
| KeyShot 2024.1 Scripting Documentation: lux — https://media.keyshot.com/scripting/doc/2024.1/lux.html | S | `SHADER_TYPE_MESH_LIGHT` present; `isUndoEnabled` / `setUndoEnabled`; `newNode` docstring |
| KeyShot 2024.1 Headless Scripting Documentation — https://media.keyshot.com/scripting/headless_doc/2024.1/lux.html | S | `SHADER_TYPE_MESH_LIGHT` present |
| KeyShot 2025.3 Headless Scripting Documentation — https://media.keyshot.com/scripting/headless_doc/2025.3/lux.html | S | `getLightingPreset`; no light-layer function found in extract |
| KeyShot 2026.1 Headless Scripting Documentation — https://media.keyshot.com/scripting/headless_doc/2026.1/lux.html | S | `SceneNode.getMetadata()`; `getSceneTree`; scene `getMetaData` |
| KeyShot 11.3 / 11.0 / 9.3 / 7.0 references — https://media.keyshot.com/scripting/doc/11.3/lux.html (and sibling versions) | S | Per-version reference structure; `SceneNode` description |
| KeyShot 2024 manual, Scripting Console — https://manuals.keyshot.com/keyshot2024/manual/scripting-console.html | S | Python 3.12; capability categories (geometry move / scale / duplicate / show / hide / lock; materials get / set / delete; lighting presets get / set) |
| KeyShot 11 manual, Scripting — https://manual.keyshot.com/keyshot11/manual/scripting/ | S | "Scripting (Pro feature)"; Python 3.10; three ways to run scripts |
| KeyShot 2024 manual, Headless Scripting — https://manuals.keyshot.com/keyshot2024/manual/exposed-headless-scripting-functionality.html | S | Headless = Pro feature, 9.3+; FlexLM features |
| KeyShot manual, scripting setup / local Python — https://manual.keyshot.com/?p=6104 | S | Local Python of the same version can be detected (preference) |
| KeyShot 2026 manual, Custom Input Dialog — https://manuals.keyshot.com/kss2026/en-us/manual/scripting-custom-input-dialog.html | S | `getInputDialog` with persistent `id` |
| KeyShot 2026 manual, Scripting: Material Graph — https://manuals.keyshot.com/kss2026/en-us/manual/scripting-material-graph.html | S | Material graph scripting in current docs |
| KeyShot forum, "Python Scripting for KeyShot 2023 is Broken" — https://community.keyshot.com/forum/t/python-scripting-for-keyshot-2023-is-broken/881 | S | Docs vs installed module mismatch (`setBrightness` on `Env`) |
| KeyShot forum, texture change via script — https://community.keyshot.com/forum/t/just-change-the-texture-image-with-python-script-and-render-it/925 | S | Material-graph node IDs change when the file is edited |
| KeyShot forum, Python modules with headless scripting — https://community.keyshot.com/forum/t/python-modules-with-headless-scripting/12069 | S | Third-party module use requires a matching local Python plus preference |

## KeyShot lighting features and behaviour

| Source | Access | Used for |
|---|---|---|
| Light Sources (2024 / 2025 manuals) — https://manuals.keyshot.com/kss2025/manual/light-sources.html | S | Lights are materials on geometry; Light Manager; Add Geometry |
| KeyShot support KB, "Applying physical lights as materials replaces or moves components" — https://support.keyshot.com/en/knowledge-base/applying-physical-lights-as-materials-replaces-or-moves-components | S | Host lights on separate primitives; light origin at the part centre |
| Area Light (2024 / 2025) — https://manuals.keyshot.com/kss2025/manual/area-light.html | S | Watt / Lumen / Lux semantics; Lux constant per m² across size |
| Area Light visibility settings (KS 11) — https://manual.keyshot.com/keyshot11/?p=3970 | S | Visible to Camera / in Reflections / in Shadows |
| Forum, "Area light reflecting in GPU mode" — https://community.keyshot.com/forum/t/area-light-reflecting-in-gpu-mode/7416 | S | GPU visibility inconsistency report |
| Planar Light (2025) — https://manuals.keyshot.com/kss2025/manual/planar-light.htm | S | Planar light material; Watt / Lumen / Lux |
| Light Positioning (2025) — https://manuals.keyshot.com/kss2025/en-us/manual/Light-Positioning.htm | S | Highlight / Normal / Target / Orbit modes; Ctrl/Cmd+L |
| Light Layers (2025) — https://manuals.keyshot.com/kss2025/en-us/manual/Light-Layers.htm | S | Light linking, max 5 layers |
| KeyShot blog, Studio 2025 lighting updates — https://www.keyshot.com/blog/keyshot-studio-2025-speed-lighting-updates/ | S | Planar lights with barndoors (2025.1); positioning tool |
| KeyShot blog, What's new 2025.2 — https://www.keyshot.com/blog/whats-new-keyshot-studio-2025-2/ | S | Light Layers |
| KeyShot blog / CG Channel, 2025.3 — https://www.keyshot.com/blog/keyshot-studio-performance-updates-version-2025-3/ ; https://www.cgchannel.com/2025/11/keyshot-releases-keyshot-studio-2025-3/ | S | Cryptomatte, OpenPBR, custom pivot (Nov 2025) |
| Release Notes 2026.1 — https://manuals.keyshot.com/kss2026/en-us/manual/Release-Notes-2026.1.htm ; blog https://www.keyshot.com/blog/keyshot-studio-performance-updates-version-2026-1/ | S | Headless `renderAnimation`; `getMetadata`; AI Shots overhaul |
| Release Notes 2026.2 — https://manuals.keyshot.com/kss2026/en-us/manual/Release-Notes-2026.2.htm ; CG Channel https://www.cgchannel.com/2026/06/keyshot-releases-keyshot-2026-2/ | S | Faster script execution; Apple Silicon GPU; KeyShot Cloud; rental-only from $1,299/yr |
| AI Shots (2026) — https://manuals.keyshot.com/kss2026/en-us/manual/AI-Shots.htm | S | Generative restyle / background; on-device |
| HDRI Editor Pins (2026) — https://manuals.keyshot.com/kss2026/en-us/manual/hdri-editor-pins.html ; HDRI Editor (Pro) — https://manuals.keyshot.com/kss2025/manual/hdri-editor.html | S | Pins GUI; Pro feature; no scripting found |
| Lighting presets (2025 manual) — https://manuals.keyshot.com/kss2025/manual/lighting.html ; blog https://www.keyshot.com/blog/using-lighting-presets-in-keyshot | S | Jewelry preset = Interior + ground illumination + more ray bounces + caustics |
| Render layers and passes quick tip — https://www.keyshot.com/blog/keyshot-quick-tip-render-layers-and-render-passes-in-keyshot | S | Clown pass coloured per material |
| Gem material (KS 11 manual) — https://manual.keyshot.com/keyshot11/?p=3773 ; Will Gibbons, Dispersion in KeyShot — https://www.willgibbons.com/articles/keyshot-dispersion | S | Abbe number control; 35–55 starting range; dispersion samples |
| KeyShot Studio editions (reseller) — https://doschdesign.com/products/keyshot/keyshot-studio.html | S | Professional / Business / Enterprise naming; 2026.2 scripting additions |
| KeyShot pricing — https://www.keyshot.com/pricing/ | S | All Studio features in every plan; plans differ by support, seats and add-ons; Professional $1,299/yr, Business $1,599/yr |
| KeyShot manual, Scripting (2025) — https://manuals.keyshot.com/kss2025/manual/scripting.html | S | Scripting window via Ribbon or Window › Scripting Console; Scripts tab lists the Scripts folder; Python 3.12 |
| KeyShot manual, Light Manager — https://manual.keyshot.com/?p=9044 | S | Shift+L overview of all light materials; edit key parameters; double-click opens the material |

## Jewelry optics

| Source | Access | Used for |
|---|---|---|
| Moses et al., "A Foundation for Grading the Overall Cut Quality of Round Brilliant Cut Diamonds", *Gems & Gemology*, Fall 2004 — https://www.gia.edu/gems-gemology/fall-2004-grading-cut-quality-brilliant-diamond-moses | S | Definitions of brightness, fire, scintillation (sparkle and pattern); brightness replaces brilliance |
| GIA 4Cs: Cut — https://www.gia.edu/4cs-cut | S | Cut grade components |
| Gem refractive index reference (Threekit gem material docs) — https://community.threekit.com/platform-documentation/project-data/assets/materials/gem-material | S | Diamond 2.417–2.419; sapphire / ruby 1.762–1.778 |
| Critical-angle calculators (several) | S | θc ≈ 24.4° (also computed directly in doc 04) |
| *Not re-verified in this pass:* diamond dispersion 0.044 (B–G); Tolkowsky 1919 proportions; moissanite and CZ values; AGS ASET angular bands | — | Marked "[Common reference value — verify]" in doc 04 |

## Competitors and workflows

| Source | Access | Used for |
|---|---|---|
| Lightmap help, HDR Light Studio KeyShot installation — https://help.lightmap.co.uk/hdrlightstudio/installation-keyshot.html | S | KeyShot connection built into KeyShot; KeyShot 3–6 on Windows listed |
| Lightmap blog, HDR Light Studio Live for KeyShot — https://www.lightmap.co.uk/blog/keyshot/ ; compatibility chart — https://help.lightmap.co.uk/hdrlightstudio/compatability-chart.html | S | Plug-in history; current builds (9.5.0, July 2026); KeyShot row not seen |
| Lightmap, area lights / LightPaint — https://www.lightmap.co.uk/blog/area-lights-added-to-modo-connection/ | S | LightPaint reflection / illumination / rim modes; area lights in other hosts |
| RhinoArtisan lights — https://www.rhinoartisan.com/docs/7/rendering/commands/lights/ ; KeyShot link — https://www.rhinoartisan.com/docs/7/rendering/keyshot/ | S | Drag-highlight light aiming (v7 beta); live linking preserves KeyShot lighting |
| Light Wrangler docs — https://blendermarket.com/products/light-wrangler/docs | S | Reflect / Orbit / Direct placement modes (Blender) |
| CGTrader KeyShot jewelry scene kits — https://www.cgtrader.com/3d-models/various/various-models/keyshot-scene-setup-for-jewelry-diamonds-renderings ; https://www.cgtrader.com/3d-models/various/various-models/dark-scene-setup-for-jewelry-3d-rendering-with-keyshot | S | Static template competitors |
| Will Gibbons, KeyShot Diamond Ring Jewelry Rendering Tutorial — https://www.willgibbons.com/blog/jewelry ; Area-light library — https://www.willgibbons.com/blog/area-light-library ; Lights in KeyShot — https://www.willgibbons.com/articles/lights-in-keyshot | S | HDRI-pin jewelry workflow; dark reflections; manual area-light library approach |

## Hosts that could not be reached from the research environment

`media.keyshot.com`, `manuals.keyshot.com`, `community.keyshot.com`, `www.keyshot.com`,
`www.cgchannel.com`, `web.archive.org`. All were blocked by the environment's network policy
(DNS / proxy). The first action of the spike (E0) replaces all **S**-level KeyShot API
evidence with first-hand inventory output.
