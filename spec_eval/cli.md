## 1. Purpose

This module is the command-line entry point for **spec-eval** — a tool that treats specifications as first-class artifacts sitting beside code, and gives a team five distinct capabilities from one command surface:

- **coverage** — find code files that have *no governing spec* (free, needs no API key).
- **context** — inventory the *external systems the code observably talks to* (free, needs no API key).
- **generate** — *author* an intent-led spec beside each spec-worthy file that lacks one.
- **audit** — detect *drift*: places where the code contradicts its spec.
- **sufficiency** — an indicator of how completely a spec captures the code's behavior (what's missing).

Its job is to parse arguments, load API keys from the environment, dispatch to the right analysis engine, write both a machine-readable JSON artifact and a human-readable Markdown report into an output directory, print a one-glance summary, and append a run record to a log.

The one governing constraint a reviewer can check: **`coverage` and `context` never need a model; the other three always do** — either an API-key provider (`anthropic:` / `openai:` / `google:`, key from the environment) or the key-free `claude-code` bridge (the Claude Code CLI's own login). If you run `coverage` or `context` with no key configured, they must still work; if you run `audit`, `sufficiency`, or `generate` without a key **and** without the `claude-code` model, they cannot.

## 2. Definitions

| Term | Meaning (bounds / units) |
|---|---|
| repo | Filesystem path to the project being analyzed — a repo root, a subdirectory, or (for `audit`/`sufficiency`/`generate`) a single code file (positional, required; displayed as `PROJECT_DIR`). |
| config | Optional YAML/JSON file declaring code↔spec pairs and/or `code_ext`/`exclude` rules. If omitted, co-located `<file>.md` specs are auto-paired. |
| model | `provider:model` string, e.g. `anthropic:claude-opus-4-8`, `openai:gpt-5.5`, `google:gemini-3.5-flash`; or `claude-code` (no API key — routes through the Claude Code CLI). Default `anthropic:claude-opus-4-8`. |
| out | Output directory for all artifacts (default `spec-reports`). Created if absent. |
| env | Path to a `.env` file holding API keys; optional. |
| fingerprint | Whether Markdown reports include a unicode-bar fingerprint. Default on. (audit/sufficiency only.) |
| pair | A (code file, governing spec) association, produced by config or auto-pairing. |
| drift finding | A high/medium-severity contradiction between a code file and its spec. |
| sufficiency | Per-pair score in `[0.0, 1.0]`; `1.0` = the grader found no gaps (an indicator, not a guarantee). |
| coverage pct | Percentage of spec-worthy files that have a governing spec. |
| layout | (generate only) spec granularity: `per-file` (default), `per-dir`, or `per-pair`. |
| overview | (generate only) navigation index to also write: `none` (default), `repo`, `per-dir`, or `both`. |
| template | (generate only) path to a custom authoring template replacing the built-in structure (the discipline is still applied). |

## 3. Behavior

**Command surface.** A required subcommand selects the capability: `audit`, `sufficiency`, `generate`, `coverage`, `context`. `audit` and `sufficiency` share the same argument set (`repo`, `--config/-c`, `--model/-m`, `--out/-o`, `--env`, `--fingerprint/--no-fingerprint`). `generate` adds `--overwrite`, `--layout`, `--overview`, and `--template`. `coverage` drops model/env/fingerprint and adds `--min`; `context` takes only `repo`, `--config`, and `--out`.

**Single-file scope.** For `audit`, `sufficiency`, and `generate`, `PROJECT_DIR` may be a single code file: the command narrows to that file's directory with one synthesized pair — the file's co-located `<stem>.md`, or the folder spec when the loaded config sets a `per-dir` layout — so no pairs config is needed to scope a check to the file just changed. `generate` then authors exactly that file's spec (overview layer forced off). `coverage` and `context` remain directory-only: given a file they exit with a message pointing at the directory. **Why:** checking the one file you just touched is the everyday case, and the previous behavior (a silently empty run) was a footgun.

**Key loading (all key-requiring commands).** Before analysis, keys are loaded in a fixed precedence sequence: (1) the explicit `--env` file if given; (2) a `.env` sitting next to the `--config` file, if a config was given; (3) a `.env` in the current working directory. **Why:** lets a team keep keys beside their pairs config or in the repo root without passing `--env` every time. `coverage` and `context` skip key loading entirely — **Why:** they never call a provider.

**audit — drift.** Loads config (or empty), runs `audit.audit_repo`, writes `findings.json` and `report.md`. Prints the count of high/medium drift findings across *audited* pairs (pairs not marked `skipped`), a ⚠ warning when any pair was graded on a partial view (input cap or reply token cap; the per-pair detail is in the report), the written paths, and the model call and token counts (no dollar figure). Logs `high_med_drift`, `pairs_audited`, `pairs_truncated`, and a per-module drift load.

**sufficiency.** Runs `sufficiency_repo`, writes `sufficiency.json` and `sufficiency.md`. Prints the average sufficiency across *scored* pairs (those with a non-null `sufficiency`), a ⚠ warning when any pair was scored on a partial view (input cap or reply token cap), paths, and the model call and token counts (no dollar figure). Logs `avg_sufficiency` (rounded to 2 dp), `pairs_scored`, `pairs_truncated`, and a per-module score map.

**generate — authoring.** Runs `authoring.generate_repo` with `overwrite` and the resolved `authoring` block (layout / overview / template — CLI flags override the config). Writes `generated.json` and prints each result's status, spec path, and any `note` (e.g. a multi-pass synthesis or a token-cap flag). While running it prints an opening line and one progress line per module/target to **stderr** (so a long, sequential run isn't silent); the final result list goes to stdout.
- Specs are written *beside* the code as ordinary new files; prints count authored and count skipped, and points the user at version control (`git diff` / `git checkout --`) to review or reject. **Why:** authored specs are plain working-tree files, so the VCS is the preview.
- Logs `authored`, `skipped`, and `flagged` (targets whose record carries a `note` — e.g. a partial view).

