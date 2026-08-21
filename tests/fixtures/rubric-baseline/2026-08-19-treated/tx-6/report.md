# Drift report — `spec_eval`
detector: `claude-code` · 1/1 pairs audited · 2 model call(s)

**0 high/medium drift finding(s) across 1 audited pair(s).**

## coverage — ✓ clean
- ~~**[low]** The Definitions-table entry for UNMODELED states the qualifying condition as "no code sibling", while the implementation requires the file's whole directory to contain no candidate code file (the precise rule given later in §3).~~ (`coverage.py:L118` vs `coverage.md:L22`)
    - *withdrawn on verification — stated-elsewhere:* The Definitions-table gloss is a loose summary, but §3 (and INV-8: "Every path in `unmodeled` sits in a directory holding no candidate code file") states the directory-level rule exactly as the code implements it, so the document is not wrong.
    - *the doc says:* “A file qualifies when it sits in a directory holding no candidate code, is not user-excluded, and is not a conventional doc name.”

### Drift fingerprint

| Pair | High+med findings |
|---|---|
| `coverage` | ✓ clean |
