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
> **Coverage 100%** (9/9 modules) · **drift 0** high/medium · **sufficiency 0.86** avg (1.0 = no gaps found — an
> indicator, not a guarantee) as of 2026-07-15, detector **`claude-code`**. One **[major]** gap remains, in
> `authoring` (0.78) — **by design**: the spec *summarizes* the `AUTHORING_STRUCTURE`/`AUTHORING_DISCIPLINE`
> rubric rather than restating the prompt verbatim (which the spec's own discipline forbids); the full text lives
> in `authoring.py`, is mirrored in the spec-authoring skill, and is pinned by `test_rubric_sync`. Every other
> gap is **[minor]** — unpinned default constants, exact templates, print-format detail — each with a searchable
> `file.py (symbol)` pointer.
> **Detector note:** the prior baseline used `anthropic:claude-opus-4-8` (0.91); `claude-code` grades stricter,
> so 0.86 is a re-baseline, not a regression. This refresh earned its keep — the stricter pass caught **5 real
> pre-existing drifts** opus had scored clean (fixed) and **2 major sufficiency gaps** (closed).

## Pipeline contract  *(machine-written; field names + types FROZEN)*
```yaml
audit_date: 2026-07-15
detector: claude-code
rollup: {coverage_pct: 100, avg_sufficiency: 0.86, total_high_drift: 0, modules_covered: 9, modules_total: 9}
modules:
  - {name: authoring,   sufficiency: 0.78, drift_high: 0, drift_med: 0}
  - {name: cli,         sufficiency: 0.82, drift_high: 0, drift_med: 0}
  - {name: coverage,    sufficiency: 0.83, drift_high: 0, drift_med: 0}
  - {name: audit,       sufficiency: 0.85, drift_high: 0, drift_med: 0}
  - {name: report,      sufficiency: 0.86, drift_high: 0, drift_med: 0}
  - {name: providers,   sufficiency: 0.90, drift_high: 0, drift_med: 0}
  - {name: rubric,      sufficiency: 0.90, drift_high: 0, drift_med: 0}
  - {name: sufficiency, sufficiency: 0.90, drift_high: 0, drift_med: 0}
  - {name: runlog,      sufficiency: 0.93, drift_high: 0, drift_med: 0}
```

## Fingerprint  *(markdown unicode bars — diffable; the full run sits beside this file)*
> **detector `claude-code` · 2026-07-15.** A different model or date can move these bars — check the
> run history below before reading a change as real.

| Module | Spec completeness | Sufficiency | Drift |
|---|---|---|---|
| `authoring`   | `████████████████░░░░` | 0.78 | ✓ clean |
| `cli`         | `████████████████░░░░` | 0.82 | ✓ clean |
| `coverage`    | `█████████████████░░░` | 0.83 | ✓ clean |
| `audit`       | `█████████████████░░░` | 0.85 | ✓ clean |
| `report`      | `█████████████████░░░` | 0.86 | ✓ clean |
| `providers`   | `██████████████████░░` | 0.90 | ✓ clean |
| `rubric`      | `██████████████████░░` | 0.90 | ✓ clean |
| `sufficiency` | `██████████████████░░` | 0.90 | ✓ clean |
| `runlog`      | `███████████████████░` | 0.93 | ✓ clean |

## Gaps / sufficiency misses  *(the backlog; full list in [sufficiency.md](sufficiency.md))*
- **`authoring`** *(the one [major])* — the `AUTHORING_STRUCTURE`/`AUTHORING_DISCIPLINE` rubric is summarized,
  not restated verbatim (**by design** — the spec's own don't-restate discipline; the full text lives in
  `authoring.py`, mirrored in the skill, pinned by `test_rubric_sync`); plus minor cap edge-cases and unpinned
  default constants (`REDUCE_CAP`, per-call token caps).
- **`cli` / `coverage`** — exact print-format and enumeration detail: the 25-entry list-cap value, full
  `CONVENTIONAL_DOC_STEMS`/`PRUNE_DIRS` membership, `.0f` percent rounding.
- **`audit` / `report`** — paraphrased detail: the `REVIEW_MAX_TOKENS` value, `_bar` rounding, exact prompt
  templates. Every gap carries a searchable `file.py (symbol)` pointer.

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
