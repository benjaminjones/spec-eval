"""Layer 1 — sufficiency gap code_refs: searchable pointers (file + nearest symbol), deliberately not links
and not line numbers. Kept when the model provides one; omitted when absent or "null"."""

from spec_eval import providers, report, sufficiency


def _pair_result(monkeypatch, tmp_path, model_json):
    (tmp_path / "w.py").write_text("def add(a, b):\n    return a + b\n")
    (tmp_path / "w.md").write_text("## 1. Purpose\nAdds.\n")
    monkeypatch.setattr(providers, "gen", lambda *a, **k: model_json)
    return sufficiency.sufficiency_pair(str(tmp_path), {"label": "w", "code": ["w.py"], "docs": ["w.md"]}, "fake:m")


def test_code_ref_is_kept_verbatim(monkeypatch, tmp_path):
    r = _pair_result(monkeypatch, tmp_path,
                     '{"sufficiency":0.8,"gaps":[{"severity":"minor","missing":"x","code_ref":"w.py (add)"}]}')
    assert r["gaps"][0]["code_ref"] == "w.py (add)"


def test_code_ref_null_or_missing_is_omitted(monkeypatch, tmp_path):
    r = _pair_result(monkeypatch, tmp_path,
                     '{"sufficiency":0.8,"gaps":[{"severity":"minor","missing":"x","code_ref":"null"},'
                     '{"severity":"minor","missing":"y"}]}')
    assert all("code_ref" not in g for g in r["gaps"])


def test_report_renders_ref_as_searchable_inline_code(monkeypatch, tmp_path):
    """The ref renders as plain inline code — greppable in any environment, no link to break."""
    results = [{"label": "w", "sufficiency": 0.8,
                "gaps": [{"severity": "minor", "missing": "x", "code_ref": "w.py (add)"},
                         {"severity": "minor", "missing": "y"}]}]
    out = tmp_path / "s.md"
    report.write_sufficiency_markdown(results, str(tmp_path), "m", str(out))
    text = out.read_text()
    assert "- **[minor]** x · `w.py (add)`" in text
    assert "- **[minor]** y\n" in text                    # no dangling separator when ref absent
