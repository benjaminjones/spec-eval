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


def _betacf(a, b, x, itmax=200, eps=3e-12):
    """Continued fraction for the incomplete beta function (Lentz's method)."""
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    if abs(d) < 1e-300:
        d = 1e-300
    d = 1.0 / d
    h = d
    for m in range(1, itmax + 1):
        m2 = 2 * m
        for num in (m * (b - m) * x / ((qam + m2) * (a + m2)),
                    -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))):
            d = 1.0 + num * d
            if abs(d) < 1e-300:
                d = 1e-300
            c = 1.0 + num / c
            if abs(c) < 1e-300:
                c = 1e-300
            d = 1.0 / d
            h *= d * c
        if abs(d * c - 1.0) < eps:
            break
    return h


def _betai(a, b, x):
    """Regularised incomplete beta I_x(a,b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbeta = (math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
             + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return math.exp(lbeta) * _betacf(a, b, x) / a
    return 1.0 - math.exp(lbeta) * _betacf(b, a, 1.0 - x) / b


def _t_cdf(t, df):
    x = df / (df + t * t)
    p = 0.5 * _betai(df / 2.0, 0.5, x)
    return 1.0 - p if t > 0 else p


def _t_ppf(p, df):
    """Student-t quantile by bisection on the CDF. No SciPy dependency.

    THE NORMAL QUANTILE IS WRONG HERE AND THE ERROR IS NOT COSMETIC. n is the number of PAIRS — 12 in the
    reference design — so df = 11 and t(.975,11) = 2.201 against z = 1.96, a 12% wider interval. Using 1.96
    delivers ~92.4% coverage on an interval labelled 95%. When a margin verdict was the deliverable that was
    a rounding concern; when the INTERVAL is the deliverable it is the published number.
    """
    if df <= 0:
        raise ValueError("df must be positive")
    lo, hi = -1e3, 1e3
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if _t_cdf(mid, df) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


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
    sha = None
    if isinstance(d, list):                       # a plain sufficiency.json — one rep
        reps, vendor = [{"rep": 1, "results": d}], vendor or path
    elif isinstance(d, dict) and "reps" in d:
        reps, vendor = d["reps"], vendor or d.get("model") or path
        sha = d.get("git_sha")
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
    return vendor, by_label, (sha if isinstance(d, dict) else None)


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


def compare(a, b, margin=None, alpha=0.05, allow_sha_mismatch=False):
    """Paired vendor contrast. `a` and `b` are (vendor, {label: [scores]}, sha) from load_reps.

    REFUSES TWO DIFFERENT SUBJECTS. If both sides carry a subject SHA and the SHAs differ, the two arms
    graded different code and the difference between them is a vendor effect confounded with a code change.
    That is not a caveat to note in the output — it is a different measurement, and the caller almost
    certainly did not mean to make it.
    """
    va, la, sha_a = (a if len(a) == 3 else (*a, None))
    vb, lb, sha_b = (b if len(b) == 3 else (*b, None))
    if sha_a and sha_b and sha_a != sha_b and not allow_sha_mismatch:
        raise ValueError(
            f"the two runs graded DIFFERENT SUBJECTS: {va} at {sha_a}, {vb} at {sha_b}. Their difference "
            f"mixes a vendor effect with a code change and is not interpretable as either. Re-run one arm "
            f"at the other's commit, or pass allow_sha_mismatch=True if you genuinely intend to compare "
            f"across commits.")
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

    # Student t at df = n-1 throughout. n is the number of PAIRS, so df is small and the normal quantile
    # under-covers: at df = 11, t(.975) = 2.201 against z = 1.96.
    df = n - 1
    tcrit = _t_ppf(1 - alpha / 2, df)
    mde = (tcrit + _t_ppf(0.80, df)) * se          # 80% power, two-sided alpha
    ci = (delta - tcrit * se, delta + tcrit * se)
    ci90 = (delta - _t_ppf(1 - alpha, df) * se, delta + _t_ppf(1 - alpha, df) * se)

    # m* — the smallest margin at which THIS run would have shown equivalence. A measured quantity that
    # answers "equivalent at m?" for any m the reader supplies, so the tool need not pick one for them.
    m_star = abs(delta) + _t_ppf(1 - alpha, df) * se

    # Per-pair contrasts with a pooled two-sample t, so Benjamini-Hochberg has p-values to correct.
    per_pair, pvals, excluded = [], [], []
    for p_, v in diffs.items():
        xa, xb = la[p_], lb[p_]
        rec = {"pair": p_, "delta": round(v, 4),
               "mean_" + va: round(_mean(xa), 4), "mean_" + vb: round(_mean(xb), 4),
               "reps": [len(xa), len(xb)]}
        dfp = len(xa) + len(xb) - 2
        sp2 = (((len(xa) - 1) * (statistics.variance(xa) if len(xa) > 1 else 0.0)
                + (len(xb) - 1) * (statistics.variance(xb) if len(xb) > 1 else 0.0)) / dfp) if dfp > 0 else 0.0
        if dfp <= 0 or sp2 <= 0:
            # NOT hypothetical: 3 of 12 pairs in the reference corpus return byte-identical reps. Dropping
            # them silently would move the BH family size without saying so.
            rec["p_value"] = None
            rec["p_unavailable_because"] = "zero within-pair variance — no computable t"
            excluded.append(p_)
        else:
            tstat = v / math.sqrt(sp2 * (1 / len(xa) + 1 / len(xb)))
            rec["p_value"] = round(2 * (1 - _t_cdf(abs(tstat), dfp)), 6)
            pvals.append((p_, rec["p_value"]))
        per_pair.append(rec)
    per_pair.sort(key=lambda r: -abs(r["delta"]))

    keep = benjamini_hochberg([q for _, q in pvals], q=alpha) if pvals else []
    bh_significant = sorted(pvals[i][0] for i in keep)

    out = {
        "vendors": [va, vb],
        "pairs_n": n,
        "df": df,
        "quantile_basis": "Student t at df = n-1",
        "shared_pairs": shared,
        "dropped_pairs": dropped,
        "dropped_note": "pairs scored by only one vendor are excluded from the paired contrast, "
                        "and listed so the exclusion is visible rather than silent",
        "mde_80pct_power": round(mde, 4),
        "delta": round(delta, 4),
        "se_delta": round(se, 4),
        "ci95": [round(ci[0], 4), round(ci[1], 4)],
        "m_star": round(m_star, 4),
        "m_star_note": "the smallest margin at which this run would have shown equivalence — supply "
                       "--margin to test a specific one",
        "noise": ({va: noise(la)} if va == vb and la == lb
                  else {va: noise(la), vb: noise(lb)} if va != vb
                  else {f"{va} (A)": noise(la), f"{vb} (B)": noise(lb)}),
        "per_pair_delta": per_pair,
        "bh_significant": bh_significant,
        "bh_family_size": len(pvals),
        "bh_excluded": excluded,
        "bh_note": "Benjamini-Hochberg applied across pairs with a computable p-value. The family size is "
                   "printed because it is smaller than the pair count whenever a pair has zero variance.",
    }
    if margin is not None:
        # Only emitted when a margin was SUPPLIED. Absence, never a default `false` — and never a default
        # `true`, which is what a built-in margin produced for practically any two graders.
        out["margin"] = margin
        out["ci90_used_for_tost"] = [round(ci90[0], 4), round(ci90[1], 4)]
        out["tost_equivalent"] = bool(-margin < ci90[0] and ci90[1] < margin)
        out["underpowered_for_margin"] = mde > margin
        out["underpowered_note"] = ("MDE exceeds the equivalence margin — this run cannot demonstrate "
                                    "equivalence, and a null from it is a statement about the design, "
                                    "not about the vendors")
    return out


def benjamini_hochberg(pvalues, q=0.05):
    """BH step-up. Returns the indices declared significant at false-discovery rate `q`."""
    idx = sorted(range(len(pvalues)), key=lambda i: pvalues[i])
    m = len(pvalues)
    # Step UP: find the LARGEST rank whose p-value clears rank/m * q, then reject everything at or below it.
    # Stepping down and stopping at the first failure would reject fewer and is the common mis-implementation.
    thresh = 0
    for rank, i in enumerate(idx, 1):
        if pvalues[i] <= rank / m * q:
            thresh = rank
    return sorted(idx[:thresh]) if thresh else []
