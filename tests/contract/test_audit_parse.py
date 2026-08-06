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
    assert out[0]["evidence"] == "line one\nline two"


def test_parse_findings_keeps_the_evidence_the_rubric_asked_for():
    """The rubric requires `evidence` ("quote the conflicting code and doc snippets") and the FAQ tells
    a reader to check a finding against it, so dropping it makes a documented instruction unfollowable —
    and leaves nothing to re-check a claim against."""
    resp = ('{"findings": [{"severity": "high", "summary": "x", "code_ref": "a.py:L3",'
            ' "doc_ref": "a.md:L9", "evidence": "code: n = 8 / doc: defaults to 4", "suggestion": "fix"}]}')
    out = audit.parse_findings(resp)
    assert out[0]["evidence"] == "code: n = 8 / doc: defaults to 4"


def test_parse_findings_missing_evidence_is_empty_not_absent():
    """A model that omits the key must still produce a finding of the declared shape, so a consumer can
    read `evidence` unconditionally."""
    out = audit.parse_findings('{"findings": [{"severity": "low", "summary": "x"}]}')
    assert out[0]["evidence"] == ""


def test_unparsed_fallback_carries_the_same_key_set():
    """The regex fallback used to emit a two-key finding while the parsed path emitted six. Any consumer
    indexing a field on a finding would raise on exactly the responses that are already going wrong."""
    parsed = audit.parse_findings('{"findings": [{"severity": "high", "summary": "x"}]}')
    fallback = audit.parse_findings('garbled ... "severity": "high" ... not json')
    assert len(fallback) == 1
    assert set(fallback[0]) == set(parsed[0])
    assert fallback[0]["evidence"] == "" and fallback[0]["code_ref"] is None


def test_parse_findings_skips_bracey_prose_before_the_json():
    """The exact cli-pair failure: the model chats first and its prose quotes brace-y contract text
    (`{status, spec, preview?}`), then emits real JSON. A greedy `{.*}` span starts at the prose brace and
    never parses; the parser must find the first PARSEABLE object with a `findings` key instead."""
    resp = ('Doc says `{status, spec, preview?}` but code uses note. Flagging it.\n\n'
            '```json\n{"findings": [{"severity": "medium", "summary": "contract names preview, code uses note"}]}\n```')
    out = audit.parse_findings(resp)
    assert len(out) == 1 and out[0]["severity"] == "medium" and "preview" in out[0]["summary"]
