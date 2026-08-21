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

---

# RESULT — recorded 2026-08-19, after the treated arm was run

**k = 1 of 5.** Runs retained in `2026-08-19-treated/`.

| Run | `not-normative` withdrawal | Total findings |
|---|---|---|
| tx-1 | **yes** — §3 "Unmodeled markdown detection" | 3 |
| tx-2 | no | 2 |
| tx-3 | no | 2 |
| tx-4 | no | 1 |
| tx-5 | no | 1 |

| Arm | Rate | Total findings per run | Mean |
|---|---|---|---|
| Untreated (`main`) | **4/5** | 2, 2, 2, 2, 1 | 1.8 |
| Treated (PR #40) | **1/5** | 3, 2, 2, 1, 1 | 1.8 |

## Disposition under the pre-registered rule

k = 1 falls in the **0 or 1** band. The rule, fixed before the arm was run, says **merge #40**. That
is the disposition, and it is not revisited below.

## The over-suppression control passes

Mean total findings is **identical across arms (1.8)** and no treated run returned zero. The rule is
not suppressing findings wholesale — the `not-normative` class thinned from 4/5 to 1/5 while total
volume held constant. Treated runs also surfaced upheld findings the untreated arm never produced
(`L101` in tx-2 and tx-3), and `stated-elsewhere` withdrawals persisted (tx-1, tx-4, tx-5). The
reduction is selective, which is what the change was supposed to do.

## A defect in this pre-registration, recorded rather than acted on

**The merge band is looser than the significance the limits section implied.** Fisher's exact,
two-sided, 5 per arm:

| Comparison | p |
|---|---|
| 4/5 vs 0/5 | 0.048 |
| **4/5 vs 1/5 — observed** | **0.206** |
| 4/5 vs 2/5 | 0.524 |

The limits section quoted p for 0/5 and for 2/5 and **skipped the 1/5 case, which is the one that
occurred**. Setting the merge band at "0 or 1" therefore admitted an outcome that is not
statistically significant. That is an error in the design, made before the data existed.

It is recorded, not corrected. Moving the threshold after seeing k is precisely the failure this
document exists to prevent, and the rule stands as written. **The merge is licensed by the
pre-registered rule, not by statistical significance**, and any downstream claim must say so.

## What would settle it

If the underlying rates really are 80% and 20%, the same effect reaches p < 0.05 at **7 runs per
arm** (6/7 vs 1/7, p = 0.029) and is comfortable at **10 per arm** (8/10 vs 2/10, p = 0.023). Two
more runs per arm would move this from rule-following to evidence. Free on `claude-code`, and the
untreated arm would need re-running alongside so the detector stays constant.

## What may be claimed from this

- That the instruction **changed first-pass behaviour on this pair**, directionally and with the
  over-suppression control holding.
- **Not** that the effect is statistically established (p = 0.21).
- **Not** anything about the tool's drift precision, which remains unmeasured.
- **Not** a rate. One pair, n=5 per arm, one detector, one afternoon.

---

# AMENDMENT — extension to n=10 per arm, registered 2026-08-19 before any extension run

The n=5 result above is final and unchanged. This amendment registers an **extension**, and it
carries two acknowledged statistical costs that are stated here rather than discovered later.

## Cost 1 — this is optional stopping

The decision to collect more data was made **after seeing k=1**. Peeking at an interim result and
then extending inflates the Type I error rate relative to an experiment whose n was fixed in
advance. A pooled p-value from this design is therefore **optimistic** and is not equivalent to the
same p-value from a fresh experiment.

Mitigations, all binding:

- **n is fixed now at 10 per arm** (5 already collected + 5 more). All 10 extension runs are made
  regardless of how the first few look. No further interim looks, no further extensions.
- **Both arms are re-run in the same session, interleaved** — untreated, treated, untreated,
  treated — so that any detector drift during the session is distributed across arms instead of
  confounded with arm. Blocking one arm then the other would put drift and treatment in the same
  place.
- The pooled result is reported **with this caveat attached**, every time.

## Cost 2 — the original n=7 target was chosen badly

The first extension proposal was n=7 per arm, selected by computing p across candidate n and taking
the smallest one that crossed 0.05. **Choosing a stopping point because it produces significance is
p-hacking**, whatever the intent. It is replaced here by n=10 — a round pre-committed target, chosen
before the extension data exists and not tuned to a threshold.

## What is analysed, and how

Two analyses, both pre-specified:

| Analysis | Basis | Role |
|---|---|---|
| **Replication** | The 5 new runs per arm, alone | Descriptive. Reported first, before pooling. |
| **Pooled** | All 10 per arm, Fisher's exact, two-sided, α = 0.05 | Primary — carrying the optional-stopping caveat. |

## Decision rule — fixed before the extension runs

This rule can **upgrade the justification for merging, or reverse it. It cannot manufacture a merge
that the original rule did not already license.**

| Pooled outcome | Reading | Action |
|---|---|---|
| p < 0.05 **and** treated rate < untreated rate | Effect established at this n, subject to the caveat above | **Merge #40** on evidence. State the caveat in the PR. |
| p ≥ 0.05 | Effect **not** established | **Merge #40 on the original n=5 rule only**, and say so explicitly. #36-option-1 and #37 do **not** get to assume rubric wording works. |
| treated rate ≥ untreated rate | Direction reversed | **Withdraw the merge and close #40.** Reshape the family as pre-model filters. |

## The over-suppression control carries forward

Mean total findings per run is compared across arms as before. **Any extension run returning zero
findings is reported prominently**, regardless of what the primary analysis says — a rule that
silences a pair entirely is a worse outcome than one that changes nothing.

---

# EXTENSION RESULT — n=10 per arm, recorded 2026-08-19

All 10 extension runs were made as registered, interleaved, in one session. Both pre-specified
analyses follow, in the registered order. Runs retained in `2026-08-19-variance/var-6..10` and
`2026-08-19-treated/tx-6..10`.

## Analysis 1 — replication (the 5 new runs per arm, alone)

| Arm | New 5 | Rate |
|---|---|---|
| Untreated | `0, 0, 1, 1, 0` | **2/5** |
| Treated | `0, 0, 0, 0, 1` | **1/5** |

Fisher's exact, two-sided: **p = 1.00**. The replication on its own shows nothing.

## Analysis 2 — pooled, PRIMARY

| Arm | All 10 | Rate |
|---|---|---|
| Untreated | `1,1,0,1,1,0,0,1,1,0` | **6/10 = 60%** |
| Treated | `1,0,0,0,0,0,0,0,0,1` | **2/10 = 20%** |

**Fisher's exact, two-sided: p = 0.1698.** Carrying the optional-stopping caveat registered above,
which makes this figure optimistic rather than conservative.

## Disposition under the registered rule

p ≥ 0.05, and the direction held (treated < untreated), so the rule's middle row applies:

> **Merge #40 on the original n=5 rule only, and say so explicitly. #36-option-1 and #37 do not get
> to assume rubric wording works.**

That is the disposition. **The effect is not statistically established.**

## The untreated rate is itself unstable, and that is the real finding

| Sitting | Untreated | Treated |
|---|---|---|
| First 5 | **4/5 = 80%** | 1/5 = 20% |
| New 5 | **2/5 = 40%** | 1/5 = 20% |

The treated rate reproduced exactly. **The untreated rate halved between sittings.** The 80% figure
that the n=10 power calculation was built on was itself a small-sample draw; the pooled estimate is
60%, with a 95% Wilson interval of roughly [31%, 83%].

So the extension did not fail because n was too small by bad luck. It failed because **the quantity
being estimated moves more than the effect being tested**, and no amount of additional sampling on
this design fixes that — it only narrows an interval around a number that drifts between sessions.

## What further runs would and would not buy

At the observed 60% vs 20%, Fisher's exact reaches p < 0.05 at **n=20 per arm** (12/20 vs 4/20,
p = 0.023). That is 40 runs, and it is **not recommended**: the calculation assumes a stable 60%
untreated rate, and the data above is direct evidence that the rate is not stable. Spending 40 runs
to narrow an interval around a moving target repeats this experiment's mistake at four times the
cost.

**No further extension is registered. This design is closed.**

## Over-suppression control — passes

| Arm | Findings per run | Mean | Zero-finding runs |
|---|---|---|---|
| Untreated | `2,2,2,2,1,1,2,1,3,1` | 1.7 | **0** |
| Treated | `3,2,2,1,1,1,2,1,1,1` | 1.5 | **0** |

No run in either arm returned zero findings. The treated mean is marginally lower, consistent with
removing one class of finding rather than suppressing generally.

## What may be claimed

- The rationale-clause failure mode is **real and frequent** on this pair — it occurs in 6 of 10
  untreated runs.
- The treated arm is **directionally lower and reproduced across two sittings** (1/5 and 1/5), with
  the over-suppression control holding.
- The difference is **not statistically established** (p = 0.17, optimistic).
- **Rubric wording is at the edge of what this instrument can measure.** A deterministic pre-model
  filter has no run-to-run variance and would be measurable at n=1, which is now the evidence-backed
  direction for this family rather than a preference.
