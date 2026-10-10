# 7. Specifications for the Ten Presets

**All numeric values in this section are initial design hypotheses.** They must be calibrated
against artist-approved reference renders in Phase 3 (doc 12). None of them has been
rendered or measured.

The angle and module notation is defined in [06](06-lighting-engine-architecture.md) §6.4:

- **α** = off-axis angle from the camera direction: 0° = behind the camera, 90° = side-on,
  >90° = behind the subject.
- **β** = clock angle: 0° = top of frame, 90° = right.
- **k** = distance factor relative to the piece's bounding-sphere radius *S*.
- Angular sizes are as seen from the target.

The metrics are defined in [08](08-automatic-optimization.md).

## 7.1 Shared module library

Every preset is a combination of these modules with preset-specific parameters. This is what
keeps ten presets affordable.

| Module | Shape | Initial placement | Initial size (angular) | Radiance ratio | Purpose |
|---|---|---|---|---|---|
| **KEY** — overhead softbox | rectangle | α 30–45°, β 0° ±15°, k 5 | 25–40° × 18–30° | 1.0 | Overall brightness; broad facet flashes; top-surface metal highlight |
| **SPARKLE** — ring of small sources | disc / small rectangle, ×N | α 15–40°, β spread with *deliberate irregular gaps* (no perfect symmetry), k 5–8 | 2–6° | 1.5–3.0 | Fire, sparkle, pattern contrast in stones |
| **STRIP** — gradient pair | long strip (aspect 1:6–1:10) | Reflection-placed on band proxy at shoulders ψ ≈ ±40–70° from the head direction, or angular α 60–85°, β ≈ 90° / 270° | 40–70° long × 4–10° wide | 0.6–0.9 | Continuous specular lines that describe metal form |
| **RIM** — separation | strip or rectangle | α 110–150°, β 0° / ±60° | 10–30° | 0.8–2.0 | Silhouette and edge highlights, especially on dark backgrounds |
| **FILL** — low card | large rectangle | α 40–70°, β 150–210° (below) | 50–80° | 0.10–0.25 | Lift the inside of the band and shadow areas; soften contrast |
| **FLAG** — negative card | black, non-emissive rectangle | Reflection-placed where darkness is wanted in metal | 20–50° | — | Edge definition on light backgrounds. **Needs a black diffuse material [E3].** Optional in the MVP. |
| **KICKER** — accent | small rectangle | Reflection-placed on a chosen proxy point (head, bail, shoulder) | 3–10° | 1.0–2.0 | One deliberate highlight |
| **ENV** — environment profile | — (cloned environment) | — | — | brightness level | Background colour; ambient level; ground shadow on/off |
| **RENDER** — optional | — | `setLightingPreset("Jewelry")` with consent, plus a minimum ray-bounce check | — | — | Removes render-setting causes of dark stones (doc 04 §4.2) |

Light type for all emissive modules: **Area Light** (Lux units), or **Planar Light** where
the version supports scripting it (2025.1+, [E4] until E0/E2). All are camera-invisible,
visible in reflections, and do not cast shadows. Single-sided, facing the target.

## 7.2 Archetypes and how the ten presets share them

| Archetype | Presets built on it | Shared modules | What differs between the presets |
|---|---|---|---|
| **S — Stone-centric** | 1 Diamond Brilliance, 2 Solitaire Ring, 3 Pavé Brilliance, 7 Multi-Stone | KEY, SPARKLE, STRIP, RIM, ENV | Target set (hero / clusters / all stones); sparkle count and size; stone-vs-metal weighting; distance factor |
| **M — Metal studio** | 4 White Gold, 5 Yellow Gold, 6 Rose Gold | KEY, STRIP, FILL, (FLAG), ENV | Kelvin; radiance (gold lower, to keep saturation); gradient width; background tone |
| **D — Detail** | 8 Intricate | KEY (larger), FILL, STRIP, KICKER (raking) | Raking-angle key for relief; lower contrast |
| **K — Dark mood** | 9 Dark Luxury | RIM (strong), KEY (narrow), STRIP, SPARKLE, ENV black | Black environment; reflection cards so metal is not black |
| **E — E-commerce** | 10 Packshot | KEY (large), FILL, STRIP, FLAG, ENV white, ground shadow | White background, neutral colour, consistency rules |

## 7.3 Adapting presets to different sizes and geometries without losing character

