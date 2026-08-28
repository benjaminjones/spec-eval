"""Compare sufficiency scores across replicate runs and across vendors.

WHY THIS EXISTS. A single sufficiency score is one draw. `spec-eval sufficiency --reps N` repeats the scoring
so the spread is visible, and `spec-eval compare` fits the two questions worth asking of the result:

  1. HOW NOISY IS THE INSTRUMENT?  Within-vendor variance as a share of total. If most of the variance is
     rep-to-rep on identical inputs, a between-vendor difference has nothing to sit on.
  2. IS THERE A VENDOR EFFECT?     Delta on the raw sufficiency scale, reported AGAINST ITS STANDARD ERROR,
     never as a bare number.

THE DESIGN IS PAIRED AND THE ESTIMATOR SAYS SO. Pair is a block, vendor is fixed, rep is replication. Each
pair contributes one difference of per-vendor means, so a pair that is hard for both vendors cancels instead
of inflating the effect. n is the number of PAIRS, never the number of calls: 11 pairs x 3 reps x 2 vendors
is 66 calls and n = 11.

EQUIVALENCE IS TESTED, NOT ASSUMED FROM A NULL RESULT. "p > 0.05" is not evidence of no difference. TOST
declares equivalence only when the whole confidence interval falls inside a margin fixed BEFORE the run.

THE MDE IS REPORTED FIRST AND UNCONDITIONALLY. If the smallest detectable effect is larger than the margin,
the run cannot demonstrate equivalence at all and says so — a null from an underpowered design is a
statement about the design.
"""
import json
import math
import statistics


def _mean(xs):
    return statistics.fmean(xs) if xs else None


def load_reps(path, vendor=None):
    """Read a sufficiency output file. Returns (vendor, {label: [scores]}).

    ACCEPTS BOTH SHAPES. `sufficiency --reps N` (N > 1) writes {"model":…, "reps":[…]}; a plain run writes a
    bare list. `--reps 1` is the DEFAULT, so a bare list is the likeliest thing a first-time caller points
    here, and it must not be a stack trace. A bare list is read as a single rep.

    A SINGLE REP GIVES NO WITHIN-VENDOR VARIANCE. The paired delta is still computable, but `noise_share`
    is undefined and is reported as None with a reason rather than as zero — zero noise is a claim, and one
    observation cannot support it.

    Skipped and unparseable pairs carry `sufficiency: null` and are DROPPED rather than coerced to 0.0. A
    pair the model could not score is missing data; scoring it zero would report a parse failure as a
    maximally bad spec, which is the one error that would masquerade as a finding.
    """
    d = json.load(open(path))
    if isinstance(d, list):                       # a plain sufficiency.json — one rep
        reps, vendor = [{"rep": 1, "results": d}], vendor or path
    elif isinstance(d, dict) and "reps" in d:
        reps, vendor = d["reps"], vendor or d.get("model") or path
    else:
        raise ValueError(
            f"{path} is neither a sufficiency.json (a list of pair records) nor a sufficiency-reps.json "
            f"(an object with a 'reps' key). `compare` reads sufficiency output only — it does not read "
            f"audit findings.")
    by_label = {}
    for rep in reps:
        for rec in rep.get("results", []):
            s = rec.get("sufficiency")
            if s is None:
                continue
            by_label.setdefault(rec["label"], []).append(float(s))
    if not by_label:
        raise ValueError(f"{path} contained no scored pairs — every `sufficiency` value was null or absent")
    return vendor, by_label


