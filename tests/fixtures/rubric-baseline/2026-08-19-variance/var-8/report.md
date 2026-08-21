# Drift report — `spec_eval`
detector: `claude-code` · 1/1 pairs audited · 2 model call(s)

**0 high/medium drift finding(s) across 1 audited pair(s).**

## coverage — ✓ clean
- ~~**[low]** The doc names an agent skill's `SKILL.md` as an example of the markdown reported under `unmodeled`, but `unmodeled_markdown` skips it because the stem `skill` is in `CONVENTIONAL_DOC_STEMS`, so `SKILL.md` files are never grouped or counted.~~ (`spec_eval/coverage.py:L123` vs `spec_eval/coverage.md:L64`)
    - *withdrawn on verification — not-normative:* The cited line is the section's "**Why:**" rationale explaining the motivation for reporting unmodeled markdown — it claims SKILL.md is invisible to same-stem pairing, not that `unmodeled_markdown` groups or counts SKILL.md files (the normative contract, AC-4, uses `skills/*/reference.md`).
    - *the doc says:* “**Why:** two real bodies of writing are invisible to a same-stem model — a spec tree keyed by requirement id (`spec/functional/FR-021-….md`) and behavior implemented AS markdown (an agent skill's `SKILL.md` and its references).”

### Drift fingerprint

| Pair | High+med findings |
|---|---|
| `coverage` | ✓ clean |
