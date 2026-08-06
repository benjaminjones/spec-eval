"""Layer 1 — verify.parse_verdicts and the report's treatment of a withdrawn finding.

The pass exists because a more carefully worded first-pass instruction did not reach the failure: on a
measured two-arm run, strengthening the drift rubric's paraphrase guard made the model quote more fully
without reducing findings, and a claim two blind readers judged a false positive was raised on six runs of
six under both rubric versions. These tests pin the properties that make a second pass safe to add — it can
only remove a finding on a named ground, and it can never remove one silently.
"""
import json

from spec_eval import report, verify


def test_a_withdrawal_needs_a_named_ground():
    """Ground is the whole safety property. Without it a verifier withdraws on unease, which makes it a
    second opinion rather than a check — and one that deletes evidence."""
    resp = '{"verdicts":[{"index":0,"verdict":"withdrawn","ground":"not-asserted","doc_quote":"lists three","why":"x"}]}'
    out = verify.parse_verdicts(resp, 1)
    assert out[0]["verdict"] == "withdrawn" and out[0]["ground"] == "not-asserted"


def test_withdrawn_without_a_ground_is_upheld():
    assert verify.parse_verdicts('{"verdicts":[{"index":0,"verdict":"withdrawn"}]}', 1)[0]["verdict"] == "upheld"


def test_withdrawn_on_an_invented_ground_is_upheld():
    """The ground vocabulary is closed. A model inventing 'seems-wrong' must not thereby delete a finding."""
    resp = '{"verdicts":[{"index":0,"verdict":"withdrawn","ground":"seems-wrong","doc_quote":"q","why":"x"}]}'
    out = verify.parse_verdicts(resp, 1)
    assert out[0]["verdict"] == "upheld" and out[0]["ground"] is None


def test_an_unparseable_verifier_upholds_everything():
    """The one failure this pass could cause that the audit alone cannot is silently deleting real findings.
    A verifier that errors, truncates or returns prose must degrade to a no-op."""
    for resp in ["", "the model chatted and returned no json", '{"nope": []}']:
        out = verify.parse_verdicts(resp, 3)
        assert len(out) == 3 and all(v["verdict"] == "upheld" for v in out)


def test_a_missing_or_out_of_range_index_leaves_its_finding_upheld():
    """Positional verdicts: a verifier that answers for finding 0 only must not shift finding 1's verdict."""
    resp = '{"verdicts":[{"index":0,"verdict":"withdrawn","ground":"scoped","doc_quote":"q","why":"x"},' \
           ' {"index":9,"verdict":"withdrawn","ground":"scoped","doc_quote":"q","why":"x"}]}'
    out = verify.parse_verdicts(resp, 2)
    assert out[0]["verdict"] == "withdrawn"
    assert out[1]["verdict"] == "upheld"


def test_upheld_filter_passes_findings_that_never_saw_the_pass():
    """--verify is off by default, so most findings carry no verification key at all."""
    fs = [{"severity": "high"}, {"severity": "low", "verification": {"verdict": "withdrawn", "ground": "scoped"}}]
    assert verify.upheld(fs) == [{"severity": "high"}]


def test_a_withdrawn_finding_is_uncounted_but_still_shown(tmp_path):
    """A withdrawal is a claim in its own right. Deleting the finding would hide it; counting it would
    defeat the pass. It is struck through, carries its ground and the doc line, and drops out of the total."""
    results = [{"label": "p", "findings": [
        {"severity": "high", "summary": "doc says 4, code says 8", "evidence": "e", "suggestion": "fix it"},
        {"severity": "high", "summary": "doc says exactly three", "evidence": "e", "suggestion": "no",
         "verification": {"verdict": "withdrawn", "ground": "not-asserted",
                          "doc_quote": "the table lists three sites", "why": "the doc never says exactly"}}]}]
    out = tmp_path / "r.md"
    total = report.write_markdown(results, ".", "m", str(out))
    text = out.read_text()
    assert total == 1                                    # one of two counted
    assert "**1 high/medium drift finding(s)" in text
    assert "~~**[high]** doc says exactly three~~" in text
    assert "withdrawn on verification — not-asserted" in text
    assert "the table lists three sites" in text
    assert "*fix:* no" not in text                       # a withdrawn finding proposes no fix
    assert "*fix:* fix it" in text                       # the upheld one still does


