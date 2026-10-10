# Phase 1 spike harness

Throw-away test code for the experiments in
[docs/feasibility/03](../docs/feasibility/03-critical-unknowns-and-experiments.md). It finds out
what KeyShot **actually** does. It is not product code.

**Status: written without access to KeyShot.**
- The pure-Python parts (geometry, maths, PNG decoding, summary) are unit-tested.
- The experiment code has been smoke-tested only against a *fake* `lux` module, which proves
  that it has no Python-level bugs, nothing more.
- The first real run on your Mac is the real test.

## Safety

- Every experiment **refuses to run** unless the scene is empty, or contains only objects
  named `JLESPIKE…`. Your work is never cleared. Save it, then open a new empty scene first.
- Output goes to `~/JLE_Spike/results` (logs) and `~/JLE_Spike/scratch` (OBJ files, renders,
  one saved `.bip`).
- E2 writes into your material library **only** if you set `kmp_path` in `config.json`. It
  then imports into a folder called `JLE_Spike`, which you can delete afterwards.
- E6 saves the spike scene to `~/JLE_Spike/scratch/*.bip` and re-opens it, replacing the
  spike scene, never yours.

## Install on the Mac

1. In KeyShot, open **Edit › Preferences › Folders** and note the **Scripts** folder.
2. Copy these into that folder:
   - the `jle_spike/` directory;
   - `JLE Spike - Run All.py`;
   - `config.json`.
3. Restart KeyShot, or re-open the Scripting window. The script appears in the **Scripts** tab
   (Window › Scripting Console).

Alternatively, keep the files in this repo and set `JLE_SPIKE_HOME` to the `spike/` path
(headless runs do this automatically).

## Run (GUI)

1. **File › New** (empty scene).
2. First run E0 only. Set `"experiments": ["E0"]` in `config.json`, then run
   **JLE Spike - Run All**. This dumps the real API of your KeyShot version and diffs it
   against 2023.2.
3. Then run the rest (`E1`, `E2`, `E3`, `E6`, `E7`). Use `E4` once the rest works; it renders a
   lot.
4. `python3 summarize.py` writes `~/JLE_Spike/results/SUMMARY.md`.

## Run many times (headless)

```bash
KEYSHOT_HEADLESS="<KeyShot headless executable>" ./run_headless.sh 20 E1,E2,E3,E6,E7
```

The executable path and flag format for macOS are **not verified**. Check the KeyShot manual
page *Headless Scripting* and set `KEYSHOT_HEADLESS_ARGS` if the flag is not `-script`. Each
run is a fresh KeyShot process, so each run also starts from a fresh scene.

## How many runs are actually useful

For these API questions, repeating the *same* test does not add confidence. The answer
is the same every time. Confidence comes from **varying the conditions**:

- different import options (`variants` in `config.json`);
- scene units;
- CPU vs GPU;
- KeyShot versions;
- real jewelry files instead of the synthetic ring.

Repeats matter only for **render-based measurements** (E3 highlight error, E4 cost and noise),
where results are noisy.

`config.json` already expands E1 into 6 variants, and E3 into 10 renders per run. A headless
loop of 20 runs gives roughly 200–300 test cases, but treat it as a matrix, not as 300 copies.

## What is automated vs manual

| Experiment | Automated here | Still manual |
|---|---|---|
| E0 API inventory | ✔ (`dir`, `help`, diff vs 2023.2, keyword search for light/primitive/layer APIs) | — |
| E1 light hosts via OBJ import | ✔ (scene diff, node structure, axis/scale fit, `duplicate`) | Count undo steps |
| E2 light materials | ✔ routes (a) graph rebuild and (c) bundled library light; parameter dump and set/read-back; independence; emission render | Route (b): build `JLE_Lights.kmp` in the GUI and set `kmp_path` |
| E3 placement maths | ✔ mirror placement on a chrome sphere, two aspect ratios, FOV axis; transform semantics | Visually confirm the renders in `scratch/` |
| E4 preview cost | ✔ time and noise per size and sample count | Run on each hardware tier |
| E6 / E13 delete, save, identity | ✔ soft delete, `deleteMaterial` (scene only), save re-target, IDs across reload | Undo behaviour (press undo after the run) |
| E7 non-destructive restore | ✔ environment clone, lighting-preset round trip, render-options isolation, unsaved camera | — |
| E5, E8, E9, E10, E11, E12, E14 | not yet | Next iteration, after E0–E3 results |

## Developer checks (no KeyShot needed)

```bash
cd spike
python3 -m unittest tests.test_common
python3 -m unittest tests.test_experiments_smoke   # run separately: it swaps in a fake lux
```
