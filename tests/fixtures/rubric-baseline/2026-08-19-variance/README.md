# Variance floor — `coverage` pair, 2026-08-19

**Five runs of the same commit, the same pair, and the same command, with no rubric change at all.**
Captured to establish what a single audit run can and cannot measure, before attempting any
before/after comparison of a `DRIFT_RUBRIC` edit.

Command, repeated five times on `main` at `052579f`:

```sh
spec-eval audit spec_eval/coverage.py --verify --model claude-code --out /tmp/var-$i
```

## What repeated

| Finding (severity · doc_ref) | r1 | r2 | r3 | r4 | r5 | runs |
|---|---|---|---|---|---|---|
| **high** · `coverage.md:§4 Invariants, INV-8` | ✔ upheld | — | — | — | — | **1/5** |
| **medium** · `coverage.md:§3 Unmodeled markdown detection` | ~ withdrawn | — | — | — | ~ withdrawn | **2/5** |
| **medium** · `spec_eval/coverage.md:L64` | — | ~ withdrawn | — | ~ withdrawn | — | **2/5** |
| **low** · `spec_eval/coverage.md:L15` | — | — | ✔ upheld | — | — | **1/5** |
| **low** · `spec_eval/coverage.md:L17` | — | — | ✔ upheld | — | — | **1/5** |
| **low** · `spec_eval/coverage.md:L22` | — | ~ withdrawn | — | ~ withdrawn | — | **2/5** |

**No finding appears in more than 2 of 5 runs.** Total findings per run: `2, 2, 2, 2, 1`.

## The headline number is not reproducible

The count a reader acts on — `N high/medium drift finding(s)` — came out **`1, 0, 0, 0, 0`** across
the five identical runs. A single run's published drift count is a draw from a distribution, not a
measurement. Anything downstream that quotes one is quoting a draw.

## What this rules out

A before/after comparison of one pair at n=1 **cannot** detect a rubric change, in either direction.
The variance between identical runs exceeds any plausible effect, so a difference between two single
runs is uninterpretable and a *lack* of difference is equally uninterpretable.

Three runs were made against that broken design before the floor was measured, and are retained here
as `after-35/` (branch, 1 finding), `A-main/` (main, 0 findings) and `B-rule/` (branch, 2 findings).
The arm carrying the suppression rule returned **more** findings than the arm without it — which a
suppression rule cannot cause. They are kept because they are the evidence that the design was
broken, not because they measure anything.

## What this makes measurable

The *class* of finding is far more stable than any individual finding. A withdrawal on the
`not-normative` ground — the rationale-clause failure mode — occurs in **4 of 5 runs**, at a
different document span each time (§3 in r1/r5, L64 in r2/r4).

So the answerable question is not *"did this finding disappear"* but *"how often does this class of
finding occur"*. That converts the rationale rule into a proportion test with a measured
untreated rate of **4/5 = 80%**. The pre-registered design is in
`../PRE-REGISTRATION-rationale-rule.md`.

## Two caveats on this data

**The detector is not pinned.** `claude-code` resolves to the Claude Code CLI's own default model,
which moves over time — see the correction in `../2026-08-06-7f711da/README.md`. Every run here was
made inside one session on one afternoon, so the detector is held constant *within* this capture and
must not be compared against captures from other days.

**The usage telemetry is not trustworthy.** Reported input tokens across these five identical runs
were `83,327 · 280,013 · 217,306 · 315,240 · 55,499` — a 6x spread on a fixed payload. Separately,
one run reported 27,412 input tokens against a payload measured at 27,443 characters, a ratio no
real tokenizer produces. Do not derive cost estimates from `runs.jsonl` figures produced through the
`claude-code` bridge.
