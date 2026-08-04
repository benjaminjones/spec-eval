"""Second-pass verification of drift findings: re-read the doc and ask whether it says what a finding claims.

Separate from `audit` because it answers a different question. The audit asks *does the code contradict the
doc?*; verification asks *does the doc assert the thing this finding contradicts?* — which is answerable only
by re-reading the document, and is the failure a more carefully worded first-pass instruction does not reach.

A measured run on a fixed subject established the reason for the split: strengthening the drift rubric's own
paraphrase guard made the model quote more fully (median evidence 263 -> 365 chars) without reducing findings,
and a claim two blind readers judged a false positive was raised on six runs of six under both rubric versions.
Reproducible means systematic, and a systematic misreading is not fixed by re-instructing the reader who made it.

KEEP IN SYNC: `skills/spec-check/SKILL.md` describes this pass for the agent-session path; the withdrawal
grounds below are the load-bearing part and `tests/contract/test_rubric_sync.py` pins them.
"""
import re

from . import audit
from . import providers

VERIFY_MAX_TOKENS = 2000   # verdicts only — no evidence re-quoting beyond the doc line each verdict cites

# A finding may be withdrawn ONLY on one of these named grounds. A free-text objection is not a ground:
# an unnameable doubt is what the audit's own "prefer false negatives" posture already handles, and letting
# the verifier withdraw on unease would make it a second opinion rather than a check.
GROUNDS = {
    "not-asserted",       # the line the finding cites does not carry the claim at the strength it needs
    "stated-elsewhere",   # the same doc states the rule correctly in another passage
    "not-normative",      # the graded text is rationale or commentary, not a claim about behaviour
    "scoped",             # the doc scoped the statement to a case the code path in question is not
}
# Every ground is a POSITIVE existential — each is settled by quoting one line that is there. An earlier
# version let `not-asserted` mean "the document does not say this", which is a negative existential and
# unprovable by a quote: a run withdrew a finding about little-endian serialization on the ground that the
# document did not assert it, quoting a line that omitted it, while three other lines including an invariant
# row asserted it outright. Right outcome, false ground. `not-asserted` is now scoped to the line the finding
# itself cites, which is a claim a quote can settle.

VERIFY_RUBRIC = """You are checking DRIFT FINDINGS against the document they were raised on. You are not looking
for drift. Each finding claims the doc asserts something the code contradicts. Your only question per finding:

  DOES THE DOCUMENT ACTUALLY ASSERT THAT, AS WRITTEN?

Read the doc yourself. Do not rely on the finding's paraphrase of it — the paraphrase is what you are checking.

WITHDRAW a finding only on one of these four named grounds, and only if you can quote the doc line that shows it.
Every ground is a POSITIVE claim about a specific line you quote. You are never asked to show that a document
does not contain something — quoting one line that omits a property does not show the document never states it,
and a document may state the same property in several places.
- not-asserted: quote THE LINE THE FINDING ITSELF CITES (its doc_ref) and show that this line does not carry
  the claim in the strength the finding needs. The finding added a word that line does not contain (exactly,
  only, always, never, all, any) or dropped a clause it does contain. A line listing three things has not said
  "exactly three". If the property appears anywhere else in the document in the strength the finding needs,
  this ground does NOT apply and the finding stands.
- stated-elsewhere: the same doc states the rule correctly in another passage — commonly a contract or
  acceptance-criteria table below the narrative. The narrative is loose; the document is not wrong.
- not-normative: the graded sentence is rationale, motivation or commentary ("Why:" text, an aside about why a
  choice was made), not a claim about what the code does.
- scoped: the doc scoped its statement to a named case, and the finding applies it to a case the doc excluded.

UPHOLD otherwise. Uphold when you are unsure. A finding you cannot withdraw on a named ground with a quote is
upheld — withdrawing on general doubt would make this a second opinion, and it is a check.

You are NOT judging whether the code is correct, whether the doc is well written, or whether the finding is
important. A finding can be trivial and still upheld: the doc says it, the code contradicts it.

Output strict JSON, no preamble. One entry per finding, in the order given, keyed by index:
{"verdicts":[{"index":0,"verdict":"upheld|withdrawn","ground":"not-asserted|stated-elsewhere|not-normative|scoped|null",
"doc_quote":"the line from the doc that settles it, verbatim","why":"one sentence"}]}
"""


