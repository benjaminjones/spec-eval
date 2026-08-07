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
> **Coverage 100%** (11/11 modules) · **drift 8** high/medium · **sufficiency 0.86** avg (1.0 = no gaps found —
> an indicator, not a guarantee) as of 2026-08-06, detector **`claude-code`**, **verified** (`audit --verify`).
> The 11th module, `verify`, is the opt-in second pass added this cycle.
> **Drift is 8, not 0, and that is the honest reading rather than a regression.** The previous receipt measured
> a tree that has since gained a module, a persisted `evidence` field, a withdrawn-finding render and a changed
> drift-load definition. Eight of the ten upheld findings are doc-accuracy gaps of the usual kind; the one
> `high` is real — `verify`'s presence check read the cited line first and returned early when there was none,
> so a withdrawal quoting text absent from the document survived on exactly the findings that named no line to
> check against, contradicting its own INV-4. **It was found in code one day old and fixed the same day:**
> the `audit` ran at `7f711da`, the fix is `1a44a72`.
> *Provenance:* the two commands ran at different commits — `audit` at `7f711da` (08:24), `sufficiency` at
> `1a44a72` (20:07), with the fix in between. `1a44a72` touches `verify.py`, `verify.md` and its tests only, so
> the `verify` row's 0.79 is the only score that could have moved; the drift findings are all from `7f711da`.
> **The second pass withdrew 7 findings and all 7 hold up on inspection.** Five were `stated-elsewhere` — a
> loose narrative sentence graded against a contract table that states the rule correctly a few lines below.
> One was `not-asserted`: a three-item list read as exhaustive when the line never says "only". One was
> `not-normative`: a `**Why:**` rationale sentence graded as a promise about behaviour. Those three grounds are
> the whole of what this cycle's withdrawals rested on.
> **Read the drift number with `verified: true` in mind.** It excludes the 7 withdrawals, so it is not
> comparable to a number from a run without the flag. The withdrawn findings are listed in `report.md` with
> their ground and the doc line, struck through rather than deleted.
> **By design (unchanged):** the `authoring` rubric is *summarized*, not restated — the spec's own
> don't-restate discipline, with the full text in `authoring.py`, mirrored in the skill, pinned by
> `test_rubric_sync`. `syscontext`'s detection tables are likewise *described*, not enumerated.

## Pipeline contract  *(machine-written; field names + types FROZEN)*
```yaml
audit_sha: 7f711da
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
> **detector `claude-code` · 2026-08-06, `--verify`.** A different model or date can move these bars — check the
> run history below before reading a change as real.

| Module | Spec completeness | Sufficiency | Drift |
|---|---|---|---|
| `authoring`   | `████████████████░░░░` | 0.80 | ✓ clean |
| `audit`       | `█████████████████░░░` | 0.83 | ✓ clean |
| `syscontext`  | `█████████████████░░░` | 0.85 | ✓ clean |
| `cli`         | `█████████████████░░░` | 0.86 | ✓ clean |
| `report`      | `██████████████████░░` | 0.88 | ✓ clean |
| `coverage`    | `██████████████████░░` | 0.90 | ✓ clean |
| `providers`   | `██████████████████░░` | 0.90 | ✓ clean |
| `rubric`      | `██████████████████░░` | 0.90 | ✓ clean |
| `sufficiency` | `██████████████████░░` | 0.90 | ✓ clean |
| `runlog`      | `███████████████████░` | 0.93 | ✓ clean |

## Gaps / sufficiency misses  *(the backlog; full list in [sufficiency.md](sufficiency.md))*
- **`authoring` (0.80)** — the rubric is summarized, not restated (**by design** — the spec's own don't-restate
  discipline; full text in `authoring.py`, mirrored in the skill, pinned by `test_rubric_sync`; graded `[major]`
  this run, `[minor]` last — it wobbles); plus unpinned budgets (`REDUCE_CAP`, `_MAX_LEVELS`, `AUTHOR_MAX_TOKENS`),
  bad-layout error semantics, synthesis-rubric section shapes, and the `_pack`/`_synthesize` mechanics.
- **`audit` (0.83)** — the shared `REVIEW_MAX_TOKENS` value, the `providers.LAST` call-ordering constraint, the
  exact user-message layout, per-field parse defaults, and the empty-findings fallback edge.
- **`syscontext` (0.85)** — the ~100-entry detection tables are described, not enumerated (**by design** — the
  tables are the code); plus unpinned constants (`EVIDENCE_CAP`/`LINE_CAP`/`FILE_CAP`/digest widths), the AWS
  plumbing skip-set, the unknown-id naming rule, the strict C# `using` matcher, and `_scoped`'s evidence-total.
- **`cli` / `report` / `coverage` / `providers` / `rubric` / `sufficiency` (0.86–0.90)** — print-format and
  enumeration detail: the 25-entry list cap, full `CONVENTIONAL_DOC_STEMS`/`PRUNE_DIRS` membership, `_bar`
  rounding, the `DEFAULT_MODEL` string, the bridge's 600 s timeout, report ordering.
- **`runlog` (0.93)** — `git_sha`'s non-zero-exit edge and `append_run`'s serialization defaults.

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
| 2026-08-06 | claude-code | 100% | 0.88→0.86 | verify 0.79 | 1 / 7 | `7f711da` | **evidence field + opt-in second pass (#25)** → new 11th module `verify`; first run with `--verify`, so the drift count excludes 7 withdrawals and is not comparable to the rows above. Drift 0→8 after a week that added a module, a persisted `evidence` field and a changed drift-load definition. The one **high** is real, found in code one day old and fixed the same day at `1a44a72` (`sufficiency` re-ran there; the drift findings are all from `7f711da`): `verify`'s presence check returned early when a finding cited no line, so an invented quote survived on exactly the withdrawals with no line to check against — contradicting its own INV-4. **All 7 withdrawals hold up on inspection** — 5 `stated-elsewhere` (loose narrative, correct contract table below it), 1 `not-asserted` (a three-item list read as exhaustive), 1 `not-normative` (a `**Why:**` clause graded as a promise). |
