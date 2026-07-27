# Drift report — `spec-eval`
detector: `claude-code` · 10/10 pairs audited · 10 model call(s)

**1 high/medium drift finding(s) across 10 audited pair(s).**

## audit — ✓ clean

## authoring — ✓ clean

## cli — ✓ clean

## coverage — ✓ clean

## providers — ✓ clean

## report — ✓ clean

## rubric — ✓ clean

## runlog — ✓ clean

## sufficiency — ✓ clean

## syscontext — ⚠ 1 drift
- **[medium]** The Purpose says the scan collects 'four evidence classes', but the code emits five distinct evidence vias, matching the doc's own five-row via table and five detection bullets. (`spec_eval/syscontext.py:add() via emitters (sdk/framework/scheme/url/env)` vs `spec_eval/syscontext.md:§1 Purpose`)
    - *fix:* Change "four evidence classes" to "five evidence classes" in the Purpose to match the via table, the §3 detection list, and the five code vias.

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
| `syscontext` | ⚠ 1 |
