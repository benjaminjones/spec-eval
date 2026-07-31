## 1. Purpose

This module gives the system the ability to **bootstrap intent-led specifications automatically**: point it at a repository, and for every code file that deserves a spec but doesn't have one yet, it authors a specification markdown. It is the generation counterpart to the drift and sufficiency checkers — where those tools *audit* existing specs, this one *creates* the missing ones.

Where a spec lands is chosen by a **layout**. The default, `per-file`, writes a spec **beside its code** (`src/x.py` → `src/x.md`: same directory, same stem). Two other layouts consolidate: `per-dir` writes **one spec per directory** (`src/parser/*.py` → `src/parser/parser.md`), and `per-pair` authors the `docs` file of each explicit config pair. An optional **overview** layer adds a navigation index (a repo-level `OVERVIEW.md` and/or a per-directory `README.md`) that links down to whatever specs the layout produced.

Two governing rules a reviewer can check:
1. **Existing work is never silently destroyed.** If a file already exists at a target path it is skipped (no model call) unless the caller passes `overwrite`. Authored specs are ordinary new files in the working tree, reviewed and accepted (or rejected) through version control.
2. **A consolidated (multi-file) spec is synthesised from the per-module *intents*, never from the raw code** — the per-module authoring runs first (map), then a synthesis pass reduces those intents into the folder/overview doc. This keeps a large directory under the character cap that raw concatenation would blow.

> Reconstructed intent (confidence: high) — inferred from the module docstring, the layout branches, and the skill reference.

## 2. Definitions

| Term | Meaning |
|------|---------|
| repo | Root directory of the repository being processed. |
| code_path | Path to a code file, **relative to `repo`**. |
| layout | Spec granularity: `per-file` (default), `per-dir`, or `per-pair`. Read from `config["authoring"]["layout"]`. |
| per-file spec path | The co-located `.md`: `code_path` with its extension replaced by `.md`. |
| per-dir spec path | `<dir>/<name>.md` for the file's directory, where `<name>` is the directory's own name (`dir_spec_name: "<dir>"`, default) or a literal like `README`. Computed by `coverage.dir_spec_path`, shared with the coverage module. |
| overview | Navigation index to also write: `none` (default), `repo`, `per-dir`, or `both`. |
| overview_min_files | A per-dir overview is written only for a directory with **at least** this many spec-worthy files (default 2). |
| template | Optional path to a custom per-module authoring template; replaces the built-in STRUCTURE. |
| authoring rubric | The per-module system prompt: `AUTHORING_STRUCTURE` + `AUTHORING_DISCIPLINE` by default; a custom template replaces the structure but the discipline is always appended. |
| synthesis rubric | `FOLDER_SPEC_RUBRIC` (self-contained folder spec), `REPO_OVERVIEW_RUBRIC` (the repo-root `OVERVIEW.md` — the full project overview, its section set pinned to `templates/OVERVIEW-template.md`), or `DIR_OVERVIEW_RUBRIC` (a per-directory `README.md` — a lean index that defers to linked specs, carrying no Architecture diagram). The Architecture instruction (`ARCH_DIAGRAM_RUBRIC`) and its closing provenance line (`ARCH_CAVEAT`) are single-sourced constants the repo overview and the `diagram` subcommand share verbatim. |
| system-context evidence | The `OBSERVED SYSTEM EVIDENCE` block from the deterministic `syscontext` scan (free, no model call), appended to an overview call's final user message. It is the ONLY source the overview's `## System context` section may draw rows from. |
| module intent | The per-module spec markdown — read from an existing co-located `<stem>.md` if present, else authored (map). Reused across synthesis passes. |
| CODE_CAP | Max code characters fed to a per-module authoring call (`caps.code` in a config, default `audit.CODE_CAP`). |
| REDUCE_CAP | Char budget for the per-module intents concatenated into one synthesis pass (`caps.reduce` in a config overrides the default). |
| overwrite | Flag: regenerate already-present targets instead of skipping them. |
| status | Per-target outcome: `authored` or `skipped`. |
| note | Optional per-target message flagging a partial view or extra work: a multi-pass (recursive) synthesis, code input over the cap, a model reply cut off at the token cap, or a per-dir overview skipped below `overview_min_files`. |
| on_progress | Optional callback invoked with a short status string as each module (map) and target is authored — never on a skip. |

