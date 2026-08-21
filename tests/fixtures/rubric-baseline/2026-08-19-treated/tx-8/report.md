# Drift report — `spec_eval`
detector: `claude-code` · 1/1 pairs audited · 2 model call(s)

**1 high/medium drift finding(s) across 1 audited pair(s).**

## coverage — ⚠ 1 drift
- **[medium]** INV-8 asserts a file can never be both `unmodeled` and paired, but `unmodeled_markdown` never consults the config pairs' `docs` globs, so an explicitly pair-declared spec living in a docs-only tree is still reported as unmodeled. (`coverage.py:unmodeled_markdown (the filter loop: `if d in code_dirs / == "user" / in CONVENTIONAL_DOC_STEMS`)` vs `coverage.md:INV-8`)
    - *evidence:*

    ```
    Doc (INV-8): "Every path in `unmodeled` sits in a directory holding no candidate code file, so no file is ever both unmodeled and paired." Doc (Definitions): "Pair | `{label, code[], docs[]}` — links code globs to spec doc(s)." Code (`unmodeled_markdown`) filters only on three conditions — `if d in code_dirs: continue`, `if classify_exclude(md, user_excludes) == "user": continue`, `if os.path.splitext(os.path.basename(md))[0].lower() in CONVENTIONAL_DOC_STEMS: continue` — with no `pair_docs` check, unlike the orphan pass which does build `pair_docs` and does `if md in pair_docs: continue  # explicitly paired — governed, wherever its code is`. Failure: config `pairs: [{code: ["src/**/*.py"], docs: ["spec/functional/FR-001.md", "spec/functional/FR-002.md", "spec/functional/FR-003.md"]}]` — those three docs are paired, yet `spec/functional` holds no code, so they are emitted as `{dir: "spec", files: 3}` in `unmodeled`.
    ```

    - *fix:* Either pass `pair_docs` into `unmodeled_markdown` and skip pair-declared docs (mirroring the orphan pass), or reword INV-8 to drop the pairing clause and state only the load-bearing rule: "Every path in `unmodeled` sits in a directory holding no candidate code file."

### Drift fingerprint

| Pair | High+med findings |
|---|---|
| `coverage` | ⚠ 1 |
