# Drift report — `spec-eval`
detector: `claude-code` · 9/9 pairs audited · 9 model call(s)

**0 high/medium drift finding(s) across 9 audited pair(s).**

## audit — ✓ clean
- **[low]** The Contracts section lists `suggestion` as a non-optional field of a Finding (only `code_ref?`/`doc_ref?` carry the optional marker), but fallback-path findings are emitted with only `severity` and `summary`, omitting `suggestion` entirely. (`spec_eval/audit.py:L75` vs `?`)
    - *fix:* Either mark `suggestion` optional in the contract (`suggestion?`) noting fallback findings carry only severity+summary, or have the fallback emit `suggestion: ""` (and `code_ref`/`doc_ref`: null) to satisfy the stated shape.

## authoring — ✓ clean

## cli — ✓ clean

## coverage — ✓ clean

## providers — ✓ clean

## report — ✓ clean

## rubric — ✓ clean

## runlog — ✓ clean

## sufficiency — ✓ clean

### Drift fingerprint

| Pair | High+med findings |
|---|---|
| `audit` | ✓ clean |
| `authoring` | ✓ clean |
| `cli` | ✓ clean |
| `coverage` | ✓ clean |
| `providers` | ✓ clean |
| `report` | ✓ clean |
| `rubric` | ✓ clean |
| `runlog` | ✓ clean |
| `sufficiency` | ✓ clean |
