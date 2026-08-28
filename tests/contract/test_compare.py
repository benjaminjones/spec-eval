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


def test_ac6_plain_sufficiency_json_loads_as_one_rep(tmp_path):
    """`--reps 1` is the DEFAULT, so a bare list is the likeliest first mistake. It must not be a traceback."""
    p = tmp_path / "sufficiency.json"
    p.write_text(json.dumps([{"label": "p1", "sufficiency": 0.8},
                             {"label": "p2", "sufficiency": 0.6}]))
    vendor, by_label = compare.load_reps(str(p))
    assert by_label == {"p1": [0.8], "p2": [0.6]}


def test_ac7_wrong_shape_names_both_accepted_shapes(tmp_path):
    p = tmp_path / "audit-findings.json"
    p.write_text(json.dumps({"findings": []}))
    try:
        compare.load_reps(str(p))
        raise AssertionError("expected a ValueError")
    except ValueError as e:
        assert "sufficiency.json" in str(e) and "sufficiency-reps.json" in str(e)
        assert "does not read" in str(e)          # says what it is NOT for
    except AttributeError:
        raise AssertionError("raised AttributeError — the bare-traceback failure this test exists to bar")


def test_ac8_one_rep_gives_null_noise_share_with_a_reason(tmp_path):
    a = _reps(tmp_path, "a.json", "A", {"p1": [0.8], "p2": [0.6], "p3": [0.4]})
    b = _reps(tmp_path, "b.json", "B", {"p1": [0.7], "p2": [0.6], "p3": [0.5]})
    r = compare.compare(a, b)
    nz = r["noise"]["A"]
    assert nz["noise_share"] is None                      # NOT zero — zero noise is a claim
    assert "only one rep per pair" in nz["unavailable_because"]
    assert r["delta"] is not None                         # the paired delta still works


def test_all_null_scores_is_an_error_not_an_empty_comparison(tmp_path):
    p = tmp_path / "empty.json"
    p.write_text(json.dumps([{"label": "p1", "sufficiency": None}]))
    try:
        compare.load_reps(str(p))
        raise AssertionError("expected a ValueError")
    except ValueError as e:
        assert "no scored pairs" in str(e)


def test_same_vendor_name_does_not_collapse_two_noise_shares(tmp_path):
    """Two runs of ONE model is the reproducibility check the README documents. Both shares must survive."""
    a = _reps(tmp_path, "a.json", "same-model", {"p1": [0.8, 0.8], "p2": [0.6, 0.6], "p3": [0.4, 0.4]})
    b = _reps(tmp_path, "b.json", "same-model", {"p1": [0.1, 0.9], "p2": [0.2, 0.8], "p3": [0.3, 0.7]})
    r = compare.compare(a, b)
    assert len(r["noise"]) == 2, f"two noise shares collapsed into {list(r['noise'])}"
    shares = sorted(v["noise_share"] for v in r["noise"].values())
    assert shares[0] < shares[1]                      # the noisier run is visibly noisier


def test_self_comparison_reports_one_noise_share(tmp_path):
    """Comparing a file with itself is the documented 'measure the wobble first' move. One share, not two."""
    a = _reps(tmp_path, "a.json", "solo", {"p1": [0.8, 0.9], "p2": [0.6, 0.5], "p3": [0.4, 0.45]})
    r = compare.compare(a, a)
    assert r["delta"] == 0.0
    assert len(r["noise"]) == 1
    assert r["noise"]["solo"]["noise_share"] is not None
