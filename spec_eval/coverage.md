## 1. Purpose

**In one line:** coverage = the fraction of spec-worthy code files that have a governing spec, reported as a percent — pure filesystem set-arithmetic, no API key and no model call.

This module answers one question about a repository: **which code files have no governing spec?** It is the spec analogue of test coverage — instead of "which lines are exercised by a test," it reports "which spec-worthy code files are described by a specification." It runs purely on the filesystem: no API key, no model call, so it is free and fast enough to run in CI on every commit.

**A code file counts as covered if — and only if — a configured pair points at it, OR a markdown file sits beside it with the same name** (`model.md` next to `model.py`), **OR — when the authoring layout is `per-dir` — a folder spec (`<dir>/<dir>.md`) exists for its directory.** A file that is neither covered nor in one of the "impractical to spec" exclusion classes is reported as **uncovered**. Reported coverage percent is the fraction of spec-worthy files that are covered.

**Why the exclusions matter:** some file classes (tests, config, generated output, glue, docs) are impractical to spec — writing a spec for them would just create a second copy of the same truth with nothing independent to cross-check against, which is the exact drift this tool exists to prevent. This "missing spec" finding is deliberately kept SEPARATE from a "drift" (accuracy) finding.

## 2. Definitions

| Term | Meaning |
|------|---------|
| Code universe (`code_ext`) | Extensions treated as code. Default: `.py .ts .tsx .js .jsx .mjs .cjs .go .rs .java .rb .kt .kts .swift .php .cs`; overridable per-repo via config `code_ext`. |
| COVERED | A code file matched by any config pair's `code` glob, OR having a sibling `<stem>.md`, OR (under `authoring.layout: per-dir`) whose directory has a folder spec `<dir>/<dir>.md`. |
| CANDIDATE | Every code file under the repo (by extension), minus pruned directories. |
| Exclusion tier | The class making a file impractical to spec: `user`, `test`, `glue`, `tooling`, `generated`, `config`, `skill/doc`. |
| SPEC-WORTHY | CANDIDATE minus all excluded files. The denominator for coverage. |
| UNCOVERED | Spec-worthy files that are not covered. The core finding. |
| ORPHAN (possible) | A spec-shaped `.md` in a directory that has code, whose same-stem code file no longer exists. Advisory heuristic — never moves the percentage. |
| Pair | `{label, code[], docs[]}` — links code globs to spec doc(s). |
| Pruned dir | A directory never walked into (vendored/build/cache/generated). |
| `pct` | `100 × covered_worthy / max(spec_worthy, 1)`, rounded to 1 decimal. |

## 3. Behavior

### Building the candidate set
Walk the repo, skipping any directory whose name is in the prune list (`.git`, `.venv`, `build`, `dist`, `target`, `node_modules`, `__pycache__`, caches, `mutants`, IDE dirs, `site-packages`, and vendored third-party dirs: `vendor`, `vendored`, `third_party`, `bower_components`, …). Any file ending in a configured code extension becomes a candidate.
**Why:** vendored and generated trees are enormous and never author-owned; descending into them wastes time and pollutes the report.

### Determining coverage
A candidate is covered by any of these routes:
- **Explicit:** it matches (via recursive glob) any `code` pattern of any pair declared in `config["pairs"]`.
- **Co-located:** a file `<stem>.md` exists beside `<stem>.<ext>`.
- **Per-directory** (only when `config["authoring"]["layout"] == "per-dir"`): a folder spec at `<dir>/<dir>.md` (or the configured `dir_spec_name`) exists for the file's directory — the same path `generate` writes, computed by the shared `dir_spec_path` helper so coverage and generate agree.

**Why co-location:** the tool's convention is "specs live beside the code," so `audit`/`sufficiency` need no explicit `pairs.yml` — a `model.md` next to `model.py` is auto-recognised. **Why per-directory parity:** after `generate --layout per-dir` writes one spec per folder, coverage must count those folders' files as covered without a hand-written pairs config.

