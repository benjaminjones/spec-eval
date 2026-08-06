"""Layer 1 — report: the unicode-bar fingerprint (pure text, no image)."""
from hypothesis import given, strategies as st

from spec_eval import report


def test_bar_boundaries():
    assert report._bar(0.0) == "░" * 20
    assert report._bar(1.0) == "█" * 20
    assert report._bar(0.5).count("█") == 10


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_bar_clamps_and_keeps_width(v):
    """Precondition: any float. Postcondition: a width-20 string of block chars (out-of-range clamped)."""
    bar = report._bar(v, width=20)
    assert len(bar) == 20 and set(bar) <= {"█", "░"}


def test_sufficiency_fingerprint_is_markdown_not_image():
    md = report.sufficiency_fingerprint([{"label": "a", "sufficiency": 0.5},
                                         {"label": "b", "sufficiency": 1.0}])
    assert "Spec completeness" in md and "0.50" in md and "█" in md
    assert ".png" not in md                                              # invariant: markdown only


def test_fingerprints_empty_on_no_data():
    assert report.sufficiency_fingerprint([]) == ""
    assert report.drift_fingerprint([]) == ""


def test_reports_render_the_partial_view_flag(tmp_path):
    """A pair carrying `truncated` notes shows a partial-view warning in both reports."""
    drift = [{"label": "p", "findings": [], "truncated": ["code input capped at ~11,000 chars"]}]
    out = tmp_path / "r.md"
    report.write_markdown(drift, ".", "m", str(out))
    assert "partial view (code input capped" in out.read_text()
    suff = [{"label": "p", "sufficiency": 0.5, "gaps": [], "truncated": ["reply hit the token cap"]}]
    out2 = tmp_path / "s.md"
    report.write_sufficiency_markdown(suff, ".", "m", str(out2))
    assert "partial view (reply hit the token cap)" in out2.read_text()


def test_drift_report_renders_the_evidence_a_finding_rests_on(tmp_path):
    """A reader is told to check a finding against its quoted evidence, which requires the report to
    carry it. Multi-line quotes stay inside the list item, so the rest of the findings still render."""
    drift = [{"label": "p", "findings": [
        {"severity": "high", "summary": "doc says 4, code says 8", "code_ref": "a.py:L3",
         "doc_ref": "a.md:L9", "evidence": "code: n = 8\ndoc: defaults to 4", "suggestion": "fix the doc"},
        {"severity": "low", "summary": "second finding", "evidence": "", "suggestion": ""}]}]
    out = tmp_path / "r.md"
    report.write_markdown(drift, ".", "m", str(out))
    text = out.read_text()
    assert "*evidence:*" in text
    assert "code: n = 8" in text and "doc: defaults to 4" in text
    assert "    doc: defaults to 4" in text          # continuation indented, so the list item holds
    assert "*fix:* fix the doc" in text
    assert "second finding" in text                   # an empty-evidence finding still renders
    assert text.count("*evidence:*") == 1             # and emits no empty block


def test_evidence_containing_a_fence_cannot_break_the_report(tmp_path):
    """Evidence is model-quoted source and may itself contain a fence, which would close ours early and
    spill the rest of the report into a code block."""
    drift = [{"label": "p", "findings": [
        {"severity": "high", "summary": "x", "evidence": "before\n```\nafter", "suggestion": ""}]}]
    out = tmp_path / "r.md"
    report.write_markdown(drift, ".", "m", str(out))
    body = out.read_text().split("*evidence:*")[1]
    assert body.count("```") == 2                     # exactly our own opening and closing fence


def test_sufficiency_markdown_survives_an_unscored_pair(tmp_path):
    """Regression (found live): a pair whose model reply didn't parse (sufficiency None, NOT skipped) used to
    crash `write_sufficiency_markdown` at the `:.2f` format — losing the whole report, the console summary, and
    the run-log row. It must render as 'not scored', sort last, and stay out of the average."""
    results = [{"label": "ok", "sufficiency": 0.4, "gaps": []},
               {"label": "raw", "sufficiency": None,
                "gaps": [{"severity": "?", "missing": '{"sufficiency":0.15,"gaps":[{"sever'}]}]
    out = tmp_path / "sufficiency.md"
    avg = report.write_sufficiency_markdown(results, ".", "fake:model", str(out))
    text = out.read_text()
    assert "not scored (unparseable model reply)" in text
    assert avg == 0.4                                                    # average over scored pairs only
    assert text.index("### ok") < text.index("### raw")                  # unscored sorts last (worst-first order)