## 3. Behavior

**Target selection.** The generator asks the coverage module for the spec-worthy files (covered + uncovered), then groups them into `{spec_path: [code files]}` per the layout:
- **per-file** — one target per file, at its co-located `.md`.
- **per-dir** — one target per directory, at `<dir>/<name>.md`, covering every spec-worthy file in that directory.
- **per-pair** — one target per config pair, at the pair's first `docs` entry, covering every file its `code` globs match.

**Why coverage drives it:** the same spec-worthiness rules (tests/config/generated/glue excluded) drive **per-file and per-dir** target selection, and — for `per-dir` — coverage and generate share `dir_spec_path`, so a folder spec that generate writes is exactly the one coverage counts as covering that folder. **`per-pair` is the exception:** its targets come directly from each pair's `code` glob matched off disk, not filtered by coverage's spec-worthiness rules.

**Per-module authoring (map).** For a single-file target the code file is read (decode errors ignored), truncated to `CODE_CAP`, embedded in a fenced user message, and sent with the authoring rubric (capped at the `AUTHOR_MAX_TOKENS` output budget). The result has any accidental outer code fence stripped. Returns `(markdown, note)` — the note flags code input over `CODE_CAP` and/or a reply cut off at the token cap, either of which can otherwise silently ship a spec that ends mid-section.

**Readability discipline in the rubric.** The built-in rubric front-loads a one-line capability headline before the Purpose prose, keeps §3 in explanation mode (exhaustive reference lists sink to a §2 term or §4 table), renders 3+ enumerable cases as a list/table rather than a prose chain, makes the inline **Why:** selective (only non-obvious or load-bearing rationale; confidence-tagged reconstructed intent always stays), opens §4 with a visible skip-on-first-read reference cue, enforces sentence economy (split past ~30 words, no nested parentheses, no meta-phrasing), and right-sizes sections to the module (a section with ≤1 real row collapses or drops), and describes each capability by what it IS rather than what it isn't. **Why:** readability comes from altitude, layering, and relocation — never from omitting behavior — so the drift/sufficiency checks grade the same facts in a calmer layout.

**Consolidation (map → reduce).** For a multi-file target (a `per-dir` directory, or a `per-pair` glob matching several files), each module's **intent** is obtained first — reused from an existing co-located spec, or authored on the fly — and those intents (not the raw code) are concatenated and synthesised into one document with `FOLDER_SPEC_RUBRIC`. The concatenation is capped at `REDUCE_CAP`; when the intents exceed it, they are packed into sub-groups, each sub-group is synthesised into an intermediate intent, and the intermediates are reduced in turn (recursively) — **modules are never dropped**. The recursion is bounded to `_MAX_LEVELS` passes. Past that (or once a pass stops shrinking the item count), the remaining intents are force-fit into one final call — each sliced to an equal share of the cap and marked `...[truncated]` — so a deep fan-out truncates content rather than dropping a module. A multi-pass synthesis is reported in the target's `note` ("synthesised in N passes … nothing dropped"), and a reply cut off at the token cap is flagged the same way. A lone intent larger than the whole cap is sliced with a visible marker so packing always terminates.

**Overview layer.** After every spec has been produced (so it can read them), an optional index is authored. The two overview surfaces carry **different section sets on purpose**:
- `repo` / `both` → a repo-root `OVERVIEW.md`, authored with `REPO_OVERVIEW_RUBRIC` — the full project overview whose section set (What it is, Governing principles, Architecture data flow, System context, Module map, Glossary, Health receipt, Reading order) is the **same as `templates/OVERVIEW-template.md`**, pinned by `test_overview_sections_sync.py`.
- `per-dir` / `both` → a `README.md` in each directory with **at least** `overview_min_files` spec-worthy files, authored with `DIR_OVERVIEW_RUBRIC` — a **lean four-section index** (Map, How it fits together, Shared contract, System context) that carries **no Architecture diagram**. A directory below the threshold is recorded as `skipped` with a note naming the shortfall — small directories are never silently omitted.