### Exclusion classification (`classify_exclude`)
Each candidate is tested in order; the first matching tier wins, else it is spec-worthy:
1. **user** — matches any config `exclude:` glob (against full relative path or basename).
2. **test** — `test_*`, `*_test`, `*.test.*`, `*.spec.*`, or living in a `tests/__tests__/test/spec/__mocks__` dir.
3. **glue** — trivial entrypoints: `__init__.py`, `__main__.py`, `conftest.py`, `setup.py`, `index.{ts,js,tsx,jsx}`, `main.go`, `mod.rs`, `lib.rs`.
4. **tooling** — inside `scripts/tools/tooling`.
5. **generated** — inside `__pycache__/build/dist/.venv/node_modules/mutants/formal`, or a minified bundle (`*.min.js` / `*.min.mjs`).
6. **config** — extension `.yml .yaml .toml .cfg .ini .txt .lock`.
7. **skill/doc** — `.md` file, or basename `SKILL.md`.

**Why language-agnostic conventions:** the tool targets polyglot repos; test/glue/config naming spans Python, TS/JS, Go, Rust, etc.

### Result assembly (`coverage`)
Returns `pct`, `spec_worthy` (count), `covered` (sorted list, intersected with spec-worthy), `uncovered` (sorted), and `excluded` grouped by tier (each list sorted).
**Why intersect covered with spec-worthy:** an excluded file that happens to have a sibling `.md` should not inflate the numerator.

### Possible-orphan detection
A `.md` file is flagged as a **possible orphaned spec** when all of these hold: it sits in a directory that contains at least one candidate code file; its stem is not a conventional doc name (README, OVERVIEW, CHANGELOG, LICENSE, SPEC-HEALTH, …); it is not the directory's folder-spec name; it is not matched by any config pair's `docs` glob; it is not matched by a user `exclude:` glob; and no code file with the same stem exists beside it.
**Why:** with agentic development, code moves fast — a spec left behind by a moved/deleted module quietly falls out of date. The check is free and advisory: docs-only directories are never scanned (their `.md` files are docs, not specs), and the result never changes `pct`, `covered`, or `uncovered` — a heuristic must not fail a CI gate.

### Pair inference (`infer_pairs`)
Independently walks the repo and, for each spec-worthy code file that has a sibling `<stem>.md`, emits a pair `{label: <stem>, code: [rel], docs: [md]}`. Result sorted by label.
**Why:** lets downstream tools operate on the co-location convention with no hand-written pair config.

### Report formatting (`format_report`)
Emits markdown: a headline percent line (`covered/spec_worthy`), an "⚠ Uncovered" section listing each uncovered file (only if any exist), a "Possible orphaned specs" section (only if any exist, marked as a heuristic), and an "Excluded … by class" section listing each tier with its count and up to 8 example files (`…` when truncated).

## 4. Contracts

Result shape of `coverage(repo, config)`:
```
{ pct: float,                     # 0.0 .. 100.0, one decimal
  spec_worthy: int,              # >= 0
  covered: [rel, ...],           # sorted, subset of spec-worthy
  uncovered: [rel, ...],         # sorted, spec_worthy minus covered
  orphans: [rel, ...],           # sorted; advisory — spec-shaped .md files whose code is gone
  excluded: { tier: [rel, ...] } # each list sorted; tiers among the 7 classes
}
```

### Invariants (*rules that must always hold*)

| ID | Invariant |
|----|-----------|
| INV-1 | `pct = round(100 × covered_worthy / max(spec_worthy, 1), 1)` — division never by zero (denominator floored at 1). |
| INV-2 | Pruned directories are never walked; no candidate path descends through a `PRUNE_DIRS` name. |
| INV-3 | Reported `covered` is always the intersection of covered files with spec-worthy files. |
| INV-4 | Every excluded file is assigned exactly one tier (first matching rule in `classify_exclude`). |
| INV-5 | `orphans` never affects `pct`, `covered`, or `uncovered` — it is advisory output only. |
| INV-6 | A conventional doc name (e.g. `README.md`), a folder spec, a pair-declared doc, a user-excluded path, and any `.md` in a docs-only directory are never reported as orphans. |

> Reconstructed intent (confidence: high) — INV-2/INV-3/INV-4 are inferred from the walk-filter, `covered & spec_worthy` intersection, and the ordered return-on-first-match in `classify_exclude`.

### Acceptance criteria (*Given / When / Then*)

| ID | Given | When | Then |
|----|-------|------|------|
| AC-1 | Repo with `model.py` and sibling `model.md`, no pairs configured | `coverage` runs | `model.py` appears in `covered`, not in `uncovered`. |
| AC-2 | Repo with `foo.py`, no `fo
