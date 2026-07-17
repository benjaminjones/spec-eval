"""Layer 1 — audit.parse_findings: tolerant JSON parsing of a drift verdict."""
from spec_eval import audit


def test_parse_findings_valid_json():
    resp = '{"findings": [{"severity": "high", "summary": "x", "code_ref": "a.py", "doc_ref": "a.md"}]}'
    out = audit.parse_findings(resp)
    assert len(out) == 1 and out[0]["severity"] == "high" and out[0]["summary"] == "x"


def test_parse_findings_drops_unknown_severity():
    assert audit.parse_findings('{"findings": [{"severity": "bogus", "summary": "x"}]}') == []


def test_parse_findings_no_json_returns_empty():
    assert audit.parse_findings("no json here, all clean") == []


def test_parse_findings_clean_verdict():
    assert audit.parse_findings('{"findings": []}') == []


def test_parse_findings_tolerates_literal_newlines_in_strings():
    """Models quote multi-line code in `evidence`; strict JSON rejects raw control chars and would
    turn a real finding into '(unparsed finding)'. The parser must tolerate them."""
    resp = '{"findings": [{"severity": "high", "summary": "x", "evidence": "line one\nline two"}]}'
    out = audit.parse_findings(resp)
    assert len(out) == 1 and out[0]["summary"] == "x"


def test_parse_findings_skips_bracey_prose_before_the_json():
    """The exact cli-pair failure: the model chats first and its prose quotes brace-y contract text
    (`{status, spec, preview?}`), then emits real JSON. A greedy `{.*}` span starts at the prose brace and
    never parses; the parser must find the first PARSEABLE object with a `findings` key instead."""
    resp = ('Doc says `{status, spec, preview?}` but code uses note. Flagging it.\n\n'
            '```json\n{"findings": [{"severity": "medium", "summary": "contract names preview, code uses note"}]}\n```')
    out = audit.parse_findings(resp)
    assert len(out) == 1 and out[0]["severity"] == "medium" and "preview" in out[0]["summary"]
