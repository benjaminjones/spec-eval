# Drift report — `spec_eval`
detector: `claude-code` · 1/1 pairs audited · 2 model call(s)

**1 high/medium drift finding(s) across 1 audited pair(s).**

## coverage — ⚠ 1 drift
- **[medium]** INV-8 claims no file can be both `unmodeled` and paired, but `unmodeled_markdown` never consults the config pairs' `docs` globs, so an explicitly paired spec that lives in a code-free directory is still reported as unmodeled. (`coverage.py:L117` vs `coverage.md:L101`)
    - *evidence:*

    ```
    Doc INV-8: "Every path in `unmodeled` sits in a directory holding no candidate code file, so no file is ever both unmodeled and paired." Doc §2 defines Pair as `{label, code[], docs[]}` — links code globs to spec doc(s), and the orphan path explicitly guards against it (`if md in pair_docs: continue` … "explicitly paired — governed, wherever its code is"). But `unmodeled_markdown(repo, candidate, mds, user_excludes)` receives no `pair_docs` and filters only on three conditions: `if d in code_dirs: continue` / `if classify_exclude(md, user_excludes) == "user": continue` / `if os.path.splitext(os.path.basename(md))[0].lower() in CONVENTIONAL_DOC_STEMS: continue`. With `pairs: [{code: ["src/**/*.py"], docs: ["spec/FR-001.md", "spec/FR-002.md", "spec/FR-003.md"]}]` and no code in `spec/`, those three paired docs are emitted as `{dir: "spec", files: 3}` — unmodeled and paired at the same time.
    ```

    - *fix:* Either pass `pair_docs` into `unmodeled_markdown` and skip pair-declared docs (mirroring the orphan check), or reword INV-8 to say only that unmodeled paths sit in directories with no candidate code and are therefore outside *same-stem* pairing, not outside explicit config pairs.
- **[low]** The module docstring's CANDIDATE definition contradicts the spec's Definitions table and the implementation — it restricts the code universe to `.py` and folds the exclusion taxonomy into CANDIDATE (which is the spec's SPEC-WORTHY). (`coverage.py:L5` vs `coverage.md:L17`)
    - *evidence:*

    ```
    Code docstring: "CANDIDATE = repo code files (.py) minus the EXCLUDES taxonomy (tests / config / generated / glue / skills/docs / user `exclude:` pragmas)". Doc §2: "CANDIDATE | Every code file under the repo (by extension), minus pruned directories." and "SPEC-WORTHY | CANDIDATE minus all excluded files"; "Code universe (`code_ext`) … Default: `.py .ts .tsx .js .jsx .mjs .cjs .go .rs .java .rb .kt .kts .swift .php .cs`". The implementation matches the doc: `candidate` collects every file ending in `exts` (16 default extensions) outside `PRUNE_DIRS`, and `spec_worthy = candidate - set(excluded)`.
    ```

    - *fix:* Update the module docstring to `CANDIDATE = repo code files (any configured `code_ext`) outside pruned dirs; SPEC-WORTHY = CANDIDATE minus the EXCLUDES taxonomy …` so the header matches `coverage.md` §2 and `DEFAULT_CODE_EXT`.

### Drift fingerprint

| Pair | High+med findings |
|---|---|
| `coverage` | ⚠ 1 |
