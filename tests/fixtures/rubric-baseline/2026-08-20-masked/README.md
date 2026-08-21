# Masking in practice — `coverage` pair, 5 runs, 2026-08-20

Five runs of the `coverage` pair with rationale masking active (#46), captured to confirm the
mechanism fires in a real run and to answer a question left open on #44.

```sh
spec-eval audit spec_eval/coverage.py --verify --model claude-code --out /tmp/post-$i
```

Every run recorded `rationale_masked: 10` — the 10 rationale lines in `spec_eval/coverage.md`.

## The class is gone, and no significance test belongs on it

| Arm | `not-normative` | Findings/run | Mean | sd | Headline |
|---|---|---|---|---|---|
| Untreated | 6/10 | `2,2,2,2,1,1,2,1,3,1` | 1.7 | 0.64 | `1,0,0,0,0,1,0,0,1,1` |
| Rubric instruction (#40) | 2/10 | `3,2,2,1,1,1,2,1,1,1` | 1.5 | 0.67 | `0,1,1,0,0,0,1,1,1,0` |
| **Masked (#46)** | **0/5** | `2,1,1,0,1` | 1.0 | 0.63 | `1,1,1,0,0` |

**Deliberately no p-value on the 0/5.** The rate is not zero because a treatment probabilistically
suppressed something — it is zero because the text was never in the payload. Testing a structural
guarantee for statistical significance is a category error. The proof is
`tests/contract/test_rationale_masking.py`; these runs only confirm the mechanism fires in practice.

The contrast with the instruction is the point of the whole exercise: 20 runs bought
*"6/10 → 2/10, p = 0.17, unestablished"*; a unit test bought certainty.

## The answer for #44 — rationale was not the driver of the instability

Standard deviation of findings per run: **0.64 → 0.63**. Unchanged.

Volume fell (1.7 → 1.0) because a class was removed, but **the instability did not**, and the
headline still swings (`1,1,1,0,0`). Removing the single most frequent failure class did not make a
single run's count reproducible. #44's candidate directions stand as written, and the
"measure the contribution" plan proposed on that issue has now been run: the contribution is
approximately none.

## One zero-finding run, flagged as pre-registered

**`post-4` returned zero findings.** Untreated: 0 zero-runs in 10. Instruction arm: 0 in 10.
Masked: **1 in 5** — the first zero in 25 runs.

The pre-registration for the instruction arm required any zero-finding run to be reported
prominently regardless of the primary result, and that discipline carries here.

**At n=5 this is not evidence of over-suppression.** The untreated arm produced a 1-finding run three
times, and removing one class from a 1-finding run leaves zero. But it is the exact shape
over-suppression would take, and it is the first one observed. Five more runs would separate the two
readings and cost nothing.

The masking mechanism itself is deterministic and inspectable — every one of the 10 masked lines in
`spec_eval/coverage.md` was checked and is genuine rationale, with no requirement caught. The open
question is about *rate of empty reports on other repos*, not about whether the filter selects the
right lines here.

## Limits

One pair, one repository, one unpinned detector alias, five runs. Not a rate. The comparison arms
were captured on 2026-08-19 under the same alias on a different day, so the detector is **not** held
constant between this capture and those — see `../2026-08-06-7f711da/README.md` for why that matters
and `../2026-08-19-variance/README.md` for what it cost the first time.
