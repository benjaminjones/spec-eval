# Drift report — `spec_eval`
detector: `claude-code` · 1/1 pairs audited · 2 model call(s)

**1 high/medium drift finding(s) across 1 audited pair(s).**

## coverage — ⚠ 1 drift
- **[high]** INV-8 guarantees no file is ever both `unmodeled` and paired, but `unmodeled_markdown` never consults the config pairs' `docs` globs, so an explicitly paired spec tree in a code-free directory is reported as unmodeled. (`spec_eval/coverage.py:L115` vs `spec_eval/coverage.md:L101`)
    - *evidence:*

    ```
    Doc INV-8: "Every path in `unmodeled` sits in a directory holding no candidate code file, so no file is ever both unmodeled and paired." (with `Pair | {label, code[], docs[]} — links code globs to spec doc(s)`, coverage.md:L23). Code: `unmodeled_markdown(repo, candidate, mds, user_excludes)` filters only on `if d in code_dirs`, `classify_exclude(md, user_excludes) == "user"`, and `CONVENTIONAL_DOC_STEMS` — there is no `pair_docs` check, and `coverage` calls it as `unmodeled_markdown(repo, candidate, mds, user_excludes)` without passing the pair docs it computed at L179-L184. The orphan branch does exactly the opposite: `if md in pair_docs: continue  # explicitly paired — governed, wherever its code is` (coverage.py:L200). Concrete case: config `pairs: [{code: ["src/*.py"], docs: ["spec/functional/FR-00{1,2,3}.md"]}]` — `spec/functional/` holds no candidate code, so all three paired docs land in `unmodeled` as `{dir: "spec", files: 3}`, and `format_report` prints them under "markdown that pairing cannot reach" even though pairing reaches them.
    ```

    - *fix:* Compute `pair_docs` before calling `unmodeled_markdown` and pass it in, skipping `if md in pair_docs` the same way the orphan check does; alternatively narrow INV-8 to say "never both unmodeled and *same-stem* paired" if the current behaviour is intended.
- **[low]** The module docstring's COVERED/CANDIDATE definitions contradict the spec: it says coverage comes only from config pair globs and that the candidate universe is `.py`, while the spec (and the implementation) also count co-located `<stem>.md` and per-dir folder specs across 16 languages. (`spec_eval/coverage.py:L4` vs `spec_eval/coverage.md:L7`)
    - *evidence:*

    ```
    Code docstring: "COVERED   = files matched by any pair's `code` globs in the config." / "CANDIDATE = repo code files (.py) minus the EXCLUDES taxonomy". Doc: "A code file counts as covered if — and only if — a configured pair points at it, OR a markdown file sits beside it with the same name … OR — when the authoring layout is `per-dir` — a folder spec …" and "Code universe (`code_ext`) … Default: `.py .ts .tsx .js .jsx .mjs .cjs .go .rs .java .rb .kt .kts .swift .php .cs`". The implementation matches the doc (`DEFAULT_CODE_EXT`, coverage.py:L16; co-located/per-dir coverage loop, coverage.py:L157-L162), so only the docstring is stale.
    ```

    - *fix:* Update the docstring to list all three coverage routes and drop the `(.py)` qualifier from CANDIDATE (it is language-agnostic via `DEFAULT_CODE_EXT`/`code_ext`).

### Drift fingerprint

| Pair | High+med findings |
|---|---|
| `coverage` | ⚠ 1 |
