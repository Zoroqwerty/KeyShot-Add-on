# 4. Jewelry Optics Research Summary

This section explains the physics the lighting engine must respect, and where that physics
limits the product. Numeric constants are labelled:

- **[Computed]**: derived here from a stated formula.
- **[Cited]**: from a source listed in [sources.md](sources.md).
- **[Common reference value — verify]**: widely published, but not re-verified in this
  research pass.

## 4.1 Vocabulary: brightness is not brilliance

GIA's cut-grading research (Moses et al., *Gems & Gemology*, Fall 2004) defines the
appearance terms that matter here [Cited]:

- **Brightness**: the total light returned to the viewer. GIA uses this in place of the older,
  vaguer word "brilliance".
- **Fire**: light dispersed into spectral colours, seen face-up.
- **Scintillation**: two parts.
  - **Sparkle**: spots of light that flash as the stone, viewer or light moves.
  - **Pattern**: the relative size, arrangement and contrast of bright and dark areas.

GIA grades brightness, fire and scintillation *together*, alongside design and
craftsmanship factors. **A stone that is bright everywhere has no pattern contrast and looks
glassy.** That is why image brightness on its own is the wrong objective (see
[08](08-automatic-optimization.md)).

In a **still image**, sparkle becomes "many small, very bright points" and the pattern
becomes "the bright/dark facet mosaic". Both can be measured in a render. Sparkle *over time*
only exists in animation, which is out of MVP scope.

## 4.2 Diamond constants and light transport

| Quantity | Value | Label | Consequence for rendering |
|---|---|---|---|
| Refractive index *n* (589 nm) | ≈ 2.417 | [Cited] | Strong refraction and strong surface reflection |
| Critical angle θc = arcsin(1/n) | ≈ 24.4° | [Computed] | Most light hitting the pavilion from inside is totally internally reflected, so diamonds "trap and redirect" light |
| Normal-incidence reflectance R₀ = ((n−1)/(n+1))² | ≈ 0.172 (17%) | [Computed] | The table alone mirrors ~17% of what is in front of it. Glass (n = 1.5) mirrors ≈ 4%. Diamonds show light sources *on their surface* as well as through them. |
| Dispersion (B–G interval) | 0.044 | [Common reference value — verify] | Fire. Needs small, intense sources and darkness around them. |
| KeyShot dispersion control | **Abbe number**: 0 = off; lower = more dispersion. The KeyShot manual suggests 35–55 as a start for subtle dispersion. | [Cited] | A material check can flag "Abbe = 0 on a diamond" |
| Other stones (approximate) | Sapphire/ruby n ≈ 1.76–1.78 [Cited]; moissanite n ≈ 2.65, dispersion ≈ 0.10; cubic zirconia n ≈ 2.15–2.18 | [Common reference value — verify] | Lower-n stones (sapphire, emerald) return less light by total internal reflection. They need different contrast targets and are shown more by body colour than by sparkle. |

**Light path in a well-cut brilliant.**

1. Light enters through the crown and table.
2. It hits the pavilion facets beyond θc and is totally reflected.
3. It reflects again from the opposite pavilion side.
4. It exits through the crown, toward the viewer.

Proportions determine whether this works. Tolkowsky's 1919 model is the widely cited
reference: about 53% table, about 34.5° crown angle, about 40.75° pavilion angle
[Common reference value — verify]. Too shallow or too deep a pavilion lets light leak out,
giving a "fish-eye" or "nail-head" look.

**Rendering consequence: dark facets are often geometry or render settings, not lighting.**
Each extra internal bounce is a ray bounce. If KeyShot's ray-bounce limit is reached, the
path terminates and renders black. KeyShot's "Jewelry" lighting preset raises ray bounces and
enables caustics [Cited]. The engine must check render settings *before* blaming or
adjusting lights (experiment E9).

**"Caustics" here means something specific.** In KeyShot's sense, caustics are light paths
that go through or off specular surfaces *onto diffuse surfaces*: coloured light patterns on
metal or the ground. A diamond's own face-up appearance (camera → facets → light source) is
governed by ray bounces and the gem material, not by the caustics setting. Caustics matter for
ground and metal glow, cost render time and are noisy in previews. They are an *aesthetic
option*, not a requirement for good stones.

