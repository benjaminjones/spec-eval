"""Layer 1 — the deterministic half of "rationale is not a claim".

The drift rubric asks a model not to flag a rationale clause. Measured over 20 runs that moved the class rate
from 6/10 to 2/10 at p=0.17 — directionally right, not established (see
`tests/fixtures/rubric-baseline/PRE-REGISTRATION-rationale-rule.md`). Masking the clause before the call removes
the class by construction instead, which is checkable here with no model and no variance."""
import os

from spec_eval import audit


WHY = "**Why:** vendored trees are enormous, so descending into them wastes time."
DOC = f"""### spec.md
# Widget spec

The widget MUST retry three times.
{WHY}

The timeout is 30 seconds.
"""


def test_a_rationale_line_never_reaches_the_model(tmp_path, monkeypatch):
    """The point of the whole exercise: the model cannot flag text it was never shown."""
    (tmp_path / "widget.py").write_text("RETRIES = 3\nTIMEOUT = 30\n")
    (tmp_path / "widget.md").write_text(DOC)
    seen = {}

    def fake_gen(model, system, user, max_tokens=1200):
        seen["user"] = user
        return '{"findings": []}'

    monkeypatch.setattr(audit.providers, "gen", fake_gen)
    rec = audit.audit_pair(str(tmp_path), {"label": "widget", "code": ["widget.py"], "docs": ["widget.md"]}, "m")

    assert "**Why:**" not in seen["user"], "the rationale marker reached the model"
    assert "vendored trees are enormous" not in seen["user"], "the rationale text reached the model"
    assert "The widget MUST retry three times." in seen["user"], "a requirement was masked"
    assert "The timeout is 30 seconds." in seen["user"], "content after the masked line was lost"
    assert rec["rationale_masked"] == 1, "the count is surfaced to the reader"


def test_masking_preserves_line_numbers():
    """Findings cite `doc_ref: file:Lxx`. Deleting a line would silently shift every reference below it."""
    masked, n = audit.mask_rationale(DOC)
    assert n == 1
    assert masked.count("\n") == DOC.count("\n"), "line count changed — every doc_ref below the cut would shift"
    assert masked.split("\n")[4] == "", "the rationale line is emptied in place"


def test_the_default_covers_this_tools_own_authoring_convention():
    """`authoring.py` emits rationale as `**Why:**` and as `**Why <clause>:**`. Both are the same convention."""
    text = "**Why:** a.\n**Why the flag exists:** b.\nA real requirement.\n"
    masked, n = audit.mask_rationale(text)
    assert n == 2
    assert "A real requirement." in masked


def test_masking_is_configurable_and_can_be_switched_off():
    """A repo whose docs use `**Why` to state a requirement needs an escape hatch, not a fork."""
    assert audit.rationale_markers_from(None) == audit.RATIONALE_MARKERS
    assert audit.rationale_markers_from({"rationale_markers": ["NOTE:"]}) == ("NOTE:",)
    assert audit.rationale_markers_from({"rationale_markers": []}) == ()
    unmasked, n = audit.mask_rationale(DOC, ())
    assert (unmasked, n) == (DOC, 0), "an empty marker list must be a true no-op"
    masked, n = audit.mask_rationale("NOTE: an aside.\nkeep me\n", ("NOTE:",))
    assert n == 1 and "keep me" in masked


def test_verify_still_sees_the_unmasked_document(tmp_path):
    """`verify` checks a withdrawal's quote against the document, and a `not-normative` withdrawal quotes
    exactly the line audit masks. Filtering there would reject every correct use of that ground."""
    (tmp_path / "widget.md").write_text(DOC)
    doc, _, _ = audit._read_globs(str(tmp_path), ["widget.md"], audit.DOC_CAP)
    assert WHY in doc, "verify's document read must not be masked"
