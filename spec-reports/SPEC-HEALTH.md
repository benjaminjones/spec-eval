# SPEC-HEALTH — spec-eval (self-audit)

> **The measurement layer. REGENERATED, never hand-edited** (only the verdict line + run history are human-written).
> Specs carry *intent*; this file carries the dated *evidence* that they still match the code.
> **Litmus:** a fact true regardless of who audited it → a spec. A score with a model + date that changes on
> re-run without the code changing → here.

**spec-eval** **specs itself**: every module in [`spec_eval/`](../spec_eval/) has a co-located `<module>.md` intent spec,
authored by `spec-eval generate` and graded by its own `audit` / `sufficiency` checks (scope:
[`configs/self-audit.yml`](../configs/self-audit.yml) — the shippable package). This is the dogfood — the raw
reports sit beside this file.

## Verdict
> **Coverage 100%** (12/12 modules) · **drift 12** high/medium · **sufficiency 0.82** avg (1.0 = no gaps found —
> an indicator, not a guarantee) as of 2026-09-29, detector **`claude-code`**, **verified** (`audit --verify`).
> The 12th module, `compare`, is graded here for the first time.
> **Drift is 12, up from 8, and the tree it measures is not the tree the last row measured.** Since 2026-08-06
> the package gained a subcommand and a module (`compare`), a process-wide call ceiling in `providers`, and
> `--max-calls` / `--reps` on `sufficiency` — none of which the specs describe. That is where the increase sits:
> `cli` went 0→3 and its sufficiency fell 0.86→0.62, `compare` arrives at 0→2, `providers` 0→1. **The code grew
> and the specs did not follow.** Nine of the twelve are doc-accuracy gaps of the usual kind.
> **One of the twelve was introduced by the documentation pass that preceded this run, and is recorded as such.**
> `cli.md`'s Artifacts & logging paragraph read "Every command creates `--out`…"; it was amended to "Every command
> **except `diagram`**…" to settle an internal disagreement with the command table. The code registers **seven**
> subcommands, and `compare` writes only `compare.json` with no Markdown and no `runlog.append_run` — so the
> sentence became more precise and stayed wrong, about a second exception the document never listed. A more
> specific false claim is worse than a vague one, and the amendment is the reason this finding is `high`.
> *Provenance.* `coverage`, `context`, `audit --verify` and `sufficiency` all ran at `4f88931`, so unlike the
> previous row every number here comes from one commit.

## Pipeline contract  *(machine-written; field names + types FROZEN)*
```yaml
coverage_sha: 0ceeff6
audit_sha: 7f711da
sufficiency_sha: 1a44a72
audit_date: 2026-08-06
detector: claude-code
verified: true
rollup:
  avg_sufficiency: 0.86
  total_high_drift: 8
  modules_covered: 11
  modules_total: 11
modules:
  - name: audit
    coverage_status: spec-worthy
    drift_high: 0
    drift_med: 1
    drift_low: 0
    sufficiency: 0.85
  - name: authoring
    coverage_status: spec-worthy
    drift_high: 0
    drift_med: 2
    drift_low: 0
    sufficiency: 0.72
  - name: cli
    coverage_status: spec-worthy
    drift_high: 0
    drift_med: 0
    drift_low: 1
    sufficiency: 0.86
  - name: coverage
    coverage_status: spec-worthy
    drift_high: 0
    drift_med: 1
    drift_low: 1
    sufficiency: 0.88
  - name: providers
    coverage_status: spec-worthy
    drift_high: 0
    drift_med: 0
    drift_low: 0
    sufficiency: 0.87
  - name: report
    coverage_status: spec-worthy
    drift_high: 0
    drift_med: 0
    drift_low: 0
    sufficiency: 0.84
  - name: rubric
    coverage_status: spec-worthy
    drift_high: 0
    drift_med: 0
    drift_low: 0
    sufficiency: 0.93
  - name: runlog
    coverage_status: spec-worthy
    drift_high: 0
    drift_med: 0
    drift_low: 0
    sufficiency: 0.92
  - name: sufficiency
    coverage_status: spec-worthy
    drift_high: 0
    drift_med: 1
    drift_low: 0
    sufficiency: 0.88
  - name: syscontext
    coverage_status: spec-worthy
    drift_high: 0
    drift_med: 2
    drift_low: 0
    sufficiency: 0.87
  - name: verify
    coverage_status: spec-worthy
    drift_high: 1
    drift_med: 0
    drift_low: 0
    sufficiency: 0.79
```

## Fingerprint  *(markdown unicode bars — diffable; the full run sits beside this file)*
> **detector `claude-code` · 2026-09-29, `--verify`, all four commands at `4f88931`.** A different model or date can move these bars — check the
> run history below before reading a change as real.

