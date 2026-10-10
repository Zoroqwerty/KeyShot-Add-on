"""Aggregate spike logs (~/JLE_Spike/results/*.jsonl) into SUMMARY.md. Plain CPython, no KeyShot needed.

Usage:  python3 summarize.py [results_dir]
"""

import collections
import glob
import json
import os
import statistics
import sys


def load(results_dir):
    records = []
    for path in sorted(glob.glob(os.path.join(results_dir, "*.jsonl"))):
        meta = {}
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if r.get("kind") == "meta":
                    meta = r
                r["_version"] = str(meta.get("getKeyShotVersion", "unknown"))
                r["_file"] = os.path.basename(path)
                records.append(r)
    return records


def summarize(records):
    runs = collections.Counter()
    checks = collections.defaultdict(lambda: [0, 0])
    failed_calls = collections.defaultdict(collections.Counter)
    cost = collections.defaultdict(list)
    highlight = collections.defaultdict(list)
    for r in records:
        key = (r["experiment"], r["_version"])
        kind = r.get("kind")
        if kind == "summary":
            runs[key] += 1
        elif kind == "check":
            checks[key + (r["label"],)][0 if r["passed"] else 1] += 1
        elif kind == "call" and not r.get("ok"):
            failed_calls[key + (r["label"],)][r.get("error", "?")[:160]] += 1
        elif kind == "preview_cost":
            cost[(r["_version"], r["size"], r["samples"])].append(r)
        elif kind == "highlight":
            errs = [e for e in (r.get("error_rel_width") or {}).values() if e is not None]
            if errs:
                highlight[(r["_version"], tuple(r["size"]))].append(min(errs))

    out = ["# JLE spike results", "",
           "Generated from %d log records. Pass counts are runs, not cases." % len(records), ""]
    out += ["## Runs per experiment", "", "| Experiment | KeyShot version | Completed runs |", "|---|---|---|"]
    for (exp, ver), n in sorted(runs.items()):
        out.append("| %s | %s | %d |" % (exp, ver, n))

    out += ["", "## Checks", "", "| Experiment | Version | Check | Passed | Failed |", "|---|---|---|---|---|"]
    for (exp, ver, label), (p, f) in sorted(checks.items()):
        flag = " **⚠**" if f else ""
        out.append("| %s | %s | %s%s | %d | %d |" % (exp, ver, label.replace("|", "/"), flag, p, f))

    out += ["", "## Failed KeyShot calls (findings, or harness bugs: read the trace)", "",
            "| Experiment | Version | Call | Count | Error |", "|---|---|---|---|---|"]
    for (exp, ver, label), errors in sorted(failed_calls.items()):
        for err, n in errors.most_common(3):
            out.append("| %s | %s | %s | %d | %s |" % (exp, ver, label.replace("|", "/"), n,
                                                       err.replace("|", "/")))

    if cost:
        out += ["", "## Preview cost (E4)", "",
                "| Version | Size | Samples | Renders | Median render s | Median CV mean-lum |",
                "|---|---|---|---|---|---|"]
        for (ver, size, samples), rows in sorted(cost.items()):
            renders = [x["render_s"] for row in rows for x in row["runs"]]
            cvs = [row["cv_mean_luminance"] for row in rows if row.get("cv_mean_luminance") is not None]
            out.append("| %s | %d | %d | %d | %.2f | %s |" % (
                ver, size, samples, len(renders), statistics.median(renders) if renders else float("nan"),
                "%.3f" % statistics.median(cvs) if cvs else "n/a"))

    if highlight:
        out += ["", "## Highlight placement error (E3, fraction of image width)", "",
                "| Version | Size | Samples | Median | Worst |", "|---|---|---|---|---|"]
        for (ver, size), errs in sorted(highlight.items()):
            out.append("| %s | %dx%d | %d | %.4f | %.4f |" % (ver, size[0], size[1], len(errs),
                                                            statistics.median(errs), max(errs)))
    return "\n".join(out) + "\n"


def main():
    results_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.expanduser("~"), "JLE_Spike", "results")
    text = summarize(load(results_dir))
    path = os.path.join(results_dir, "SUMMARY.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)
    print("written:", path)


if __name__ == "__main__":
    main()
