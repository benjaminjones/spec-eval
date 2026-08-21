# Drift report — `spec_eval`
detector: `claude-code` · 1/1 pairs audited · 2 model call(s)

**1 high/medium drift finding(s) across 1 audited pair(s).**

## coverage — ⚠ 1 drift
- **[medium]** `unmodeled_markdown` never filters out docs that are explicitly declared in a config pair's `docs` globs, so a pair-governed spec tree is still reported as "markdown pairing cannot reach" — contradicting INV-8's claim that no file is ever both unmodeled and paired. (`coverage.py:L117` vs `coverage.md:L101`)
    - *evidence:*

    ```
    Doc, Invariants table: "INV-8 | Every path in `unmodeled` sits in a directory holding no candidate code file, so no file is ever both unmodeled and paired." and §3: "Markdown that same-stem pairing cannot reach ... A file qualifies when it sits in a directory holding no candidate code, is not user-excluded, and is not a conventional doc name."
    
    Code, `unmodeled_markdown`:
    '''
    for md in mds:
        d = os.path.dirname(md)
        if d in code_dirs:
            continue
        if classify_exclude(md, user_excludes) == "user":
            continue
        if os.path.splitext(os.path.basename(md))[0].lower() in CONVENTIONAL_DOC_STEMS:
            continue
        ...
        groups.setdefault(top, []).append(md)
    '''
    No `pair_docs` guard — unlike the orphan pass in `coverage`, which has `if md in pair_docs: continue  # explicitly paired — governed, wherever its code is`.
    
    Failure scenario: config declares `pairs: [{code: ["src/auth.py"], docs: ["spec/functional/FR-021-auth.md"]}, …]` with 3 such docs under `spec/functional/`. `src/auth.py` is reported as covered *via those docs*, yet the same three docs are emitted in `unmodeled` and printed under "outside the same-stem pairing model — neither covered nor uncovered" — they are simultaneously paired and unmodeled.
    ```

    - *fix:* Pass the pair-declared doc set into `unmodeled_markdown` (as `coverage` already computes `pair_docs` for the orphan pass) and `continue` on `md in pair_docs`; or, if the current behavior is intended, reword INV-8 to drop the "so no file is ever both unmodeled and paired" clause and scope it explicitly to same-stem pairing.

### Drift fingerprint

| Pair | High+med findings |
|---|---|
| `coverage` | ⚠ 1 |
