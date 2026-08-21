# Drift report — `spec_eval`
detector: `claude-code` · 1/1 pairs audited · 2 model call(s)

**1 high/medium drift finding(s) across 1 audited pair(s).**

## coverage — ⚠ 1 drift
- **[high]** INV-8 claims no file can be both `unmodeled` and paired, but `unmodeled_markdown` never consults the config's pair `docs` globs, so an explicitly pair-declared spec in a docs-only directory is still reported as unmodeled. (`coverage.py:L117` vs `coverage.md:§4 Invariants, INV-8`)
    - *evidence:*

    ```
    Doc INV-8: "Every path in `unmodeled` sits in a directory holding no candidate code file, so no file is ever both unmodeled and paired." (with §2 defining Pair as `{label, code[], docs[]}` — links code globs to spec doc(s)). Code: `def unmodeled_markdown(repo, candidate, mds, user_excludes)` filters only on `if d in code_dirs: continue`, `if classify_exclude(md, user_excludes) == "user": continue`, and the CONVENTIONAL_DOC_STEMS check — it receives no `config`/`pairs` at all. Contrast the orphan path, which does build `pair_docs` and skips `if md in pair_docs: continue`. So `pairs: [{code: ["src/**/*.py"], docs: ["spec/functional/FR-*.md"]}]` (the doc's own motivating requirement-id spec tree) yields files that are simultaneously paired and listed under `unmodeled`.
    ```

    - *fix:* Either pass `pair_docs` into `unmodeled_markdown` and skip pair-declared docs (mirroring the orphan check), or restate INV-8 to drop the "so no file is ever both unmodeled and paired" clause and say only that unmodeled paths sit in directories with no candidate code.
- ~~**[medium]** The doc gives an agent skill's `SKILL.md` as a canonical example of markdown surfaced by the unmodeled report, but `SKILL.md` is in CONVENTIONAL_DOC_STEMS and is therefore always filtered out of the groups and counts.~~ (`coverage.py:L123` vs `coverage.md:§3 Unmodeled markdown detection`)
    - *withdrawn on verification — not-normative:* The `SKILL.md` mention sits in explicit "Why:" rationale explaining what kinds of writing pairing cannot see, not a claim that `SKILL.md` itself is surfaced; the normative sentence above it says a file qualifies only if it "is not a conventional doc name", and AC-4 uses `skills/*/reference.md`.
    - *the doc says:* “**Why:** two real bodies of writing are invisible to a same-stem model — a spec tree keyed by requirement id (`spec/functional/FR-021-….md`) and behavior implemented AS markdown (an agent skill's `SKILL.md` and its references).”

### Drift fingerprint

| Pair | High+med findings |
|---|---|
| `coverage` | ⚠ 1 |
