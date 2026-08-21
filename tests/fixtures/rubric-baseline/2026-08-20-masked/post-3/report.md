# Drift report — `spec_eval`
detector: `claude-code` · 1/1 pairs audited · 2 model call(s)

**1 high/medium drift finding(s) across 1 audited pair(s).**

## coverage — ⚠ 1 drift
- *10 rationale line(s) masked before review — non-normative clauses are not shown to the model*
- **[medium]** `unmodeled_markdown` never filters out docs declared by a config pair, so a pair-declared spec living in a docs-only directory is reported as "markdown pairing cannot reach" — contradicting INV-8's claim that no file is ever both unmodeled and paired. (`coverage.py:unmodeled_markdown (the filter loop — only `d in code_dirs`, `classify_exclude(...)=='user'`, and CONVENTIONAL_DOC_STEMS are skipped; `pair_docs` is never consulted)` vs `coverage.md:§4 Invariants, INV-8`)
    - *evidence:*

    ```
    Doc INV-8: "Every path in `unmodeled` sits in a directory holding no candidate code file, so no file is ever both unmodeled and paired." (with §2 defining Pair as `{label, code[], docs[]}` — links code globs to spec doc(s)). Code, `unmodeled_markdown`: `for md in mds: d = os.path.dirname(md); if d in code_dirs: continue; if classify_exclude(md, user_excludes) == "user": continue; if os.path.splitext(os.path.basename(md))[0].lower() in CONVENTIONAL_DOC_STEMS: continue; ... groups.setdefault(top, []).append(md)` — no `pair_docs` check, unlike the orphan pass which does `if md in pair_docs: continue  # explicitly paired — governed, wherever its code is`. With `pairs: [{label: x, code: ['src/x.py'], docs: ['docs/x.md']}]` and three markdown files under `docs/`, `docs/x.md` is both explicitly paired and reported in `unmodeled`.
    ```

    - *fix:* Either pass the pair-declared doc set into `unmodeled_markdown` and `continue` on `md in pair_docs` (mirroring the orphan pass), or reword INV-8 to state only the directory condition and scope the pairing clause to same-stem pairing, e.g. "…so no file is ever both unmodeled and same-stem paired; explicitly pair-declared docs may still appear."

### Drift fingerprint

| Pair | High+med findings |
|---|---|
| `coverage` | ⚠ 1 |
