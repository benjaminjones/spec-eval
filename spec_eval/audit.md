## 1. Purpose

**In one line:** pair each code file with its doc, ask a model for contradictions, and return severity-tagged drift findings.

This module lets a system **automatically check whether a repository's code and its documentation have drifted apart** — that is, whether the docs still describe what the code actually does. It does this by grouping code and doc files into configured "pairs", handing each pair to a language model with a drift-review rubric, and collecting the model's structured findings about mismatches.

**Every finding the audit reports must carry a severity of exactly `high`, `medium`, or `low`** — nothing else counts as a finding. If the model emits anything with another (or missing) severity, it is discarded rather than reported.

The module is deliberately **portable**: the repository being audited is always passed in as a path argument, so the same audit logic works against any checkout without hard-coded locations.

## 2. Definitions

| Term | Meaning (bounds / units) |
|------|--------------------------|
| Repo | Filesystem path to the repository under audit; base for all glob resolution. |
| Config | A YAML or JSON document of shape `{pairs: [...][, caps: {code, docs}]}`. |
| Pair | One audit unit: `{label, code: [globs], docs: [globs]}`. |
| Label | Human name identifying a pair in the output. |
| Code side | Concatenated text of files matched by a pair's `code` globs, capped at the code cap (`caps.code`, default **64 000 chars**). |
| Doc side | Concatenated text of files matched by a pair's `docs` globs, capped at the doc cap (`caps.docs`, default **28 000 chars**). |
| Severity | One of `high`, `medium`, `low` (ranked 3 / 2 / 1). Any other value is invalid. |
| Finding | A reported drift item: `{severity, summary, code_ref, doc_ref, evidence, suggestion}`. |
| Rubric | `DRIFT_RUBRIC`, the fixed system prompt sent with every pair. |
| Skipped pair | A pair where either side matched **zero** files; reported but not sent to the model. |

## 3. Behavior

**Configuration loading.** A config is read from disk and parsed as YAML if its path ends in `.yml`/`.yaml`, otherwise as JSON. Both forms are expected to yield `{pairs: [...]}`.
> **Why:** supports either serialization format without a separate flag — the file extension is the signal.

**Pair discovery.** When auditing a repo, the configured `pairs` list is used directly. If it is absent or empty, pairs are **inferred** from the repo via the coverage module.
> **Why:** repositories that keep specs co-located with code need no explicit `pairs.yml` — the pairing can be derived.

**Side assembly (code / docs).** For each side, the pair's globs are resolved against the repo path (recursive globbing enabled) **in config order**; each glob's own matches are sorted, and the per-glob results are concatenated (so the assembled order is globally sorted only when a side lists a single glob). Each readable, non-empty regular file is emitted as a `### <relative-path>` header followed by its contents; sections are joined with blank lines. Unreadable files are skipped silently. The assembled text is truncated to its side's cap (config-overridable via `caps:`; defaults **64 000** for code, **28 000** for docs), appending a `...[truncated]` marker when truncation occurs; the reader also returns a per-side `capped` flag so the cut is surfaced to the USER (the marker only tells the model).
> **Why:** the caps bound per-request cost and are directional — code is given more room than docs.

**Skip semantics.** If either side matched zero files, the pair is **not** sent to the model. Instead the result records the label, a `skipped` message stating the match counts, and an empty findings list.
> **Why:** a drift comparison is meaningless without both sides present.

**Model invocation.** For a live pair, a user message is built embedding the label, the code block, and the doc block, and is sent with the drift rubric to the provider. The provider's raw response is parsed for findings.

**Finding extraction (two-stage).**
- *Primary:* the response is scanned for the **first parseable JSON object carrying a `findings` key** — immune to brace-containing prose before or after the JSON, and tolerant of literal newlines/tabs inside quoted strings (models often quote multi-line code in `evidence`). Each entry under `findings` whose `severity` is one of the valid three (case-insensitive) is kept, normalizing `severity`, `summary`, `code_ref`, `doc_ref`, `evidence`, and `suggestion`. `evidence` is the model's quotation of the conflicting code and doc snippets, kept so a reader can check a finding rather than take it on trust; an omitted `evidence` normalizes to the empty string, never to a missing key.
- *Fallback:* if no valid JSON object is found or parsing fails, the response is scanned for `"severity": "high|medium|low"` patterns, and each match is recorded as a finding whose summary marks it unparsed and suggests re-running the pair for detail. A fallback finding carries the **same key set** as a parsed one, with the unavailable fields empty or null, so a consumer can index any field without checking which path produced the finding.
> **Why:** the model is expected to return JSON, but the fallback still surfaces the count/severity of drift even when the response is malformed, rather than losing the signal entirely.

