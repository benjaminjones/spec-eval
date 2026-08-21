# Drift report — `spec_eval`
detector: `claude-code` · 1/1 pairs audited · 2 model call(s)

**1 high/medium drift finding(s) across 1 audited pair(s).**

## coverage — ⚠ 1 drift
- **[medium]** `unmodeled_markdown` never checks the config pairs' `docs` globs, so an explicitly paired spec that lives in a docs-only directory is reported as unmodeled — contradicting INV-8's "no file is ever both unmodeled and paired". (`spec_eval/coverage.py:117` vs `spec_eval/coverage.md:101`)
    - *evidence:*

    ```
    Doc INV-8: "Every path in `unmodeled` sits in a directory holding no candidate code file, so no file is ever both unmodeled and paired." Doc §2 defines Pair as "`{label, code[], docs[]}` — links code globs to spec doc(s)." Code (unmodeled_markdown) filters only on three conditions: `if d in code_dirs: continue` / `if classify_exclude(md, user_excludes) == "user": continue` / `if os.path.splitext(os.path.basename(md))[0].lower() in CONVENTIONAL_DOC_STEMS: continue` — `pair_docs` is not passed in and is only computed later, inside `coverage()` for the orphan check (`if md in pair_docs: continue  # explicitly paired — governed, wherever its code is`). So with `pairs: [{code: [src/*.py], docs: [docs/a-spec.md]}, …]` and 3+ such specs under `docs/`, those paired docs land in `unmodeled` as "outside the same-stem pairing model" while their code is simultaneously counted as covered.
    ```

    - *fix:* Either pass `pair_docs` into `unmodeled_markdown` and skip pair-declared docs the same way the orphan check does, or reword INV-8 to drop the "never both unmodeled and paired" clause (e.g. "…so an unmodeled file never has a same-stem code sibling; explicitly pair-declared docs may still appear").
- ~~**[medium]** The doc names an agent skill's `SKILL.md` as a body of writing the unmodeled report surfaces, but `skill` is in `CONVENTIONAL_DOC_STEMS`, so every `SKILL.md` is filtered out before grouping.~~ (`spec_eval/coverage.py:53` vs `spec_eval/coverage.md:64`)
    - *withdrawn on verification — not-normative:* The cited line is explicitly "Why:" rationale explaining what the same-stem pairing model cannot reach — motivation for the section rather than a claim that `unmodeled_markdown` reports `SKILL.md` files (the normative behavior is the three-condition sentence above it and AC-4).
    - *the doc says:* “**Why:** two real bodies of writing are invisible to a same-stem model — a spec tree keyed by requirement id (`spec/functional/FR-021-….md`) and behavior implemented AS markdown (an agent skill's `SKILL.md` and its references).”
- ~~**[low]** The §2 glossary defines UNMODELED by "no code sibling", but the code qualifies a file by "its directory holds no candidate code file" — a stricter condition that §3 states correctly.~~ (`spec_eval/coverage.py:119` vs `spec_eval/coverage.md:22`)
    - *withdrawn on verification — stated-elsewhere:* §3 states the qualifying rule exactly as implemented (directory holding no candidate code), and INV-8 repeats it, so the loose glossary phrasing does not make the document wrong.
    - *the doc says:* “A file qualifies when it sits in a directory holding no candidate code, is not user-excluded, and is not a conventional doc name.”

### Drift fingerprint

| Pair | High+med findings |
|---|---|
| `coverage` | ⚠ 1 |
