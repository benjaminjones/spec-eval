"""Contract tests for `compare` — one per acceptance row in spec_eval/compare.md §7."""
import json

from spec_eval import compare


def _reps(tmp_path, name, model, per_pair):
    """Write a --reps file. `per_pair` maps label -> list of scores (None allowed)."""
    n = max(len(v) for v in per_pair.values())
    reps = [{"rep": i + 1,
             "results": [{"label": lbl, "sufficiency": (scores[i] if i < len(scores) else None)}
                         for lbl, scores in per_pair.items()]}
            for i in range(n)]
    p = tmp_path / name
    p.write_text(json.dumps({"model": model, "reps": reps}))
    return compare.load_reps(str(p))


def test_ac1_too_few_shared_pairs_errors(tmp_path):
    a = _reps(tmp_path, "a.json", "A", {"x": [0.5, 0.5]})
    b = _reps(tmp_path, "b.json", "B", {"y": [0.5, 0.5]})
    r = compare.compare(a, b)
    assert "error" in r and "delta" not in r


def test_ac2_null_only_pair_is_dropped_not_zeroed(tmp_path):
    a = _reps(tmp_path, "a.json", "A", {"p1": [0.8, 0.8], "p2": [0.7, 0.7], "gone": [None, None]})
    b = _reps(tmp_path, "b.json", "B", {"p1": [0.8, 0.8], "p2": [0.7, 0.7], "gone": [0.9, 0.9]})
    r = compare.compare(a, b)
    assert "gone" in r["dropped_pairs"]
    assert r["pairs_n"] == 2
    # The load path must not have coerced the nulls to 0.0 — that would show as a huge delta.
    assert abs(r["delta"]) < 1e-9


def test_ac3_identical_scores_give_zero_delta_and_equivalence(tmp_path):
    scores = {"p1": [0.8, 0.8, 0.8], "p2": [0.6, 0.6, 0.6], "p3": [0.4, 0.4, 0.4]}
    a = _reps(tmp_path, "a.json", "A", scores)
    b = _reps(tmp_path, "b.json", "B", scores)
    r = compare.compare(a, b)
    assert r["delta"] == 0.0
    assert r["tost_equivalent"] is True


def test_ac4_mde_is_always_present(tmp_path):
    a = _reps(tmp_path, "a.json", "A", {"p1": [0.8, 0.9], "p2": [0.6, 0.5], "p3": [0.4, 0.45]})
    b = _reps(tmp_path, "b.json", "B", {"p1": [0.7, 0.8], "p2": [0.6, 0.6], "p3": [0.5, 0.4]})
    r = compare.compare(a, b)
    assert "mde_80pct_power" in r and r["mde_80pct_power"] is not None


def test_ac5_interval_straddling_the_margin_is_not_equivalent(tmp_path):
    # A large, variable difference: the 90% interval must not fit inside +/-0.5.
    a = _reps(tmp_path, "a.json", "A", {"p1": [1.0], "p2": [1.0], "p3": [1.0], "p4": [0.0]})
    b = _reps(tmp_path, "b.json", "B", {"p1": [0.0], "p2": [0.0], "p3": [0.0], "p4": [1.0]})
    r = compare.compare(a, b, margin=0.5)
    assert r["tost_equivalent"] is False


def test_inv5_noise_share_rises_with_noise_and_says_so(tmp_path):
    quiet = _reps(tmp_path, "q.json", "Q", {"p1": [0.5, 0.5, 0.5], "p2": [0.9, 0.9, 0.9]})
    noisy = _reps(tmp_path, "n.json", "N", {"p1": [0.1, 0.9, 0.5], "p2": [0.2, 0.8, 0.5]})
    nq, nn = compare.noise(quiet[1]), compare.noise(noisy[1])
    assert nq["noise_share"] < nn["noise_share"]
    assert "RISES with noise" in nn["definition"]


def test_underpowered_flag_fires_when_mde_exceeds_margin(tmp_path):
    a = _reps(tmp_path, "a.json", "A", {"p1": [1.0], "p2": [0.0], "p3": [1.0]})
    b = _reps(tmp_path, "b.json", "B", {"p1": [0.0], "p2": [1.0], "p3": [0.0]})
    r = compare.compare(a, b, margin=0.1)
    assert r["underpowered_for_margin"] is True


def test_benjamini_hochberg_is_stricter_than_uncorrected():
    """One strong result and one borderline among 11. BH keeps the strong one and drops the borderline.

    The borderline p = 0.04 clears a naive 0.05 cut but fails its BH threshold of 2/11 x 0.05 = 0.0091,
    and no higher rank rescues it because the rest sit at 0.06.
    """
    p = [0.001, 0.04] + [0.06] * 9
    keep = compare.benjamini_hochberg(p, q=0.05)
    assert sum(1 for x in p if x < 0.05) == 2          # a naive cut would keep two
    assert keep == [0]                                 # BH keeps only the strongest