1. **Scale.** Positions are `p + k·S·ω` and sizes come from angular sizes, so a 6 mm stud and
   a 60 mm pendant get *the same-looking* rig. With Lux units, highlight brightness also
   stays the same (E14 verifies this).
2. **Geometry.** Modules attach to **targets** (hero, clusters, band proxy, jewelry) found by
   doc 05. When a target is missing (e.g. no hero stone in a metal-only ring), the module
   falls back to the jewelry target or is skipped. The skip is logged and shown.
3. **Camera.** All directions are camera-relative, so the *photographic* character (key from
   upper left, rims behind) survives any camera move. Re-generate after changing the camera.
4. **Resolution-aware stone rules.** If the hero stone's projected diameter is under about
   80 px, sparkle sources become sub-pixel noise. The rule then reduces the sparkle count and
   increases their size. The threshold is an initial guess.
5. **Invariants per preset.** Each preset declares its *character invariants*, for example:
   - Dark Luxury: background below 5% luminance, rim present;
   - Packshot: background ≥ 99% white, Kelvin 5000–6500.

   Adaptation may never break an invariant. If it would have to, the preset warns instead.

---

## 7.4 Preset 1 — Diamond Brilliance

- **Objective.** Make the diamonds read as *bright, contrasty and lively*: a crisp bright/dark
  facet mosaic with visible fire. Metal is secondary but must not be black or blown out.
- **Intended jewelry.** Any piece where diamonds are the selling point: solitaires, halos,
  studs, tennis pieces, close-ups.
- **Required info.**
  - *Must:* at least one stone component (material class stone).
  - *Recommended:* hero stone, cut family, table-normal estimate.
- **Initial strategy.** A camera-centred sparkle ring and a moderate key. A strong
  near-axis keep-out and a dark-grey cloned environment create contrast. Metal gets only
  low-radiance strips.
- **Light types.** Area (or planar); 1 KEY, 4–6 SPARKLE, 2 STRIP, 0–1 RIM.
- **Placement logic.**
  - SPARKLE: α 15–35°, with β chosen from the cut family's high-response bands (§6.5).
    Until the maps exist, use an irregular spread such as β = {20°, 95°, 160°, 215°, 300°}.
    Size 2–4°.
  - KEY: α 35–45°, β ≈ 0°. Keep it **off** the table-flash direction by ≥ 10°.
  - STRIP at α ≈ 70°.
  - α_min (near-axis keep-out) = 10°.
- **Important parameters (tunables).** Global *G*; SPARKLE radiance and size; KEY size;
  environment brightness; α of the sparkle ring.
- **Material considerations.**
  - Check the gem material: IOR ≈ 2.4, Abbe > 0 for fire; warn if it is "glass".
  - Check ray bounces and offer the Jewelry render preset.
  - For coloured stones (low IOR), switch to the "coloured stone" profile: larger sources and
    less darkness, because body colour reads better with more transmitted light.
- **Camera considerations.** Best for face-up to about 45° views. In a profile view the table
  turns away, so suggest Solitaire Ring or multi-view mode.
- **Known limitations.** It cannot fix bow-ties (oval, pear, marquise), CAD proportion leakage
  or dark facets caused by ray bounces. Fire is sensitive to noise in previews.
- **Failure conditions (warn or refuse).**
  - No stone components → refuse and suggest a metal preset.
  - Stone material not a gem or dielectric → warn.
  - Hero projected size < 40 px → warn ("stones too small in frame for brilliance lighting").
- **Evaluation criteria (initial targets).**
  - hero_dark_frac 0.15–0.40;
  - hero_bright_frac ≥ 0.25;
  - sparkle_count above the cut-specific floor;
  - fire_frac > 0 when Abbe > 0;
  - metal_clip_frac ≤ 0.04.

## 7.5 Preset 2 — Solitaire Ring

- **Objective.** A balanced hero shot of a ring: a lively centre stone **and** a readable band
  and shoulders, with clear gradients describing the shank's form.
- **Intended jewelry.** Solitaire and solitaire-with-accents rings: engagement, cocktail.
- **Required info.**
  - *Must:* ring type (confirmed), metal band.
  - *Recommended:* hero stone, finger axis, up direction.
- **Initial strategy.** Archetype S with metal weighting raised. Reflection-placed strips put
  continuous highlight lines along both shoulders. The sparkle ring is reduced to 3–4 sources.
