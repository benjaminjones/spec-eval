"""Audit a repo's configured code↔doc pairs for drift. Filesystem-based, portable (repo path is an argument)."""
import os
import re
import json
import glob
from .rubric import DRIFT_RUBRIC
from . import providers

SEV = {"high": 3, "medium": 2, "low": 1}
REVIEW_MAX_TOKENS = 3000   # output-token budget for the two review checks (drift + sufficiency): each emits a
                           # JSON list (findings / gaps) that is unparseable if cut mid-list — sufficiency reads
                           # THIS constant so the "same budget" coupling is structural, not a comment.
CODE_CAP, DOC_CAP = 64000, 28000   # char caps per side (bound cost; directional). CODE_CAP=64k covers p99 of a
                                   # broad real-world corpus (~20k tokens, under the ~50k onset where long-context
                                   # accuracy measurably degrades); DOC_CAP=28k is p95 of real design docs.
                                   # Larger inputs get a partial-view flag.


def load_config(path):
    """A config is YAML or JSON: {pairs: [{label, code: [globs], docs: [globs]}]}."""
    text = open(path).read()
    if path.endswith((".yml", ".yaml")):
        import yaml
        return yaml.safe_load(text)
    return json.loads(text)


def _read_globs(repo, patterns, cap):
    """Concatenate the files matching `patterns` (relative headers included), capped at `cap` chars.
    Returns (text, file_count, capped) — `capped` is True when the cap cut material, so callers can surface
    the partial view to the USER (the `[truncated]` marker below only tells the MODEL)."""
    chunks = []
    for pat in (patterns or []):
        for f in sorted(glob.glob(os.path.join(repo, pat), recursive=True)):
            if os.path.isfile(f):
                try:
                    c = open(f, errors="ignore").read()
                except OSError:
                    continue
                if c.strip():
                    chunks.append(f"### {os.path.relpath(f, repo)}\n{c}")
    text = "\n\n".join(chunks)
    capped = len(text) > cap
    return (text[:cap] + ("\n...[truncated]" if capped else "")), len(chunks), capped


def first_json_object(resp, *keys):
    """The first PARSEABLE JSON object in `resp` carrying any of `keys` — immune to brace-y prose around the
    JSON (a greedy `{.*}` regex spans from the first prose brace and never parses). strict=False tolerates
    literal newlines/tabs inside quoted strings (models quote multi-line code in `evidence`)."""
    dec = json.JSONDecoder(strict=False)
    for m in re.finditer(r"\{", resp):
        try:
            obj, _ = dec.raw_decode(resp, m.start())
        except ValueError:
            continue
        if isinstance(obj, dict) and any(k in obj for k in keys):
            return obj
    return None


def parse_findings(resp):
    out = []
    d = first_json_object(resp, "findings")
    if d is not None:
        try:
            for f in d.get("findings", []):
                s = str(f.get("severity", "")).lower()
                if s in SEV:
                    out.append({"severity": s, "summary": str(f.get("summary", "")),
                                "code_ref": f.get("code_ref"), "doc_ref": f.get("doc_ref"),
                                "evidence": str(f.get("evidence", "")),
                                "suggestion": f.get("suggestion", "")})
            return out
        except Exception:
            pass
    for s in re.findall(r'"severity"\s*:\s*"(high|medium|low)"', resp, re.I):
        out.append({"severity": s.lower(),                                        # same key set as the parsed path:
                    "summary": "(unparsed finding — the response was not valid JSON; re-run this pair to get detail)",
                    "code_ref": None, "doc_ref": None, "evidence": "", "suggestion": ""})
    return out


def caps_from(config):
    """The per-side input caps in chars, config-overridable: `caps: {code, docs}`. The defaults are calibrated
    to real-world percentiles; raising them trades cost for coverage of larger files (e.g. `code: 100000` for
    C/C++-sized modules), lowering them tightens the cost ceiling."""
    c = (config or {}).get("caps") or {}
    return int(c.get("code", CODE_CAP)), int(c.get("docs", DOC_CAP))


def truncation_notes(code_capped, doc_capped, code_cap=CODE_CAP, doc_cap=DOC_CAP):
    """The pair-level partial-view notes shared by audit and sufficiency: the two input caps, plus whether the
    model's REPLY was cut off at the token cap (read from the call just made)."""
    notes = ([f"code input capped at ~{code_cap:,} chars"] if code_capped else []) \
        + ([f"docs input capped at ~{doc_cap:,} chars"] if doc_capped else [])
    if providers.LAST["truncated"]:
        notes.append("reply hit the token cap")
    return notes


def audit_pair(repo, pair, model, code_cap=CODE_CAP, doc_cap=DOC_CAP):
    code, nc, code_capped = _read_globs(repo, pair.get("code", []), code_cap)
    doc, nd, doc_capped = _read_globs(repo, pair.get("docs", []), doc_cap)
    if nc == 0 or nd == 0:
        return {"label": pair["label"], "skipped": f"no files matched (code={nc}, docs={nd})", "findings": []}
    user = f"# Drift review: {pair['label']}\n\n## Code\n```\n{code}\n```\n\n## Docs / spec\n{doc}\n"
    findings = parse_findings(providers.gen(model, DRIFT_RUBRIC, user, max_tokens=REVIEW_MAX_TOKENS))   # headroom: a truncated findings list is unparseable
    rec = {"label": pair["label"], "code_files": nc, "doc_files": nd, "findings": findings}
    notes = truncation_notes(code_capped, doc_capped, code_cap, doc_cap)
    if notes:
        rec["truncated"] = notes
    return rec


def audit_repo(repo, config, model):
    from . import coverage as coverage_mod
    pairs = config.get("pairs") or coverage_mod.infer_pairs(repo, config)   # co-located specs need no pairs.yml
    code_cap, doc_cap = caps_from(config)
    return [audit_pair(repo, p, model, code_cap, doc_cap) for p in pairs]