## 4.3 What a diamond "sees": environment sampling and camera dependency

Seen from the camera, each pixel inside a stone corresponds to a ray that bounces through the
facets and leaves the stone in some *world direction*. The stone's appearance is therefore an
image of the *lighting environment*, re-ordered by the facet geometry. Three consequences:

1. **What surrounds the camera matters most.** For a face-up view, most exit directions of a
   well-cut brilliant lie in a cone around the viewing direction. GIA's analysis and common
   tools such as AGS's ASET describe this by angular bands and an "obstruction" zone around
   the viewer [Common reference value — verify specifics]. **Lights in a cone around the
   camera axis drive brightness. Darkness near the axis, standing in for the photographer's
   head and camera, drives pattern contrast.** In a render the camera blocks nothing, so this
   contrast must be *created deliberately*, with a dark environment or black flags.
2. **The appearance changes sharply with the camera.** A few degrees of camera rotation
   reshuffles the facet mosaic. A rig is designed *for a camera*, and good results from other
   cameras are not guaranteed (see [09](09-failure-mode-analysis.md), F-13).
3. **The relationship is measurable without theory.** Sweep a single small light over a grid
   of directions in camera space and record the stone region's response. This gives an
   **angular response map** for each cut family. These maps (Phase 3/4 experiment) turn
   gemology into data-driven placement rules without any ML (see
   [06](06-lighting-engine-architecture.md) §6.5).

## 4.4 Cut families: what lighting can and cannot do

| Cut | Optical character | Lighting implication | Lighting cannot fix |
|---|---|---|---|
| **Round brilliant** | Radial symmetry; arrows pattern; most robust to light direction | A ring of small sources around the camera axis plus a soft overhead key; symmetric gaps give a balanced pattern | Poor CAD proportions (leakage) |
| **Princess** (square brilliant) | Chevron / X pattern; corners can go dark | Add corner-diagonal sparkle sources; avoid relying on one axis | Corner leakage from geometry |
| **Oval, pear, marquise** (elongated brilliants) | **Bow-tie**: a dark band across the centre, set by pavilion angles along the long axis | Light from the directions the bow-tie region "sees" (from the angular response map) can *soften* it. Lights positioned along the long axis matter. | The bow-tie itself is geometry. Removing it entirely looks fake. |
| **Emerald / Asscher** (step cuts) | "Hall of mirrors": broad, parallel flashes; little fire; shows clarity | **Long linear sources and strong dark bands**; fewer, larger sources; contrast over sparkle | Inclusion modelling; the absence of fire is correct |
| **Cushion, radiant, others** | Mixed | Treat as closest family; validate via response map | — |

**MVP implication.** The cut family **cannot be inferred from KeyShot's API**: there is no mesh
access. The MVP asks the user, with "Round" as the default. Automatic classification
requires mesh export (Phase 4, gated).

## 4.5 Light-source size, shape, position, orientation and intensity

| Property | Effect on stones | Effect on polished metal |
|---|---|---|
| **Angular size** (as seen from the piece) | Large → bright, soft facets, less fire, less pattern. Small → crisp sparkles and fire flashes, more dark area. | Sets highlight size. Large sources make broad smooth gradients; small ones make specular dots. |
| **Shape** | Strips produce linear flashes, which are good for step cuts | Strips trace curvature, which is the classic way to show a band's shape. Rectangles appear as "windows". |
| **Direction relative to the camera** | Near the camera axis → face-up return. Behind the subject → rim and edge light. Below → lights the pavilion directly, an unnatural "backlit" style. | Mirror rule: a highlight appears where the surface normal bisects camera and light directions |
| **Orientation of the emitter** | Area lights emit toward their normal. A light facing away is seen from behind: dark if single-sided. | Same |
| **Radiance** (brightness per area per solid angle) | Sets sparkle and facet brightness. Clipping small sparkles is acceptable. | **Sets highlight brightness regardless of distance.** Clipping broad metal areas destroys gold colour and form. |
| **Distance** | Affects parallax: near lights give each stone a different highlight (variety); far lights behave like an environment (uniformity) | Irrelevant for highlight brightness, which is radiance-driven. Relevant for *diffuse* fill falloff. |

