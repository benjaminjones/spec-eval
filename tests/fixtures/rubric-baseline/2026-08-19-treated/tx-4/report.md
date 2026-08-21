# Drift report — `spec_eval`
detector: `claude-code` · 1/1 pairs audited · 2 model call(s)

**0 high/medium drift finding(s) across 1 audited pair(s).**

## coverage — ✓ clean
- ~~**[medium]** The Definitions table defines UNMODELED by "no code sibling", but the code excludes markdown by whole-directory test (any directory containing a candidate code file is skipped), contradicting both the implementation and INV-8/§3.~~ (`coverage.py:L114-L119` vs `coverage.md:L22`)
    - *withdrawn on verification — stated-elsewhere:* The Definitions-table gloss "no code sibling" is a loose summary, but the same document states the actual whole-directory rule precisely in §3 ("A file qualifies when it sits in a directory holding no candidate code") and in the INV-8 contract, which match the code.
    - *the doc says:* “| INV-8 | Every path in `unmodeled` sits in a directory holding no candidate code file, so no file is ever both unmodeled and paired. |”

### Drift fingerprint

| Pair | High+med findings |
|---|---|
| `coverage` | ✓ clean |
