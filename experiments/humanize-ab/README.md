# Does humanizing a spec cost sufficiency?

An A/B experiment against spec-eval's own graders, on one small spec.

## The question

Editing passes that remove AI-writing tells work on prose: they cut filler, drop boilerplate emphasis, and
dissolve bolded inline-header lists into flowing sentences. Applied to a generated spec, the last of those
changes the artifact spec-eval measures.

`SUFFICIENCY_RUBRIC` grades whether a spec captures the code's behaviors, contracts, defaults and rules, and
states that "1:1 line restatement is NOT required". Read literally, that means it scores **content**. But a spec
carries much of its content in tables: Definitions, `INV-*` invariants, and `AC-*` acceptance criteria. If the
grader also rewards **shape**, then prose-ifying those tables costs score even when every fact survives.

Nobody has measured which. This experiment answers it for about ten model calls.

## Design

One module, `spec_eval/runlog.py`, and three versions of its spec. `runlog.md` is the smallest spec in the repo
(4,502 bytes) and still carries 3 invariants and 6 acceptance criteria, so it exercises the table question at
minimum cost.

| Variant | What changed |
|---------|--------------|
| `baseline` | The shipped `runlog.md`, unmodified. Establishes the score and the noise floor. |
| `frozen` | Prose-only edit. Tables, code fences, IDs, numbers and rubric markers are protected; only sentences change. |
| `naive` | Every table dissolved into prose. All facts kept, all structure lost. |

Both variants preserve every checkable literal from the baseline. `scripts/verify_facts.py` enforces this before
any model call is spent: it extracts the baseline's backticked spans and bare numbers and asserts each survives.
A variant that dropped a fact would produce a score drop explained by the missing fact rather than by the lost
shape, and the run would prove nothing.

The `naive` variant drops all 9 structural IDs. That is the variable under test, not a defect, so the guard
reports IDs separately from facts.

### The freeze list

`frozen` protects, verbatim: markdown tables, fenced code blocks, `INV-*` and `AC-*` rows and IDs, every number
and identifier, section headings, the `**Why:**` marker, and the `> Reconstructed intent (confidence: …)` label
that `AUTHORING_DISCIPLINE` requires.

It changes only prose: em dashes outside tables, filler, hedging, and meta-phrasing. One edit is worth naming:
the baseline opens §1 with "The one governing constraint a reviewer can check:", which `AUTHORING_STRUCTURE`
explicitly forbids ("never as meta-phrasing like 'the one governing constraint a reviewer can check'").
`frozen` states the constraint directly instead.

Passive-voice edits are restricted to cases where the actor is verifiable in the code — `git_sha()` and
`append_run()` are named because they exist. Naming an actor the code does not have would read as "mechanism
described differently", which is a **medium** finding under `DRIFT_RUBRIC`. That restraint is part of what
`frozen` is testing.

## Running it

```bash
export ANTHROPIC_API_KEY=...
REPS=3 experiments/humanize-ab/run.sh
```

`REPS` defaults to 3 and `MODEL` to the repo default. The script swaps each variant into `spec_eval/runlog.md`,
scores it with `sufficiency` and `audit`, and restores the original on every exit path including Ctrl-C. All
output lands in `.results/`; the repo's own `spec-reports/` is never written to.

## Reading the result

`scripts/collect.py --summarize` prints per-variant means with the min..max spread and each variant's delta
against the baseline.

**Read the spread before the deltas.** spec-eval has never measured its own run-to-run noise on a fixed
artifact: `spec-reports/runs.jsonl` contains no same-SHA repeat, so the often-cited score movement is confounded
with the doc fixes made between those runs. The baseline reps here are that missing noise floor. A variant delta
smaller than the baseline's own spread is indistinguishable from grader variance.

Three outcomes and what each one means:

- **`naive` drops well past the noise floor, `frozen` sits inside it.** The grader rewards shape as well as
  content. A prose pass must protect tables, and a freeze list is mandatory rather than optional.
- **Both sit inside the noise floor.** The grader scores content, as its rubric claims. Presentation is free,
  and the cost question becomes the only one that matters.
- **`frozen` also drops.** Something in the prose edits is load-bearing. The per-run `sufficiency.json` gap
  lists say which, since each gap carries a `code_ref`.

## Watch the drift number too

`audit` runs alongside `sufficiency` because drift can move in the flattering direction. `DRIFT_RUBRIC` reserves
**high** severity for a measurable guarantee the code breaks, and adds: "If you must paraphrase the doc to see
the violation, it is NOT high." Its do-not-flag list also protects "missing-but-implied behaviour where a doc
could plausibly be silent (silence is not drift)."

So a rewrite that paraphrases a threshold can demote a real finding, and one that omits it can convert that
finding into protected silence. Either way the drift count improves without a line of code changing. A run where
sufficiency holds steady but drift findings disappear is the outcome most worth understanding, because it looks
like an improvement and is not one.

## Attribution

The editing rules exercised here come from the `humanizer` skill (<https://github.com/blader/humanizer>,
MIT, © 2025 Siqi Chen), whose own catalogue derives from Wikipedia's "Signs of AI writing" page maintained by
WikiProject AI Cleanup. No text from either source is reproduced in this repository; the variants are original
prose written to test the effect those rules describe.
