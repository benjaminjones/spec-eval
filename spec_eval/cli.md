## 1. Purpose

**In one line:** the command-line surface for the six checks, routing each to its engine and reporting the result.

This module is the command-line entry point for **spec-eval** — a tool that treats specifications as first-class artifacts sitting beside code, and gives a team six distinct capabilities from one command surface:

- **coverage** — find code files that have *no governing spec* (free, needs no API key).
- **context** — inventory the *external systems the code observably talks to* (free, needs no API key).
- **generate** — *author* an intent-led spec beside each spec-worthy file that lacks one.
- **audit** — detect *drift*: places where the code contradicts its spec.
- **sufficiency** — an indicator of how completely a spec captures the code's behavior (what's missing).
- **diagram** — print (or write) the repo's Mermaid *architecture diagrams* — an invocation sequence (how it's run) plus the data-flow pipeline (how data moves).

Its job is to parse arguments, load API keys from the environment, dispatch to the right analysis engine, write both a machine-readable JSON artifact and a human-readable Markdown report into an output directory, print a one-glance summary, and append a run record to a log.

**`coverage` and `context` never need a model; `audit`, `sufficiency`, `generate`, and `diagram` always do** — either an API-key provider (`anthropic:` / `openai:` / `google:`, key from the environment) or the key-free `claude-code` bridge (the Claude Code CLI's own login). If you run `coverage` or `context` with no key configured, they must still work; if you run any of the other four without a key **and** without the `claude-code` model, they cannot. `diagram` is the cheapest of the four: the picture itself is always one synthesis call, and a repo whose modules all have co-located specs needs no further calls to derive their intents.

## 2. Definitions

| Term | Meaning (bounds / units) |
|---|---|
| repo | Filesystem path to the project being analyzed — a repo root, a subdirectory, or (for `audit`/`sufficiency`/`generate`/`diagram`) a single code file (positional, required; displayed as `PROJECT_DIR`). |
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

**Command surface.** A required subcommand selects the capability: `audit`, `sufficiency`, `generate`, `coverage`, `context`, `diagram`. `audit` and `sufficiency` share a base argument set (`repo`, `--config/-c`, `--model/-m`, `--out/-o`, `--env`, `--fingerprint/--no-fingerprint`); `audit` adds `--verify`. `generate` adds `--overwrite`, `--layout`, `--overview`, and `--template`. `coverage` drops model/env/fingerprint and adds `--min`; `context` takes `repo`, `--config`, `--out`, and `--check`. `diagram` takes `repo`, `--config`, `--model`, `--env`, `--write`, and `--add-section` (no `--out`/`--fingerprint`).

**Single-file scope.** For `audit`, `sufficiency`, and `generate`, `PROJECT_DIR` may be a single code file: the command narrows to that file's directory with one synthesized pair — the file's co-located `<stem>.md`, or the folder spec when the loaded config sets a `per-dir` layout — so no pairs config is needed to scope a check to the file just changed. `generate` then authors exactly that file's spec (overview layer forced off). `diagram` given a file diagrams that file's **directory** (a single file has no meaningful data flow). `coverage` and `context` remain directory-only: given a file they exit with a message pointing at the directory. **Why:** checking the one file you just touched is the everyday case, and the previous behavior (a silently empty run) was a footgun.

**Key loading (all key-requiring commands).** Before analysis, keys are loaded in a fixed precedence sequence: (1) the explicit `--env` file if given; (2) a `.env` sitting next to the `--config` file, if a config was given; (3) a `.env` in the current working directory. **Why:** lets a team keep keys beside their pairs config or in the repo root without passing `--env` every time. `coverage` and `context` skip key loading entirely — **Why:** they never call a provider.

**audit — drift.** Loads config (or empty), runs `audit.audit_repo`, writes `findings.json` and `report.md`. Prints the count of high/medium drift findings across *audited* pairs (pairs not marked `skipped`), a ⚠ warning when any pair was graded on a partial view (input cap or reply token cap; the per-pair detail is in the report), the written paths, and the model call and token counts (no dollar figure). Logs `high_med_drift`, `pairs_audited`, `pairs_truncated`, and a per-module drift load.

- **`--verify` second pass (off by default):** the audit's findings are written **before** the pass runs, so a failure in it — a transient provider error, a malformed reply — leaves the unverified findings on disk and prints a warning instead of discarding a completed audit. On success the files are rewritten with the verdicts attached. Runs `verify.verify_repo` after the audit, attaching a verdict to every finding on every pair that produced one — one extra model call per such pair. A withdrawn finding stays in `findings.json` and `report.md`, struck through with its ground and the doc line, and is excluded from the count; a separate line reports how many were withdrawn.
  > **Why off by default:** the pass can only remove findings, never add one, so it can only lower a number a reader acts on.

**sufficiency.** Runs `sufficiency_repo`, writes `sufficiency.json` and `sufficiency.md`. Prints the average sufficiency across *scored* pairs (those with a non-null `sufficiency`), a ⚠ warning when any pair was scored on a partial view (input cap or reply token cap), paths, and the model call and token counts (no dollar figure). Logs `avg_sufficiency` (rounded to 2 dp), `pairs_scored`, `pairs_truncated`, and a per-module score map.

**generate — authoring.** Runs `authoring.generate_repo` with `overwrite` and the resolved `authoring` block (layout / overview / template — CLI flags override the config). Writes `generated.json` and prints each result's status (`authored` / `skipped` / `failed` / `stray`), spec path, and any `note` (e.g. a multi-pass synthesis, a token-cap flag, downgraded provenance labels, repaired or broken links, or the reason a target failed). A `failed` target wrote nothing, so the summary line counts it separately from `skipped` and flags it with ⚠. A `stray` is markdown that appeared on disk without being a declared target — the model wrote it directly — and is reported on its own ⚠ line pointing at `git status`; nothing is deleted. Every status is counted by name rather than by subtraction, so a new status can never inflate `skipped`. While running it prints an opening line and one progress line per module/target to **stderr** (so a long, sequential run isn't silent); the final result list goes to stdout.
- Specs are written *beside* the code as ordinary new files; prints count authored and count skipped, and points the user at version control (`git diff` / `git checkout --`) to review or reject. **Why:** authored specs are plain working-tree files, so the VCS is the preview.
- Logs `authored`, `skipped`, and `flagged` (targets whose record carries a `note` — e.g. a partial view).

