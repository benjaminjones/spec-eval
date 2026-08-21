# Drift report — `spec_eval`
detector: `claude-code` · 1/1 pairs audited · 2 model call(s)

**0 high/medium drift finding(s) across 1 audited pair(s).**

## coverage — ✓ clean
- **[low]** The module docstring defines the candidate universe as Python-only (`.py`), while the spec (and `DEFAULT_CODE_EXT` in the same file) define it as a 15-extension, language-agnostic set. (`spec_eval/coverage.py:L5` vs `spec_eval/coverage.md:L15`)
    - *evidence:*

    ```
    code: `CANDIDATE = repo code files (.py) minus the EXCLUDES taxonomy …` (coverage.py:5) vs `DEFAULT_CODE_EXT = (".py", ".ts", ".tsx", ".js", …, ".cs")` (coverage.py:16); doc: "Code universe (`code_ext`) | Extensions treated as code. Default: `.py .ts .tsx .js .jsx .mjs .cjs .go .rs .java .rb .kt .kts .swift .php .cs`" (coverage.md:15)
    ```

    - *fix:* Update the docstring line to `CANDIDATE = repo code files (see DEFAULT_CODE_EXT / config `code_ext`) …` so the header matches the language-agnostic default it sits directly above.
- **[low]** The module docstring folds the exclusion taxonomy into CANDIDATE, whereas the spec's definition table (and the implementation) treat CANDIDATE as pre-exclusion and call the post-exclusion set SPEC-WORTHY. (`spec_eval/coverage.py:L5` vs `spec_eval/coverage.md:L17`)
    - *evidence:*

    ```
    code: `CANDIDATE = repo code files (.py) minus the EXCLUDES taxonomy (tests / config / generated / glue / skills/docs / user `exclude:` pragmas)` (coverage.py:5), but the implementation is `candidate.add(...)` for every code-ext file and `spec_worthy = candidate - set(excluded)`; doc: "CANDIDATE | Every code file under the repo (by extension), minus pruned directories." / "SPEC-WORTHY | CANDIDATE minus all excluded files." (coverage.md:17,19)
    ```

    - *fix:* Reword the docstring to match the implemented vocabulary: CANDIDATE = all code-ext files minus pruned dirs; SPEC-WORTHY = CANDIDATE minus the EXCLUDES taxonomy (and mention the `tooling` tier, which the docstring's list omits).

### Drift fingerprint

| Pair | High+med findings |
|---|---|
| `coverage` | ✓ clean |