def parse_verdicts(resp, n):
    """Verdicts for `n` findings, positionally. A finding with no parseable verdict is UPHELD — an unreachable
    or malformed verifier must not silently delete findings, which is the one failure this pass could cause
    that the audit alone cannot."""
    out = [{"verdict": "upheld", "ground": None, "doc_quote": "", "why": "no verdict returned; upheld by default"}
           for _ in range(n)]
    d = audit.first_json_object(resp, "verdicts")
    if d is None:
        return out
    for v in d.get("verdicts", []):
        try:
            i = int(v.get("index", -1))
        except (TypeError, ValueError):
            continue
        if not (0 <= i < n):
            continue
        ground = v.get("ground") if v.get("ground") in GROUNDS else None
        withdrawn = str(v.get("verdict", "")).lower() == "withdrawn" and ground is not None
        out[i] = {"verdict": "withdrawn" if withdrawn else "upheld",
                  "ground": ground if withdrawn else None,
                  "doc_quote": str(v.get("doc_quote", "")),
                  "why": str(v.get("why", ""))}
    return out


def _cited_line(doc_ref):
    """The line number in a `file:L50` / `file:50` reference, or None."""
    if not doc_ref:
        return None
    m = re.search(r":L?(\d+)\b", str(doc_ref))
    return int(m.group(1)) if m else None


def check_not_asserted(finding, verdict, doc, window=3):
    """Reject a `not-asserted` withdrawal whose quote is not where the finding said to look.

    The ground is a claim about ONE line — the one the finding cites — so it is checkable without a model.
    A run withdrew a finding citing `prepare.md:L50` by quoting a table header that really sits at line 56,
    while line 50 was an invariant row asserting the very property at issue. The quote existed, so a
    does-this-text-appear check passed it; only its POSITION falsifies it.

    Applies to `not-asserted` alone. The other grounds are claims about the document as a whole — a rule
    stated elsewhere is by definition not at the cited line — so a position check would reject them wrongly."""
    if verdict.get("verdict") != "withdrawn" or verdict.get("ground") != "not-asserted":
        return verdict
    want = _cited_line(finding.get("doc_ref"))
    quote = (verdict.get("doc_quote") or "").strip()
    if want is None or not quote:
        return verdict                      # nothing to check against; leave the model's call alone
    lines = doc.split("\n")
    hits = [i + 1 for i, ln in enumerate(lines) if quote and quote in ln]
    if hits and not any(abs(h - want) <= window for h in hits):
        return {"verdict": "upheld", "ground": None, "doc_quote": quote,
                "why": f"withdrawal rejected: the quoted line is at {hits[0]}, not the cited {want}"}
    return verdict


def verify_pair(repo, pair, findings, model, code_cap=audit.CODE_CAP, doc_cap=audit.DOC_CAP):
    """Attach a verdict to every finding on one pair. One model call per pair carrying the whole doc, because
    the check is 'does this document say it' and half a document cannot answer that."""
    if not findings:
        return findings
    doc, nd, _ = audit._read_globs(repo, pair.get("docs", []), doc_cap)
    code, nc, _ = audit._read_globs(repo, pair.get("code", []), code_cap)
    if nd == 0:
        return findings
    listing = "\n".join(
        f"[{i}] severity={f['severity']} · {f['summary']}\n    doc_ref={f.get('doc_ref')} code_ref={f.get('code_ref')}"
        f"\n    evidence: {f.get('evidence', '')}"
        for i, f in enumerate(findings))
    user = (f"# Findings to check: {pair['label']}\n\n{listing}\n\n"
            f"## The document, in full\n{doc}\n\n## The code\n```\n{code}\n```\n")
    verdicts = parse_verdicts(providers.gen(model, VERIFY_RUBRIC, user, max_tokens=VERIFY_MAX_TOKENS), len(findings))
    verdicts = [check_not_asserted(f, v, doc) for f, v in zip(findings, verdicts)]
    return [{**f, "verification": v} for f, v in zip(findings, verdicts)]


def upheld(findings):
    """Findings that survived verification, or every finding when the pass did not run. Withdrawn findings are
    kept in the record and excluded from counts — a withdrawal is a claim in its own right and is reviewable."""
    return [f for f in findings if f.get("verification", {}).get("verdict", "upheld") != "withdrawn"]


def verify_repo(repo, config, results, model):
    from . import coverage as coverage_mod
    pairs = {p["label"]: p for p in (config.get("pairs") or coverage_mod.infer_pairs(repo, config))}
    code_cap, doc_cap = audit.caps_from(config)
    for rec in results:
        p = pairs.get(rec.get("label"))
        if p and rec.get("findings"):
            rec["findings"] = verify_pair(repo, p, rec["findings"], model, code_cap, doc_cap)
    return results
