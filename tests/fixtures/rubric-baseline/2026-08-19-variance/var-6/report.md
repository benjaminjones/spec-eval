# Drift report — `spec_eval`
detector: `claude-code` · 1/1 pairs audited · 2 model call(s)

**1 high/medium drift finding(s) across 1 audited pair(s).**

## coverage — ⚠ 1 drift
- **[medium]** INV-8 claims no file can be both `unmodeled` and paired, but `unmodeled_markdown` never consults the config's pair `docs` globs, so an explicitly pair-declared spec living in a docs-only tree is still reported as outside the pairing model. (`coverage.py:L119` vs `coverage.md:INV-8`)
    - *evidence:*

    ```
    Doc INV-8: "Every path in `unmodeled` sits in a directory holding no candidate code file, so no file is ever both unmodeled and paired." Doc §2 defines Pair as "`{label, code[], docs[]}` — links code globs to spec doc(s)." Code (`unmodeled_markdown`) filters only on three conditions — `if d in code_dirs: continue`, `if classify_exclude(md, user_excludes) == "user": continue`, `if os.path.splitext(os.path.basename(md))[0].lower() in CONVENTIONAL_DOC_STEMS: continue` — and never checks `config["pairs"][*]["docs"]`. By contrast the orphan pass does guard on pairs: `pair_docs = ...` / `if md in pair_docs: continue`. So a config declaring `{code: ["src/**/*.py"], docs: ["spec/functional/FR-021-auth.md"]}` (the doc's own motivating example) yields specs that are both paired and listed under "Unmodeled markdown … neither covered nor uncovered", even though they do move `pct` via their paired code.
    ```

    - *fix:* Either make the code skip pair-declared docs in `unmodeled_markdown` (pass `pair_docs` in and `continue` on membership, mirroring the orphan pass), or restate INV-8 as "…so no file is ever both unmodeled and *same-stem* paired" and add "is not a pair-declared doc" to the §3 qualification list only if the code is changed.

### Drift fingerprint

| Pair | High+med findings |
|---|---|
| `coverage` | ⚠ 1 |
