# Drift report — `spec-eval`
detector: `claude-code` · 11/11 pairs audited · 18 model call(s)

**8 high/medium drift finding(s) across 11 audited pair(s).**

## audit — ⚠ 1 drift
- **[medium]** The per-side file count (and therefore the skip decision and the `code_files`/`doc_files` fields) counts only non-empty, readable files that were emitted, not the files the globs matched, so a side whose globs match only empty files is reported as having matched zero files. (`spec_eval/audit.py:L44` vs `spec_eval/audit.md:§2 "Skipped pair" / §3 "Skip semantics" / AC-1`)
    - *evidence:*

    ```
    Code: `if c.strip(): chunks.append(...)` … `return (text[:cap] + ...), len(chunks), capped`; then `if nc == 0 or nd == 0: return {..., "skipped": f"no files matched (code={nc}, docs={nd})", ...}`. Doc: "Skipped pair | A pair where either side matched **zero** files" and "**Skip semantics.** If either side matched zero files, the pair is **not** sent to the model"; AC-1: "A pair whose code globs match 3 files and doc globs match 2 files | audited | Result has `code_files=3`, `doc_files=2`".
    ```

    - *fix:* Either track matched-file count separately from contributed-section count (report `code_files`/`doc_files` as glob matches, skip only on zero matches), or reword the doc to say a pair is skipped when a side contributes zero readable non-empty files and that `code_files`/`doc_files` count contributing files.

## authoring — ⚠ 2 drift
- **[medium]** The doc says the data-flow diagram ends at the observed external systems, but the rubric in code mandates it terminate in the user-facing result and treats external systems only as boundary nodes. (`spec_eval/authoring.py:L161` vs `spec_eval/authoring.md:L72`)
    - *evidence:*

    ```
    Doc: "`diagram_block` builds just the repo's Architecture section body — an invocation sequenceDiagram (scanner-verified entry points, provenance-noted) plus a pure data-flow pipeline **ending at the observed external systems** — for the `diagram` subcommand". Code (`ARCH_DIAGRAM_RUBRIC`, subsection (b)): "It MUST span the pipeline end to end and TERMINATE in the user-facing result (a) shows the User receiving — generated samples, a served response, a written report. An intermediate artifact ... is NOT that result ... External systems come ONLY from the OBSERVED SYSTEM EVIDENCE block, **at the boundary**, joined by dashed -.-> edges labeled with the transfer". A repo with no observed external systems still gets a data-flow diagram, and it must end at the user-facing result node, not at an external system.
    ```

    - *fix:* Reword the doc to: "plus a pure data-flow pipeline that terminates in the user-facing result, with any observed external systems drawn at the boundary".
- **[medium]** The 'Freshness stamp' section describes only the conditional system-context fingerprint, but the repo OVERVIEW.md is also stamped unconditionally with an architecture fingerprint. (`spec_eval/authoring.py:L497` vs `spec_eval/authoring.md:L66`)
    - *evidence:*

    ```
    Doc: "**Freshness stamp.** When the repo `OVERVIEW.md` renders a System context section (an evidence block was present), an invisible `<!-- system-context-fingerprint: <digest> -->` comment (`syscontext.stamp_comment`) is appended to the file ... The per-dir `README.md` overviews are not stamped." Code (`_repo_overview`): "if syscontext.evidence_block(ctx): md = md.rstrip() + \"\\n\\n\" + syscontext.stamp_comment(ctx)" followed unconditionally by "md = md.rstrip() + \"\\n\\n\" + syscontext.architecture_stamp_comment(ctx, ep, files)". Two receipts can be written, one of them on every authored OVERVIEW.md regardless of evidence; `_STAMP_COMMENT_RE` likewise matches both `system-context` and `architecture` fingerprints.
    ```

    - *fix:* Add the architecture fingerprint to the Freshness stamp paragraph: state that `OVERVIEW.md` always receives `<!-- architecture-fingerprint: ... -->` (stamped from `ctx`, `ep`, and `module_set`), while the system-context fingerprint is written only when an evidence block was present.
- ~~**[low]** The Definitions table enumerates status as authored/skipped/failed and omits `stray`, which the code emits and the same doc lists elsewhere.~~ (`spec_eval/authoring.py:L560` vs `spec_eval/authoring.md:L32`)
    - *withdrawn on verification — stated-elsewhere:* The same document states the complete status set including `stray` in the Result reporting passage (and INV-15), so the loose Definitions row does not make the doc wrong.
    - *the doc says:* “**Result reporting.** Returns a list of records, one per target, each carrying `code`, `spec`, `status` (`authored` | `skipped` | `failed` | `stray`), and optionally `note`.”

