# spec-eval — Build fast with AI. Validate with specs.

**Your code changes fast. Your docs fall behind. spec-eval keeps them honest.**

*The trust layer for [spec-driven development](https://en.wikipedia.org/wiki/Spec-driven_development) — iterate fast, keep the spec and code in agreement.*

*A trust-eval for your specs — coverage, drift, and sufficiency, measured against the code.*

[Get started](#try-it) · [Tutorial](https://github.com/benjaminjones/spec-eval/blob/main/GETTING-STARTED.md) · [No API key?](#run-via-prompt-chat-no-setup) · [Second opinion](#higher-stakes-get-a-second-opinion) · [FAQ](https://github.com/benjaminjones/spec-eval/blob/main/FAQ.md)

A **spec** is short for **specification** — a plain-English description of what your code should do. **spec-eval**
keeps one beside your code — per file, or per folder — and checks the two still agree, so the spec stays worth
trusting. How far you lean on it is up to you. **No specs yet? spec-eval writes them for you.**

## Table of contents

- [The problem](#the-problem)
- [What it checks](#what-it-checks)
- [What it creates](#what-it-creates)
- [Try it](#try-it)
  - [Run via prompt chat (no setup)](#run-via-prompt-chat-no-setup)
  - [Run in the terminal, no key (Claude subscription)](#run-in-the-terminal-no-key-claude-subscription)
  - [Run in the terminal with an API key (for CI)](#run-in-the-terminal-with-an-api-key-for-ci)
- [How the scores are made](#how-the-scores-are-made)
- [Reading the scores](#reading-the-scores)
- [Higher stakes? Get a second opinion](#higher-stakes-get-a-second-opinion)
- [Proof it works](#proof-it-works)
- [More](#more)
- [FAQ](#faq)
- [Feedback](#feedback)
- [Acknowledgements](#acknowledgements)

## The problem

Specs go stale the moment code moves on — and one stale spec is enough to stop a reader trusting all of them.
AI coding agents make code move faster than any hand-maintained doc can follow.

**spec-eval** treats specs like code: **run a check — via a chat prompt, an ordinary command, or a CI step — and
the spec is measured against the source.** A spec you can check is a spec you can trust.

## What it checks

Three simple questions:

| Check | The question it answers | How |
|---|---|---|
| **coverage** | Does this code have a spec at all? | Just counts files. Free — no AI, no key. |
| **drift** | Does the spec say something the code doesn't do? | An AI reads each spec and its code and lists the clashes. |
| **sufficiency** | How completely does the spec capture the code's behavior? | An AI lists what the spec misses and scores it 0–1 — an indicator, not a guarantee. |

Your **code is the source of truth** — the spec is what gets graded against it.

## What it creates

Everything it writes is plain markdown, right next to your code:

```text
your-project/
├─ src/
│  ├─ parser.py
│  ├─ parser.md        ← generate: a spec beside each code file
│  ├─ api.py
│  └─ api.md
├─ OVERVIEW.md         ← optional overview of the spec set (--overview repo)
└─ spec-reports/       ← the checks write here
   ├─ coverage.md        which files have a spec
   ├─ system-context.md  which external systems the code talks to (with file:line evidence)
   ├─ report.md          drift findings
   ├─ sufficiency.md     0–1 completeness per spec
   ├─ runs.jsonl         run history
   └─ SPEC-HEALTH.md     one-page scorecard (ask the skill to write it, or edit by hand)
```

## Try it

Prefer a guided walkthrough? **[Getting-started tutorial →](https://github.com/benjaminjones/spec-eval/blob/main/GETTING-STARTED.md)**

**The commands** — in the order you'll typically use them:

- **coverage** — which files have no spec yet? *(free — no AI)*
- **context** — which external systems does the code talk to (S3, databases, partner APIs)? *(free — no AI)*
  Strong support for the mainstream stacks (Python, JS/TS, Java, Kotlin, C#, Go, Rust, Swift, Ruby) — the
  exact list lives in [`spec_eval/syscontext.md`](https://github.com/benjaminjones/spec-eval/blob/main/spec_eval/syscontext.md).
- **generate** — writes a plain-English spec beside each file that has none *(uses AI)*
- **sufficiency** — how completely does each spec capture the code? Scored 0–1 *(uses AI)*
- **audit** — the drift check: does any spec clash with the code? Run it at every milestone *(uses AI)*

None of them change your files — reports go to `spec-reports/`. The exception is `generate`, which writes new
specs beside your code: review them and commit the keepers like code.

The `(uses AI)` commands (`generate`, `sufficiency`, `audit`) need an AI behind them — `coverage` and
`context` never do. Three ways to run them, least setup first:

### Run via prompt chat (no setup)

Ask the coding agent you already have (Claude Code, Copilot, Cursor, …) — nothing to install, no key, answers
land in the chat. Copy a block, adjust the `{{slots}}` if you want, paste it — each slot shows its default
after `=`, and the agent echoes the settings for your OK before it writes.

<!-- KEEP IN SYNC: the defaults in these two blocks (layout per-file, overview none + its four values,
     spec-reports/) mirror spec_eval/cli.py + spec_eval/authoring.py; tests/contract/test_prompt_snippets_sync.py
     pins them so a code change can't silently leave the snippets stale. -->
#### Write specs

The [authoring skill](https://github.com/benjaminjones/spec-eval/blob/main/skills/spec-authoring/SKILL.md) carries the spec structure
(the `INV-*` invariant and `AC-*` acceptance-criteria tables come from its rubric and templates):
```text
Read {{SKILL = https://github.com/benjaminjones/spec-eval/blob/main/skills/spec-authoring/SKILL.md}}
and its templates/ folder, then follow it to write specs for: {{TARGET = ./  (a file, a folder, or the whole project)}}

Settings — defaults below. Before writing anything, echo TARGET and these three settings back in one
message — each setting with its full option list from the comments, so I can pick in my reply — and
wait for my OK:
  - layout:   per-file    # per-file (a spec beside each file: src/x.py -> src/x.md) | per-dir (one spec per folder) | per-pair (folders you map in a config)
  - overview: none        # none | repo | per-dir | both — none = no overview files; any other value adds them (both = top-level OVERVIEW.md + a README.md per folder). A repo-level OVERVIEW.md carries an Architecture (data flow) Mermaid diagram + a System context section (the external systems the code talks to, when any are observed); per-folder READMEs are a lean index.
  - reports:  chat only   # chat only (results land in the chat) | save (also save the results to spec-reports/)
Do one scoped job at a time (one file, or one folder) so a small-context agent doesn't run out of tokens.
```

#### Check specs

The [checking skill](https://github.com/benjaminjones/spec-eval/blob/main/skills/spec-check/SKILL.md) grades what exists (drift + sufficiency):
```text
Read {{SKILL = https://github.com/benjaminjones/spec-eval/blob/main/skills/spec-check/SKILL.md}}
and follow it to check specs for: {{TARGET = ./  (a file, a folder, or the whole project)}}
Before checking, echo TARGET and the report setting back in one message — with its full option list
from the comment, so I can pick in my reply — and wait for my OK:
  - run both passes, in order: 1) coverage (which files have no spec), 2) drift (do the specs match the code)
  - reports:  chat only   # chat only (results land in the chat) | save (also save the results to spec-reports/)
Check one folder at a time so a small-context agent doesn't run out of tokens.
```

> [!TIP]
> Cloned the repo? Point `{{SKILL}}` at your local `path/to/spec-eval/skills/…/SKILL.md`. With the remote
> default, your agent may ask you to approve each fetch (the skill, then its templates) — that's normal; the
> local path skips the prompts. If your prompt and
> the skill disagree, your prompt wins — the skill carries the method, your slots carry the choices.
> The `overview` values: `none` *(default)* — no overview files · `repo` — one `OVERVIEW.md` at the top of the
> scanned path · `per-dir` — a `README.md` overview in each folder with 2+ modules · `both` — repo + per-dir.
> (`layout` places the *specs*; `overview` only adds overview files.)

> [!TIP]
> **Author and check in separate sessions.** A checker that still remembers its authoring decisions tends to
> echo them instead of re-reading the code — the same reason a PR isn't reviewed by its author. Write specs in
> one session; open a fresh one to check them.

**Make it a standing command** *(optional, one-time)* — copy the [`skills/`](https://github.com/benjaminjones/spec-eval/tree/main/skills/) into your agent's skills
folder (Claude Code: `.claude/skills/`). Then the prompt is the command:
```bash
mkdir -p .claude/skills && cp -r path/to/spec-eval/skills/* .claude/skills/
```
```text
Which files have no spec yet?              # coverage
Write a spec for src/parser.py             # generate
How completely do my specs cover my code?  # sufficiency
Check my specs against my code             # audit (drift)
Show me the architecture diagram           # diagram
```

### Run in the terminal, no key (Claude subscription)

Install once, then add `--model claude-code` to any `(uses AI)` command — **spec-eval** routes through the
`claude` CLI you're already logged into (no key; your `ANTHROPIC_API_KEY` is hidden from the call, so it can't
accidentally bill the paid API). The same commands, in the same order as the list above:
```bash
pip install spec-eval                                     # or, from a clone:  pip install -e .
spec-eval coverage    ./your-project                      # free — no AI, no key
spec-eval context     ./your-project                      # free — no AI, no key
spec-eval generate    ./your-project --model claude-code
spec-eval sufficiency ./your-project --model claude-code
spec-eval audit       ./your-project --model claude-code
spec-eval diagram     ./your-project --model claude-code  # Mermaid architecture diagram → stdout (--write to save)
```
Every terminal run writes its reports to `spec-reports/` (plus a `runs.jsonl` history line).

### Run in the terminal with an API key (for CI)

Export a key and run any command above **without** `--model claude-code` — an API key is the default. This is
the option for CI, the checks that run automatically on every push (store the key as a repo secret):
```bash
export ANTHROPIC_API_KEY=sk-ant-...     # or OPENAI_API_KEY / GOOGLE_API_KEY
```

> [!NOTE]
> A typical first run is `coverage → generate → sufficiency`, then at every milestone after: `audit` — plus
> `sufficiency` when you've added behavior. The [tutorial](https://github.com/benjaminjones/spec-eval/blob/main/GETTING-STARTED.md) has step-by-step guides for
> starting with no specs and for existing docs.

> [!TIP]
> **Version control is also your preview.** The three checks never modify your project; `generate` adds
> ordinary new files — review them with `git diff`, edit what's off, and drop any you don't want with
> `git checkout -- <file>`. (A full `generate --overwrite` rewrites everything, so save it for first setup.)

A few things worth knowing:

- **No config needed** — by default each spec pairs with the code file of the same name beside it (`parser.md` ↔ `parser.py`).
  Prefer one spec per folder? `--layout per-dir` ([FAQ](https://github.com/benjaminjones/spec-eval/blob/main/FAQ.md#can-i-use-one-spec-per-folder-instead-of-one-per-file)).
- **Any language, three providers** — swap the model with `--model openai:…`, `google:…`, or `claude-code`
  (Anthropic is the default); code is read as plain text. Want another provider? [Open an issue](#feedback).
- **Your other docs are safe** — by default only a `.md` next to code with the same name counts as a spec, so your
  READMEs are left alone. (Folder specs and overview files only appear if you opt in with `--layout` / `--overview`.)
- **What's shared** — to grade a spec, its code and text go to your AI provider. That's it. (`coverage` and `context` send nothing — they run fully on your machine.)

**Keep it honest on every commit** — add one line to a git hook (a script git runs before each commit) so new
code always needs a spec; copy-paste setup in [the tutorial](https://github.com/benjaminjones/spec-eval/blob/main/GETTING-STARTED.md#make-it-routine):
```bash
spec-eval coverage . --min 90    # fails the commit if coverage drops below 90%  (free — no AI)
```

## How the scores are made

Three scores, three simple ideas:

- **coverage** = spec files you *have* ÷ spec files you *need* → a percent. Just counting, **no AI**.
  *(9 of 10 code files have a spec → 90%.)*
- **drift** = the number of spots where the AI reader *found* the spec and the code flat-out disagreeing.
  **`0` means it found nothing this run. It is not proof that your spec and code agree.**
- **sufficiency** = how much of what the code does is actually written in the spec, from **`0` to `1`**.
  *(`1.0` = it's all there; `0.1` = almost none of it is.)*

Those three are **per spec**. The repo's one **sufficiency** score is just their **average** — each spec's
`0`–`1`, added up and divided by how many specs were scored. *(coverage is already one repo-wide `%`; drift is
the total count across specs.)*

`coverage` is pure counting. The other two need an **AI reader**: it reads each spec next to its code and grades
the pair against a fixed rubric — one model call per pair (`audit --verify` adds one more, but only for pairs that had findings). Two things follow from that:

> [!NOTE]
> AI scores **wobble**: the same spec might get 0.78 one run and 0.72 the next, like two teachers grading the same
> essay. Watch the **trend**, not the decimal — a jump like 0.72 → 0.85 is a real improvement.

> [!IMPORTANT]
> AI calls **spend tokens** — through your API key, your Claude subscription with `--model claude-code`, or
> your coding agent's own usage if you asked in chat. Every CLI run prints its exact call and token counts.

**Want the exact rules behind each score?** spec-eval specs its own scoring — read
[`spec_eval/coverage.md`](https://github.com/benjaminjones/spec-eval/blob/main/spec_eval/coverage.md) (how coverage counts),
[`spec_eval/rubric.md`](https://github.com/benjaminjones/spec-eval/blob/main/spec_eval/rubric.md) (the drift rules), and
[`spec_eval/sufficiency.md`](https://github.com/benjaminjones/spec-eval/blob/main/spec_eval/sufficiency.md) (how the 0–1 score is decided).

## Reading the scores

Each run writes a short report to `spec-reports/` (a `.md` you read, a `.json` for tools):

- **coverage** — the % of your code that has a spec, and which files don't. *(live example: [coverage.md](https://github.com/benjaminjones/spec-eval/blob/main/spec-reports/coverage.md))*
- **drift** — each place the AI reader found a spec and the code disagreeing: the code line and the spec line it quoted, plus a suggested fix. `0` means this run found nothing. *(live example: [report.md](https://github.com/benjaminjones/spec-eval/blob/main/spec-reports/report.md))*
- **sufficiency** — a `0`–`1` score per spec (worst first), listing what's missing with a searchable code pointer
  (`file.py (function)`). `1.0` = the grader found nothing missing — guidance, not a guarantee. *(live example: [sufficiency.md](https://github.com/benjaminjones/spec-eval/blob/main/spec-reports/sufficiency.md))*

> [!IMPORTANT]
> **A finding can be wrong.** The AI reader sometimes reports a clash that isn't really there. That is why every
> finding quotes the code line and the spec line it rests on — read the quote before you change anything. If the
> quote doesn't back up the finding, the finding is the mistake. Leave your spec alone.

**Not sure about the findings? Double-check them.** Add `--verify` and a second AI pass re-reads your spec and
throws out findings the spec doesn't actually support:

```bash
spec-eval audit . --verify
```

It only ever *removes* findings, never adds any, so it can make the report shorter but never longer. Thrown-out
findings still show up — crossed out, with the reason and the spec line — so you can disagree with it. It costs
one extra AI call per file that had findings, which is why it's off unless you ask.

*Why a second pass and not a more careful first one? A reader that has talked itself into something stays
talked into it — [longer answer in the FAQ](FAQ.md#not-sure-a-finding-is-real-double-check-it-with---verify).*

The three examples are **spec-eval grading itself**, rolled up in [SPEC-HEALTH.md](https://github.com/benjaminjones/spec-eval/blob/main/spec-reports/SPEC-HEALTH.md).

Every command also appends a line to `runs.jsonl` — timestamp, git commit, scores — so you can track change over
time.

## Higher stakes? Get a second opinion

`drift` and `sufficiency` are **AI judgments** — one model can miss something or be too generous. For a spec that needs extra attention — a critical path, complex design, or compliance code — run the
**same check with two different AI vendors** and compare. Give each run its own
`--out` folder (otherwise the second run overwrites the first report):

```bash
spec-eval audit ./your-project --model anthropic:claude-opus-4-8 --out spec-reports/claude
spec-eval audit ./your-project --model google:gemini-3.5-flash   --out spec-reports/gemini

diff spec-reports/claude/report.md spec-reports/gemini/report.md   # or read them side by side
```

How to read two reports:

- **Both flag it** → almost certainly real. Fix these first.
- **Only one flags it** → a judgment call. Read the quoted evidence and decide.
- **Sufficiency scores differ a little** → normal wobble. Compare the **gaps lists**, not the decimals — the same
  missing behavior named by both graders is the signal.

Each vendor reads its own key from the environment — `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY` —
so put both keys in one `.env` and each run picks up the one it needs. (Want one fewer key? Swap either side for
`--model claude-code`, which uses your Claude Code login instead.)

## Proof it works

- **spec-eval specs itself** — every module in [`spec_eval/`](https://github.com/benjaminjones/spec-eval/tree/main/spec_eval/) has its own spec:
  **coverage 100% · drift 0 · sufficiency ≈0.88** ([receipt](https://github.com/benjaminjones/spec-eval/blob/main/spec-reports/SPEC-HEALTH.md) — the exact, dated score).

## More

- **Works with [spec-driven development](https://en.wikipedia.org/wiki/Spec-driven_development).** SDD's goal is a spec you can *trust*, and **spec-eval** is that trust layer.
  Use it three ways: **grade the specs you already have**, **generate specs** for code that has none, or **check as
  you write** (with the skills). Spec-first, code-first, or in between — it meets you where you are.
- **Grow the spec and the code together.** The best version of "in between": draft a little spec, write a little
  code, check they still agree — repeat. The two can even move in parallel (you shape the spec while your coding
  agent writes the code; the check is where they meet), so the spec is *born accurate* instead of written up
  afterward.
- **Just want to vibe code?** Fine — build first, check later, automatically: a pre-commit gate and a GitHub
  Action can run the checks for you — see [Make it routine](https://github.com/benjaminjones/spec-eval/blob/main/GETTING-STARTED.md#make-it-routine).
- **Higher-stakes spec?** Run it past two vendors and compare — see [Higher stakes? Get a second opinion](#higher-stakes-get-a-second-opinion) above.

## FAQ

Common questions — from *"which command do I run first?"* through costs, layouts, and score accuracy — live in
**[FAQ.md](https://github.com/benjaminjones/spec-eval/blob/main/FAQ.md)**.

## Feedback

Found a bug, a bad score, or a spec that misses the point? [Open an issue](https://github.com/benjaminjones/spec-eval/issues) — a report snippet and the command you ran is plenty.

## Acknowledgements

Built on the Anthropic, OpenAI, and Google SDKs (MIT / Apache-2.0) + PyYAML.

---
*Terms you may be searching for: software specification · documentation drift · living documentation · docs as code · backfill
documentation · spec-driven development (SDD) · agentic development · AI-assisted coding · vibe coding · vibe engineering ·
AI code documentation · LLM-as-judge / trust eval. MIT licensed.*
