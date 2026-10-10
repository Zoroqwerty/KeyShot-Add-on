# Jewelry Light Engine: Phase 1 spike runner (doc 03).
# Run from KeyShot's Scripting window (Scripts tab) in a NEW, EMPTY scene, or headless.
# Which experiments run: "experiments" in config.json, or env JLE_SPIKE_EXPERIMENTS="E1,E2".
import importlib
import os
import sys


def _home():
    if os.environ.get("JLE_SPIKE_HOME"):
        return os.environ["JLE_SPIKE_HOME"]
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except NameError:  # some script hosts do not define __file__
        import lux
        return lux.getKeyShotFolder(lux.FOLDER_SCRIPTS)


sys.path.insert(0, _home())
import jle_spike.common  # noqa: E402
import jle_spike.experiments  # noqa: E402

importlib.reload(jle_spike.common)
importlib.reload(jle_spike.experiments)

_cfg = jle_spike.common.load_config()
_names = os.environ.get("JLE_SPIKE_EXPERIMENTS")
_names = _names.split(",") if _names else _cfg.get("experiments", ["E0", "E1", "E2", "E3", "E6", "E7"])
_results = jle_spike.experiments.run([n.strip() for n in _names if n.strip()], _cfg)
print("JLE spike finished. Logs in", jle_spike.common.results_dir())
for _k, _v in _results.items():
    print(" ", _k, _v)
