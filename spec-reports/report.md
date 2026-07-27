# Drift report — `spec-eval`
detector: `claude-code` · 10/10 pairs audited · 10 model call(s)

**0 high/medium drift finding(s) across 10 audited pair(s).**

## audit — ✓ clean

## authoring — ✓ clean

## cli — ✓ clean
- **[low]** The doc's blanket claim that every command writes both a JSON and a Markdown artifact is false for `context --check`, which writes neither. (`spec_eval/cli.py (context --check branch: raises SystemExit before json.dump/system-context.md write)` vs `spec_eval/cli.md (§3 Artifacts & logging)`)
    - *fix:* Qualify the summary, e.g. "every command (except `context --check`, which only reads the baseline) writes both a JSON and a Markdown artifact".

## coverage — ✓ clean

## providers — ✓ clean

## report — ✓ clean

## rubric — ✓ clean

## runlog — ✓ clean

## sufficiency — ✓ clean

## syscontext — ✓ clean

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
| `syscontext` | ✓ clean |
