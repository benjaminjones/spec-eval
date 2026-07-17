"""Spec SUFFICIENCY — how completely does the spec capture the code's behavior?

The inverse of drift:
  - drift       = the spec CONTRADICTS the code (the drift auditor; "silence is not drift" — it ignores omissions).
  - sufficiency = the spec OMITS behavior that's in the code.
The grader is prompted with the rebuild question ("what would a rebuild-from-spec have to guess?") as its
calibration device; the resulting 0..1 score is an INDICATOR of completeness plus a list of what's missing — not
a proof that a rebuild would succeed. 1:1 line restatement is NOT the bar — intent-level
behavior/contracts/defaults are.
"""
from . import providers, audit

SUFFICIENCY_RUBRIC = (
    "You assess whether a SPEC is SUFFICIENT to REBUILD the code's BEHAVIOR — could a developer restart the "
    "project from the SPEC alone? 1:1 line restatement is NOT required; pure implementation detail may be "
    "omitted. List the key BEHAVIORS / CONTRACTS / DEFAULTS / RULES / EVENTS present in the CODE that are NOT "
    "captured in the SPEC — what a rebuild-from-spec would MISS or have to guess — each with a severity:\n"
    "  - major: a whole feature, contract, or component missing from the spec.\n"
    "  - minor: a default, threshold, edge-case, or event-shape missing.\n"
    "Be calibrated, not generous. EVERY gap carries `code_ref`, a SEARCHABLE pointer to where the missing "
    "behavior lives: the file plus the nearest enclosing function/class name — NOT a line number. When the gap "
    "spans the whole module, use the file name alone. Output strict JSON, no preamble:\n"
    '{"sufficiency":0.0,"gaps":[{"severity":"major|minor","missing":"one sentence",'
    '"code_ref":"file.py (function_or_class)"}]}\n'
    "sufficiency 1.0 = the behavior is fully rebuildable from the spec; 0.0 = the spec barely constrains the code."
)


def sufficiency_pair(repo, pair, model, code_cap=None, doc_cap=None):
    code_cap = audit.CODE_CAP if code_cap is None else code_cap
    doc_cap = audit.DOC_CAP if doc_cap is None else doc_cap
    code, nc, code_capped = audit._read_globs(repo, pair.get("code", []), code_cap)
    doc, nd, doc_capped = audit._read_globs(repo, pair.get("docs", []), doc_cap)
    if nc == 0 or nd == 0:
        return {"label": pair["label"], "skipped": f"no files matched (code={nc}, docs={nd})",
                "sufficiency": None, "gaps": []}
    user = f"# Sufficiency review: {pair['label']}\n\n## Code\n```\n{code}\n```\n\n## Spec\n{doc}\n"
    resp = providers.gen(model, SUFFICIENCY_RUBRIC, user, max_tokens=audit.REVIEW_MAX_TOKENS)   # same budget as drift — a truncated gap list is unparseable
    notes = audit.truncation_notes(code_capped, doc_capped, code_cap, doc_cap)
    d = audit.first_json_object(resp, "sufficiency", "gaps")
    if d is not None:
        try:
            gaps = []
            for g in d.get("gaps", []):
                gap = {"severity": str(g.get("severity", "")).lower(), "missing": str(g.get("missing", ""))}
                ref = g.get("code_ref")
                if ref and str(ref).lower() != "null":
                    gap["code_ref"] = str(ref)                  # searchable pointer (file + symbol), kept verbatim
                gaps.append(gap)
            rec = {"label": pair["label"], "code_files": nc, "doc_files": nd,
                   "sufficiency": float(d.get("sufficiency", 0)), "gaps": gaps}
            if notes:
                rec["truncated"] = notes
            return rec
        except Exception:
            pass
    rec = {"label": pair["label"], "sufficiency": None, "gaps": [{"severity": "?", "missing": resp[:200]}]}
    if notes:
        rec["truncated"] = notes                                # names the likely cause of the unparseable reply
    return rec


def sufficiency_repo(repo, config, model):
    from . import coverage as coverage_mod
    pairs = config.get("pairs") or coverage_mod.infer_pairs(repo, config)   # co-located specs need no pairs.yml
    code_cap, doc_cap = audit.caps_from(config)
    return [sufficiency_pair(repo, p, model, code_cap, doc_cap) for p in pairs]
