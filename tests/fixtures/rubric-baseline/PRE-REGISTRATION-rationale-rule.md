# Pre-registration — does the rationale rule change the first pass?

**Written and committed before the treatment runs were made.** The decision rule below is fixed at
commit time. Reading the result and then choosing a threshold is the failure this document exists to
prevent, and it is a failure this project has recorded twice.

- **Issue:** #35 — the drift rubric grades a non-normative rationale clause as a falsifiable assertion.
- **Change under test:** PR #40, branch `fix/35-rationale-is-not-a-claim`. Adds one exclusion to
  `DRIFT_RUBRIC`'s do-not-flag list: *a clause that explains WHY rather than states WHAT, which you
  can delete without changing anything the document requires (rationale is not a claim)*.
- **Underlying question:** the rule already exists in the tool, as `verify`'s `not-normative`
  withdrawal ground. `--verify` is off by default, so the first pass emits the finding and a user who
  does not opt in never sees it withdrawn. The change moves the judgment into the pass that always
  runs. This measures whether it arrives there.

## Why the obvious design was abandoned

*"Run the pair once before and once after, and see whether the rationale finding disappeared."*

That design cannot work. Five runs of the same commit on the same pair produced no finding that
recurred in more than 2 of 5 runs, and a headline drift count of `1, 0, 0, 0, 0` — see
`2026-08-19-variance/README.md`. At n=1 the run-to-run variance exceeds any plausible rubric effect,
so both a difference and a lack of difference are uninterpretable.

## Metric

**The proportion of runs producing at least one withdrawal on the ground `not-normative`.**

The individual finding is unstable; the class is not. In the variance capture the rationale-clause
failure mode fired in 4 of 5 runs, at a different document span each time. The class is what the
rubric change targets, so the class is what is counted.

Counted from `findings.json` — a run scores 1 if any finding has
`verification.ground == "not-normative"`, else 0. Withdrawn findings count: the question is whether
the *first pass* stopped emitting them, and a withdrawal is proof that the first pass emitted one.

## Arms

| Arm | Commit | Runs | Result |
|---|---|---|---|
| **Untreated** | `main` @ `052579f` | 5 | **4/5** — measured 2026-08-19, retained in `2026-08-19-variance/` |
| **Treated** | `fix/35-rationale-is-not-a-claim` | 5 | *to be run* |

Identical command per run, differing only by output directory:

```sh
spec-eval audit spec_eval/coverage.py --verify --model claude-code --out <dir>
```

Both arms must be run with the detector held constant. `claude-code` resolves to the CLI's own
default model and moves over time, so the treated arm must be run in one session and compared only
against an untreated arm captured close to it — not against a capture from another day.

## Decision rule — fixed at commit time

Let **k** be the number of treated runs (of 5) producing at least one `not-normative` withdrawal.

| k | Reading | Action |
|---|---|---|
| **0 or 1** | The rule reaches the first pass. | **Merge #40.** |
| **2** | Inconclusive at this n. | **Do not merge.** Either widen to more pairs, or drop the family. |
| **3, 4 or 5** | No detectable effect. | **Close #40 unmerged.** Reshape #35, #36-option-1 and #37 as pre-model filters rather than rubric wording. |

No threshold is to be renegotiated after the count is known. If the design turns out to be wrong in
some way not anticipated here, the correct response is to record that and re-register — not to
reinterpret this table.

## Stated limits

- **One pair, n=5 per arm.** Fisher's exact on 4/5 versus 0/5 is p≈0.048; 4/5 versus 2/5 is not
  significant. This design can detect a large effect and nothing smaller.
- **It is not a precision figure** and must never be quoted as one. It measures how often one failure
  class appears on one pair under one detector, not the tool's drift precision, which remains
  unmeasured.
- **A pass licenses one claim only:** that the instruction changed first-pass behaviour on this pair.
  It says nothing about whether the suppressed findings deserved suppressing — the two upheld
  findings in the variance capture are the control for over-suppression, and any treated run losing
  *all* findings should be read as a warning rather than a success.
- **The 4/5 untreated rate carries its own interval.** At n=5 the 95% Wilson interval on 4/5 spans
  roughly [38%, 96%]. The point estimate is not the finding; the design's ability to separate 4/5
  from 0/5 is.
