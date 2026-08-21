# Drift report — `spec_eval`
detector: `claude-code` · 1/1 pairs audited · 2 model call(s)

**1 high/medium drift finding(s) across 1 audited pair(s).**

## coverage — ⚠ 1 drift
- *10 rationale line(s) masked before review — non-normative clauses are not shown to the model*
- **[medium]** INV-8 guarantees no file is ever both `unmodeled` and paired, but `unmodeled_markdown` never consults `config["pairs"]`, so a doc explicitly declared in a pair's `docs` glob is still reported as unmodeled. (`coverage.py:L119 (unmodeled_markdown filter loop)` vs `coverage.md:§4 Invariants, INV-8`)
    - *evidence:*

    ```
    Doc INV-8: "Every path in `unmodeled` sits in a directory holding no candidate code file, so no file is ever both unmodeled and paired." Doc §2 defines Pair as "`{label, code[], docs[]}` — links code globs to spec doc(s)." Code (`unmodeled_markdown`) filters on only three conditions: `if d in code_dirs: continue`, `if classify_exclude(md, user_excludes) == "user": continue`, `if os.path.splitext(os.path.basename(md))[0].lower() in CONVENTIONAL_DOC_STEMS: continue` — no `pair_docs` check, unlike orphan detection which does have `if md in pair_docs: continue  # explicitly paired — governed, wherever its code is`.
    ```

    - *fix:* Pass the computed `pair_docs` set into `unmodeled_markdown` and skip any md in it (mirroring the orphan rule), or reword INV-8 to claim only same-stem pairing ("no file is ever both unmodeled and co-located-paired").
- ~~**[low]** The Definitions table says a markdown file is unmodeled when it has "no code sibling", but the code's actual test is that its whole directory holds no candidate code file.~~ (`coverage.py:L119` vs `coverage.md:§2 Definitions, UNMODELED row`)
    - *withdrawn on verification — stated-elsewhere:* §3 "Unmodeled markdown detection" states the directory-level rule correctly; the Definitions-table gloss "no code sibling" is the loose shorthand of the same rule, so the document is not wrong.
    - *the doc says:* “A file qualifies when it sits in a directory holding no candidate code, is not user-excluded, and is not a conventional doc name.”

### Drift fingerprint

| Pair | High+med findings |
|---|---|
| `coverage` | ⚠ 1 |
