# Getting started

A quick tutorial: pick your setup, pick your path, run four steps. Everything here works from a **repo root
or any subdirectory** — point the commands at whatever folder you want checked.

**The three numbers you'll see:** **coverage** = % of files that have a spec · **drift** = the count of
spec↔code disagreements (`0` = clean) · **sufficiency** = a `0`–`1` score for how completely each spec captures
its code. Full definitions: [How the scores are made](README.md#how-the-scores-are-made).

- [Pick your setup](#pick-your-setup)
- [Path 1 — No specs yet](#path-1--no-specs-yet)
- [Path 2 — You already have specs or docs](#path-2--you-already-have-specs-or-docs)
- [Choosing a layout](#choosing-a-layout)
- [Make it routine](#make-it-routine)
- [Advanced: a second opinion](#advanced-a-second-opinion)
- [If something looks wrong](#if-something-looks-wrong)

> [!IMPORTANT]
> **Before any tool writes to your project — this one included — put your work under version control (or at
> least a backup copy).** It makes every change reviewable and reversible — the #1 safety habit for
> AI-assisted coding.

## Pick your setup

> [!TIP]
> **Option A — zero setup, nothing to install:** skip the terminal entirely — ask the coding agent you
> already have to read `skills/spec-check/SKILL.md` (in your clone of this repo, or
> [straight from GitHub](https://github.com/benjaminjones/spec-eval/blob/main/skills/spec-check/SKILL.md)) and
> check your specs. This tutorial sticks to the terminal (that's where the report files come from); the chat
> path lives in [README → "Run via prompt chat"](README.md#run-via-prompt-chat-no-setup).

Staying in the terminal? You need **Python 3.9 or newer** — check with `python3 -V`. Then install once:

```bash
pip install spec-eval          # once it's on PyPI; until then, from a clone:  pip install -e .
```

Then pick **B** or **C** — every command below works with either.

**B. Your Claude subscription (no API key).** If you're logged into Claude Code, add `--model claude-code` to any
AI command. That's the whole setup.

```bash
spec-eval audit . --model claude-code
```

**C. An API key.** Export a key and use the default model (or any `provider:model`):

```bash
export ANTHROPIC_API_KEY=sk-ant-...      # or OPENAI_API_KEY / GOOGLE_API_KEY
```

`coverage` and `context` need neither — they're free and never call an AI.

## Path 1 — No specs yet

Four steps, in order:

```bash
spec-eval coverage .                     # 1. FREE — see which files need a spec
spec-eval generate .                     # 2. write a spec beside each of them
git diff                                 # 3. review like code — edit or drop what you don't like
spec-eval sufficiency .                  # 4. score how complete the new specs are
```

Why this order:

1. **`coverage` first, always** — it's free, and it shows exactly what step 2 will write. No surprises.
2. **`generate`** writes ordinary new files beside your code. Want a top-level `OVERVIEW.md` too? Add `--overview repo`.
3. **Your version control is the review.** Edit the specs that miss the point; `git checkout -- <file>` rejects
   one entirely; commit the keepers like code.
4. **`sufficiency`** tells you what the specs still miss, worst-first — fix the `major` gaps and re-run.

(No need to `audit` yet — the specs were just written from the code, so audit rarely finds anything this early;
the `git diff` review in step 3 is the check that matters here. Audit earns its keep once the code starts
changing: see [Make it routine](#make-it-routine).)

## Path 2 — You already have specs or docs

```bash
spec-eval coverage .                     # 1. FREE — what's governed, what's not
spec-eval audit .                        # 2. the main event: where do docs contradict the code?
spec-eval generate .                     # 3. fill ONLY the missing specs (existing files are never touched)
spec-eval sufficiency .                  # 4. what do the specs still leave out?
```

Fix `audit`'s findings first — a spec that *contradicts* the code is worse than no spec. Each finding says which
side to change (sometimes the spec is right and the code is the bug).

**Touched just one file?** The AI commands also take a single file — handy before a commit:

```bash
spec-eval audit src/parser.py            # grade only the file you changed (its parser.md is the spec)
```

**Docs that don't sit beside the code** (a `docs/` folder, a design doc): adopt them with a small config —

```yaml
# pairs.yml
pairs:
  - label: parser
    code: [src/parser/**/*.py]
    docs: [docs/parser-design.md]
```

```bash
spec-eval audit . --config pairs.yml
```

> [!TIP]
> Three tips for docs-folder projects: use **globs** for `code:` so renames don't break the link; a missing doc can
> be **written for you** at the path the config names (`spec-eval generate . --config pairs.yml --layout per-pair`);
> and on big projects, **mirror the code tree** (`src/api/parser.py` ↔ `docs/src/api/parser.md`) so two files named
> `parser.py` never collide.

## Choosing a layout

Four shapes — the first three are one flag; the fourth adds a config:

| You want | Command |
|---|---|
| One spec per code file *(default)* | `spec-eval generate .` |
| One spec per folder | `spec-eval generate . --layout per-dir` |
| Per-file specs **plus** an overview `README.md` per folder | `spec-eval generate . --overview per-dir` |
| Specs in a `docs/` folder — you name each path in a config | `spec-eval generate . --config pairs.yml --layout per-pair` |

Add `--overview repo` to any of them for a single top-level `OVERVIEW.md`. The checks (`coverage`,
`audit`, `sufficiency`) understand whichever layout you pick — put it in a config so they all agree:

```yaml
authoring:
  layout: per-dir
```

## Make it routine

Specs only stay trustworthy if the checks run when the code changes. Three habits, smallest first:

**Before merging a PR** — run `audit` on what changed: it flags where the diff *contradicts* the spec. Added
new behavior? Run `sufficiency` too — audit stays quiet about things the spec merely omits (*silence is not
drift*); sufficiency is the check that catches them.

**Pre-commit hook** — the free coverage gate keeps new code from landing spec-less:

```bash
echo 'spec-eval coverage . --min 90' >> .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

**CI (GitHub Actions)** — coverage gate free on every PR; drift check with a key stored as a secret:

```yaml
# .github/workflows/spec-eval.yml
name: spec-eval
on: [pull_request]
jobs:
  specs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install spec-eval
      - run: spec-eval coverage . --min 90        # free gate
      - run: spec-eval audit .                    # drift check
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

## Advanced: a second opinion

For a spec you really depend on, run the same check on **two vendors** and trust what they agree on. Give each
run its own `--out` folder so the reports don't overwrite each other:

```bash
spec-eval audit . --model claude-code             --out spec-reports/claude
spec-eval audit . --model google:gemini-3.5-flash --out spec-reports/gemini
diff spec-reports/claude/report.md spec-reports/gemini/report.md
```

Both flag it → fix it. Only one flags it → judgment call. (More in the README: "Higher stakes? Get a second
opinion".)

## If something looks wrong

- **`0/0 audited pair(s)`** — `audit`/`sufficiency` found nothing to check: there are no `.md` files beside your
  code and no `--config` pairs. Run `generate` first, or point a pairs config at your existing docs (Path 2).
- **"Where did the reports go?"** — every command prints the absolute path it wrote to (default: a
  `spec-reports/` folder under your *current* directory, not the project's).
- **`claude-code` errors** — the bridge needs the Claude Code CLI installed and logged in (`claude` on your PATH).
- **Costs** — `coverage` and `context` are always free; the AI commands print exact token/call counts. Estimating spend:
  [FAQ → "How much does a run cost?"](FAQ.md#how-much-does-a-run-cost).
- **"Is this finding real?"** — add `--verify` and a second AI pass throws out findings your spec doesn't
  actually support. It only removes findings, never adds any. Costs one extra call per file that had findings:
  [FAQ → "Not sure a finding is real?"](FAQ.md#not-sure-a-finding-is-real-double-check-it-with---verify).