Both link down to the specs without restating their detail; the repo Module map and the per-dir Map reuse each spec's canonical `**In one line:**` sentence verbatim (a copy-pointer, not a paraphrase that could drift). The System-context section instruction is single-sourced (`_OV_SYSTEM_CONTEXT`) so both rubrics carry the same honesty rules.

**System context (evidence-fed, never invented).** When any overview is authored, the deterministic
`syscontext` scan runs once (free — no model call) and its `OBSERVED SYSTEM EVIDENCE` block is appended to the
overview call's **final** user message (intermediate synthesis passes summarise modules and do not receive it).
The rubric renders it as a `## System context` table — one row per observed system, evidence `file:line`
copied verbatim, unknowable cells written as `unknown from this repo` — closed by a fixed boundary line saying
inbound callers and partner-system behavior are not observable from this repo. The repo overview receives the
whole scan; a per-dir overview receives only the evidence sitting directly in its directory. **When the scan
observes nothing (or nothing in that directory), no block is passed and the section is omitted entirely** — an
overview can never carry an invented system-context row.

**Freshness stamp.** When the repo `OVERVIEW.md` renders a System context section (an evidence block was
present), an invisible `<!-- system-context-fingerprint: <digest> -->` comment (`syscontext.stamp_comment`) is
appended to the file, recording the scan the section came from. A later `spec-eval context --check` reads it
back to flag an overview whose systems have drifted from the code. The per-dir `README.md` overviews are not
stamped.

**On-demand architecture diagrams.** `diagram_block` builds just the repo's Architecture section body — an invocation sequenceDiagram (scanner-verified entry points, provenance-noted) plus a pure data-flow pipeline ending at the observed external systems — for the `diagram` subcommand, reusing the same synthesis engine with a diagram-only rubric. It reads existing specs and derives any **missing** module intent in memory via the shared `_module_intent` (never writing a spec), so a diagram touches nothing. The **diagram itself is always a model call**: `diagram` avoids the per-module authoring calls a fully-specced repo doesn't need, not the synthesis call that draws the picture. Its output keeps the ```mermaid fence (`_synthesize` skips the outer-fence strip when `unfence=False`).

A diagram is drawn in **one pass** (`single_pass`). **Why:** the multi-pass reduce feeds a rubric's own output back through that rubric, which is coherent for prose but not for a picture — intermediate passes would render partial diagrams that never saw the scanner evidence (it reaches only the final call), and the final pass would draw a diagram of diagrams. Over the cap, every module intent is instead sliced to an equal share so all of them still reach the one call, and the shortfall is reported in the returned note alongside a reply cut off at the token cap.

`set_architecture_section` replaces the body of an existing `## Architecture (data flow)` section (replace-only by default — it raises rather than invent a section in an arbitrary doc; an explicit `create` opt-in inserts the section above the doc's stamp footer, but never invents the doc). The body ends at the next `#`/`##` heading or the first fingerprint receipt — **not** at a `###`, which is one of the section's own two subsections; ending there would replace only the first diagram and leave the rest of the stale section in place. `module_set` is the sorted code-file identifier set the architecture fingerprint binds to, and `generate`, `diagram`, and `context --check` all obtain it from that one function.

**Custom template.** When `authoring.template` is set, its text replaces the built-in `AUTHORING_STRUCTURE`; `AUTHORING_DISCIPLINE` (the quality rules the drift/sufficiency checkers rely on) is always appended. **Why:** users own the structure, but the output stays gradeable.

**Write policy** (uniform for specs and overviews):
- If a target file already exists and `overwrite` is false, it is **skipped** (`skipped`) and **no model call is made** — this protects both hand-written specs and hand-edited overviews.
- Otherwise the file is written at `<repo>/<spec path>` (`authored`) — an ordinary new file, reviewed via version control.
- All writes create parent directories as needed and end the file with exactly one trailing newline.

**Result reporting.** Returns a list of records, one per target, each carrying `code`, `spec`, `status`, and optionally `note`.

