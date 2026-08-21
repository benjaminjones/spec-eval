# Drift report — `spec_eval`
detector: `claude-code` · 1/1 pairs audited · 2 model call(s)

**0 high/medium drift finding(s) across 1 audited pair(s).**

## coverage — ✓ clean
- ~~**[medium]** The doc says an agent skill's `SKILL.md` is part of the unmodeled-markdown corpus that gets reported, but `"skill"` is in `CONVENTIONAL_DOC_STEMS`, so `SKILL.md` is filtered out of the group count and sample entirely.~~ (`spec_eval/coverage.py:L55` vs `spec_eval/coverage.md:L64`)
    - *withdrawn on verification — not-normative:* The cited line 64 is explicitly "Why:" rationale for the feature's existence, not a claim about what is reported; the normative rule on line 63 ("is not a conventional doc name") and AC-4 (which uses `skills/*/reference.md`) describe the behavior.
    - *the doc says:* “**Why:** two real bodies of writing are invisible to a same-stem model — a spec tree keyed by requirement id (`spec/functional/FR-021-….md`) and behavior implemented AS markdown (an agent skill's `SKILL.md` and its references).”
- ~~**[low]** The Definitions table defines UNMODELED by "no code sibling", but the code's predicate is the stronger "sits in a directory containing no candidate code file" (as §3 and INV-8 correctly state).~~ (`spec_eval/coverage.py:L119` vs `spec_eval/coverage.md:L22`)
    - *withdrawn on verification — stated-elsewhere:* The finding itself concedes §3 ("it sits in a directory holding no candidate code") and INV-8 state the stronger directory-level predicate correctly, so the loose Definitions-table gloss does not make the document wrong.
    - *the doc says:* “| INV-8 | Every path in `unmodeled` sits in a directory holding no candidate code file, so no file is ever both unmodeled and paired. |”

### Drift fingerprint

| Pair | High+med findings |
|---|---|
| `coverage` | ✓ clean |