**context — system inventory, free.** No key loading, no model calls. Runs `syscontext.scan` (a deterministic external-system scan), writes `system-context.json` (the diffable fingerprint, carrying scanner provenance) and `system-context.md` (the table + boundary note). Prints the observed-system count, one line per system with its first evidence site, a ⚠ `Not scanned:` line when the repo contains source files in languages outside the scan's support, and the written paths. Logs `systems_observed`, `files_scanned`, and `files_unscanned`. Given a file path it exits with a message pointing at the directory, like `coverage`.
- **`--check` gate:** diffs a fresh scan against the stored `system-context.json` baseline in `--out` (`syscontext.diff`), prints the named-delta receipt (`syscontext.diff_receipt`), and **exits 1 only when a system was added or removed** (`drift`); a scanner change is a `rebaseline` and a no-change run is `clean`, both exit 0. It also reads `<repo>/OVERVIEW.md` and prints a ⚠ *overview stale* warning when the overview's system-context fingerprint stamp no longer matches the fresh scan (`syscontext.overview_stale`), and a separate ⚠ *architecture diagram stale* warning when its architecture fingerprint no longer matches (`syscontext.diagram_stale`, computed from a fresh entry-point scan and the module set) — neither warning changes the exit code (regenerating a doc is a separate action from investigating code drift). It never overwrites the baseline (a plain `context` run does that); a missing baseline prints a hint and exits 0, and a corrupt/empty/non-dict baseline degrades to a re-store hint and exits 0 rather than crashing. Logs a `context-check` run with the `outcome`, the `added`/`removed` counts, `overview_stale`, and `diagram_stale`. **Why:** lets CI catch when the code starts (or stops) talking to an external system without failing on scanner upgrades.

