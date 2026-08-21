# Drift report — `spec_eval`
detector: `claude-code` · 1/1 pairs audited · 2 model call(s)

**1 high/medium drift finding(s) across 1 audited pair(s).**

## coverage — ⚠ 1 drift
- **[medium]** `unmodeled_markdown` never consults the config pairs' `docs` globs, so a spec that is explicitly pair-declared but lives in a docs-only directory is reported as unmodeled, contradicting INV-8's guarantee that no file is ever both unmodeled and paired. (`spec_eval/coverage.py:L119` vs `spec_eval/coverage.md:L101`)
    - *evidence:*

    ```
    Code (`unmodeled_markdown`, coverage.py L104-L126) filters only on directory, user-excludes and conventional stems — `def unmodeled_markdown(repo, candidate, mds, user_excludes):` … `if d in code_dirs: continue` / `if classify_exclude(md, user_excludes) == "user": continue` / `if os.path.splitext(os.path.basename(md))[0].lower() in CONVENTIONAL_DOC_STEMS: continue`. `pair_docs` is built only inside `coverage()` for the orphan pass (`if md in pair_docs: continue  # explicitly paired — governed, wherever its code is`, L200-L201) and is never passed to `unmodeled_markdown` (L210). Doc: "INV-8 | Every path in `unmodeled` sits in a directory holding no candidate code file, so no file is ever both unmodeled and paired." together with "Pair | `{label, code[], docs[]}` — links code globs to spec doc(s)." Failure case: `pairs: [{label: x, code: ["src/x.py"], docs: ["docs/*.md"]}]` with 3+ `.md` files in a code-free `docs/` dir yields a group the report labels "outside the same-stem pairing model" even though every one of those files is pair-declared.
    ```

    - *fix:* Thread `pair_docs` into `unmodeled_markdown` and skip any `md in pair_docs` (mirroring the orphan pass), or restate INV-8 as "no file is ever both unmodeled and *same-stem* paired".
- **[low]** The module docstring's glossary defines COVERED as pair-glob matches only and CANDIDATE as `.py` files already minus the exclusion taxonomy, contradicting the spec's definitions (and the language-agnostic implementation). (`spec_eval/coverage.py:L4` vs `spec_eval/coverage.md:L16`)
    - *evidence:*

    ```
    Code docstring: "COVERED   = files matched by any pair's `code` globs in the config." / "CANDIDATE = repo code files (.py) minus the EXCLUDES taxonomy …". Implementation: `DEFAULT_CODE_EXT = (".py", ".ts", … ".cs")` (L16-17); `covered` also grows via the co-located `<stem>.md` and per-dir folder-spec branches (L155-L159); `candidate` is every `code_ext` file minus pruned dirs, with `spec_worthy = candidate - set(excluded)` (L145-L167). Doc: "COVERED | A code file matched by any config pair's `code` glob, OR having a sibling `<stem>.md`, OR (under `authoring.layout: per-dir`) whose directory has a folder spec `<dir>/<dir>.md`." / "CANDIDATE | Every code file under the repo (by extension), minus pruned directories." / "SPEC-WORTHY | CANDIDATE minus all excluded files."
    ```

    - *fix:* Update the module docstring to match the spec and code: COVERED = pair glob OR sibling `<stem>.md` OR per-dir folder spec; CANDIDATE = all `code_ext` files minus pruned dirs; SPEC-WORTHY = CANDIDATE minus the exclusion tiers.

### Drift fingerprint

| Pair | High+med findings |
|---|---|
| `coverage` | ⚠ 1 |