| Module | Spec completeness | Sufficiency | Drift |
|---|---|---|---|
| `cli`         | `████████████░░░░░░░░` | 0.62 | ⚠ 3 |
| `providers`   | `██████████████░░░░░░` | 0.72 | ⚠ 1 |
| `compare`     | `███████████████░░░░░` | 0.76 | ⚠ 2 |
| `audit`       | `████████████████░░░░` | 0.80 | ⚠ 1 |
| `verify`      | `████████████████░░░░` | 0.80 | ⚠ 1 |
| `syscontext`  | `████████████████░░░░` | 0.82 | ✓ clean |
| `authoring`   | `█████████████████░░░` | 0.85 | ⚠ 1 |
| `sufficiency` | `█████████████████░░░` | 0.85 | ⚠ 3 |
| `report`      | `█████████████████░░░` | 0.87 | ✓ clean |
| `coverage`    | `██████████████████░░` | 0.88 | ✓ clean |
| `runlog`      | `██████████████████░░` | 0.90 | ✓ clean |
| `rubric`      | `██████████████████░░` | 0.92 | ✓ clean |

## Gaps / sufficiency misses  *(the backlog; full list in [sufficiency.md](sufficiency.md))*
Only two modules carry a `[major]` this run; everything below them is enumeration and print-format detail.
- **`authoring` (0.72, was 0.80)** — the largest move on the board, and it is the diagram work landing faster
  than the spec absorbed it. Four `[major]`s: the Architecture rendering contract is named in one clause with
  its actual budgets missing (at most 5 sequence participants, 10 messages); the repo `OVERVIEW.md` is given a
  trailing architecture fingerprint receipt **unconditionally**, which the spec does not say; and the built-in
  per-module skeleton and the folder-spec rubric's own section set are never given. The first two are worth
  fixing. The last two are the don't-restate discipline reappearing in new places. Then the usual `[minor]`s:
  unpinned budgets (`REDUCE_CAP` 48000, `_MAX_LEVELS` 4, `AUTHOR_MAX_TOKENS` 5000), bad-layout error semantics,
  stray-write detection, and the broken-link note's 5-path cap.
- **`verify` (0.79)** — new this cycle, one `[major]`: `verify_repo` itself is undescribed (it resolves pairs
  from config or `coverage.infer_pairs`, and skips verification entirely when the doc globs match nothing —
  a second no-op path the spec never names). `[minor]`s pin the numbers the prose left soft: the position
  window is 3 lines, the verifier call is capped at 2000 tokens, quote presence is a substring match against a
  single line (so a quote spanning a line break cannot match), and `doc_ref` parses both `file:L50` and `file:50`.
- **`report` (0.84) · `audit` (0.85) · `cli` (0.86)** — shapes and constants the specs describe but do not
  pin: both fingerprint headings and their column sets, `_bar`'s rounding and configurable width, the shared
  `REVIEW_MAX_TOKENS` of 3000, the `providers.LAST` call-ordering constraint, the exact user-message layout,
  and the 25-entry terminal list cap.
- **`providers` (0.87) · `syscontext` (0.87)** — the `DEFAULT_MODEL` string and the bridge's 600 s timeout are
  never stated; `syscontext`'s ~100-entry detection tables are *described*, not enumerated (**by design** — the
  tables are the code), graded `[minor]` this run, alongside unpinned caps (`EVIDENCE_CAP` 8, `LINE_CAP` 160)
  and the AWS plumbing skip-set.
- **`coverage` (0.88) · `sufficiency` (0.88) · `runlog` (0.92) · `rubric` (0.93)** — membership and formatting
  detail: the 24-entry `CONVENTIONAL_DOC_STEMS` list, `PRUNE_DIRS`, the `"."` root grouping key, the skip
  string's exact format, `git_sha`'s unchecked return code, and that the rubric is a second-person prompt.

Every gap carries a searchable `file.py (symbol)` pointer.

## Run history  *(summary stats over time — spot whether a change came from the eval, the model, or the code)*
> Fingerprint diff over time: **`git log -p spec-reports/SPEC-HEALTH.md`**. Each run's exact git SHA + per-module scores are
> auto-logged to [runs.jsonl](runs.jsonl).

