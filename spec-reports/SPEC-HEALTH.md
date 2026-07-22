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
> **Coverage 100%** (9/9 modules) · **drift 0** high/medium · **sufficiency 0.91** avg (1.0 = no gaps found — an
> indicator, not a guarantee) as of 2026-07-21, detector **`claude-code`**. **Every gap is [minor]** — the
> long-standing `authoring` [major] (the spec *summarizes* the `AUTHORING_STRUCTURE`/`AUTHORING_DISCIPLINE`
> rubric rather than restating it — **by design**; the full text lives in `authoring.py`, is mirrored in the
> spec-authoring skill, and is pinned by `test_rubric_sync`) is still listed, now graded [minor]. The rest are
> unpinned default constants, print-format detail, and helper-contract edges — each with a searchable
> `file.py (symbol)` pointer.
> **Detector note:** same detector as the 2026-07-15 baseline; read the 0.86 → 0.91 rise as part wobble, part
> real — this release's sync work landed more of the authoring semantics (layout/overview axes, threshold and
> skip-record behavior) in the specs. Drift stayed 0 **including on the `authoring` pair this release changed** —
> a fresh checker confirmed the code and spec edits agree.

## Pipeline contract  *(machine-written; field names + types FROZEN)*
```yaml
audit_date: 2026-07-21
detector: claude-code
rollup: {coverage_pct: 100, avg_sufficiency: 0.91, total_high_drift: 0, modules_covered: 9, modules_total: 9}
modules:
  - {name: authoring,   sufficiency: 0.87, drift_high: 0, drift_med: 0}
  - {name: audit,       sufficiency: 0.88, drift_high: 0, drift_med: 0}
  - {name: cli,         sufficiency: 0.90, drift_high: 0, drift_med: 0}
  - {name: coverage,    sufficiency: 0.90, drift_high: 0, drift_med: 0}
  - {name: report,      sufficiency: 0.90, drift_high: 0, drift_med: 0}
  - {name: sufficiency, sufficiency: 0.90, drift_high: 0, drift_med: 0}
  - {name: providers,   sufficiency: 0.92, drift_high: 0, drift_med: 0}
  - {name: rubric,      sufficiency: 0.95, drift_high: 0, drift_med: 0}
  - {name: runlog,      sufficiency: 0.95, drift_high: 0, drift_med: 0}
```

## Fingerprint  *(markdown unicode bars — diffable; the full run sits beside this file)*
> **detector `claude-code` · 2026-07-21.** A different model or date can move these bars — check the
> run history below before reading a change as real.

| Module | Spec completeness | Sufficiency | Drift |
|---|---|---|---|
| `authoring`   | `█████████████████░░░` | 0.87 | ✓ clean |
| `audit`       | `██████████████████░░` | 0.88 | ✓ clean |
| `cli`         | `██████████████████░░` | 0.90 | ✓ clean |
| `coverage`    | `██████████████████░░` | 0.90 | ✓ clean |
| `report`      | `██████████████████░░` | 0.90 | ✓ clean |
| `sufficiency` | `██████████████████░░` | 0.90 | ✓ clean |
| `providers`   | `██████████████████░░` | 0.92 | ✓ clean |
| `rubric`      | `███████████████████░` | 0.95 | ✓ clean |
| `runlog`      | `███████████████████░` | 0.95 | ✓ clean |

## Gaps / sufficiency misses  *(the backlog; full list in [sufficiency.md](sufficiency.md))*
- **`authoring` (0.87)** — the rubric is summarized, not restated verbatim (**by design** — the spec's own
  don't-restate discipline; full text in `authoring.py`, mirrored in the skill, pinned by `test_rubric_sync`;
  the long-standing gap, now graded [minor]); plus unpinned budgets (`REDUCE_CAP`, `_MAX_LEVELS`,
  `AUTHOR_MAX_TOKENS`), bad-layout error semantics, synthesis-rubric section shapes, and the cross-artifact
  sync obligation.
- **`audit` (0.88)** — the shared `REVIEW_MAX_TOKENS` value, lossy `errors="ignore"` reads,
  contributing-files counting, exported-helper contracts, the `providers.LAST` call-ordering constraint.
- **`cli` / `coverage` / `report` / `sufficiency` (0.90)** — print-format and enumeration detail: the 25-entry
  list cap, full `CONVENTIONAL_DOC_STEMS`/`PRUNE_DIRS` membership, `_bar` rounding, report ordering rules,
  falsy-`pairs` fallback edges.
- **`providers` / `rubric` / `runlog` (0.92–0.95)** — the `DEFAULT_MODEL` string, the bridge's 600 s timeout,
  `git_sha`'s standalone contract and empty-output edge.

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