def test_a_not_asserted_withdrawal_must_quote_the_line_the_finding_cited():
    """The ground is a claim about one line, so it is checkable without a model. A run withdrew a finding
    citing L50 by quoting a table header that sits at line 56, while line 50 asserted the very property at
    issue. The quote existed in the document, so only its position falsifies the withdrawal."""
    doc = "\n".join([f"line {i}" for i in range(1, 50)] +
                    ["| INV-1 | ids are little-endian uint16 |"] +          # line 50
                    [f"line {i}" for i in range(51, 56)] +
                    ["| ID | Given | When | Then |"])                        # line 56
    finding = {"doc_ref": "prepare.md:L50", "summary": "x"}
    bad = {"verdict": "withdrawn", "ground": "not-asserted",
           "doc_quote": "| ID | Given | When | Then |", "why": "the cited line does not assert it"}
    out = verify.check_not_asserted(finding, bad, doc)
    assert out["verdict"] == "upheld" and "not the cited 50" in out["why"]


def test_a_not_asserted_withdrawal_quoting_the_right_line_survives():
    doc = "\n".join([f"line {i}" for i in range(1, 50)] + ["the table lists three sites"])
    finding = {"doc_ref": "model.md:L50", "summary": "x"}
    good = {"verdict": "withdrawn", "ground": "not-asserted",
            "doc_quote": "the table lists three sites", "why": "no 'exactly' on this line"}
    assert verify.check_not_asserted(finding, good, doc)["verdict"] == "withdrawn"


def test_the_position_check_does_not_touch_the_other_grounds():
    """`stated-elsewhere` quotes a line that is BY DEFINITION not the cited one; a position check would
    reject every correct use of it."""
    doc = "\n".join(["elsewhere the rule is stated correctly"] + [f"line {i}" for i in range(2, 60)])
    finding = {"doc_ref": "model.md:L50", "summary": "x"}
    v = {"verdict": "withdrawn", "ground": "stated-elsewhere",
         "doc_quote": "elsewhere the rule is stated correctly", "why": "AC-1 gets it right"}
    assert verify.check_not_asserted(finding, v, doc)["verdict"] == "withdrawn"


def test_a_not_asserted_withdrawal_quoting_text_that_is_nowhere_is_rejected():
    """A quote found nowhere in the document is stronger evidence of fabrication than a misplaced one, and
    was the weaker check: an earlier version rejected only a misplaced quote, so a wholly invented one passed."""
    doc = "\n".join([f"line {i}" for i in range(1, 60)])
    finding = {"doc_ref": "model.md:L50", "summary": "x"}
    v = {"verdict": "withdrawn", "ground": "not-asserted",
         "doc_quote": "a sentence this document does not contain", "why": "not asserted"}
    out = verify.check_not_asserted(finding, v, doc)
    assert out["verdict"] == "upheld" and "does not appear" in out["why"]


def test_a_crashing_verifier_does_not_cost_the_audit(tmp_path, monkeypatch, capsys):
    """The second pass runs between a completed audit and the write of its results, so a failure there used
    to discard every pair already paid for — a transient 529 on the verify call threw away eleven audited
    pairs. verify's contract is that an unusable verifier is a no-op; a crashing one has to be one too."""
    from spec_eval import cli

    findings = [{"label": "p", "code_files": 1, "doc_files": 1,
                 "findings": [{"severity": "high", "summary": "real drift", "evidence": "e",
                               "suggestion": "fix", "code_ref": "a.py:L1", "doc_ref": "a.md:L2"}]}]
    monkeypatch.setattr(cli.audit, "audit_repo", lambda *a, **k: findings)
    monkeypatch.setattr(cli, "_load_keys", lambda *a, **k: None)

    def boom(*a, **k):
        raise RuntimeError("API Error: 529 Overloaded")
    import spec_eval.verify as verify_mod
    monkeypatch.setattr(verify_mod, "verify_repo", boom)

    out = tmp_path / "reports"
    cli.main(["audit", str(tmp_path), "--model", "x", "--verify", "--out", str(out)])

    written = json.loads((out / "findings.json").read_text())
    assert written[0]["findings"][0]["summary"] == "real drift"   # the audit survived
    assert (out / "report.md").exists()
    assert "verification failed" in capsys.readouterr().out       # and the user is told why
