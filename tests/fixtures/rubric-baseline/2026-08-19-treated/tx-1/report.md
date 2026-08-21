# Drift report — `spec_eval`
detector: `claude-code` · 1/1 pairs audited · 2 model call(s)

**0 high/medium drift finding(s) across 1 audited pair(s).**

## coverage — ✓ clean
- ~~**[medium]** The doc uses an agent skill's `SKILL.md` as the canonical example of markdown the unmodeled detector surfaces, but the code filters every `SKILL.md` out as a conventional doc stem, so such a corpus is never reported.~~ (`coverage.py:L53 (CONVENTIONAL_DOC_STEMS) / unmodeled_markdown conventional-doc filter` vs `coverage.md:§3 "Unmodeled markdown detection"`)
    - *withdrawn on verification — not-normative:* The only line naming `SKILL.md` in §3 is the "Why:" rationale explaining what same-stem pairing cannot see, not a claim about which files the detector reports; §3's normative rule ("is not a conventional doc name") matches the code, and the doc's conventional-name enumeration is open-ended ("/ …").
    - *the doc says:* “**Why:** two real bodies of writing are invisible to a same-stem model — a spec tree keyed by requirement id (`spec/functional/FR-021-….md`) and behavior implemented AS markdown (an agent skill's `SKILL.md` and its references).”
- ~~**[low]** The Definitions table gates UNMODELED on "no code sibling", but the code gates it on the whole directory containing no candidate code file (§3 states this correctly).~~ (`coverage.py:unmodeled_markdown (`if d in code_dirs: continue`)` vs `coverage.md:§2 Definitions, UNMODELED row`)
    - *withdrawn on verification — stated-elsewhere:* §3 and INV-8 ("Every path in `unmodeled` sits in a directory holding no candidate code file") state the directory-level gate exactly as the code implements it, so the loose §2 table row does not make the document wrong.
    - *the doc says:* “A file qualifies when it sits in a directory holding no candidate code, is not user-excluded, and is not a conventional doc name.”
- **[low]** The module docstring describes a `.py`-only candidate universe and a pairs-only definition of COVERED, contradicting the spec's polyglot `code_ext` default and its three coverage routes. (`coverage.py:L4-L5 (module docstring)` vs `coverage.md:§2 Definitions, `code_ext` row; §3 "Determining coverage"`)
    - *evidence:*

    ```
    code docstring: "COVERED   = files matched by any pair's `code` globs in the config." / "CANDIDATE = repo code files (.py) minus the EXCLUDES taxonomy"; doc: "Default: `.py .ts .tsx .js .jsx .mjs .cjs .go .rs .java .rb .kt .kts .swift .php .cs`" and "COVERED | A code file matched by any config pair's `code` glob, OR having a sibling `<stem>.md`, OR (under `authoring.layout: per-dir`) whose directory has a folder spec" — which is what `DEFAULT_CODE_EXT` and the co-located/per-dir branches in `coverage()` actually implement.
    ```

    - *fix:* Update the module docstring to say the candidate universe is the configurable `code_ext` list (default polyglot) and that COVERED also includes co-located `<stem>.md` and per-dir folder specs.

### Drift fingerprint

| Pair | High+med findings |
|---|---|
| `coverage` | ✓ clean |