## cli — ✓ clean
- ~~**[medium]** The generate result contract enumerates only two statuses, but the code produces (and branches on) four.~~ (`spec_eval/cli.py:L224-L227` vs `spec_eval/cli.md:L75`)
    - *withdrawn on verification — stated-elsewhere:* The §3 behavior narrative states the full four-status set correctly, so the document as a whole is not wrong about the statuses the code produces.
    - *the doc says:* “Writes `generated.json` and prints each result's status (`authored` / `skipped` / `failed` / `stray`), spec path, and any `note`”
- ~~**[medium]** The documented generate run-log key set omits `failed` and `stray`, which the code always writes.~~ (`spec_eval/cli.py:L235-L237` vs `spec_eval/cli.md:L53`)
    - *withdrawn on verification — not-asserted:* The cited line lists three logged keys but never says these are the only keys, so it does not carry the exhaustiveness the finding needs.
    - *the doc says:* “- Logs `authored`, `skipped`, and `flagged` (targets whose record carries a `note` — e.g. a partial view).”
- ~~**[medium]** The `cov` result-shape contract omits the `unmodeled` field the coverage branch reads and logs.~~ (`spec_eval/cli.py:L260,L267` vs `spec_eval/cli.md:L73`)
    - *withdrawn on verification — stated-elsewhere:* The same document's §3 coverage narrative states that the coverage result carries unmodeled markdown groups (printed as ⚠ `unmodeled:` lines and logged as `unmodeled_md`), so the doc does state the property the finding says is missing.
    - *the doc says:* “Logs `coverage_pct`, `covered`, `spec_worthy`, `orphans`, and `unmodeled_md`.”