**Result shape per pair.** A live pair yields `{label, code_files, doc_files, findings[, truncated]}` — `truncated`, present only when something was cut, is a list of partial-view notes (an input side over its cap, and/or the model reply cut off at the token cap). A skipped pair yields `{label, skipped, findings: []}`. The repo audit returns a list of these, one per pair, in pair order.

> Reconstructed intent (confidence: med) — the two-stage parse and the `(unparsed finding)` placeholder are inferred to be a resilience measure against non-conforming model output; the code shows the mechanism but not the stated goal.

## 4. Contracts

Semantic shapes:
- **Config** → `{pairs: [{label, code:[glob], docs:[glob]}]}` or empty/absent `pairs`.
- **Assembled side** → `(text ≤ cap chars, file_count ≥ 0, capped: bool)`.
- **Finding** → `{severity ∈ {high,medium,low}, summary, code_ref?, doc_ref?, evidence, suggestion}`.
- **Repo audit result** → list of per-pair result objects, length = number of pairs.

### Invariants (*rules that must always hold*)

| ID | Invariant |
|----|-----------|
| INV-1 | Only findings whose severity is `high`, `medium`, or `low` (case-insensitive) are retained; all others are dropped. |
| INV-2 | Assembled code text never exceeds the configured code cap (default 64 000 chars); assembled doc text never exceeds the doc cap (default 28 000) — excluding the truncation marker. |
| INV-3 | A pair with zero matched files on either side is skipped and returns an empty `findings` list. |
| INV-4 | Only readable, non-empty regular files contribute to an assembled side; unreadable files raise no error. |
| INV-5 | Every returned finding carries the same key set — `severity`, `summary`, `code_ref`, `doc_ref`, `evidence`, `suggestion` — whether it came from the parsed or the fallback path. |

### Acceptance criteria (*Given / When / Then*)

| ID | Given | When | Then |
|----|-------|------|------|
| AC-1 | A pair whose code globs match 3 files and doc globs match 2 files | audited | Result has `code_files=3`, `doc_files=2`, and `findings` from the model. |
| AC-2 | A pair whose doc globs match 0 files | audited | Result has `skipped="no files matched (code=N, docs=0)"` and `findings=[]`; the model is not called. |
| AC-3 | Model returns `{"findings":[{"severity":"HIGH","summary":"x"},{"severity":"trivial"}]}` | parsed | Exactly 1 finding retained, with `severity="high"`. |
| AC-4 | Model returns prose containing `"severity": "medium"` but no valid JSON object | parsed | 1 finding with `severity="medium"`, a summary marking it unparsed, and the same six keys a parsed finding carries. |
| AC-10 | Model returns a finding with `"evidence": "code: n = 8 / doc: defaults to 4"` | parsed | The finding's `evidence` holds that string verbatim; a finding omitting the key gets `evidence=""`. |
| AC-5 | Code side assembles to 80 000 chars of matched content | audited | Sent code text is 64 000 chars plus a trailing `...[truncated]` marker. |
| AC-8 | Code side exceeds its cap, or the model reply stops at the token cap | audited | Result carries `truncated` notes naming each cut (e.g. "code input capped …", "reply hit the token cap"). |
| AC-9 | Config sets `caps: {code: 100}` | audited | The code side is capped at 100 chars and the pair's `truncated` note names ~100, not the default. |
| AC-6 | Config path ends in `.yaml` | loaded | Parsed as YAML; a `.json` (or other) path parsed as JSON. |
| AC-7 | Config has no `pairs` key | audited | Pairs are inferred via the coverage module and audited. |
