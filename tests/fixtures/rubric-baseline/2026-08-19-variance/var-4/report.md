# Drift report — `spec_eval`
detector: `claude-code` · 1/1 pairs audited · 2 model call(s)

**0 high/medium drift finding(s) across 1 audited pair(s).**

## coverage — ✓ clean
- ~~**[medium]** The doc names an agent skill's `SKILL.md` as a body of writing the unmodeled report surfaces, but `unmodeled_markdown` filters it out because the stem `skill` is in `CONVENTIONAL_DOC_STEMS`.~~ (`spec_eval/coverage.py:L123` vs `spec_eval/coverage.md:L64`)
    - *withdrawn on verification — not-normative:* The cited line (L64) is the section's "**Why:**" rationale explaining the motivation for the feature, not a normative claim about which files the report emits; the normative rule on L63 ("is not a conventional doc name") and AC-4 (`skills/*/reference.md`) match the code.
    - *the doc says:* “**Why:** two real bodies of writing are invisible to a same-stem model — a spec tree keyed by requirement id (`spec/functional/FR-021-….md`) and behavior implemented AS markdown (an agent skill's `SKILL.md` and its references).”
- ~~**[low]** The Definitions table defines UNMODELED by "no code sibling", while the code excludes any markdown whose whole directory contains candidate code.~~ (`spec_eval/coverage.py:L119` vs `spec_eval/coverage.md:L22`)
    - *withdrawn on verification — stated-elsewhere:* The loose Definitions gloss on L22 is stated correctly elsewhere in the same doc — §3 L63 ("sits in a directory holding no candidate code") and INV-8 — which match the code exactly.
    - *the doc says:* “| INV-8 | Every path in `unmodeled` sits in a directory holding no candidate code file, so no file is ever both unmodeled and paired. |”

### Drift fingerprint

| Pair | High+med findings |
|---|---|
| `coverage` | ✓ clean |
