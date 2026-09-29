# Drift report — `spec-eval`
detector: `claude-code` · 12/12 pairs audited · 23 model call(s)

**12 high/medium drift finding(s) across 12 audited pair(s).**

## audit — ⚠ 1 drift
- **[medium]** The doc defines the rubric as fixed, but the code lets a config key `rubric.drift` replace `DRIFT_RUBRIC` with the contents of a file path for every pair in the run. (`spec_eval/audit.py:L108-L138 (rubric_from), L207 (audit_repo)` vs `spec_eval/audit.md:L24`)
    - *evidence:*

    ```
    doc (L24): "| Rubric | `DRIFT_RUBRIC`, the fixed system prompt sent with every pair. |"
    code (L207-L208): `rubric = rubric_from(config, "drift", DRIFT_RUBRIC, repo)` / `return [audit_pair(repo, p, model, code_cap, doc_cap, markers, rubric) for p in pairs]`
    code (L192): `providers.gen(model, rubric or DRIFT_RUBRIC, user, ...)`
    code (L109): "The grading rubric, config-overridable per check: `rubric: {sufficiency, drift}` → a FILE path."
    ```

    - *fix:* Reword the Rubric row to "`DRIFT_RUBRIC` by default, config-overridable per check via `rubric: {drift}` pointing at a file path; the resolved rubric is the system prompt sent with every pair", and add a Behavior note that a missing or empty rubric file is a hard error (`SystemExit`), never a silent fallback.
- ~~**[medium]** The Config shape in the Definitions table (and the Contracts section) enumerates the optional config keys but omits `rubric`, which the code reads.~~ (`spec_eval/audit.py:L127 (rubric_from)` vs `spec_eval/audit.md:L16`)
    - *withdrawn on verification — not-asserted:* The cited line enumerates optional keys but never says these are the only or all permitted keys, so listing three does not amount to the exhaustiveness claim the finding needs.
    - *the doc says:* “| Config | A YAML or JSON document of shape `{pairs: [...][, caps: {code, docs}][, rationale_markers: [...]]}`. |”

