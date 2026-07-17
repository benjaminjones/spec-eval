"""Layer 2 — command acceptance criteria (GWT). Model-backed commands use the fake provider (no API key)."""
import os

from spec_eval import audit, authoring, coverage, sufficiency


def test_ac001_coverage_100_when_every_module_has_a_colocated_spec(tmp_path):
    """AC-001. Given a repo where every spec-worthy module has a sibling `.md`,
    When coverage runs with no config, Then coverage is 100% and nothing is uncovered."""
    (tmp_path / "a.py").write_text("x = 1\n")
    (tmp_path / "a.md").write_text("## 1. Purpose\nModule A.\n")
    cov = coverage.coverage(str(tmp_path), {})
    assert cov["pct"] == 100.0 and cov["uncovered"] == []


def test_ac002_audit_auto_pairs_colocated_specs_without_a_config(repo, fake_model):
    """AC-002. Given co-located specs and NO pairs config,
    When audit runs, Then it audits exactly the auto-paired module(s) and reports the drift verdict."""
    results = audit.audit_repo(str(repo), {}, fake_model)
    assert len(results) == 1 and results[0]["label"] == "widget"
    assert results[0]["findings"] == []


def test_ac003_sufficiency_scores_each_colocated_pair(repo, fake_model):
    """AC-003. Given a co-located spec, When sufficiency runs, Then each pair gets a 0..1 score."""
    results = sufficiency.sufficiency_repo(str(repo), {}, fake_model)
    assert results[0]["label"] == "widget" and results[0]["sufficiency"] == 0.90


def test_ac004_generate_fills_gaps_and_never_clobbers(repo, fake_model):
    """AC-004. Given one covered module and one uncovered, When generate runs, Then the missing spec is
    authored beside its code and the existing spec is skipped byte-for-byte intact (review happens in VCS)."""
    before = (repo / "widget.md").read_text()
    res = authoring.generate_repo(str(repo), {"pairs": []}, fake_model)
    by_spec = {r["spec"]: r["status"] for r in res}
    assert by_spec["helper.md"] == "authored" and os.path.exists(os.path.join(str(repo), "helper.md"))
    assert by_spec["widget.md"] == "skipped"
    assert (repo / "widget.md").read_text() == before                     # existing spec untouched