**Progress.** When an `on_progress` callback is supplied, it is invoked with a short status line as each module (map call) and each target is authored — never on a skip — so a long run reports as it goes instead of running silent. **Why:** authoring is one sequential model call per module and prints its result list only at the end; without progress a multi-module run looks hung.

## 4. Contracts

Semantic shapes:
- **per-file spec path**: string ending in `.md`, same directory and stem as `code_path`.
- **per-dir spec path**: `<dir>/<name>.md`, shared with `coverage.dir_spec_path`.
- **generate result**: list of records `{code, spec, status[, note]}`, one per target.
- **authored markdown**: raw markdown (no outer code fence).

### Invariants (*rules that must always hold*)

| ID | Invariant |
|----|-----------|
| INV-1 | The default layout is `per-file`; its spec path is the code path with its extension replaced by `.md` (same dir, same stem). |
| INV-2 | A `per-dir` spec path equals `coverage.dir_spec_path(code_path, repo_name, dir_spec_name)`, so coverage and generate agree on where the folder spec lives. |
| INV-3 | Code sent to a per-module authoring call is truncated to at most `CODE_CAP` characters. |
| INV-4 | A synthesis (reduce) is fed per-module **intents**, never raw code; when the concatenation exceeds `REDUCE_CAP` the items are recursively synthesised in sub-group passes — modules are **never dropped** (recursion bounded to `_MAX_LEVELS`; past it the remaining intents are force-fit into one final call, content sliced and marked `...[truncated]`), and a multi-pass synthesis is reported in the target's `note`. A reply cut off at the token cap is likewise noted. |
| INV-5 | When `overwrite` is false and a target file already exists, that file is not written and no model call is made (for specs and overviews alike). |
| INV-7 | Every authored file ends with exactly one trailing newline. |
| INV-8 | A custom `template` replaces the built-in structure, but `AUTHORING_DISCIPLINE` is always appended to the rubric. |
| INV-9 | If generated markdown begins with a code fence, the outer fence is removed before writing — except on the diagram path (`unfence=False`), whose output IS a fenced ```mermaid block. |
| INV-10 | `diagram_block` makes exactly ONE synthesis call (`single_pass`): a diagram is never synthesised from other diagrams. Over the cap, every module intent is sliced to an equal share rather than dropped, and the returned note says so. |
| INV-11 | `set_architecture_section` replaces from the `## Architecture (data flow)` heading to the next `#`/`##` heading or the first fingerprint receipt — never to a `###` subheading of its own body, and never past a stamp. Replacing an already-generated section is idempotent: the result carries exactly one copy of the section. |

### Acceptance criteria (*Given / When / Then*)

| ID | Given | When | Then |
|----|-------|------|------|
| AC-1 | code_path `src/x.py` | `spec_path_for` is called | returns `src/x.md`. |
| AC-2 | an uncovered file, default (per-file) layout | `generate_repo` runs | spec written to `<repo>/<dir>/<stem>.md`, status `authored`. |
| AC-3 | a target whose file already exists, `overwrite=False` | `generate_repo` runs | status `skipped`, no write, no model call. |
| AC-5 | a directory of ≥2 modules, `layout: per-dir` | `generate_repo` runs | one folder spec `<dir>/<dir>.md` is authored from the modules' intents; no per-file specs are written. |
| AC-6 | explicit pairs, `layout: per-pair` | `generate_repo` runs | each pair's `docs` file is authored from its `code` glob. |
| AC-7 | `overview: repo` | `generate_repo` runs | a repo-root `OVERVIEW.md` index is authored after the specs. |
| AC-8 | a custom `template` path | rubric is built | the template's text is used and `AUTHORING_DISCIPLINE` is appended. |
| AC-9 | model returns text wrapped in triple-backtick fences | authoring runs | the returned markdown has the outer fence removed. |
| AC-10 | `overview: repo`, code with observable external systems | `generate_repo` runs | the overview call's user message carries the `OBSERVED SYSTEM EVIDENCE` block from the `syscontext` scan. |
| AC-11 | `overview: repo`, code with no observable external systems | `generate_repo` runs | no evidence block is passed — the overview carries no `## System context` section. |
