# 10. Competitive and Market Analysis

## Scope and caveat

Sources are listed in [sources.md](sources.md). Direct access to keyshot.com was blocked
during research; KeyShot facts come from search extracts of official pages.

**Not finding a product is not evidence that none exists.** §10.5 lists the searches still
needed before calling any feature novel.

## 10.1 Inventory of alternatives

| # | Alternative | What it is | Comparable? |
|---|---|---|---|
| 1 | **KeyShot Light Positioning tool** (2025.1) | GUI tool. Right-click a part or press Ctrl/Cmd+L, then drag a physical light over the real-time view. Modes: **Highlight** (puts the light so its reflection lands where you point), Normal, Target, Orbit. Mouse wheel changes distance. | **Closest built-in competitor.** Geometry-aware, but **manual**, one light at a time |
| 2 | **KeyShot HDRI Editor + pins** (Pro) | Pins are soft shapes painted into the environment; "Set highlight" aims a pin at a clicked point; pins are stored in the scene | Geometry-aware placement, **manual**; the dominant jewelry workflow (e.g. Will Gibbons' ring tutorial) |
| 3 | **KeyShot Lighting Presets** (incl. "Jewelry") | Render-quality presets: ray bounces, caustics, ground illumination. **Not lights.** | Not comparable (a complement; we use it) |
| 4 | **KeyShot Planar lights** (2025.1) and **Light Layers** (2025.2) | Softbox lights with barndoors; light linking (up to 5 layers) | Building blocks, not automation |
| 5 | **KeyShot Studios** | Saved combinations of camera, environment, model sets and image style | Building block for per-shot rigs |
| 6 | **KeyShot AI Shots** (2025–2026) | Generative restyle, background and imagine modes; on-device GPU. Produces *images*, not lights. | Substitute for some e-commerce or marketing visuals; **not editable, not physically constrained** |
| 7 | **HDR Light Studio** (Lightmap) | Dedicated lighting-design app. LightPaint places lights by clicking where a reflection or illumination should appear. Area-light support in several hosts (Maya, 3ds Max, Cinema 4D, MODO, VRED). A "HDR Light Studio Live" plug-in for KeyShot has existed since 2011. | Comparable for **manual, geometry-aware** lighting design. **Current KeyShot support unverified:** Lightmap help lists KeyShot 3–6 on Windows. Not jewelry-specific; not automatic. |
| 8 | **RhinoArtisan** (Rhino jewelry CAD) | v7 (beta) has point, directional, rectangular and linear lights and *aim by dragging the highlight*. KeyShot plug-in with live linking that keeps KeyShot lighting across geometry updates. | Partly comparable, upstream in CAD. Manual. |
| 9 | **Template scenes and HDRI kits** (e.g. CGTrader "KeyShot scene setup for jewelry diamonds", "dark scene setup"; Will Gibbons project files; courses) | Fixed HDRIs, materials and render settings for KeyShot 7–11+ | **Static presets.** Not adaptive; cheap; artists already own many. |
| 10 | **Light Wrangler** (Blender) | Cursor-targeted placement with Reflect, Orbit and Direct modes; wheel adjusts power, size and distance | Not KeyShot. Shows demand for highlight-targeted placement. Manual. |
| 11 | **Jewelry CAD suites with bundled renderers** (e.g. MatrixGold, others) | Render modules with presets | **Not researched in depth.** Must be checked (§10.5). |

## 10.2 Feature matrix

| Capability | KS Light Positioning | KS HDRI pins | KS presets | AI Shots | HDR Light Studio | RhinoArtisan | Templates / HDRIs | **Proposed tool** |
|---|---|---|---|---|---|---|---|---|
| Automatic light placement | ✘ | ✘ | ✘ | n/a (no lights) | ✘ | ✘ | ✘ (fixed) | **✔ goal** |
| Geometry-aware | ✔ manual click | ✔ manual click | ✘ | ◐ implicit | ✔ manual click | ✔ manual drag | ✘ | **✔ automatic, coarse** |
| Jewelry-specific presets | ✘ | ✘ | ◐ ("Jewelry" render settings only) | ✘ | ✘ | ◐ (jewelry CAD context) | ✔ (static) | **✔ adaptive** |
| Automatic gemstone lighting | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ◐ (one HDRI fits all) | **✔ goal** |
| Editable physical lights | ✔ (native) | ◐ pins, not geometry | n/a | ✘ | ◐ (HDRI; area lights in some hosts) | ✔ in Rhino | ◐ | **✔ native** |
| Preview-based optimization | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | **◐ later (Phase 5)** |
| Offline | ✔ | ✔ | ✔ | ✔ on-device | ? | ? | ✔ | **✔ required** |
| Version compatibility | ✔ native | ✔ native | ✔ native | ✔ native | ? (unverified for current KS) | ? | ◐ (scene files need a recent KS) | ◐ tested matrix |
| Override-preserving regeneration | n/a | n/a | n/a | n/a | ? | ? | n/a | **✔ goal** |
| Catalogue consistency (same look across SKUs) | ✘ | ◐ (reuse environment) | ✘ | ✘ | ◐ | ◐ | ◐ (copy scene) | **✔ goal (look files)** |
| Diagnostics (materials, render settings, metrics) | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | **✔ goal** |

✔ yes · ◐ partial · ✘ no · ? unverified

## 10.3 Genuinely comparable vs merely related

- **Genuinely comparable** means it automatically produces geometry-aware, jewelry-specific,
  editable lights inside KeyShot. **None was found.**
- **Comparable in mechanism, but manual:** KeyShot Light Positioning tool, HDRI pins with
  Set Highlight, HDR Light Studio LightPaint, RhinoArtisan highlight aiming, Light Wrangler.
  These make an expert fast, and they are the real benchmark the product must beat on time.
- **Static presets or rigs:** KeyShot lighting presets (render settings), template scenes,
  HDRI packs.
- **Substitutes:** generative AI imagery (KeyShot AI Shots and others). Strong for mood images,
  weak for accurate, consistent catalogue imagery that must match the physical product.

## 10.4 Strongest alternatives and how to be meaningfully different

1. **KeyShot's own tools, used by an expert with personal templates.** They are free with the
   licence, always compatible, and familiar.
   - *To differ:* zero-click generation for the camera and piece at hand; diagnostics that
     catch non-lighting causes of bad stones; regeneration that keeps edits.
   - *Proof needed:* expert time-to-approved-image with the tool is lower than with their
     templates and the Light Positioning tool. That is the doc 12 baseline.
2. **Template scenes and HDRIs.** Cheap and good enough for many.
   - *To differ:* adapts to scale, camera and piece type; physical lights instead of one baked
     HDRI; consistency across SKUs.
   - *Proof needed:* blind preference and lower failure rate across the varied benchmark, not
     just on a hero ring.
3. **HDR Light Studio** (if KeyShot support is current). Professional and flexible.
   - *To differ:* jewelry knowledge and automation, native lights, no second application.
4. **Platform risk.** Luxion shipped highlight-based light positioning and planar lights in
   2025 and AI features in 2025–2026. An "auto-light" feature from Luxion would remove the
   core of this product.
   - *Mitigation:* the defensible parts are jewelry-domain knowledge (presets, response maps,
     diagnostics), catalogue workflow (look files, consistency, batch), and override-safe
     regeneration. Build these early. Consider partnering with Luxion rather than competing.

**Most promising commercial angle (hypothesis to test in interviews).** **Catalogue
consistency at volume.** Jewelry e-commerce and manufacturing studios render many similar
SKUs and need the same look on each. A rule-based, scale-invariant rig applied in seconds,
with diagnostics, is worth more there than in one-off hero shots, where artists want full
manual control anyway.

## 10.5 Searches still required before claiming novelty

- KeyShot community forum "Scripts" category, and Luxion's own example script library in each
  version.
- Marketplaces: Gumroad, ArtStation, CGTrader and Blender Market for "KeyShot script
  lighting".
- Jewelry CAD vendors' render modules (MatrixGold, RhinoGold, JewelCAD, 3Design) and their
  KeyShot bridges.
- Regional jewelry-CAD communities in major manufacturing hubs (India, China, Thailand, Turkey,
  Italy); some tools are published only in local languages.
- Lightmap's current compatibility chart for KeyShot (U5).
- Patent search for "automatic light placement" / "lighting design from geometry and camera"
  (freedom to operate). Professional legal review is recommended before launch.
- Luxion roadmap conversation (doubles as partnership exploration).