**context — system inventory, free.** No key loading, no model calls. Runs `syscontext.scan` (a deterministic external-system scan), writes `system-context.json` (the diffable fingerprint, carrying scanner provenance) and `system-context.md` (the table + boundary note). Prints the observed-system count, one line per system with its first evidence site, a ⚠ `Not scanned:` line when the repo contains source files in languages outside the scan's support, and the written paths. Logs `systems_observed`, `files_scanned`, and `files_unscanned`. Given a file path it exits with a message pointing at the directory, like `coverage`.
- **`--check` gate:** diffs a fresh scan against the stored `system-context.json` baseline in `--out` (`syscontext.diff`), prints the named-delta receipt (`syscontext.diff_receipt`), logs a `context-check` run with the `outcome`, and **exits 1 only when a system was added or removed** (`drift`); a scanner change is a `rebaseline` and a no-change run is `clean`, both exit 0. It never overwrites the baseline (a plain `context` run does that), and with no baseline present it prints a hint and exits 0. **Why:** lets CI catch when the code starts (or stops) talking to an external system without failing on scanner upgrades.

**coverage — free.** No key loading, no model calls. Runs `coverage.coverage`, writes `coverage.json` and `coverage.md`. Prints the coverage percentage and covered/spec-worthy counts; if any files are uncovered, lists each on its own line (capped, with an `… and N more` overflow note pointing at `coverage.md`); if any possible orphaned specs are found, lists them each on its own line as well (also capped, advisory — never affects the `--min` gate). Logs `coverage_pct`, `covered`, `spec_worthy`, `orphans`. The written report paths print as absolute paths.
- **`--min` gate:** if `--min` is set and coverage percent is below it, prints a `FAIL` line and exits with status **1**. **Why:** lets CI enforce a coverage floor.

**Artifacts & logging.** Every command creates `--out` if needed, writes both a JSON and (except generate, which writes only JSON) a Markdown file, and calls `runlog.append_run` with the command, repo, model (null for `coverage` and `context`), and command-specific metrics.

> Reconstructed intent (confidence: high) — the run-log call at the end of each branch is a consistent audit trail of every invocation, inferred from the uniform `append_run` usage.

## 4. Contracts

**Dispatch result shapes (semantic):**
- `results` (audit) — list of pair findings; each may carry `skipped` and a `label`.
- `results` (sufficiency) — list of pairs; each carries `label` and `sufficiency ∈ [0.0,1.0] | null`.
- `cov` (coverage) — `{ pct, covered[], uncovered[], spec_worthy, orphans[] }`.
- `ctx` (context) — `{ schema, scanner{version, tables_digest}, repo, files_scanned, unscanned{ext:count}, entries[] }`.
- `res` (generate) — list of `{ status, spec, note? }`; status ∈ {`authored`, `skipped`}.

### Invariants (*rules that must always hold*)

| ID | Invariant |
|---|---|
| INV-1 | A subcommand is required; invoking with none causes argparse to error and exit non-zero. |
| INV-2 | The output directory is created before any artifact is written. |
| INV-3 | For `coverage` with `--min` set, if `pct < min` the process exits with status 1. |
| INV-4 | `coverage` given a file path exits non-zero with guidance; it never emits a 0/0 report for a file. |
| INV-5 | `context` never loads a key and never calls a provider; given a file path it exits non-zero with guidance. |

### Acceptance criteria (*Given / When / Then*)

| ID | Given | When | Then |
|---|---|---|---|
| AC-1 | A repo with a config | `spec-eval coverage <repo> -c pairs.yml` runs | No key is loaded; `coverage.md` + `coverage.json` are written under `spec-reports/`; a `%` summary prints. |
| AC-2 | Coverage computes 40% and `--min 80` | `spec-eval coverage <repo> --min 80` runs | A `FAIL` line prints and the process exits with status 1. |
| AC-3 | A repo with observable external systems | `spec-eval context <repo>` runs | No key is loaded; `system-context.md` + `system-context.json` are written under `spec-reports/`; the observed systems print one per line. |
