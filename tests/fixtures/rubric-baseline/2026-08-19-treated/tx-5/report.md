# Drift report — `spec_eval`
detector: `claude-code` · 1/1 pairs audited · 2 model call(s)

**0 high/medium drift finding(s) across 1 audited pair(s).**

## coverage — ✓ clean
- ~~**[low]** The Definitions table states the UNMODELED test as "no code sibling", but the code's actual test is that the markdown's whole directory contains no candidate code file — a stricter rule that §3 and INV-8 state correctly.~~ (`spec_eval/coverage.py:L119` vs `spec_eval/coverage.md:L22`)
    - *withdrawn on verification — stated-elsewhere:* The loose Definitions-table gloss is corrected by the normative statements in §3 ("it sits in a directory holding no candidate code") and INV-8, which state the code's actual rule exactly, so the document as a whole is not wrong.
    - *the doc says:* “| INV-8 | Every path in `unmodeled` sits in a directory holding no candidate code file, so no file is ever both unmodeled and paired. |”

### Drift fingerprint

| Pair | High+med findings |
|---|---|
| `coverage` | ✓ clean |
