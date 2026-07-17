"""Layer 1 — coverage: the exclusion taxonomy, co-located pairing, and the % computation."""
from hypothesis import given, strategies as st

from spec_eval import coverage


# --- classify_exclude: precondition = a repo-relative path; postcondition = a tier string, or None if spec-worthy
def test_classify_exclude_tiers():
    assert coverage.classify_exclude("test_widget.py", []) == "test"
    assert coverage.classify_exclude("widget_test.py", []) == "test"
    assert coverage.classify_exclude("pkg/tests/x.py", []) == "test"
    assert coverage.classify_exclude("__init__.py", []) == "glue"
    assert coverage.classify_exclude("setup.py", []) == "glue"
    assert coverage.classify_exclude("conf.yml", []) == "config"
    assert coverage.classify_exclude("NOTES.md", []) == "skill/doc"
    assert coverage.classify_exclude("scripts/tool.py", []) == "tooling"
    assert coverage.classify_exclude("widget.py", []) is None            # spec-worthy


def test_classify_exclude_honors_user_pragma():
    assert coverage.classify_exclude("vendor/x.py", ["vendor/**"]) == "user"


@given(st.text())
def test_classify_exclude_is_total(name):
    """Invariant: never raises; returns a str tier or None for any name."""
    out = coverage.classify_exclude(name + ".py", [])
    assert out is None or isinstance(out, str)


# --- infer_pairs: a <stem>.md beside a <stem>.py is auto-paired
def test_infer_pairs_colocated(repo):
    pairs = coverage.infer_pairs(str(repo), {})
    assert {p["label"] for p in pairs} == {"widget"}                     # helper.py has no sibling .md
    (p,) = pairs
    assert p["code"] == ["widget.py"] and p["docs"] == ["widget.md"]


# --- coverage: covered / uncovered / pct
def test_coverage_counts(repo):
    cov = coverage.coverage(str(repo), {})
    assert cov["spec_worthy"] == 2                                       # widget.py + helper.py
    assert cov["covered"] == ["widget.py"]                              # has a sibling .md
    assert cov["uncovered"] == ["helper.py"]
    assert cov["pct"] == 50.0
    assert "test_widget.py" in cov["excluded"].get("test", [])
