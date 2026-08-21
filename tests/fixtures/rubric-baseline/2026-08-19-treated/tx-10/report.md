# Drift report — `spec_eval`
detector: `claude-code` · 1/1 pairs audited · 2 model call(s)

**0 high/medium drift finding(s) across 1 audited pair(s).**

## coverage — ✓ clean
- ~~**[medium]** The doc names an agent skill's `SKILL.md` as a canonical example of markdown surfaced by `unmodeled`, but the code filters any file whose stem is `skill` out of the unmodeled groups via `CONVENTIONAL_DOC_STEMS`, so `SKILL.md` files are never reported.~~ (`coverage.py:L124 (`unmodeled_markdown`, conventional-stem skip)` vs `coverage.md:§3 "Unmodeled markdown detection" (**Why:** paragraph)`)
    - *withdrawn on verification — not-normative:* The cited line is the section's "Why:" rationale explaining what same-stem pairing cannot see, not a claim that `SKILL.md` is reported; the normative rule in the same section ("A file qualifies when it sits in a directory holding no candidate code, is not user-excluded, and is not a conventional doc name.") matches the code's conventional-stem skip.
    - *the doc says:* “**Why:** two real bodies of writing are invisible to a same-stem model — a spec tree keyed by requirement id (`spec/functional/FR-021-….md`) and behavior implemented AS markdown (an agent skill's `SKILL.md` and its references).”

### Drift fingerprint

| Pair | High+med findings |
|---|---|
| `coverage` | ✓ clean |
