# Drift report — `spec_eval`
detector: `claude-code` · 1/1 pairs audited · 2 model call(s)

**1 high/medium drift finding(s) across 1 audited pair(s).**

## coverage — ⚠ 1 drift
- **[medium]** `unmodeled_markdown` never consults the config's pair-declared docs, so a spec explicitly declared in `config["pairs"][*]["docs"]` that lives in a docs-only directory is reported as unmodeled, contradicting INV-8's guarantee that no file is ever both unmodeled and paired. (`coverage.py:unmodeled_markdown (the per-md filter loop — only `code_dirs`, `user` exclude, and `CONVENTIONAL_DOC_STEMS` are checked)` vs `coverage.md:INV-8`)
    - *evidence:*

    ```
    Doc (INV-8): "Every path in `unmodeled` sits in a directory holding no candidate code file, so no file is ever both unmodeled and paired." Doc also defines "Pair | `{label, code[], docs[]}` — links code globs to spec doc(s)." Code (`unmodeled_markdown`) filters only on: `if d in code_dirs: continue` / `if classify_exclude(md, user_excludes) == "user": continue` / `if os.path.splitext(os.path.basename(md))[0].lower() in CONVENTIONAL_DOC_STEMS: continue` — there is no `pair_docs` guard, unlike the orphan pass in `coverage()` which does `if md in pair_docs: continue  # explicitly paired — governed, wherever its code is`. Repro: pairs `[{code: ["src/*.py"], docs: ["docs/api.md"]}]` plus `docs/api.md`, `docs/audit.md`, `docs/generate.md` (no code in `docs/`) yields `unmodeled: [{dir: "docs", files: 3, ...}]`, and `format_report` prints those explicitly paired specs under "Unmodeled markdown *(outside the same-stem pairing model — neither covered nor uncovered)*" even though their code is counted as covered.
    ```

    - *fix:* Either compute `pair_docs` once in `coverage()` and pass it to `unmodeled_markdown` so pair-declared docs are skipped (mirroring the orphan pass), or restate INV-8 to scope its second clause to same-stem pairing, e.g. "…so no file is ever both unmodeled and same-stem paired; explicitly pair-declared docs in a docs-only directory may still be listed."

### Drift fingerprint

| Pair | High+med findings |
|---|---|
| `coverage` | ⚠ 1 |