## authoring — ⚠ 1 drift
- ⚠ *partial view (docs input capped at ~28,000 chars) — findings may be incomplete*
- *2 rationale line(s) masked before review — non-normative clauses are not shown to the model*
- **[medium]** AC-16 specifies link repair inside an `OVERVIEW.md` sitting at `src/a/`, but `generate_repo` only ever writes `OVERVIEW.md` at the repo root, where the repair branch is dead by construction, so the criterion can never be met as written. (`spec_eval/authoring.py:L607` vs `spec_eval/authoring.md:L169`)
    - *evidence:*

    ```
    Doc (AC-16): "| `OVERVIEW.md` at `src/a/`, link written as `(src/a/list.md)`, that file exists | `generate_repo` runs | the written link is `(list.md)` and the repair count appears in the note. |"
    
    Code (`generate_repo`, the only OVERVIEW.md write path): `md, fixed, broken = repair_links(md, repo, "OVERVIEW.md")` … `emit("OVERVIEW.md", ".", _repo_overview, …)` — the doc path is hard-coded to the repo root, so `doc_dir = os.path.dirname("OVERVIEW.md")` is `""`. In `repair_links` the two probes then collapse to the same test: `os.path.exists(os.path.join(repo, doc_dir, path))` == `os.path.exists(os.path.join(repo, path))`, so a link either returns early unchanged or falls through to `broken` — `fixed` is always 0 and no repair count can appear in the note. The only overview the repair can fire on is the per-dir `os.path.join(d, "README.md")`, repaired via `repair_links(md, repo, readme)`.
    ```

    - *fix:* Restate AC-16 against the surface that actually exercises the repair: "Given a per-dir `README.md` at `src/a/` whose link is written as `(src/a/list.md)` and that file exists, When `generate_repo` runs, Then the written link is `(list.md)` and the repair count appears in the note." (The same mis-located `src/a/OVERVIEW.md` example appears in the §3 'Resolving links from the document' paragraph and in `repair_links`' own docstring; update those to `src/a/README.md` too so the illustration matches a reachable path.)

## cli — ⚠ 3 drift
- **[high]** The doc guarantees every command but `diagram` writes a JSON + Markdown pair and appends a run record, but the `compare` command writes only `compare.json` and never calls `runlog.append_run`. (`spec_eval/cli.py:L257-L297` vs `spec_eval/cli.md:L64`)
    - *evidence:*

    ```
    doc: "**Artifacts & logging.** Every command except `diagram` creates `--out` if needed, writes both a JSON and (except generate, which writes only JSON) a Markdown file, and calls `runlog.append_run` with the command, repo, model … `diagram` has no `--out` at all: it never writes an artifact there and never appends a run record"
    code: `elif args.cmd == "compare": os.makedirs(args.out, exist_ok=True) … json.dump(res, open(os.path.join(args.out, "compare.json"), "w"), indent=2) … print(f"wrote compare.json → {os.path.abspath(args.out)}")` — no Markdown write and no `runlog.append_run(...)` anywhere in the branch.
    ```

    - *fix:* Amend the Artifacts & logging paragraph to carve out `compare` alongside `generate`/`diagram`: it creates `--out`, writes `compare.json` only (no Markdown), and appends no run record — or add a `runlog.append_run(..., "compare", ...)` call and a `compare.md` writer to match the stated rule.
- **[medium]** The CLI exposes a seventh subcommand, `compare`, that the doc's capability list and command-surface enumeration omit entirely. (`spec_eval/cli.py:L103-L115` vs `spec_eval/cli.md:L38`)
    - *evidence:*

    ```
    doc: "the command-line surface for the six checks" … "**Command surface.** A required subcommand selects the capability: `audit`, `sufficiency`, `generate`, `coverage`, `context`, `diagram`."
    code: `_cmp = sub.add_parser("compare", help="COMPARE two `--reps` runs — noise share, vendor delta against its standard error, and TOST equivalence. Makes NO model calls.")` with positionals `a` (`REPS_A.json`) / `b` (`REPS_B.json`) and flags `--margin`, `--out/-o`, `--allow-sha-mismatch`.
    ```

    - *fix:* Add `compare` to the capability list (seven checks) and to the command-surface enumeration, documenting its two positional reps files and `--margin` / `--out` / `--allow-sha-mismatch` flags, plus the `SystemExit(2)` on a refused comparison.
- ~~**[medium]** `sufficiency` accepts `--max-calls` and `--reps` and can write a third artifact, `sufficiency-reps.json`, none of which the doc mentions.~~ (`spec_eval/cli.py:L98-L101` vs `spec_eval/cli.md:L38`)
    - *withdrawn on verification — not-asserted:* The cited line calls it a *base* argument set and never says sufficiency accepts only these flags or writes only two artifacts, so the finding supplies an exhaustiveness the line does not carry.
    - *the doc says:* “`audit` and `sufficiency` share a base argument set (`repo`, `--config/-c`, `--model/-m`, `--out/-o`, `--env`, `--fingerprint/--no-fingerprint`); `audit` adds `--verify`.”
- ~~**[medium]** The doc says `generate` logs three metrics, but the code logs five — `failed` and `stray` are also written to the run log.~~ (`spec_eval/cli.py:L334-L335` vs `spec_eval/cli.md:L53`)
    - *withdrawn on verification — not-asserted:* The cited line lists three logged metrics without "only"/"exactly", and it remains true of code that also logs `failed` and `stray`.
    - *the doc says:* “- Logs `authored`, `skipped`, and `flagged` (targets whose record carries a `note` — e.g. a partial view).”
- **[medium]** The audit section describes the summary count and run log only in terms of *audited* pairs, but the code introduces a separate *graded* denominator that it both prints and logs as `pairs_graded`. (`spec_eval/cli.py:L200-L208` vs `spec_eval/cli.md:L44`)
    - *evidence:*

    ```
    doc: "Prints the count of high/medium drift findings across *audited* pairs (pairs not marked `skipped`) … Logs `high_med_drift`, `pairs_audited`, `pairs_truncated`, and a per-module drift load."
    code: `graded = sum(1 for r in results if not r.get("skipped") and not report.not_graded(r))` … `if graded != audited: print(f"{total} high/medium drift finding(s) across {graded} graded pair(s) ({audited} attempted, {len(results)} total).")` … `{"high_med_drift": total, "pairs_audited": audited, "pairs_graded": graded, "pairs_truncated": truncated, …}`
    ```

    - *fix:* Describe the graded-vs-attempted distinction (an ungraded pair stays in the denominator rather than reading as clean) and add `pairs_graded` to the list of logged metrics.
- **[low]** The `--check` gate is documented as reading `<repo>/OVERVIEW.md`, but the code resolves the staleness target as OVERVIEW.md *or*, failing that, README.md. (`spec_eval/cli.py:L391-L393` vs `spec_eval/cli.md:L56`)
    - *evidence:*

    ```
    doc: "It also reads `<repo>/OVERVIEW.md` and prints a ⚠ *overview stale* warning when the overview's system-context fingerprint stamp no longer matches the fresh scan"
    code: `overview_path = _diagram_target(args.repo)` where `_diagram_target` iterates `for name in ("OVERVIEW.md", "README.md")`, and the warning prints `doc = os.path.basename(overview_path)`.
    ```

    - *fix:* Change the phrase to "reads `<repo>/OVERVIEW.md` (or `README.md` if no OVERVIEW.md exists)", matching the resolution order already documented for `diagram --write`.

## compare — ⚠ 2 drift
- **[high]** A pair whose `sufficiency` is null in every rep of *both* inputs is silently discarded in `load_reps` and can never appear in `dropped_pairs`, violating AC-2/INV-1's promise that an unscored pair is listed rather than silently dropped. (`spec_eval/compare.py:L181` vs `spec_eval/compare.md:L87`)
    - *evidence:*

    ```
    code: `if s is None: continue` (L127) means the label never enters `by_label`; `compare` then computes `dropped = sorted((set(la) | set(lb)) - set(shared))` (L181) — a label missing from *both* `la` and `lb` is in neither the union nor `shared`, so it is reported nowhere. doc: "**AC-2** | a pair with `sufficiency: null` in every rep | that pair appears in `dropped_pairs`" and "**INV-1** … A pair either vendor failed to score is excluded and listed."
    ```

    - *fix:* Have `load_reps` also return the set of labels seen but unscored (e.g. `null_labels`), and union it into `dropped` in `compare` so a pair both vendors failed to score is still listed in `dropped_pairs`.
- **[medium]** INV-11 states `noise_share` carries a `definition` field on every emission, but the one-rep return path emits `noise_share` with no `definition` key. (`spec_eval/compare.py:L149` vs `spec_eval/compare.md:L72`)
    - *evidence:*

    ```
    doc: "**INV-11** `noise_share` **rises with noise** — it is the complement of a classic ICC, and carries a `definition` field saying so on every emission." code (L149-152): `return {"within_vendor_variance": None, "total_variance": None, "noise_share": None, "unavailable_because": …, "pairs_with_replication": 0}` — no `definition`; only the fully-computed branch sets `"definition": "within-vendor variance / total variance; RISES with noise…"` (L160). The unreachable `len(all_scores) < 2` branch (L154) omits it too.
    ```

    - *fix:* Add the same `definition` string to both early-return branches of `noise()` (or build the dict from one shared base that always includes `definition`).
- **[low]** The `noise()` docstring calls this quantity "the spec's `ICC` field", but the spec has no `ICC` field — it names the emitted key `noise_share` (which is what the code actually emits). (`spec_eval/compare.py:L136` vs `spec_eval/compare.md:L54`)
    - *evidence:*

    ```
    code (L136): "Within-vendor variance as a share of total — the spec's `ICC` field" and (L139) "It is reported under the name the programme pre-registered". doc (L54): "| `noise.<vendor>.noise_share` | Within-vendor variance ÷ total |"; the only mention of ICC is INV-11's "it is the complement of a classic ICC".
    ```

    - *fix:* Update the docstring to say the field is emitted as `noise_share` (the complement of a classic ICC), removing the stale reference to a spec `ICC` field.

## coverage — ✓ clean
- *10 rationale line(s) masked before review — non-normative clauses are not shown to the model*
- ~~**[low]** The Definitions row defines UNMODELED markdown as having "no code sibling", but the implementation (and the doc's own §3 and INV-8) require the file's whole directory to contain no candidate code.~~ (`spec_eval/coverage.py:L119` vs `spec_eval/coverage.md:L22`)
    - *withdrawn on verification — stated-elsewhere:* The §3 behavior narrative (L63) and INV-8 (L101) both state the directory-level rule exactly as the code implements it; the Definitions row at L22 is a loose gloss of the same rule, so the document is not wrong.
    - *the doc says:* “Markdown that same-stem pairing cannot reach is grouped by top-level directory and reported when a group holds at least 3 files. A file qualifies when it sits in a directory holding no candidate code, is not user-excluded, and is not a conventional doc name.”

## providers — ⚠ 1 drift
- **[medium]** The spec's definitions table says `max_tokens` is not passed to OpenAI, but the v1/responses fallback path forwards it as `max_output_tokens`. (`spec_eval/providers.py:L148` vs `spec_eval/providers.md:L16`)
    - *evidence:*

    ```
    doc (§2 Definitions): "| `max_tokens` | Upper bound on generated output tokens. Default 1200. Applies to Anthropic and Google; not passed to OpenAI or the `claude-code` bridge. |"  —  code (`_gen_openai_responses`): "r = client.responses.create(model=model, instructions=system, input=user, max_output_tokens=max_tokens)", reached from `gen` via "return _gen_openai_responses(client, model, system, user, max_tokens)". Only the chat-completions path omits the cap.
    ```

    - *fix:* Amend the definitions row to: "Applies to Anthropic, Google, and the OpenAI v1/responses fallback (as `max_output_tokens`); not passed to OpenAI chat completions or the `claude-code` bridge."
- ~~**[medium]** The process-wide call ceiling (`MAX_CALLS`, `set_max_calls`, `CallBudgetExceeded`, the pre-call `_guard()`) is a public part of the module that the spec's Error semantics and Contracts sections never mention.~~ (`spec_eval/providers.py:L167` vs `spec_eval/providers.md:L51`)
    - *withdrawn on verification — not-asserted:* The cited line makes a single positive statement about unrecognized providers and contains no exhaustiveness word (only/all/never), so it does not assert that the module raises no other errors or that the Contracts list is the complete public surface — indeed the doc documents another error path elsewhere ("Fails loudly if the CLI is not on PATH", AC-13).
    - *the doc says:* “**Error semantics.** An unrecognized provider raises `ValueError` naming the offending provider and listing the valid prefixes.”

## report — ✓ clean
- *2 rationale line(s) masked before review — non-normative clauses are not shown to the model*
- ~~**[medium]** The Purpose section (and the `write_markdown` return-value contract) promises the headline equals the total high+medium findings shown below it, but the headline counts `drift_load`, which excludes findings that are `stale` or withdrawn — so the two disagree whenever such a finding is rendered.~~ (`spec_eval/report.py:L18` vs `spec_eval/report.md:L7`)
    - *withdrawn on verification — stated-elsewhere:* The same document states the rule correctly in the Definitions table ("Drift load" excludes withdrawn and `stale` findings; "Stale finding" is "Shown in the report, not counted in the drift load"), in the Behavior section ("a `stale` finding renders `**[stale · severity]**` and does not raise that count"), and in AC-11/AC-13 — the Purpose line and the contract row are the loose passages, not a wrong document.
    - *the doc says:* “| AC-13 | One pair with one `drift` and one `stale` high finding | `write_markdown` | headline reads `1 high/medium drift finding(s)`; both findings appear; the stale one renders `**[stale · high]**`. |”

## rubric — ✓ clean
- ~~**[medium]** The Definitions table's `Finding` row enumerates a finding's fields but omits `class`, which the rubric's output schema requires on every finding.~~ (`spec_eval/rubric.py:L43` vs `spec_eval/rubric.md:L18`)
    - *withdrawn on verification — stated-elsewhere:* The Definitions row at L18 is a loose gloss of the term, while the same document states the finding's field set correctly — including `class` — in §3 (L47) and the §4 output-shape contract (L58), so the document is not wrong.
    - *the doc says:* “**Output format.** The reviewer must emit strict JSON with no preamble: an object with a `findings` array. Each finding carries `severity`, `class`, `code_ref`, `doc_ref`, `summary`, `evidence`, and `suggestion`. When no drift exists, the output is `{"findings": []}`.”

## runlog — ✓ clean

## sufficiency — ⚠ 3 drift
- *4 rationale line(s) masked before review — non-normative clauses are not shown to the model*
- **[medium]** The spec says `truncated` is present only when an input side was cut, but the code also populates it when the model's reply hit the output-token cap, so the key appears with no input truncation. (`spec_eval/sufficiency.py:L39 (via spec_eval/audit.py:truncation_notes L171-178)` vs `spec_eval/sufficiency.md:L64-65`)
    - *evidence:*

    ```
    doc: "Either live shape may carry `truncated` — a list of partial-view notes (an input side over its cap), present only when an input was cut."  code: `notes = audit.truncation_notes(code_capped, doc_capped, code_cap, doc_cap)` where `truncation_notes` does `if providers.LAST["truncated"]: notes.append("reply hit the token cap")` in addition to the two input-cap notes.
    ```

    - *fix:* Reword §4 to: `truncated` is a list of partial-view notes — one per input side over its cap, plus a `reply hit the token cap` note when the model's response was cut — present whenever any of those occurred.
- **[medium]** The documented model call states the system prompt is always `SUFFICIENCY_RUBRIC`, but the code passes a config-overridable rubric loaded by `audit.rubric_from(config, "sufficiency", ...)`, which the spec never mentions. (`spec_eval/sufficiency.py:L38,L67` vs `spec_eval/sufficiency.md:L53`)
    - *evidence:*

    ```
    doc: "**Model call:** `providers.gen(model, SUFFICIENCY_RUBRIC, user, max_tokens=audit.REVIEW_MAX_TOKENS)`"  code: `resp = providers.gen(model, rubric or SUFFICIENCY_RUBRIC, user, max_tokens=audit.REVIEW_MAX_TOKENS)` and `rubric = audit.rubric_from(config, "sufficiency", SUFFICIENCY_RUBRIC, repo)`.
    ```

    - *fix:* State the contract as `providers.gen(model, rubric or SUFFICIENCY_RUBRIC, ...)` and document that `rubric.sufficiency` in the config replaces the built-in rubric (`SUFFICIENCY_RUBRIC` is the default only).
- **[medium]** The spec bounds the result's `sufficiency` to `[0.0, 1.0]`, but the parser coerces whatever the model returned to float with no range check or clamp, so an out-of-range score propagates into the result. (`spec_eval/sufficiency.py:L51` vs `spec_eval/sufficiency.md:L23,L56`)
    - *evidence:*

    ```
    doc: "| sufficiency | Score in `[0.0, 1.0]` ... |" and "`{label, code_files, doc_files, sufficiency: float∈[0,1], ...}`"  code: `"sufficiency": float(d.get("sufficiency", 0))` — no clamping or validation.
    ```

    - *fix:* Either clamp on parse (e.g. `min(1.0, max(0.0, float(...)))`) or drop the `∈[0,1]` bound from the result-shape contract and say the score is the model's value coerced to float.

## syscontext — ✓ clean
- **[low]** The doc says `diff_receipt` renders one delta line per changed system *with an evidence site*, but `_delta_lines` emits removed systems with no `file:line` at all. (`spec_eval/syscontext.py:L737` vs `spec_eval/syscontext.md:L51`)
    - *evidence:*

    ```
    Doc (syscontext.md:51): "`diff_receipt` renders the outcome as named `+`/`-` delta lines in the SPEC-HEALTH click-to-verify style — one line per changed system with an evidence site, never a full-table reprint or an evidence-churn row."
    
    Code (syscontext.py:733-737):
    '''
        for e in d["added"]:
            ev = f" — {e['evidence']}" if e["evidence"] else ""
            lines.append(f"  + {e['system']} ({e['direction']}, via {', '.join(e['via'])}){ev}")
        for e in d["removed"]:
            lines.append(f"  - {e['system']} ({e['direction']})")
    '''
    Only the `added` branch appends `ev`; the `removed` branch drops both `via` and the evidence ref, even though `_delta_entry` computed one from the baseline. (AC-21 in the same doc — "`added` = Redis (with a `file:line`), `removed` = PostgreSQL" — describes the diff dict, not the receipt, so the §3 sentence is the only statement about receipt rendering and it overclaims.)
    ```

    - *fix:* Reword the doc sentence to "one line per changed system, each added system with an evidence site (a removed system has no current site to cite)" — or, if the click-to-verify guarantee is meant to hold for both, render the baseline's `e['evidence']` on the `-` lines too.

## verify — ⚠ 1 drift
- **[medium]** The spec states the verification call carries the whole document, but `verify_pair` reads the doc side through the same character cap as the audit and silently sends a truncated document when the pair's docs exceed it. (`spec_eval/verify.py:L147` vs `spec_eval/verify.md:L25`)
    - *evidence:*

    ```
    Doc (verify.md:25): "Verification is **per pair, not per finding**. One call carries the whole document plus every finding raised on that pair, because the question is *does this document say it* and half a document cannot answer that."
    
    Code (verify.py:142-147):
        def verify_pair(repo, pair, findings, model, code_cap=audit.CODE_CAP, doc_cap=audit.DOC_CAP):
            ...
            doc, nd, _ = audit._read_globs(repo, pair.get("docs", []), doc_cap)
    
    and `audit._read_globs` truncates (audit.py:53-55):
        text = "\n\n".join(chunks)
        capped = len(text) > cap
        return (text[:cap] + ("\n...[truncated]" if capped else "")), len(chunks), capped
    
    with `DOC_CAP = 28000` (audit.py:24). The `capped` flag is discarded (`_`), so unlike `audit_pair` — which records it via `truncation_notes` into `rec["truncated"]` — the verify pass surfaces no partial-view note. Sibling specs state the cap explicitly (audit.md:21 "capped at the doc cap (`caps.docs`, default **28 000 chars**)"; sufficiency.md:20 likewise); verify.md instead asserts the whole document.
    ```

    - *fix:* Either state the cap in verify.md §3 ("one call carries the pair's document, capped at the doc cap (`caps.docs`, default 28 000 chars), plus every finding raised on that pair") and add a note/invariant for the truncated case, or keep the guarantee and make the code honour it — surface the discarded `capped` flag as a partial-view note on the record so a verification run against a truncated document is visible to the reader.

### Drift fingerprint

| Pair | High+med findings |
|---|---|
| `audit` | ⚠ 1 |
| `authoring` | ⚠ 1 |
| `cli` | ⚠ 3 |
| `compare` | ⚠ 2 |
| `coverage` | ✓ clean |
| `providers` | ⚠ 1 |
| `report` | ✓ clean |
| `rubric` | ✓ clean |
| `runlog` | ✓ clean |
| `sufficiency` | ⚠ 3 |
| `syscontext` | ✓ clean |
| `verify` | ⚠ 1 |