**Key physical principle.** For mirror-like reflections, what the camera sees is the source's
**radiance** (brightness) over its **solid angle** (size), mapped by the surface. Neither
depends on distance once angular size is fixed. **A preset written in angular size and
radiance therefore scales to any jewelry size.** KeyShot's area-light **Lux** unit (emittance
per m², constant as the light is resized [Cited]) behaves like constant radiance for a
diffuse emitter. That makes it the right unit for reflection-driven lights (to be confirmed
by E14).

## 4.6 Metals and how they interact with gemstone lighting

- Polished precious metals are near-mirror conductors. They show *images of their
  surroundings*. **On a black background with no reflection cards, polished metal renders
  black.** Every "dark luxury" setup needs reflection cards.
- Metal colour comes from wavelength-dependent reflectance. Yellow and rose gold show their
  hue in *mid-tone* reflections. **Clipped highlights turn white and wash out the gold
  colour.** Overexposed gold is a lighting-radiance problem.
- The two needs conflict:

  | Stones want | Metal wants |
  |---|---|
  | Small, high-radiance sources plus darkness near the view axis | Large, graded sources and few dark voids |

  Resolve this by giving light modules separate roles. Large gradient sources go at side and
  low angles, where metal surfaces reflect them toward the camera but the stone's face-up
  response is weak. Small sparkle sources go near the axis. KeyShot 2025.2 **Light Layers**
  could separate them fully, but they are not scriptable as far as is documented.
- **Colour temperature.**

  | Metal | Effect |
  |---|---|
  | White gold / platinum | Warm lights make it look yellowish |
  | Yellow gold | Cool lights make it look dull or greenish |
  | Rose gold | Warm lights push it toward copper |

  For **e-commerce colour accuracy**, use neutral, near-daylight sources and leave stylistic
  warmth to presets that are explicitly stylistic.

## 4.7 Roughness and surface finish

- **Polished** (low roughness): sharp images of the sources. The rectangle edges of softboxes
  are visible, so their shape and gradients are art-directed.
- **Satin / brushed** (anisotropic): highlights stretch across the brushing direction. Light
  direction relative to the brushing matters, and the brushing direction cannot be read
  without material parameters.
- **Hammered, textured or sandblasted**: highlights break up or spread. These are forgiving,
  and broader and more frontal lighting reads better.
- **Micro-imperfections** (scratch or fingerprint maps) show only inside highlights. They are a
  material choice, not a lighting one.

## 4.8 Model defects that lighting cannot solve

| Defect | Typical symptom | Detectable via API? | Response |
|---|---|---|---|
| Stones and metal merged into one mesh (common in STL exports) | Gem material cannot be assigned, so the "stone" looks like metal | Partly: one object with a metal material where stones are expected | Explain; ask the user to separate them in CAD or KeyShot |
| Gem with inverted normals or an open (non-watertight) mesh | Black, glassy or "hollow" stone | No (needs mesh) | Mesh check in Phase 4; MVP lists it as a likely cause |
| Duplicated or overlapping stones | Muddy or dark stones, noise | Yes, heuristically: near-identical stone bounding boxes | Warn |
| Stone intersecting prongs or seat | Dark wedges, odd refraction | Partly: bounding-box overlap is weak evidence | Warn only with high confidence |
| Coplanar overlapping surfaces | Noisy speckles | No | — |
| Coarse tessellation of curved metal | Faceted, jagged highlights. Strip lights make this *worse*. | Partly: triangle count vs size | Suggest re-import at higher tessellation |
| Wrong scale (e.g. ring 2 m wide) | Wrong depth of field, wrong light falloff, odd ground shadows | Yes: bounding box vs plausible jewelry sizes | Warn; never rescale automatically |
| Unrealistic CAD stone proportions | Leakage and dark patterns | No (needs mesh plus analysis) | Explain in diagnostics |
| Wrong material values (IOR 1.5 on a "diamond", Abbe 0) | Glassy stone, no fire | Yes: read gem material parameters | Warn, with a one-click explanation. **Do not change user materials silently.** |
| Too few ray bounces, caustics off | Dark facets | Yes: render options | Offer the "Jewelry" lighting preset as an explicit, reversible option |

