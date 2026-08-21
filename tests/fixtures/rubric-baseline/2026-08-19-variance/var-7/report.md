# Drift report — `spec_eval`
detector: `claude-code` · 1/1 pairs audited · 2 model call(s)

**0 high/medium drift finding(s) across 1 audited pair(s).**

## coverage — ✓ clean
- ~~**[low]** The Definitions table describes UNMODELED as markdown with "no code sibling", but the code's actual test is "sits in a directory holding no candidate code file" (as the Behavior section and INV-8 correctly state).~~ (`coverage.py:L107` vs `coverage.md:L2 (Definitions table, UNMODELED row)`)
    - *withdrawn on verification — stated-elsewhere:* The finding itself concedes the Behavior section and INV-8 state the directory-level rule exactly as the code implements it, so the loose Definitions-table gloss is a narrative shorthand and the document is not wrong.
    - *the doc says:* “| INV-8 | Every path in `unmodeled` sits in a directory holding no candidate code file, so no file is ever both unmodeled and paired. |”
- **[low]** The module docstring defines CANDIDATE as `.py`-only and as already having the exclusion taxonomy subtracted, contradicting the spec's language-agnostic CANDIDATE (all `code_ext` files minus pruned dirs) and its separate SPEC-WORTHY term — which is what the implementation actually does. (`coverage.py:L5` vs `coverage.md:L2 (Definitions: Code universe, CANDIDATE, SPEC-WORTHY)`)
    - *evidence:*

    ```
    code docstring: "CANDIDATE = repo code files (.py) minus the EXCLUDES taxonomy (tests / config / generated / glue / …)"  vs  code body: `exts = tuple(config.get("code_ext") or DEFAULT_CODE_EXT)` … `candidate.add(...)` then `spec_worthy = candidate - set(excluded)`  vs  doc: "CANDIDATE | Every code file under the repo (by extension), minus pruned directories." / "SPEC-WORTHY | CANDIDATE minus all excluded files."
    ```

    - *fix:* Update the module docstring to drop the `(.py)` restriction and to use the spec's two-step vocabulary (CANDIDATE = all `code_ext` files minus pruned dirs; SPEC-WORTHY = CANDIDATE minus the EXCLUDES taxonomy).

### Drift fingerprint

| Pair | High+med findings |
|---|---|
| `coverage` | ✓ clean |
