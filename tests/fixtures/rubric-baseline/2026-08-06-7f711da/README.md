# Retained drift baseline — `7f711da`, 2026-08-06

The pre-change record that any `DRIFT_RUBRIC` edit is measured against. Issues #35, #36 and #37 each
state that no rubric change lands without one, because the last change in that family was promoted,
measured, found to have no effect, and reverted — and two earlier measurement arms are permanently
unrecoverable because their per-fixture records went to `/tmp` and to a stripped JSON.

This baseline cost nothing to create: it is a copy of the tracked whole-repo `audit --verify` output
that was already in `spec-reports/`, taken before any rubric edit.

## What is here

| File | Role |
|---|---|
| `findings.json` | **The comparison surface.** Every finding for all 11 pairs, with its verification verdict, ground and `doc_quote`. |
| `report.md` | The rendered view of the same run. Useful for reading; **not** the comparison surface — see below. |
| `runs.jsonl` | Provenance: the run at `git_sha` `7f711da`, 11 pairs audited, 8 high/medium drift findings. |

**Compare against `findings.json`, not `report.md`.** Issue #26 changes report wording (`not graded`
vs `✓ clean`, and the headline denominator), so `report.md` text moves for reasons that have nothing
to do with the rubric. `findings.json` does not.

## The rule

Re-capture before any `DRIFT_RUBRIC` edit. A baseline captured *after* a rubric change measures a
rubric that has already moved.

## Which pairs this baseline is still valid for

Only pairs whose code **and** doc are unchanged since `7f711da`. A pair that has been edited would
differ from the baseline for reasons unrelated to the rubric. Recompute the surviving set rather than
trusting a list — free, no model call:

```sh
for m in audit authoring cli coverage providers report rubric runlog sufficiency syscontext verify; do
  [ -z "$(git diff --name-only 7f711da..HEAD -- spec_eval/$m.py spec_eval/$m.md)" ] && echo "valid: $m"
done
```

At capture time the surviving set was: `audit`, `coverage`, `rubric`, `runlog`, `sufficiency`,
`syscontext`. (`report` and `cli` leave the set with the #26 change that accompanies this capture;
`authoring`, `providers` and `verify` had already moved.)

`coverage` is the pair that matters for #35: it retains a `medium` finding whose entire `doc_quote` is
a `**Why:**` rationale sentence, withdrawn on the `not-normative` ground. That is the single
byte-identical before/after case for the rationale rule.

## What this baseline is not

It is one run, on one repository, with one model. It supports a **per-pair** before/after comparison
and nothing else. It is not a fixture set large enough to produce a rate, and no proportion should be
computed from it.
