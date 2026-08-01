"""Collect one A/B run into a CSV row, and summarise the finished CSV.

Two modes, both driven by run.sh:

  collect.py <out_dir> <variant> <rep>   -> one CSV row on stdout
  collect.py --summarize <results.csv>   -> a per-variant table with the spread across reps

The spread matters more than the means here. spec-eval has never measured its own run-to-run noise on a fixed
artifact (`spec-reports/runs.jsonl` carries no same-SHA repeat), so the baseline reps in this experiment ARE that
missing noise floor. A variant's delta is only meaningful once it is larger than the baseline's own spread.
"""
import os
import sys
import json


def _load(path):
    try:
        return json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        return []


def _severities(items, key):
    """Count severity labels in a record list, tolerating the grader's unparseable-reply shape."""
    out = {}
    for rec in items:
        for entry in rec.get(key, []) or []:
            sev = str(entry.get("severity", "?")).lower()
            out[sev] = out.get(sev, 0) + 1
    return out


def row(out_dir, variant, rep):
    suff = _load(os.path.join(out_dir, "sufficiency.json"))
    find = _load(os.path.join(out_dir, "findings.json"))
    scores = [r["sufficiency"] for r in suff if r.get("sufficiency") is not None]
    score = f"{sum(scores) / len(scores):.2f}" if scores else ""
    g = _severities(suff, "gaps")
    d = _severities(find, "findings")
    return ",".join([variant, str(rep), score,
                     str(g.get("major", 0)), str(g.get("minor", 0)),
                     str(d.get("high", 0)), str(d.get("medium", 0)), str(d.get("low", 0))])


def summarize(csv_path):
    lines = [line.strip() for line in open(csv_path, encoding="utf-8") if line.strip()]
    rows = [line.split(",") for line in lines[1:]]          # lines[0] is the header, not data
    by_variant = {}
    for r in rows:
        by_variant.setdefault(r[0], []).append(r)

    print(f"{'variant':<10} {'n':>2}  {'sufficiency (min..max)':<26} {'gaps maj/min':<14} {'drift h/m/l':<12}")
    print("-" * 72)
    baseline_mean = None
    for variant in ("baseline", "frozen"):
        rs = by_variant.get(variant)
        if not rs:
            continue
        scores = [float(r[2]) for r in rs if r[2]]
        mean = sum(scores) / len(scores) if scores else float("nan")
        if variant == "baseline":
            baseline_mean = mean
        spread = f"{mean:.3f}  ({min(scores):.2f}..{max(scores):.2f})" if scores else "n/a"
        maj = sum(int(r[3]) for r in rs) / len(rs)
        mnr = sum(int(r[4]) for r in rs) / len(rs)
        drift = "/".join(str(round(sum(int(r[i]) for r in rs) / len(rs), 1)) for i in (5, 6, 7))
        delta = ""
        if baseline_mean is not None and variant != "baseline" and scores:
            delta = f"   delta vs baseline {mean - baseline_mean:+.3f}"
        print(f"{variant:<10} {len(rs):>2}  {spread:<26} {maj:>4.1f}/{mnr:<9.1f} {drift:<12}{delta}")

    base_scores = [float(r[2]) for r in by_variant.get("baseline", []) if r[2]]
    if len(base_scores) > 1:
        noise = max(base_scores) - min(base_scores)
        print("")
        print(f"Baseline spread on a FIXED artifact: {noise:.3f}. Treat any variant delta smaller than this as "
              f"indistinguishable from grader noise.")
    elif base_scores:
        print("")
        print("Only one baseline rep — no noise floor. Re-run with REPS=3 or more before reading the deltas.")


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    if argv[0] == "--summarize":
        summarize(argv[1])
        return 0
    print(row(argv[0], argv[1], argv[2]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
