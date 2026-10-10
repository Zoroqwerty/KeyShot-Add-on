# 11. MVP Scope and Exclusions

## 11.1 MVP definition

> An offline KeyShot script package that, for a selected jewelry piece and the active camera,
> generates an **editable rig of native KeyShot area lights** from one of ten presets (built
> on five archetypes). It identifies stone and metal parts automatically where it can, and
> manually where it cannot. It explains each light, preserves the artist's edits on
> regeneration, can be removed without trace, and runs a **one-preview diagnostic** of the
> result. It is supported on an explicitly tested set of KeyShot versions.

## 11.2 Requirements: essential vs deferred

| Requirement (from the brief) | MVP decision | Notes |
|---|---|---|
| Offline operation after installation | **Essential** | stdlib-only; offline licence file; E12 |
| Ten initial presets | **Essential as user-facing presets; implemented as 5 archetypes** | Ship the three validated archetypes first (S, M, E), then the rest as profiles. A release with 3 validated archetypes / 6 presets is acceptable if the other 4 are not validated in time. **Quality beats count.** |
| Editable physical KeyShot lights | **Essential** | Area lights, Lux units; planar only if scriptable |
| Geometry-aware initial placement | **Essential (coarse)** | Bounding boxes, roles, ring and plate proxies, reflection placement, collision and frustum checks |
| Diamond and metal components | **Essential** | Stone and metal roles; hero, secondary and pavé from separate parts |
| Manual component identification | **Essential** | Tag selection as…; model memory |
| Yellow, white and rose gold | **Essential** | Metal Studio profiles; alloy auto-classification with confirmation |
| Adjustable position, orientation, size, intensity | **Essential** | Native KeyShot tools; overrides detected |
| Save and restore | **Essential** | Sidecar plus backup; look files |
| Safe regeneration and removal | **Essential** | G/A/O/L state model; apply plans; remove-rig verification |
| Preservation of existing scene state | **Essential** | Allow-list guard; environment clone; consented scene actions |
| Compatibility with explicitly tested versions | **Essential** | Proposal: 2025.3 and 2026.2, Windows and macOS (decided after E0/U1) |
| Diagnostics (pre-flight checks plus one-preview metrics) | **Essential** | Without this, many failures are blamed on the tool (doc 09 §9.3) |
| Single-view automatic optimization | **Deferred → v1.1** | Gated by E4/E5 cost and stability |
| Multi-view evaluation (diagnostics across cameras) | **Should** (v1.0 if time allows) | Renders N cameras, reports the worst view; no optimization |
| Multi-view optimization | **Deferred → v1.2+** | |
| Per-shot rigs via Studios / model sets | Deferred | |
| HTML browser UI | **Should** | MVP may ship with `getInputDialog` UI if E10 shows the browser dialog is unreliable |
| Mesh export analysis (cut classification, table normal, merged-mesh splitting) | Deferred (gated by the doc 05 §5.9 experiment) | |
| Angular response maps per cut | Phase 3/4 data work; used if ready | Improves sparkle placement; not a blocker |
| Black flags (negative fill) | Should | Depends on creating a black material (E2) |
| Light Layers integration | Excluded | No documented API |
| HDRI pin generation / HDR image synthesis | Excluded | Not editable as pins; possible later "environment add-on" |
| Animation / turntables / scintillation over time | Excluded | |
| Watches, electronics, general products | Excluded | Architecture allows it later (archetypes and modules) |
| Machine learning | Excluded | See doc 06 §6.10 |
| Batch processing of many SKUs (GUI loop or headless) | Deferred → v1.1 | Strong commercial angle; validate demand first |
| Automatic material fixes | **Excluded by principle** | Suggest only; never modify user materials |

## 11.3 Supported-case statement (to publish with the MVP)

**Supported:** single-piece scenes with separate stone and metal parts and reasonable
materials, for these types:

- solitaire, halo, three-stone and pavé rings;
- stud and drop earrings;
- pendants;
- simple bracelets;
- necklaces with fewer than about 60° of angular spread in the frame.

**Supported with manual tagging:** generic names, unassigned materials, scenes with props.

**Limited:** merged stone-and-metal meshes (jewelry-level lighting only); very complex
assemblies; chains with thousands of links (performance unknown until E4).

**Unsupported:** fixing broken gem geometry or materials; animation; non-jewelry.

## 11.4 Out-of-scope guarantees (stated plainly to users)

- The tool does **not** guarantee that diamonds look good if the model or materials are wrong.
  It **tells** you when it suspects this.
- The tool does **not** guarantee that a rig looks good from cameras it was not generated for.
  It can **check** them.
- "Automates ~90%" is **not** a launch claim unless doc 12's validation supports it, and then
  only for the measured case categories.

## 11.5 Recommended development sequence (replaces "build ten presets")

1. **Spike** (doc 03).
2. **Engine core:** adapter, analysis T0–T4, generator, realizer, state.
3. **Archetype S** as *Solitaire Ring*, plus diagnostics. Artist review cycle 1.
4. **Archetype M** (three metal profiles) and **Archetype E** (Packshot). Artist review
   cycle 2. **Phase 3 gate.**
5. Profiles: Diamond Brilliance, Pavé, Multi-Stone (S); Dark Luxury (K); Intricate (D). Artist
   review cycle 3.
6. Hardening, offline install, version matrix, beta.
7. v1.1: single-view optimizer and batch look application, if gates pass.
