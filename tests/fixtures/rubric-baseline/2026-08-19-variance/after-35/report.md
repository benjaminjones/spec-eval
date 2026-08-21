# Drift report — `spec_eval`
detector: `claude-code` · 1/1 pairs audited · 2 model call(s)

**0 high/medium drift finding(s) across 1 audited pair(s).**

## coverage — ✓ clean
- ~~**[low]** The Definitions-table row for UNMODELED states the qualifying rule as "no code sibling", but the code excludes markdown by whole-directory test (any candidate code file in the same directory), so a `.md` with no same-stem sibling that sits beside other code is never unmodeled.~~ (`spec_eval/coverage.py:L115-L120` vs `spec_eval/coverage.md:L22`)
    - *withdrawn on verification — stated-elsewhere:* The glossary row is a loose one-line gloss, but the document states the code's actual whole-directory rule normatively in §3 ("A file qualifies when it sits in a directory holding no candidate code") and in the invariant table as INV-8, so the document is not wrong.
    - *the doc says:* “| INV-8 | Every path in `unmodeled` sits in a directory holding no candidate code file, so no file is ever both unmodeled and paired. |”

### Drift fingerprint

| Pair | High+med findings |
|---|---|
| `coverage` | ✓ clean |
