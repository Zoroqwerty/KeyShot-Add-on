"""Smoke test: every experiment runs end-to-end against the fake lux without a harness crash.

Run on its own (it swaps lux into sys.modules):  python3 -m unittest tests.test_experiments_smoke
"""

import importlib
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)


class SmokeTest(unittest.TestCase):
    def setUp(self):
        import fake_lux
        lux, luxmath = fake_lux.build_modules()
        sys.modules["lux"], sys.modules["luxmath"] = lux, luxmath
        self.tmp = tempfile.mkdtemp()
        os.environ["JLE_SPIKE_OUT"] = os.path.join(self.tmp, "results")
        import jle_spike.common
        import jle_spike.experiments
        self.C = importlib.reload(jle_spike.common)
        self.E = importlib.reload(jle_spike.experiments)

    def tearDown(self):
        sys.modules.pop("lux", None)
        sys.modules.pop("luxmath", None)

    def test_all_experiments_complete(self):
        cfg = self.C.load_config()
        cfg.update({"repeats": 1, "e4_sizes": [32], "e4_samples": [4], "e4_repeats": 2,
                    "variants": {"E1": [{}, {"e1_variant": {"geometry_units": 1000}}]}})
        results = self.E.run(list(self.E.EXPERIMENTS), cfg)
        aborted = {k: v for k, v in results.items() if "aborted" in v}
        self.assertEqual(aborted, {}, aborted)
        self.assertEqual(len(results), len(self.E.EXPERIMENTS) + 1)
        # every log line must be valid JSON
        out = os.environ["JLE_SPIKE_OUT"]
        for name in os.listdir(out):
            if name.endswith(".jsonl"):
                with open(os.path.join(out, name)) as f:
                    for line in f:
                        json.loads(line)

    def test_refuses_foreign_scene(self):
        lux = sys.modules["lux"]
        import fake_lux
        root = lux.getSceneTree()
        root.children.append(fake_lux.SceneNode("customer_ring", 2, parent=root))
        cfg = self.C.load_config()
        results = self.E.run(["E1"], cfg)
        self.assertIn("Scene is not empty", list(results.values())[0]["aborted"])
        self.assertEqual(root.children[0].name, "customer_ring")


if __name__ == "__main__":
    unittest.main()
