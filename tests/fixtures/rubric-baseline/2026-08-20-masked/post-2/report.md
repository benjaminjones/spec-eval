# Drift report — `spec_eval`
detector: `claude-code` · 1/1 pairs audited · 2 model call(s)

**1 high/medium drift finding(s) across 1 audited pair(s).**

## coverage — ⚠ 1 drift
- *10 rationale line(s) masked before review — non-normative clauses are not shown to the model*
- **[medium]** INV-8 guarantees no file is ever both `unmodeled` and paired, but `unmodeled_markdown` never consults `config["pairs"]` docs globs, so a doc explicitly declared in a pair that lives in a docs-only directory is still reported as unmodeled. (`coverage.py:unmodeled_markdown (L119-L128, the per-md filter loop)` vs `coverage.md:INV-8`)
    - *evidence:*

    ```
    Doc INV-8: "Every path in `unmodeled` sits in a directory holding no candidate code file, so no file is ever both unmodeled and paired." (with §2 defining Pair as `{label, code[], docs[]}` — a config pair). Code filters only on three conditions: `if d in code_dirs: continue` / `if classify_exclude(md, user_excludes) == "user": continue` / `if os.path.splitext(os.path.basename(md))[0].lower() in CONVENTIONAL_DOC_STEMS: continue` — there is no `if md in pair_docs: continue`, unlike the orphan pass which does build `pair_docs` and skips them (`if md in pair_docs: continue  # explicitly paired — governed, wherever its code is`). Given `pairs: [{code: ["src/a.py"], docs: ["spec/a-spec.md"]}]` and three `.md` files under `spec/`, `spec/a-spec.md` is both pair-declared and returned inside the `{dir: "spec", files: 3}` unmodeled group.
    ```

    - *fix:* Either pass the already-computed `pair_docs` set into `unmodeled_markdown` and skip members of it (mirroring the orphan pass), or restate INV-8/§3 to say unmodeled only excludes same-stem co-located pairing and may include config-pair-declared docs.

### Drift fingerprint

| Pair | High+med findings |
|---|---|
| `coverage` | ⚠ 1 |