- **Light types.** 1 KEY, 3–4 SPARKLE, 2 STRIP (reflection-placed), 1 RIM, optional FILL.
- **Placement logic.**
  - STRIP: reflection placement on the band proxy at ψ = ±55° from the head direction; long
    axis aligned to the band tangent; γ_max = 40°.
  - KEY: α 35°, β −20° (classic upper left).
  - RIM: α 130°, β 0°.
  - SPARKLE: as Preset 1, size 3–5°.
- **Important parameters.** *G*; strip ψ and width; key size; sparkle radiance; rim radiance.
- **Material considerations.**
  - Yellow and rose gold: lower strip radiance (~0.7) to protect saturation.
  - White metals: allow 0.9.
  - Satin bands: wider strips (10–15°).
- **Camera considerations.** Designed for the typical three-quarter ring view, and robust
  between about 20° and 60° camera elevation. Top-down views lose the shoulder strips (they
  fall outside the band's visible normals), so warn.
- **Known limitations.** The band proxy assumes a roughly circular shank. Square, knife-edge
  or split shanks reduce strip accuracy.
- **Failure conditions.** Finger axis confidence < 0.5 → ask the user to confirm the ring
  orientation. No metal band found → fall back to Diamond Brilliance.
- **Evaluation criteria.**
  - hero metrics as Preset 1 (relaxed by 10%);
  - metal_gradient_energy above the floor on the band region;
  - metal_clip_frac ≤ 0.03;
  - shoulder highlight continuity (fraction of band-arc pixels with a highlight line) ≥ 0.5.

## 7.6 Preset 3 — Pavé Brilliance

- **Objective.** A pavé field that **sparkles evenly** (many points of light distributed
  across the field) instead of reading as grey gravel, with the metal between stones still
  defined.
- **Intended jewelry.** Pavé bands, halos, micro-pavé pendants, eternity rings.
- **Required info.**
  - *Must:* stone components (≥ 8 small stones or a pavé cluster, or a user tag).
  - *Recommended:* cluster centres and extents.
- **Initial strategy.** Many small sparkle sources at **varied α and β**, using near-field
  parallax (smaller *k*) so neighbouring stones catch different sources. A soft key and
  strips for the metal.
- **Light types.** 6–8 SPARKLE (cap), 1 KEY, 2 STRIP.
- **Placement logic.**
  - SPARKLE: α 10–45°, β spread over 360°, k 3.5–4.5 (more parallax), size 2–3°.
  - Target = cluster centroid(s); one sparkle sub-group per cluster for up to 3 clusters.
- **Important parameters.** Sparkle count, size, radiance and *k*; *G*.
- **Material considerations.**
  - Pavé stones in CAD are often low-poly or simplified, with fewer facets. Expect weaker
    sparkle and say so in diagnostics.
  - Merged pavé meshes are fine for this preset: it targets the cluster, not individual
    stones.
- **Camera considerations.** Works across a wider camera range than Preset 1, because pavé
  has many orientations. Close-ups need more samples (noise).
- **Known limitations.** Noise: many small bright sources converge slowly. The preview cost
  rises (E4).
- **Failure conditions.**
  - Fewer than 8 small stones and no pavé tag → suggest Diamond Brilliance.
  - Projected stone size < 6 px → sparkles become noise; reduce the count and warn.
- **Evaluation criteria.**
  - sparkle_density (blobs per 1,000 px of pavé mask) within the target band;
  - spatial uniformity of sparkle (coefficient of variation across a 4×4 grid over the pavé
    mask) ≤ 0.6;
  - stone_dark_frac 0.2–0.5;
  - noise_est below the threshold at the final sample count.

## 7.7 Preset 4 — White Gold Studio

- **Objective.** Crisp, neutral white metal: clean gradients, no colour cast, form described
  by strips and controlled darkness. Stones present but secondary.
- **Intended jewelry.** White gold, platinum, silver, rhodium-plated pieces; bands; minimal
  designs.
- **Required info.**
  - *Must:* metal components.
  - *Recommended:* alloy (white), finish, ring frame.
- **Initial strategy.** Archetype M: KEY plus a strip pair plus a low fill, in a light-grey
  cloned environment. Kelvin 6000–6500 to keep the metal from looking yellow.
- **Light types.** 1 KEY, 2 STRIP, 1 FILL, optional FLAG ×1–2.
- **Placement logic.**
  - STRIP reflection-placed at ψ ±50°.
  - FLAG reflection-placed between the strips, to add a dark line that defines the edges.
  - KEY α 40°, β 0°. FILL α 60°, β 180°.
- **Important parameters.** Kelvin; *G*; strip width; environment brightness.
- **Material considerations.** Very low roughness shows the edges of the rectangular lights.
  Use wider strips with soft edges, or a gradient texture (if E2 shows texture inputs can be
  set). Satin needs a larger key.
- **Camera considerations.** Robust across views. Flags are camera-specific, so re-generate
  after camera moves.
- **Known limitations.** The black material for flags depends on E2/E3. Without flags, rely on
  environment darkness.
- **Failure conditions.** Metal classified as yellow or rose gold → suggest the matching
  preset. No metal → refuse.
- **Evaluation criteria.**
  - metal mean chroma ≤ the white-metal threshold (no cast);
  - metal_clip_frac ≤ 0.04;
  - metal_crush_frac ≤ 0.10;
  - gradient energy above the floor;
  - silhouette_contrast ≥ the threshold.

## 7.8 Preset 5 — Yellow Gold Luxury

- **Objective.** Rich, saturated yellow gold that looks warm and expensive. Highlights must not
  clip to white, and mid-tones must carry the gold colour.
- **Intended jewelry.** Yellow gold bands, chains, pendants, signet rings, gold-dominant pieces.
- **Required info.**
  - *Must:* metal components.
  - *Recommended:* alloy = yellow gold (from colour or name).
- **Initial strategy.** Archetype M with **lower radiance and wider, graded sources**. Gold
  colour lives in reflections of mid-luminance sources. A warm-neutral 4500–5000 K, *not*
  very warm: orange lights fake the saturation and break e-commerce colour accuracy. A darker
  warm-grey environment for contrast.
- **Light types.** 1 KEY (large), 2 STRIP (wide), 1 RIM (subtle), FILL.
- **Placement logic.** As White Gold, with radiance ratios × 0.7 and strip width 8–14°.
- **Important parameters.** *G* (critical); Kelvin; strip width; environment brightness.
- **Material considerations.** Saturation suffers from (a) clipping and (b) a bright, broad
  environment in reflections. Watch for green or dull shifts under cool light.
- **Camera considerations.** As White Gold.
- **Known limitations.** Perceived gold "richness" is partly tone mapping and image style,
  which are not scriptable for exposure [E4]. The preset can only manage what lights control.
- **Failure conditions.** Alloy not yellow → suggest a match. Metal material colour outside
  the plausible gold range → warn about the material, not the lighting.
- **Evaluation criteria.**
  - metal_clip_frac ≤ 0.02;
  - metal hue within the yellow-gold band;
  - chroma of mid-tones ≥ the threshold;
  - gradient energy above the floor.

## 7.9 Preset 6 — Rose Gold Studio

- **Objective.** Rose gold that reads unmistakably *rose*: distinct from yellow gold and from
  copper, with soft, flattering gradients.
- **Intended jewelry.** Rose gold rings, bracelets, mixed rose/white designs.
- **Required info.**
  - *Must:* metal.
  - *Recommended:* alloy = rose.
- **Initial strategy.** Archetype M with neutral 5000–5500 K. Warm light pushes rose toward
  copper, cool light toward a dull pink-grey. Soft wide strips, moderate radiance, and a
  neutral light-grey environment.
- **Light types.** As White Gold; FLAG optional.
- **Placement logic.** As White Gold; strip width 8–12°.
- **Important parameters.** Kelvin (narrow allowed range); *G*; strip width.
- **Material considerations.** Mixed-metal pieces (rose plus white) need a compromise of
  about 5500 K. Diagnostics check both hue bands.
- **Camera considerations.** As White Gold.
- **Known limitations.** Hue identity depends on the material colour definition. Lighting only
  preserves it.
- **Failure conditions.** Alloy not rose → suggest a match.
- **Evaluation criteria.** Metal hue within the rose band and outside the yellow band;
  metal_clip_frac ≤ 0.03; gradient energy above the floor.

**Preset 4/5/6 note.** These three presets share one archetype and differ only in a
*metal profile* (Kelvin, radiance multiplier, strip width, environment tone, hue targets).
They should be implemented as **one "Metal Studio" engine path with three profiles**,
auto-selected from the alloy classification, while keeping the three user-facing names.

## 7.10 Preset 7 — Multi-Stone Jewelry

- **Objective.** Every significant stone looks good, not just the largest one. Balance
  attention across stones and keep the metal readable.
- **Intended jewelry.** Three-stone rings, toi-et-moi, clusters, multi-stone pendants and
  necklaces, station pieces.
- **Required info.**
  - *Must:* ≥ 2 significant stones (or user tags).
  - *Recommended:* the stones' positions and sizes.
- **Initial strategy.** Archetype S. Sparkle and key target a **shared cone** covering all
  significant stones: the cone axis is the mean of the per-stone view vectors, and *k* is
  chosen so parallax ≤ 5°, or β is spread intentionally. Optionally one KICKER per stone
  beyond the second.
- **Light types.** 1 KEY, 5–8 SPARKLE (cap), 2 STRIP, 0–2 KICKER, 1 RIM.
- **Placement logic.** §6.4.4 multi-target cone; `D ≥ 11.5 · max|p_j − p_ref|` for tight
  parallax.
- **Important parameters.** *k*; sparkle count and β spread; per-stone kickers.
- **Material considerations.**
  - Mixed species (e.g. diamond with sapphire): the coloured stones need larger sources.
  - Keep "worst stone" metrics separated by species.
- **Camera considerations.** Necklaces and large pieces span a wide angle of view. Directions
  differ per stone even with a shared rig, so evaluate the worst stone.
- **Known limitations.** Large spatial spread plus close camera means one rig cannot be ideal
  for all stones. A lower-k compromise is inherent.
- **Failure conditions.** Significant stones span more than about 60° of the view → warn and
  suggest splitting into multiple shots or cameras.
- **Evaluation criteria.** **min over significant stones** of the stone score (doc 08); the
  spread between the best and worst stone ≤ the threshold; metal metrics as Solitaire.

## 7.11 Preset 8 — Intricate Jewelry

- **Objective.** Make fine detail legible: engraving, milgrain, filigree, openwork, textures.
  Lighting reveals relief and avoids hotspots that hide detail.
- **Intended jewelry.** Vintage and antique-style pieces, engraved bands, filigree pendants,
  signet rings.
- **Required info.**
  - *Must:* metal.
  - *Recommended:* user confirmation that detail is the priority (detail cannot be detected
    without mesh or material analysis).
- **Initial strategy.** Archetype D:
  - a **raking key** at a low grazing angle relative to the dominant surface (engraving
    relief appears as light/shadow pairs);
  - a larger, softer overall key at lower radiance;
  - fill to keep recesses from going black;
  - lower contrast targets.
- **Light types.** 1 KEY (soft), 1 KICKER (raking), 1–2 STRIP, 1 FILL.
- **Placement logic.**
  - Raking light: direction ω with an angle of about 70–80° to the dominant surface normal
    (plate proxy or band proxy at ψ facing the camera), placed on the side opposite the key.
  - KEY: size 40–50°.
- **Important parameters.** Raking angle; fill ratio; *G*.
- **Material considerations.**
  - Bump- or displacement-based engravings respond to lighting like geometry, but only if
    the shader uses them.
  - Very glossy metal makes detail read through reflections, not shading. Sometimes a less
    polished look reads better, but **the tool never changes materials**; it may suggest.
- **Camera considerations.** Raking direction is relative to the surface *and* the camera.
  Re-generate after camera changes.
- **Known limitations.** Without mesh access, the dominant surface is a proxy. Openwork
  (holes) needs a background that contrasts with the metal, which is an environment choice.
- **Failure conditions.** No metal → refuse. Projected detail too small (unknown without mesh)
  → rely on the user's choice.
- **Evaluation criteria.**
  - local contrast (high-frequency energy) in the metal region relative to a flat-lit
    baseline render, ≥ the threshold;
  - metal_clip_frac ≤ 0.02 (hotspots hide detail);
  - metal_crush_frac ≤ 0.08.

## 7.12 Preset 9 — Dark Luxury

- **Objective.** Dramatic, high-end mood: a near-black background, the piece carved out by rim
  and edge light, stones sparkling, metal glowing in controlled strips — and **metal never
  reading as black**.
- **Intended jewelry.** Hero and campaign images; high-jewelry; watches later.
- **Required info.** *Must:* the jewelry bounding box. *Recommended:* stones and metal roles.
- **Initial strategy.** Archetype K:
  - black cloned environment, brightness ≈ 0;
  - strong RIM pair behind;
  - narrow KEY;
  - **reflection cards**: STRIP modules reflection-placed so polished metal has something to
    reflect;
  - SPARKLE for stones.
- **Light types.** 2 RIM, 1 KEY (narrow), 2 STRIP, 3–5 SPARKLE.
- **Placement logic.**
  - RIM: α 120–150°, β ±60°.
  - KEY: α 40°, size 12–18°.
  - STRIP reflection-placed on the band or plate proxies.
  - Ground shadows off, or ground reflections on, as a style option.
- **Important parameters.** Rim radiance; strip radiance; key size; ground style.
- **Material considerations.**
  - Mirror metal + black environment = black metal. Strips are mandatory.
  - Gold on black needs mid-tone reflections to show colour.
- **Camera considerations.** Rims depend strongly on the camera (they must sit behind the
  subject relative to the camera), so re-generate after camera changes.
- **Known limitations.** Pure-black backgrounds expose noise in dark gradients. Fine
  silhouettes may need higher samples.
- **Failure conditions.** If no metal or stone surface can be reflection-targeted (unknown
  geometry), warn that metal may read dark.
- **Evaluation criteria.**
  - background mean luminance ≤ 0.03;
  - silhouette_contrast ≥ the threshold (rim present along ≥ 40% of the silhouette);
  - metal_crush_frac ≤ 0.25 (dark is allowed, black is not);
  - stone metrics as Diamond Brilliance (relaxed).

## 7.13 Preset 10 — E-commerce Packshot

- **Objective.** Clean, consistent, colour-accurate catalogue images: a pure white background
  (marketplace main-image rules commonly call for pure white RGB 255,255,255; Amazon's is
  the usual example, not re-verified in this research pass), soft contact shadow, neutral light, readable metal and stones, and **the same look across many
  products**.
- **Intended jewelry.** Every type, for catalogue and marketplace listings.
- **Required info.** *Must:* the jewelry bounding box. *Recommended:* alloy (to choose a metal
  profile), stones.
- **Initial strategy.** Archetype E:
  - large soft KEY and FILL;
  - white cloned environment;
  - ground shadows on;
  - neutral 5500–6500 K;
  - STRIP for metal form;
  - **FLAGs** to stop polished metal from vanishing into white reflections;
  - modest SPARKLE.
- **Light types.** 1 KEY (large), 1 FILL, 2 STRIP, 0–2 FLAG, 2–3 SPARKLE.
- **Placement logic.** KEY α 30°, β 0°, size 40–50°; FILL α 50°, β 180°; FLAGs
  reflection-placed to put dark lines at the band edges.
- **Important parameters.** Background white level (environment brightness vs background
  colour); *G*; flag strength.
- **Material considerations.** White metal on white needs flags, or it disappears. Gold needs
  clipping protection, as in Preset 5.
- **Camera considerations.** Catalogue work uses a **fixed camera template per product
  type**. The preset's real value is applying *the same* rig, scaled, across SKUs via look
  files (doc 06 §6.8).
- **Known limitations.**
  - A pure white background with a soft shadow may need the image style or background colour
    rather than lights. Background colour is scriptable (`Env.setBackgroundColor`) [E1].
  - Marketplace rules vary by channel and change over time; check the target channel's
    current rules.
- **Failure conditions.** If the background cannot reach ≥ 99% pure white without clipping the
  metal, warn and suggest an alpha-channel render (`setOutputAlphaChannel`) plus compositing.
- **Evaluation criteria.**
  - bg_white_frac ≥ 0.995;
  - metal_clip_frac ≤ 0.03;
  - colour neutrality (mean background a\*, b\* ≈ 0; metal hue in the alloy band);
  - **catalogue consistency**: the variance of exposure and metal metrics across a batch of
    SKUs below the threshold.

---

## 7.14 Do ten distinct presets delay the MVP?

**Yes, if they are built as ten separate rule sets.** Most of the engineering and calibration
effort sits in the *modules* and *metrics*, not in the preset names. Recommended sequence:

1. **Engine plus three archetypes first:** S (as Solitaire Ring), M (as White / Yellow / Rose
   via profiles) and E (Packshot). Between them they cover every module except the raking
   KICKER and the Dark-mood environment.
2. **Validate with artists** on the benchmark (doc 12, Phase 3 gate).
3. **Then** express Diamond Brilliance, Pavé and Multi-Stone as S-profiles, Dark Luxury as K,
   and Intricate as D. Each is mostly parameters, plus one or two module behaviours.

This delivers ten user-facing presets with about **five** maintained behaviours, and lets
calibration findings from the first three improve all ten.