**diagram — the architecture pictures.** Loads keys (the picture is one synthesis call; extra calls derive only the module intents with no co-located spec), then builds the repo's Architecture section body via `authoring.diagram_block` — two Mermaid diagrams: an invocation sequenceDiagram (the scanner-verified entry points, provenance-noted, plus any intents-documented conventional invocations) and a pure data-flow `flowchart` pipeline terminating in the user-facing result the sequence diagram shows, with any observed external systems at its boundary. **Default:** prints the fenced ```mermaid blocks to **stdout** and writes nothing — no `--out`, no report, no run log; progress and the model-call/token summary go to **stderr** so stdout stays a clean, pasteable/redirectable block. **`--write`:** REPLACE-ONLY — replaces the body of the **existing** `## Architecture (data flow)` section of `OVERVIEW.md` (or `README.md`) at the scope and re-stamps **only** the architecture fingerprint (`syscontext.restamp_architecture` — a diagram update never re-stamps, and so never re-blesses, a stale System context table). If the target doc has no Architecture section, `--write` exits pointing at `--add-section` (or `generate --overview`) rather than touch it. **`--add-section`** is the explicit opt-in for the first-time add: when the target doc has no Architecture section it **inserts** one (deterministically, above the doc's stamp footer) instead of erroring — so a lean per-directory `README.md` can gain a diagram on request. Either flag writes, and either requires the target doc to already exist; **neither ever creates a doc** (that stays `generate`'s job). **Why:** the everyday need is *see the diagram*; replace-only keeps `--write` from silently altering a hand-written README (e.g. a project's marketing README with no Architecture section), while `--add-section` makes adding one a deliberate act, not a surprise.
- **A doc is only ever overwritten with a diagram.** If the synthesis reply carries no ```mermaid block, the write is refused and the doc is left byte-identical — an empty or derailed reply must not blank a good diagram. A partial view (module intents sliced to fit the single pass, or a reply cut off at the token cap) prints as a ⚠ note on stderr rather than being written silently.

**coverage — free.** No key loading, no model calls. Runs `coverage.coverage`, writes `coverage.json` and `coverage.md`. Prints the coverage percentage and covered/spec-worthy counts; if any files are uncovered, lists each on its own line (capped, with an `… and N more` overflow note pointing at `coverage.md`); if any possible orphaned specs are found, lists them each on its own line as well (also capped, advisory — never affects the `--min` gate). Prints one ⚠ `unmodeled:` line per directory tree of markdown the same-stem pairing model cannot reach, so the percentage is read as scoped to same-stem pairs rather than to the whole project. Logs `coverage_pct`, `covered`, `spec_worthy`, `orphans`, and `unmodeled_md`. The written report paths print as absolute paths.
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
| INV-6 | `diagram` with neither `--write` nor `--add-section` writes nothing: it prints the mermaid block to stdout only (no `--out`, no report, no run log); progress and the usage summary go to stderr. |
| INV-7 | `diagram --write` is replace-only — it updates ONLY the body of an existing `## Architecture (data flow)` section (with `--add-section`, it inserts the section if absent), re-stamps ONLY the architecture fingerprint, and leaves any system-context stamp byte-identical. A missing target doc is an error; neither flag ever creates a doc. |
| INV-8 | No write happens unless the synthesised block contains a ```mermaid fence; otherwise the command exits non-zero and the target doc is byte-identical. |
| INV-9 | `context --check` runs the entry-point scan and the module walk only when the target doc carries an architecture stamp — a repo with no diagram pays nothing for the third edge. |

### Acceptance criteria (*Given / When / Then*)

| ID | Given | When | Then |
|---|---|---|---|
| AC-1 | A repo with a config | `spec-eval coverage <repo> -c pairs.yml` runs | No key is loaded; `coverage.md` + `coverage.json` are written under `spec-reports/`; a `%` summary prints. |
| AC-2 | Coverage computes 40% and `--min 80` | `spec-eval coverage <repo> --min 80` runs | A `FAIL` line prints and the process exits with status 1. |
| AC-3 | A repo with observable external systems | `spec-eval context <repo>` runs | No key is loaded; `system-context.md` + `system-context.json` are written under `spec-reports/`; the observed systems print one per line. |
| AC-4 | Any repo | `spec-eval diagram <repo>` runs | A fenced ```mermaid block prints to stdout; no file under the repo is created or changed. |
| AC-5 | An `OVERVIEW.md`/`README.md` with no `## Architecture (data flow)` section (or none at the scope) | `spec-eval diagram <repo> --write` runs | The process exits non-zero pointing at `--add-section`/`generate`; the doc is left byte-identical. |
| AC-6 | An existing `README.md` with no `## Architecture (data flow)` section | `spec-eval diagram <repo> --write --add-section` runs | The section is added to the README and the architecture fingerprint is stamped; a doc that does not exist is still an error. |
| AC-7 | An `OVERVIEW.md` already carrying a generated Architecture section (two `###` subsections) | `spec-eval diagram <repo> --write` runs a second time | The doc carries exactly one `### How it is invoked` and one `### Data flow`; the old bodies are replaced, not duplicated. |
| AC-8 | A model reply with no ```mermaid block | `spec-eval diagram <repo> --write` runs | The process exits non-zero and the target doc is byte-identical. |