- **[low]** `context --check` is documented as reading `<repo>/OVERVIEW.md`, but the code falls back to `README.md` when OVERVIEW.md is absent. (`spec_eval/cli.py:L293` vs `spec_eval/cli.md:L56`)
    - *evidence:*

    ```
    doc: "It also reads `<repo>/OVERVIEW.md` and prints a ⚠ *overview stale* warning …"  code: `overview_path = _diagram_target(args.repo)  # OVERVIEW.md, else README.md — the doc`, whose helper loops `for name in ("OVERVIEW.md", "README.md")`.
    ```

    - *fix:* Reword to "reads `<repo>/OVERVIEW.md`, else `<repo>/README.md`" to match the same target resolution `diagram --write` uses.
- ~~**[low]** The "Artifacts & logging" paragraph claims every command creates `--out`, writes JSON+Markdown, and calls `append_run`, none of which the `diagram` branch does.~~ (`spec_eval/cli.py:L330-L360` vs `spec_eval/cli.md:L64`)
    - *withdrawn on verification — stated-elsewhere:* The invariant table (and the diagram narrative's "writes nothing — no `--out`, no report, no run log") states the diagram exception correctly, so the loose "Every command" sentence is not the document's rule.
    - *the doc says:* “| INV-6 | `diagram` with neither `--write` nor `--add-section` writes nothing: it prints the mermaid block to stdout only (no `--out`, no report, no run log); progress and the usage summary go to stderr. |”

## coverage — ⚠ 1 drift
- **[medium]** `unmodeled_markdown` never consults the config pairs' `docs` globs, so an explicitly pair-declared spec that lives in a docs-only directory is reported as unmodeled — contradicting INV-8's claim that no file is ever both unmodeled and paired. (`spec_eval/coverage.py:L119` vs `spec_eval/coverage.md:§4 INV-8`)
    - *evidence:*

    ```
    Code (`unmodeled_markdown`) filters only on directory, user-excludes and conventional stems: `if d in code_dirs: continue` / `if classify_exclude(md, user_excludes) == "user": continue` / `if os.path.splitext(os.path.basename(md))[0].lower() in CONVENTIONAL_DOC_STEMS: continue` — `pair_docs` is built only inside `coverage()` for the orphan pass (`if md in pair_docs: continue  # explicitly paired — governed, wherever its code is`) and is never passed to `unmodeled_markdown`. Doc: "INV-8 | Every path in `unmodeled` sits in a directory holding no candidate code file, so no file is ever both unmodeled and paired." with "Pair | `{label, code[], docs[]}` — links code globs to spec doc(s)." So a config `pairs: [{docs: ["docs/*.md"]}]` covering 3+ docs in a docs-only dir yields a group the report labels "outside the same-stem pairing model" even though those docs are paired.
    ```

    - *fix:* Thread `pair_docs` into `unmodeled_markdown` and skip any `md in pair_docs` (mirroring the orphan pass), or restate INV-8 as "no file is ever both unmodeled and *same-stem* paired".
- ~~**[medium]** `SKILL.md` — the doc's headline example of markdown that should be reported as unmodeled — is filtered out by `CONVENTIONAL_DOC_STEMS`, which contains `"skill"`.~~ (`spec_eval/coverage.py:L52` vs `spec_eval/coverage.md:§3 Unmodeled markdown detection`)
    - *withdrawn on verification — not-normative:* The only place `SKILL.md` is named as an unmodeled example is this "**Why:**" rationale sentence; the section's normative rule ("A file qualifies when it sits in a directory holding no candidate code, is not user-excluded, and is not a conventional doc name") and AC-4 (`skills/*/reference.md`) make no claim that `SKILL.md` itself is reported.
    - *the doc says:* “**Why:** two real bodies of writing are invisible to a same-stem model — a spec tree keyed by requirement id (`spec/functional/FR-021-….md`) and behavior implemented AS markdown (an agent skill's `SKILL.md` and its references).”
- **[low]** The module docstring's glossary is stale: it defines COVERED as pair-glob matches only and CANDIDATE as `.py` files already minus the exclusion taxonomy, contradicting the spec's definitions and the language-agnostic implementation. (`spec_eval/coverage.py:L4` vs `spec_eval/coverage.md:§2 Definitions`)
    - *evidence:*

    ```
    Code docstring: "COVERED   = files matched by any pair's `code` globs in the config." / "CANDIDATE = repo code files (.py) minus the EXCLUDES taxonomy …". Implementation and doc disagree: `DEFAULT_CODE_EXT = (".py", ".ts", … ".cs")`, `covered` also grows via the co-located `<stem>.md` and `per-dir` folder-spec branches, and the doc says "CANDIDATE | Every code file under the repo (by extension), minus pruned directories" with "SPEC-WORTHY | CANDIDATE minus all excluded files".
    ```

    - *fix:* Update the module docstring to match: COVERED = pair glob OR sibling `<stem>.md` OR per-dir folder spec; CANDIDATE = all `code_ext` files minus pruned dirs; SPEC-WORTHY = CANDIDATE minus the exclusion tiers.

## providers — ✓ clean

## report — ✓ clean

## rubric — ✓ clean

## runlog — ✓ clean

## sufficiency — ⚠ 1 drift
- **[medium]** The spec says the `truncated` field is present only when an input side exceeded its cap, but the shared helper also adds a note when the model's reply hit the token cap, so `truncated` can appear with neither input cut. (`spec_eval/sufficiency.py:L39` vs `spec_eval/sufficiency.md:L64-65`)
    - *evidence:*

    ```
    Code — sufficiency.py L39 delegates to the shared helper: `notes = audit.truncation_notes(code_capped, doc_capped, code_cap, doc_cap)`; audit.py L95-99: `notes = ([f"code input capped at ~{code_cap:,} chars"] if code_capped else []) + ([f"docs input capped at ~{doc_cap:,} chars"] if doc_capped else []); if providers.LAST["truncated"]: notes.append("reply hit the token cap")` — so `if notes: rec["truncated"] = notes` fires on reply truncation alone. Doc — sufficiency.md: "Either live shape may carry `truncated` — a list of partial-view notes (an input side over its cap), present only when an input was cut." The sibling spec states it correctly (audit.md L47: "an input side over its cap, and/or the model reply cut off at the token cap").
    ```

    - *fix:* Reword sufficiency.md §4 to match audit.md: "`truncated`, present only when something was cut, is a list of partial-view notes (an input side over its cap, and/or the model reply cut off at the token cap)."

## syscontext — ⚠ 2 drift
- **[medium]** `evidence_block` returns `""` before it can append the `Not scanned:` language-gap line, so a repo with only unsupported source files produces no gap statement in the evidence block that INV-7 names as one of its three carriers. (`spec_eval/syscontext.py:L614` vs `spec_eval/syscontext.md:L49`)
    - *evidence:*

    ```
    Code (`evidence_block`): `entries = _scoped(result, scope_dir)` / `if not entries:` / `        return ""` — the `note = unscanned_note(result)` / `if note and scope_dir is None:` branch is unreachable in that case. Doc L49: "every surface that shows the inventory carries the fixed `Not scanned: …` line — the CLI summary, the report, and the repo-level evidence block"; INV-7 (L81) repeats "surfaced with the fixed `Not scanned:` line in the CLI output, the report, and the repo-level evidence block — a language gap is stated, never silent." This is exactly the case the doc calls the worst failure shape ("a confidently near-empty report on a repo it couldn't read"), and it also collides with INV-6 (L80).
    ```

    - *fix:* Either emit the gap line alone when there are no entries but `unscanned` is non-empty (keeping INV-6's "no System context section" contract by making it a standalone note), or amend INV-7/L49 to carve out the empty-entry case explicitly ("…the repo-level evidence block, except when the block is empty per INV-6, where the report and CLI carry it").
- **[medium]** `_scoped` overwrites `evidence_total` with the count of in-scope sites, so a scoped entry's `evidence_total` is neither repo-wide nor a count of every observed site in that directory once the per-directory cap bites. (`spec_eval/syscontext.py:L593` vs `spec_eval/syscontext.md:L19`)
    - *evidence:*

    ```
    Code: `scoped.append({**rec, "evidence": ev, "evidence_total": len(ev)})   # kept in-scope sites` — `ev` is already truncated to at most `EVIDENCE_CAP` sites per directory by `add()`. Doc L19: "`evidence_total` always counts all of them repo-wide"; INV-5 (L79): "`evidence_total` still counts every observed site — capping is visible, never silent." With 12 Redis sites in one directory, the per-dir `evidence_block` renders "(+7 more site(s))" and the four dropped sites are silent.
    ```

    - *fix:* Either carry the true in-scope observed count through `add()` (e.g. a per-directory tally alongside `evidence_total`) so the scoped view can report it, or document in §2/INV-5 that `_scoped`/`evidence_block(scope_dir=…)` recomputes `evidence_total` as the number of retained in-scope sites.
- ~~**[low]** The Reduction paragraph says evidence sites are "capped at `EVIDENCE_CAP`", omitting the per-directory qualifier the code actually implements (and that §2/INV-5 state correctly).~~ (`spec_eval/syscontext.py:L413` vs `spec_eval/syscontext.md:L41`)
    - *withdrawn on verification — stated-elsewhere:* The per-directory qualifier is stated correctly in §2's evidence-site definition and in INV-5, so the loose Reduction narrative does not make the document wrong.
    - *the doc says:* “At most `EVIDENCE_CAP` sites are kept per entry **per directory** (so per-dir scoping always finds a dir's own sites); `evidence_total` always counts all of them repo-wide.”

## verify — ⚠ 1 drift
- **[high]** The `not-asserted` position/presence check is silently skipped whenever the finding's `doc_ref` carries no parseable line number (or is null), so a withdrawal quoting text that appears nowhere in the document survives — contradicting INV-4 and AC-9, which state the conversion to `upheld` unconditionally. (`spec_eval/verify.py:L123` vs `spec_eval/verify.md:L50`)
    - *evidence:*

    ```
    Code (verify.py:L121-124): `want = _cited_line(finding.get("doc_ref"))` / `quote = (verdict.get("doc_quote") or "").strip()` / `if want is None or not quote:` / `return verdict  # nothing to check against; leave the model's call alone` — the absent-quote branch at L127 (`if not hits: ... upheld`) is never reached for such findings. `_cited_line` returns None for a null `doc_ref` or one without a `:L<n>` component, and the audit finding schema permits `"doc_ref": "file:Lxx or null"`. Doc (verify.md:L50, INV-4): "A `not-asserted` withdrawal whose quote is absent from the document, or found only outside the window around the cited line, is converted to `upheld`." Doc (verify.md:L66, AC-9): "A `not-asserted` withdrawal quoting text that appears nowhere in the document | checked | Converted to `upheld`, with the why naming the absent quote." Doc (verify.md:L35): "the quoted line must appear in the document at all, and within a small window of the line the finding cited. A quote found nowhere is rejected outright". Doc (verify.md:L5) also makes the quote load-bearing: "each settled by quoting one line that exists; a finding that cannot be withdrawn on a named ground with a quote is upheld" — yet an empty `doc_quote` likewise takes the early return and the withdrawal stands.
    ```

    - *fix:* Split the two checks so the presence test is unconditional for `not-asserted`: reject the withdrawal when the quote is empty, and when the quote is non-empty run the `hits` search regardless of `want`, applying the window comparison only when `want is not None`. E.g. `if not quote: return upheld(...)`; `hits = [...]`; `if not hits: return upheld("quoted line does not appear in the document")`; `if want is not None and not any(abs(h-want) <= window for h in hits): return upheld(position message)`. Alternatively, if skipping the check for line-less `doc_ref`s is intended, state that exception in INV-4/AC-9 and in §3.

### Drift fingerprint

| Pair | High+med findings |
|---|---|
| `audit` | ⚠ 1 |
| `authoring` | ⚠ 2 |
| `cli` | ✓ clean |
| `coverage` | ⚠ 1 |
| `providers` | ✓ clean |
| `report` | ✓ clean |
| `rubric` | ✓ clean |
| `runlog` | ✓ clean |
| `sufficiency` | ⚠ 1 |
| `syscontext` | ⚠ 2 |
| `verify` | ⚠ 1 |