def noise(by_label):
    """Within-vendor variance as a share of total — the spec's `ICC` field, and its definition is stated.

    NOTE THE DIRECTION. A classic ICC rises as measurements agree; this quantity is its complement — it
    rises as the instrument gets NOISIER. It is reported under the name the programme pre-registered, with
    this note attached so no reader inverts it.
    """
    within, all_scores = [], []
    for scores in by_label.values():
        all_scores.extend(scores)
        if len(scores) >= 2:
            within.append(statistics.variance(scores))
    if not within:
        # Every pair has a single observation: the paired delta still works, the noise share does not.
        return {"within_vendor_variance": None, "total_variance": None, "noise_share": None,
                "unavailable_because": "only one rep per pair — within-vendor variance needs >= 2. "
                                       "Re-run `sufficiency --reps 3` to measure the instrument's spread.",
                "pairs_with_replication": 0}
    if len(all_scores) < 2:
        return {"within_vendor_variance": None, "total_variance": None, "noise_share": None}
    total = statistics.variance(all_scores)
    w = _mean(within)
    return {"within_vendor_variance": None if w is None else round(w, 6),
            "total_variance": round(total, 6),
            "noise_share": None if (w is None or total == 0) else round(w / total, 4),
            "definition": "within-vendor variance / total variance; RISES with noise, unlike a classic ICC",
            "pairs_with_replication": len(within)}


def compare(a, b, margin=0.5, alpha=0.05):
    """Paired vendor contrast. `a` and `b` are (vendor, {label: [scores]}) from load_reps."""
    va, la = a
    vb, lb = b
    shared = sorted(set(la) & set(lb))
    dropped = sorted((set(la) | set(lb)) - set(shared))
    diffs = {p: _mean(la[p]) - _mean(lb[p]) for p in shared}
    n = len(diffs)
    if n < 2:
        return {"error": f"only {n} shared pair(s) — a paired contrast needs at least 2",
                "shared_pairs": shared, "dropped_pairs": dropped}

    d = list(diffs.values())
    delta = _mean(d)
    sd = statistics.stdev(d)
    se = sd / math.sqrt(n)

    # MDE at 80% power, two-sided alpha. Reported FIRST and whatever the result is.
    mde = 2.80 * se
    z = 1.96 if alpha == 0.05 else 1.645
    ci = (delta - z * se, delta + z * se)
    # TOST uses a 90% interval for a 5% one-sided pair — equivalence iff it sits inside the margin.
    ci90 = (delta - 1.645 * se, delta + 1.645 * se)
    equivalent = -margin < ci90[0] and ci90[1] < margin

    per_pair = sorted(({"pair": p, "delta": round(v, 4),
                        "mean_" + va: round(_mean(la[p]), 4), "mean_" + vb: round(_mean(lb[p]), 4),
                        "reps": [len(la[p]), len(lb[p])]} for p, v in diffs.items()),
                      key=lambda r: -abs(r["delta"]))

    return {
        "vendors": [va, vb],
        "pairs_n": n,
        "shared_pairs": shared,
        "dropped_pairs": dropped,
        "dropped_note": "pairs scored by only one vendor are excluded from the paired contrast, "
                        "and listed so the exclusion is visible rather than silent",
        "mde_80pct_power": round(mde, 4),
        "margin": margin,
        "underpowered_for_margin": mde > margin,
        "underpowered_note": "MDE exceeds the equivalence margin — this run cannot demonstrate equivalence, "
                             "and a null from it is a statement about the design, not about the vendors",
        "delta": round(delta, 4),
        "se_delta": round(se, 4),
        "ci95": [round(ci[0], 4), round(ci[1], 4)],
        "ci90_used_for_tost": [round(ci90[0], 4), round(ci90[1], 4)],
        "tost_equivalent": equivalent,
        "noise": {va: noise(la), vb: noise(lb)},
        "per_pair_delta": per_pair,
        "per_pair_note": "exploratory. Apply Benjamini-Hochberg before reading any single pair as a finding; "
                         "with n pairs examined, the largest |delta| is expected to be large by chance",
    }


def benjamini_hochberg(pvalues, q=0.05):
    """BH step-up. Returns the indices declared significant at false-discovery rate `q`."""
    idx = sorted(range(len(pvalues)), key=lambda i: pvalues[i])
    m = len(pvalues)
    keep, thresh = [], 0
    for rank, i in enumerate(idx, 1):
        if pvalues[i] <= rank / m * q:
            thresh = rank
    return sorted(idx[:thresh]) if thresh else []
