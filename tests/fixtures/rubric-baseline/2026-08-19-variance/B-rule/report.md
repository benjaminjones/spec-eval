# Drift report — `spec_eval`
detector: `claude-code` · 1/1 pairs audited · 2 model call(s)

**0 high/medium drift finding(s) across 1 audited pair(s).**

## coverage — ✓ clean
- **[low]** The module docstring defines CANDIDATE as Python-only and already minus the exclusion taxonomy, which contradicts the spec's CANDIDATE definition (every code extension, minus only pruned dirs) that the implementation actually follows. (`coverage.py:L6` vs `coverage.md:L14`)
    - *evidence:*

    ```
    code (module docstring): "CANDIDATE = repo code files (.py) minus the EXCLUDES taxonomy (tests / config / generated / glue / skills/docs / user `exclude:` pragmas)" — but the implementation uses `exts = tuple(config.get("code_ext") or DEFAULT_CODE_EXT)` with 16 extensions and builds `candidate` from the walk with no exclusion filter (`spec_worthy = candidate - set(excluded)` is a later, separate step).
    doc §2: "CANDIDATE | Every code file under the repo (by extension), minus pruned directories." and "SPEC-WORTHY | CANDIDATE minus all excluded files."
    ```

    - *fix:* Update the coverage.py module docstring to say CANDIDATE = repo code files in any configured `code_ext` (default: the 16-language list) minus pruned directories, and that the EXCLUDES taxonomy is subtracted to produce SPEC-WORTHY.
- ~~**[low]** The §2 definition of UNMODELED states the criterion as "no code sibling", whereas the code (and §3/INV-8) require the markdown's whole directory to contain no candidate code file.~~ (`coverage.py:L100` vs `coverage.md:L21`)
    - *withdrawn on verification — stated-elsewhere:* §3 "Unmodeled markdown detection" (and INV-8) state the directory-level rule correctly, so the loose §2 table gloss does not make the document wrong.
    - *the doc says:* “A file qualifies when it sits in a directory holding no candidate code, is not user-excluded, and is not a conventional doc name.”

### Drift fingerprint

| Pair | High+med findings |
|---|---|
| `coverage` | ✓ clean |
