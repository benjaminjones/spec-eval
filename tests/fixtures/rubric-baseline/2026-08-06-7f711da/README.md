# Retained drift baseline — `7f711da`, 2026-08-06

> ## ⚠ CORRECTED 2026-08-19 — this capture is not a usable comparison point
>
> This file described a single retained run as the thing a rubric change is measured against. That
> was wrong in two ways, and both were found by trying to use it.
>
> **1. The detector was never pinned.** `claude-code` resolves to the Claude Code CLI's *own default
> model* (`spec_eval/providers.py`), which moves over time. This capture is from 2026-08-06; a run
> made on any later day is a different detector. The rule below controls which *pairs* stayed valid
> and says nothing about the detector — the one variable a rubric measurement turns on. Pin it with
> `claude-code:<name>`, or use an API model, or capture both arms in one session.
>
> **2. One run is not a baseline for a nondeterministic detector.** Five runs of the same commit on
> the same pair produced no finding recurring in more than 2 of 5 runs, and a headline drift count of
> `1, 0, 0, 0, 0`. See `../2026-08-19-variance/README.md`. Comparing one run against one run cannot
> detect a rubric change in either direction.
>
> **What this capture is still good for:** provenance, and a record of what the tool reported on
> 2026-08-06. **Do not** diff a later single run against it and read the difference as an effect.
> The replacement design is a repeated-run proportion test — see
> `../PRE-REGISTRATION-rationale-rule.md`.

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

**And pin the detector, or re-capture it alongside the treated arm.** A baseline is only a baseline
in the variables it actually holds fixed. `claude-code` is an alias, not a model; reusing a capture
made under it on an earlier day silently varies the detector. Either pass `claude-code:<name>` (the
bridge forwards `<name>` to the CLI's `--model`), name an API model, or run both arms inside one
session and compare only within it.

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
a `**Why:**` rationale sentence, withdrawn on the `not-normative` ground. ~~That is the single
byte-identical before/after case for the rationale rule.~~ **Withdrawn 2026-08-19** — the pair's code
and doc are byte-identical, but the finding is not: it recurs in only 2 of 5 identical runs. The
rationale-clause *class* recurs in 4 of 5, which is what the replacement design counts.

## What this baseline is not

It is one run, on one repository, under an unpinned detector alias. ~~It supports a **per-pair**
before/after comparison and nothing else.~~ **It supports no before/after comparison at all** — see
the correction at the top. It is not a fixture set large enough to produce a rate, and no proportion
should be computed from it.
