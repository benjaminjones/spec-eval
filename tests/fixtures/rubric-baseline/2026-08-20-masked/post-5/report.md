# Drift report — `spec_eval`
detector: `claude-code` · 1/1 pairs audited · 2 model call(s)

**0 high/medium drift finding(s) across 1 audited pair(s).**

## coverage — ✓ clean
- *10 rationale line(s) masked before review — non-normative clauses are not shown to the model*
- ~~**[medium]** INV-8 claims no file can be both `unmodeled` and paired, but `unmodeled_markdown` never filters out docs declared by a config pair's `docs` glob (unlike orphan detection, which does).~~ (`coverage.py:unmodeled_markdown` vs `coverage.md:§4 INV-8`)
    - *withdrawn on verification — stated-elsewhere:* The §3 "Unmodeled markdown detection" narrative states the qualification rule exactly as the code implements it (three conditions, no pair-docs filter), so INV-8's trailing "so no file is ever both unmodeled and paired" is a loose restatement of the same-stem pairing model ("Markdown that same-stem pairing cannot reach"), not a separate contradicted claim about config pairs.
    - *the doc says:* “A file qualifies when it sits in a directory holding no candidate code, is not user-excluded, and is not a conventional doc name.”

### Drift fingerprint

| Pair | High+med findings |
|---|---|
| `coverage` | ✓ clean |