| Date | Detector | Coverage | Avg suff | Worst | Drift H/M | Commit | What changed |
|---|---|---|---|---|---|---|---|
| 2026-07-03 | opus-4-8 | 100% | 0.93→0.92 | — | 0 / 0 | `ed8e4d2` · `8ccc688` | first self-audit (8 modules); re-measured. |
| 2026-07-03 | opus-4-8 | 100% | 0.92 | cli 0.85 | 0 / 0 | `b3a36f6` | INV guardrail + new `runlog` module → 9 modules; false-invariant gaps gone. |
| 2026-07-08 | opus-4-8 | 100% | 0.91 | authoring/cli 0.85 | 0 / 0 | `444202d` | layouts + `claude-code` bridge + calibrated phrasing. The audit **caught 3 real drifts** that change set introduced (authoring's silent-truncation fallback, providers' three-vendor contract, cli's stale `preview`/`proposed` contract) and exposed a parser bug (brace-y prose before the JSON) — all fixed before these receipts. |
| 2026-07-09 | opus-4-8 | 100% | 0.91 | authoring 0.82 | 0 / 0 | — | full audit + sufficiency refresh: **searchable code_refs required on every gap** (28/28 carry `file.py (symbol)`), ` · ` ref separator, runlog seconds timestamps; `rubric` +0.05, `authoring` −0.03 (wobble range). |
| 2026-07-15 | claude-code | 100% | 0.86 | authoring 0.78 | 0 / 0 | `906a202` | **detector switch to `claude-code`** (stricter than opus): caught **5 real pre-existing drifts** opus scored clean (fixed) + **2 major sufficiency gaps** (closed); minGPT example removed. One [major] remains by design (authoring rubric summarized, not restated). |
| 2026-07-21 | claude-code | 100% | 0.91 | authoring 0.87 | 0 / 0 | `fc67265` | prompt-chat release (#6–#8): `overview_min_files` true minimum + recorded skips, SPEC-HEALTH moved into `spec-reports/`, README prompt blocks + standing prompts. Audit clean **incl. the changed `authoring` pair**; former [major] (rubric summarized, by design) now graded [minor]; 0.86→0.91 same detector = wobble + the sync work landing more semantics in the specs. |
| 2026-07-27 | claude-code | 100% | 0.91→0.88 | authoring 0.80 | 0 / 0 | `e573694` | **system-context feature + drift check (#11–#14)** → new 10th module `syscontext`. The audit **caught 6 real drifts across three runs (4 → 2 → 1)** — all doc-accuracy fixes incl. the `_tables_digest` completeness (found by review **and** dogfood — the matching + gating regexes), `cli --check` docs, `audit`/`authoring`/`rubric` over-claims, and a §1 four→five miscount — and **closed the one fixable [major]** (OVERVIEW.md stamp undocumented). Clean re-measure confirms 0/0. 0.91→0.88 = the new module + drift-check surface, not regression; `syscontext` table sampling joins the `authoring` rubric as a by-design [major]↔[minor] wobble. |
| 2026-08-06 | claude-code | 100% | 0.88→0.86 | verify 0.79 | 1 / 7 | `0ceeff6` · `7f711da` · `1a44a72` | **evidence field + opt-in second pass (#25)** → new 11th module `verify`; first run with `--verify`, so the drift count excludes 7 withdrawals and is not comparable to the rows above. Drift 0→8 after a week that added a module, a persisted `evidence` field and a changed drift-load definition. One SHA per measurement: coverage · audit · sufficiency. The one **high** is real, found in code under eight hours old and fixed the same day at `1a44a72`: `verify`'s presence check returned early when a finding cited no line, so an invented quote survived on exactly the withdrawals with no line to check against — contradicting its own INV-4. **All 7 withdrawals hold up on inspection** — 5 `stated-elsewhere` (a loose sentence or table row against a correct passage elsewhere in the same doc), 1 `not-asserted` (a three-item list read as exhaustive), 1 `not-normative` (a `**Why:**` clause graded as a promise). Unverified the row would read 12 / 0. **Contract change (frozen fields):** `audit_sha` became one SHA per measuring command — `coverage_sha`, `audit_sha`, `sufficiency_sha` — because this run's three numbers came from three commits and one field could not say which. `null` means that command did not run. Pinned to the template by `test_health_contract_sync`. **Acted on since:** 3 of the 8 — the `verify` **high** at `1a44a72` (#29), and both `authoring` **medium**s at `1a227a5` (#31: the data-flow diagram's termination, and the undocumented architecture fingerprint receipt). 5 remain open — `audit` 1, `coverage` 1, `sufficiency` 1, `syscontext` 2. The row's 8 is what this run measured at `7f711da` and is left as measured; re-running to lower it would score the gaps this run named. |
| 2026-09-29 | claude-code | 100% | 0.86→0.82 | cli 0.62 | 1 / 7 | `4f88931` | **documentation pass (#59) + first grading of `compare`** → 12th module. Every number at ONE commit this time, unlike the row above. Drift 8→12 on a like-for-like verified basis, and the tree is not the same tree: since 2026-08-06 the package gained the `compare` subcommand and module, a process-wide call ceiling in `providers`, and `--max-calls` / `--reps` on `sufficiency`, none of them specced. That is where the rise sits — `cli` 0→3 with sufficiency 0.86→0.62, `compare` 0→2, `providers` 0→1 — so **the code grew and the specs did not follow**. **One of the 12 was introduced by #59 itself and is left in the count.** `cli.md`'s Artifacts & logging paragraph was amended from "Every command creates `--out`…" to "Every command **except `diagram`**…" to settle an internal disagreement with the command table; the code registers seven subcommands and `compare` writes only `compare.json`, no Markdown, no `runlog.append_run`. The sentence became more precise and stayed wrong about a second exception the document never listed, which is why it grades `high` — a more specific false claim is worse than a vague one. It is recorded rather than quietly repaired, on the same principle as the row above: re-running to lower the number would score the gap this run named. **The 7 withdrawals** match the previous run's count and were spot-checked: each cites a ground from the closed set and a document line that exists. **Acted on since:** 0 of 12 — this row is the measurement, not the repair. |
