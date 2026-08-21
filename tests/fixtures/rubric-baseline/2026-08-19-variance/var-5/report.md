# Drift report — `spec_eval`
detector: `claude-code` · 1/1 pairs audited · 2 model call(s)

**0 high/medium drift finding(s) across 1 audited pair(s).**

## coverage — ✓ clean
- ~~**[medium]** The doc says unmodeled-markdown detection exists to surface an agent skill's `SKILL.md`, but `unmodeled_markdown` skips any file whose stem is a conventional doc name, and `"skill"` is in that set — so `SKILL.md` files are never reported as unmodeled.~~ (`coverage.py:L54` vs `coverage.md:§3 Unmodeled markdown detection`)
    - *withdrawn on verification — not-normative:* The only line mentioning `SKILL.md` in this section is the "Why:" rationale explaining why such writing is invisible to same-stem pairing, not a claim about which files the detector reports; the section's normative sentence — "A file qualifies when it sits in a directory holding no candidate code, is not user-excluded, and is not a conventional doc name" — matches the code's `CONVENTIONAL_DOC_STEMS` skip exactly.
    - *the doc says:* “**Why:** two real bodies of writing are invisible to a same-stem model — a spec tree keyed by requirement id (`spec/functional/FR-021-….md`) and behavior implemented AS markdown (an agent skill's `SKILL.md` and its references).”

### Drift fingerprint

| Pair | High+med findings |
|---|---|
| `coverage` | ✓ clean |