## 4.9 Physically accurate vs commercially pleasing

Real jewelry photography is not a single physical capture. It uses black and white cards,
diffusion tents, focus stacking, multi-exposure composites, and retouched sparkle and fire.
Renders can "cheat" in ways a studio cannot: lights invisible to the camera, lights that
affect only some parts, an infinite dark void.

The product goal is **photographic plausibility with commercial clarity**:

- stones show a crisp bright/dark pattern with some fire;
- metal shows clean, continuous gradients and correct colour;
- the piece separates from the background.

Physically complete studio simulation is a non-goal. Camera-invisible lights are allowed and
expected.

## 4.10 What can be inferred, and from what

| Characteristic | Scene API: tree, names, bounding boxes | Mesh export (Phase 4) | Material info | Needs user input |
|---|---|---|---|---|
| Overall size and scale | ✔ bounding box plus scene units | ✔ | — | Only if implausible |
| Jewelry type (ring / pendant / earring / bracelet / necklace) | ◐ aspect ratios, a ring's hole axis, part counts | ✔ | — | Confirm (one click) |
| Stone vs metal parts | ◐ size and shape only | ◐ closed, planar-faceted solids | ✔ shader type (`lux_gem`, `lux_metal`) | When unassigned or merged |
| Hero stone | ✔ if stones are separate parts (largest stone bounding box) | ✔ | ◐ | If ambiguous (e.g. three similar stones) |
| Stone count / pavé cluster | ✔ if separate parts | ✔ connected components | ◐ shared material | For merged meshes |
| **Cut family** | ✘ | ✔ facet-normal analysis | ✘ | **Yes in MVP** (dropdown, default Round) |
| Table orientation | ◐ ring-centre-to-stone vector heuristic | ✔ | ✘ | Optional override |
| Gem species | ✘ | ✘ | ✔ IOR, colour, name | If generic material |
| Metal alloy (YG / WG / RG / Pt) | ✘ | ✘ | ✔ colour, name | If unassigned |
| Finish (polished / satin / brushed) | ✘ | ✘ | ✔ roughness, shader type | Rarely |
| Engraving, milgrain, filigree | ✘ | ◐ curvature statistics | ◐ bump or displacement nodes | **Yes** (choose "Intricate") |
| Mesh defects (normals, holes, intersections) | ✘ (except scale and duplicates) | ✔ | — | — |
| Shot purpose and mood (catalogue, hero, dark) | ✘ | ✘ | ✘ | **Yes** (preset choice) |
| Camera set for multi-view | ✔ cameras API | — | — | Choose which cameras |

✔ reliable · ◐ heuristic or partial · ✘ not possible

## 4.11 Problems lighting alone cannot solve (must be diagnosed, not "fixed")

1. Wrong or missing gem material (IOR, dispersion, colour, transparency).
2. Bad mesh: inverted normals, open shells, intersections, duplicates, merged materials.
3. Unrealistic cut proportions in CAD stone libraries.
4. Ray-bounce limits, caustic settings, and the CPU vs GPU feature gap.
5. Noise from too few samples, especially with dispersion.
6. Coarse tessellation of curved metal.
7. Tone mapping and image style (exposure, curves, bloom, denoise) choices.
8. Camera: depth of field, focal length, an unflattering angle.
9. Post-production expectations such as retouched star sparkles.
10. Physical impossibility, e.g. demanding maximum fire *and* maximum brightness in the same
    stone from the same view.

**The product promise must exclude these explicitly.** The diagnostics layer should name them
so artists do not blame the lighting tool.
