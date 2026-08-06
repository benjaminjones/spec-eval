# FAQ

Grouped by theme, from getting-started basics to scoring details. New here? Start with the
[Getting-started tutorial](GETTING-STARTED.md).

- [Getting started](#getting-started)
  - [Which command do I run first?](#which-command-do-i-run-first)
  - [Do I need a spec for every file?](#do-i-need-a-spec-for-every-file)
  - [Does it work for front-end code?](#does-it-work-for-front-end-code)
- [Running the checks](#running-the-checks)
  - [Can I check a single folder or a single file?](#can-i-check-a-single-folder-or-a-single-file)
  - [Can I run `audit` / `sufficiency` without an API key?](#can-i-run-audit--sufficiency-without-an-api-key)
  - [Can I set the commands up as slash commands?](#can-i-set-the-commands-up-as-slash-commands)
  - [How much does a run cost?](#how-much-does-a-run-cost)
  - [Can I redirect where specs or reports are written — say, to compare two models?](#can-i-redirect-where-specs-or-reports-are-written--say-to-compare-two-models)
- [Writing and adopting specs](#writing-and-adopting-specs)
  - [Can I use one spec per folder instead of one per file?](#can-i-use-one-spec-per-folder-instead-of-one-per-file)
  - [I already have docs/markdown from before spec-eval — are they used?](#i-already-have-docsmarkdown-from-before-spec-eval--are-they-used)
  - [The spec came first — can I check the code against it?](#the-spec-came-first--can-i-check-the-code-against-it)
  - [How do I change the spec template?](#how-do-i-change-the-spec-template)
  - [If I hand-edit a generated spec, will re-running `generate` clobber it?](#if-i-hand-edit-a-generated-spec-will-re-running-generate-clobber-it)
  - [The generated specs read very technical — can I make them plainer?](#the-generated-specs-read-very-technical--can-i-make-them-plainer)
- [Keeping specs current](#keeping-specs-current)
  - [What gets flagged when I change the spec or the code?](#what-gets-flagged-when-i-change-the-spec-or-the-code)
  - [How do I prevent orphaned specs?](#how-do-i-prevent-orphaned-specs)
  - [Can I ask an AI to fix the gaps for me?](#can-i-ask-an-ai-to-fix-the-gaps-for-me)
- [Trusting the scores](#trusting-the-scores)
  - [Why a rubric and a second opinion instead of just asking my agent?](#why-a-rubric-and-a-second-opinion-instead-of-just-asking-my-agent)
  - [Could a custom template change the scores or the fingerprint?](#could-a-custom-template-change-the-scores-or-the-fingerprint)
  - [How accurate are the scores (and the fingerprint)?](#how-accurate-are-the-scores-and-the-fingerprint)

## Getting started

### Which command do I run first?

`coverage` (free) shows which files have no spec; then `generate` authors the missing ones (or write them
yourself); then `sufficiency` grades what you have — `audit` earns its keep at the next milestone, once the
code has moved. The [tutorial](GETTING-STARTED.md) walks the full order for both starting points.

### Do I need a spec for every file?

No — `coverage` only counts *spec-worthy* code. It already excludes tests, config, generated files,
glue/entrypoints, and tooling; add `exclude:` globs in a config to skip more.

For the files that do count, "has a spec" means a markdown file paired with the code — by default the `.md`
with the same name beside it (`parser.md` ↔ `parser.py`), which is exactly what `generate` writes. Prefer one
spec per folder, or one doc covering many files? Both are layouts:
[Can I use one spec per folder instead of one per file?](#can-i-use-one-spec-per-folder-instead-of-one-per-file)

### Does it work for front-end code?

Yes — `.ts`, `.tsx`, `.js`, `.jsx` count as code by default (add `.vue`/`.svelte` with `code_ext:` in a config),
and the noise is already filtered: `*.spec.ts`/`*.test.tsx` classify as tests, minified bundles as generated,
`node_modules` is never walked. A front-end spec captures the **behavioral contract** — props and defaults, events
emitted, state transitions, routing, design-token values. The visual half (layout, "looks right") can't be checked
by comparing text against text — pair spec-eval with screenshot or visual-regression tests for that.

## Running the checks

### Can I check a single folder or a single file?

**A folder — yes, directly.** Every command takes any directory, not just the repo root:

```bash
spec-eval audit src/parser/
```

**A single file — also directly** (for `audit`, `sufficiency`, and `generate`):

```bash
spec-eval audit    src/parser.py     # grades parser.py against its parser.md — one model call
spec-eval generate src/parser.py     # or author that one spec
```

The file's co-located `<stem>.md` is the spec (under a per-dir layout, the folder spec). `coverage` stays
directory-only. Need a *custom* doc path, or one doc covering several files? Name the pair in a config:

```yaml
# one-pair.yml
pairs:
  - label: parser
    code: [src/parser.py]
    docs: [docs/parser-design.md]     # any path you like
```

```bash
spec-eval audit . --config one-pair.yml
```

**How multiple files are analyzed:** each pair is graded independently, one model call per pair. A pair whose
`code` globs match *several* files is graded as one unit — the files are concatenated under a size cap
(default ~64k characters of code, ~28k of spec — adjustable with a `caps:` block in a config), so very large
groups are judged on a truncated view. Prefer smaller,
focused pairs when you can.

### Can I run `audit` / `sufficiency` without an API key?

Yes, two ways.

- **From chat:** the [`spec-check` skill](skills/spec-check/SKILL.md) does the same job inside your
  coding-agent session — answers land in the chat, not in report files.
- **From the terminal:** add `--model claude-code` and **spec-eval** routes through the Claude Code CLI you're
  already logged into — same commands, same report files, billed to your subscription.

Step-by-step for both: [**"Run via prompt chat"** in the README](README.md#run-via-prompt-chat-no-setup),
or the [tutorial's setup step](GETTING-STARTED.md#pick-your-setup).

### Can I set the commands up as slash commands?

**spec-eval** itself doesn't ship slash commands — those belong to your coding tool. What it *does* ship is two
**agent skills** ([`skills/`](skills/): `spec-authoring`, `spec-check`). Claude Code loads them from
`.claude/skills/`; any agent that can read files (Copilot, Cursor, …) can follow the same skill files from
wherever it keeps reusable instructions (setup:
[README → "Run via prompt chat"](README.md#run-via-prompt-chat-no-setup)). If your tool supports custom slash
commands, point one at a skill or at a `spec-eval <subcommand>` shell call.

### How much does a run cost?

`coverage` and `context` are always free — no AI, no key, no tokens. For the AI commands, it depends on how you pay:

- **Claude subscription** (`--model claude-code`) — no per-token bill; runs count as normal subscription usage.
- **API key** — you pay per token. **spec-eval** never prints dollars (prices change); it prints the exact
  **token and call counts** so you can price a run against your provider's current rates.

The cost shape: **one model call per pair** (per spec-worthy file, or per config pair). A pair's cost tracks
its file's size, up to a hard per-file ceiling set by the input caps — adjustable with a `caps:` block in a
config (see [`configs/spec-eval.example.yml`](configs/spec-eval.example.yml)).

> [!IMPORTANT]
> **The figures below are rough estimates, not quotes — verify fully before relying on them.** They assume
> July 2026 list prices, and model prices, tokenizers, and discounts change often. Check your provider's
> current pricing page, and price real runs from the exact token counts **spec-eval** prints after every run.

| Model | `audit` / `sufficiency` per pair | `generate` per file |
|---|---|---|
| Claude Opus 4.8 | ~$0.06 typical · ~$0.23 at the cap | ~$0.07 · ~$0.23 |
| Claude Sonnet 5 | ~$0.04 · ~$0.14 | ~$0.04 · ~$0.14 |
| Claude Haiku 4.5 | ~$0.01 · ~$0.05 | ~$0.01 · ~$0.05 |

A full audit, by repo size:

| Repo size | Opus 4.8 | Haiku 4.5 |
|---|---|---|
| ~40 files — a small library | ~$3–4 | <$1 |
| ~200 files — a typical repo | ~$14–18 | ~$3 |
| ~1,000 files — a framework or app | ~$70–90 | ~$15–18 |
| ~10,000 files — a large monorepo | ~$700–900 | ~$150–180 |

Two durable ways to pay less: provider **batch APIs** (async — fine for audits; typically about half price)
and a **cheaper model** for routine runs. And at any size, `coverage` and `context` stay free, and `--model claude-code`
bills your subscription, not an API.

### Can I redirect where specs or reports are written — say, to compare two models?

**Reports — yes:** every command takes `--out`, and that's exactly how you compare two graders:

```bash
spec-eval audit . --model claude-code             --out spec-reports/claude
spec-eval audit . --model google:gemini-3.5-flash --out spec-reports/gemini
```

**Authored specs — no flag.** `generate` deliberately writes beside the code (or at the folder/pair location
your layout names) — co-location is the convention every check understands. To compare what two models *write*,
use branches, which is what specs-as-code is for:

```bash
git checkout -b specs-claude && spec-eval generate . --model claude-code
git checkout -b specs-gemini main && spec-eval generate . --model google:gemini-3.5-flash
git diff specs-claude specs-gemini -- '*.md'
```

(Advanced: `--layout per-pair` authors each pair's doc wherever the config's `docs:` path points — e.g.
`docs/claude/parser.md` — if you'd rather steer paths through a config.)

**Also worth comparing:** `runs.jsonl` accumulates every run's scores per `--out` dir, and the report
fingerprints are plain markdown tables — both diff cleanly across models or over time.

## Writing and adopting specs

### Can I use one spec per folder instead of one per file?

Yes — set the authoring **layout**. `generate --layout per-dir` writes one spec per directory
(`src/parser/parser.md` covering `src/parser/*.py`), synthesised from each module's intent so a big folder never
blows the size cap; `coverage`/`audit`/`sufficiency` then treat that folder spec as governing the whole
directory. Layouts (in a config or via flags):

```yaml
authoring:
  layout: per-dir          # spec granularity: per-file (default) | per-dir | per-pair
  overview: repo           # overview files over the specs — pick one:
                           #   none    (default) no overview files
                           #   repo    one OVERVIEW.md at the top of the path you scan
                           #   per-dir a README.md overview inside each folder with 2+ modules
                           #           (overview_min_files adjusts the bar; specs themselves are never size-gated)
                           #   both    repo + per-dir
```

Note `layout` and `overview` both offer `per-dir`, but they mean different things: `layout: per-dir` changes where
the *specs* go, `overview: per-dir` only adds overview files beside per-file specs.

`per-pair` authors the `docs` file of each explicit `pairs` entry from its `code` glob — the escape hatch for
groupings the conventions don't cover.

### I already have docs/markdown from before spec-eval — are they used?

Not automatically. By default only a `.md` with the same name beside a code file counts as a spec, so your
README and `docs/` folder are ignored. To adopt a pre-existing doc, point a pairs config at it:

```yaml
pairs:
  - label: parser
    code: [src/parser/**/*.py]
    docs: [docs/parser-design.md]     # your existing doc, wherever it lives
```

Then run the checks against exactly that path — the config scopes them:

```bash
spec-eval audit       . --config pairs.yml      # drift: does docs/parser-design.md contradict the code?
spec-eval sufficiency . --config pairs.yml      # completeness: what does it leave out?
```

`coverage` counts the paired files as covered too. Same mechanism works for one code file — see
["Can I check a single folder or a single file?"](#can-i-check-a-single-folder-or-a-single-file).

### The spec came first — can I check the code against it?

Yes. Say `docs/feature-x.md` was written first, then the code (by an agent, or by hand):

**In chat:**

```text
Read skills/spec-check/SKILL.md and follow it —
check docs/feature-x.md against the code that implements it.
```

Name the code paths in the prompt if you want exact scope.

**From the terminal:** point a pair at it (previous question), then run both checks — "matches" has two halves:

```bash
spec-eval audit       . --config pairs.yml   # the spec promises something the code doesn't do
spec-eval sufficiency . --config pairs.yml   # the code does something the spec never captured
```

Each finding says which side to change.

> [!TIP]
> - Split a big feature into a few small pairs — one giant pair gets truncated before grading.
> - A short spec isn't flagged for what it leaves unsaid — that's the gap `sufficiency` catches.

### How do I change the spec template?

Depends on which path authors your specs:

**Terminal (`generate`):**
1. Write a template — a short markdown file describing the sections you want. Start from the shipped sample:
   [`configs/spec-template.example.md`](configs/spec-template.example.md).
2. Point at it: `spec-eval generate . --template my-template.md` (or set `authoring.template` in a config).

Your template controls the spec's **structure**. **spec-eval** always appends its built-in authoring **discipline**
(assert only invariants the code enforces, drop code trivia, label inferred intent) so the output stays
gradeable. With no template, the built-in structure (`AUTHORING_RUBRIC` in
[`spec_eval/authoring.py`](spec_eval/authoring.py)) is used.

**Chat (skills):** edit [`skills/spec-authoring/templates/spec-template.md`](skills/spec-authoring/templates/spec-template.md) —
your agent authors from it.

Either way, a generated `.md` is a plain file — you can always just edit it afterward. (Wondering whether a new
template moves your scores? See
[Could a custom template change the scores or the fingerprint?](#could-a-custom-template-change-the-scores-or-the-fingerprint))

### If I hand-edit a generated spec, will re-running `generate` clobber it?

No. `generate` **skips any target that already has a file** — per-file specs, folder specs, and overviews
alike — so your edits persist. Only `--overwrite` re-authors (save it for first-time setup).
`audit`/`sufficiency` only *read* specs; they never rewrite them.

### The generated specs read very technical — can I make them plainer?

Yes — a spec is a plain markdown file you own, and the checkers grade **meaning, not tone**. Two ways to
change the voice:

**Rewrite the specs you have** — edit by hand, or paste one into a chat with a prompt like:

```text
Rewrite this spec in plainer language for a reader new to the codebase.
Keep every number, default, name, and rule exactly as written — simplify
the words around them, not the facts.
```

That one rule is the whole trick: friendly wording costs nothing, but a dropped threshold or a reworded
contract is a real change. (Your edits persist — see the previous question.)

**Change the voice of future specs** — put audience guidance in a custom template ("write for a reader new
to the codebase; explain jargon in plain words") and pass it with `--template`
(see [How do I change the spec template?](#how-do-i-change-the-spec-template)).

Either way, let the tools check the rewrite: `audit` catches a simplification that now *contradicts* the
code, and `sufficiency` catches one that *dropped* behavior. If both hold steady, that's strong evidence the
plainer wording lost nothing that matters. Rewrite in small batches and review the diffs like any code change.

## Keeping specs current

### What gets flagged when I change the spec or the code?

Each check watches a different kind of change:

| You change… | What notices |
|---|---|
| a value in the spec so it disagrees with the code | `audit` — a numeric/signature/default clash is a **high** drift finding |
| the spec's wording (same meaning) | nothing — style isn't drift |
| **delete** a claim from the spec | `sufficiency` — that behavior becomes a gap. `audit` stays quiet: *silence is not drift* |
| the code, so the spec is now wrong | `audit` — same drift, found from the other side |
| **add** new behavior to the code | `sufficiency` — the spec now omits it |
| add a whole new code file | `coverage` — it shows up as uncovered |
| delete or rename a code file, leaving its old spec behind | `coverage` — lists it under **possible orphaned specs** (a heuristic: conventional docs like README are never flagged, and it never moves the coverage %) |

Nothing "syncs" automatically: the checks **report**, and *you* decide which side to fix — update the spec, or
fix the code. `generate` only fills *missing* specs; it never edits existing ones.

### How do I prevent orphaned specs?

Mostly, you don't have to do anything special — **detection is built in**: every `coverage` run lists *possible
orphaned specs* (a spec-shaped `.md` whose same-stem code file is gone), so if `coverage` is in your pre-commit
hook or CI, orphans surface on the next run automatically. To keep them from appearing at all, two habits:

1. **Treat the spec as part of the file.** When you move or rename `parser.py`, move `parser.md` with it; when
   you delete code, delete its spec in the same commit. (Tell your coding agent this once — "specs move with
   their code" — and agentic churn stops creating orphans.)
2. **Pin docs that live elsewhere with a pairs config.** A pair whose `code` globs stop matching shows up in
   `audit` as *skipped (no files matched)* — the config-side version of the same signal.

The orphan list is advisory — it never fails your `--min` gate — so it nags without breaking builds.

### Can I ask an AI to fix the gaps for me?

Yes — that's the intended loop. Each gap in `spec-reports/sufficiency.md` says what's missing and points at the
code (`file.py (function)`), so a coding agent can read that code and add the missing piece to the right spec.
A good prompt:

```text
For each gap in spec-reports/sufficiency.md, check the code at its pointer,
then add the load-bearing ones to the matching spec. List anything you
skipped as trivia, so I can review.
```

Two habits keep it honest: **don't add every minor gap** (some details belong in code, not specs — a spec that
restates everything is just a second copy of the code), and **re-run `sufficiency` and `audit` afterward** — the
score should rise, and nothing new should contradict the code.

## Trusting the scores

### Why a rubric and a second opinion instead of just asking my agent?

You can just ask — *"does this spec match my code?"* — and for a quick look it's fine. What a fixed rubric and
an optional second vendor add is **reliability**: how much of the real disagreement a check actually catches.

- **One open-ended "does this match?" tends to skim.** Asked to judge a whole spec at once, a model gives a
  plausible overall verdict and often settles on "looks fine," passing over a specific clash. `audit` and
  `sufficiency` grade against a **fixed rubric** — the same defined checks, applied point by point — so a
  contradiction or a missing behavior has to be looked at, not glossed over.
- **One model has blind spots.** A grader can miss what a different model catches, and a model checking work
  it just produced tends to be too generous. The optional
  [second opinion](README.md#higher-stakes-get-a-second-opinion) runs the same check with a **different
  vendor** and keeps what they agree on — so no single model is marking its own homework.
- **The run is repeatable and recorded.** Every run appends to `runs.jsonl` and writes the same report tables,
  so you watch a score move over time instead of trusting one off-the-cuff answer.

You can reproduce the effect on **spec-eval's own specs**: run `audit` with two different vendors over the same
pairs and compare — where they disagree is exactly where a single pass would have handed you false confidence.
The current dated receipt from spec-eval grading itself is in [SPEC-HEALTH.md](spec-reports/SPEC-HEALTH.md).

None of this turns a score into a guarantee — `drift` and `sufficiency` are still AI judgments that wobble
([How accurate are the scores?](#how-accurate-are-the-scores-and-the-fingerprint)). The rubric and the second
opinion raise how far you can lean on them; they don't replace reading the evidence each finding quotes.

### Could a custom template change the scores or the fingerprint?

The scoring machinery doesn't change: `audit` and `sufficiency` grade the spec's **content** against the code
with their own fixed rubrics, and the fingerprint is just a bar-chart of the resulting numbers. But the template
shapes what a generated spec *contains* — and content is exactly what gets graded. A template that drops the
sections where behavior, defaults, and contracts live will produce specs that capture less, and sufficiency will
(correctly) score them lower. The always-appended discipline keeps the output gradeable, not complete.

> [!TIP]
> After switching templates, re-generate one pilot folder and compare its `sufficiency` trend against the old
> template before rolling out.

### Not sure a finding is real? Double-check it with `--verify`

Think of `audit` as a metal detector. You sweep it over your project and it beeps. Most beeps are coins. Some
are bottle caps.

`--verify` is the second look before you start digging:

```bash
spec-eval audit . --verify
```

It sends each finding back to a fresh AI reader with the whole spec, and asks one question: **does the spec
actually say the thing this finding says it says?** If not, the finding is thrown out.

A finding can only be thrown out for one of four reasons, and the reader has to quote the line that proves it:

- the spec line the finding points at doesn't actually claim that
- the spec says the right thing somewhere else, further down
- the sentence was explaining *why*, not promising what the code does
- the spec was talking about a different case

Anything else stays. If the reader isn't sure, it stays.

**Use it when you're about to act on the findings** — before a release, or before editing a spec you didn't
write. **Skip it for a quick look around**, because it costs one extra AI call for each file that had findings.

Thrown-out findings don't disappear. They show up crossed out, with the reason and the spec line, so you can
disagree. And it can only ever *remove* findings — it never finds new ones. So a clean report after `--verify`
means the same thing a clean report always means: nothing was found this run.

### How accurate are the scores (and the fingerprint)?

First, what each number *is*: [How the scores are made](README.md#how-the-scores-are-made). How much to *trust*
each — three different answers for the three layers:

- **coverage** and **context** are exact and deterministic: they count files and scan code text, no AI involved.
- **drift** and **sufficiency** are **AI judgments**, and they wobble — the same spec might score 0.78 one run
  and 0.72 the next.
- **The fingerprint** adds no error of its own — it's a bar-chart of the numbers behind it.

So treat the AI scores as calibrated guidance you still validate:

1. Watch the **trend**, not the exact decimal.
2. Read the **evidence** quoted in each finding, not just the number.
3. For high-stakes results, run **two vendors** and trust what they agree on — commands in
   [README → "Higher stakes? Get a second opinion"](README.md#higher-stakes-get-a-second-opinion).
