# Sufficiency Specification

## 1. Purpose

**In one line:** sufficiency = a per-pair completeness score from 0 to 1 — 1.0 = the code's behavior is fully rebuildable from the spec, 0 = the spec barely constrains the code.

This module gives the system the ability to score how much *load-bearing behavior* present in the CODE is MISSING from its SPEC. The grader is prompted with a portability question — **"Could a developer restart this project from the specs alone?"** — as its calibration device; the resulting score is an **indicator of completeness** plus a list of what's missing, not a proof that a rebuild would succeed.

It is the deliberate inverse of the drift auditor. Where drift asks "does the spec *contradict* the code?" and treats silence as acceptable, sufficiency asks "does the spec *omit* behavior that's in the code?" — silence IS the finding here. The bar is not line-by-line restatement; pure implementation trivia may be omitted freely. The bar is intent-level behavior, contracts, defaults, and events.

The one governing constraint a reviewer can check: **every reported gap is something a rebuild-from-spec would have to guess, and each carries a severity of either `major` or `minor`.** A whole missing feature is major; a missing default or edge-case is minor.

## 2. Definitions

| Term | Meaning (bounds/units) |
|------|------------------------|
| pair | A `{label, code, docs}` mapping: a set of code globs paired with spec/doc globs. |
| label | Human-readable name identifying the pair in the result. |
| code | Concatenated source text of all matched code files, capped at the code cap (`caps.code`, default `audit.CODE_CAP`). |
| doc | Concatenated spec/doc text of all matched doc files, capped at the doc cap (`caps.docs`, default `audit.DOC_CAP`). |
| gap | One missing behavior: `{severity, missing[, code_ref]}` — `missing` is a one-sentence description; `code_ref` is a **plain-text pointer you can search for** — the file plus the nearest enclosing function/class (the file name alone when the gap spans the module). The rubric requires it on every gap; the parser still tolerates a missing one. Symbols are used instead of line numbers because they stay valid as the code moves, and plain text works in any viewer or editor. |
| severity | `major` (whole feature/contract/component missing) or `minor` (default/threshold/edge-case/event-shape missing). |
| sufficiency | Score in `[0.0, 1.0]`; 1.0 = the grader found no load-bearing gaps, 0.0 = spec barely constrains the code. An indicator, not a guarantee. |
| skipped | Marker returned when no code or no doc files matched. |

## 3. Behavior

**Per-pair review.** For each pair, the module reads the code globs and doc globs (each capped), then asks a model — under the sufficiency rubric — to list behaviors/contracts/defaults/rules/events present in the CODE but absent from the SPEC, plus an overall sufficiency score.

**Why:** the rubric explicitly frames omissions (not contradictions) as the target, and instructs the model to be "calibrated, not generous" — the score is meant to reflect real rebuild risk, not reward verbosity.

**Skip semantics.** If either side matched zero files (`code=0` or `docs=0`), the pair is skipped: it returns a result with a `skipped` explanation string, `sufficiency: None`, and an empty `gaps` list. No model call is made.

**Why:** a sufficiency comparison is meaningless without both a code side and a spec side to compare.

**Response parsing.** The model is expected to return strict JSON, but the module is defensive: it scans for the first **parseable JSON object carrying a `sufficiency` or `gaps` key** — immune to brace-containing prose around the JSON, tolerant of literal newlines/tabs inside quoted strings. On success it normalizes each gap: `severity` is lowercased and stringified, `missing` is stringified, and `code_ref` is kept verbatim (required by the rubric on every gap; a missing or `"null"` ref is tolerated and dropped rather than failing the parse); `sufficiency` is coerced to float (defaulting to `0`).

**Parse-failure fallback.** If no JSON span is found, or JSON parsing raises, the result carries `sufficiency: None` and a single gap `{"severity": "?", "missing": <first 200 chars of raw response>}`.

**Why:** preserve a diagnostic trace of the malformed response rather than discarding it, while signalling (via `None` score and `"?"` severity) that the result is not a valid assessment.

**Repo-level run.** Over a whole repo, the module uses `config["pairs"]` if present; otherwise it infers pairs via the coverage module.

**Why:** co-located specs need no explicit `pairs.yml`, so pairs can be inferred rather than mandated.

**Rubric-defined scoring anchors** (part of the model contract — the rubric phrases 1.0 as "fully rebuildable" to calibrate the grader; users should read the score as a completeness indicator):
- `sufficiency = 1.0` — the grader found no load-bearing gaps.
- `sufficiency = 0.0` — spec barely constrains the code.
- 1:1 line restatement is NOT required; implementation detail may be omitted.

## 4. Contracts

**Model call:** `providers.gen(model, SUFFICIENCY_RUBRIC, user, max_tokens=audit.REVIEW_MAX_TOKENS)` where `user` embeds the label, the fenced code, and the spec text. The budget is the drift auditor's `REVIEW_MAX_TOKENS` — the same constant, imported, not a re-typed number — because a gap list truncated mid-JSON is unparseable, so gap-heavy pairs need the headroom.

**Per-pair result shape (success):**
`{label, code_files, doc_files, sufficiency: float∈[0,1], gaps: [{severity, missing[, code_ref]}][, truncated]}`

**Per-pair result shape (skipped):**
`{label, skipped: str, sufficiency: null, gaps: []}`

**Per-pair result shape (parse failure):**
`{label, sufficiency: null, gaps: [{severity: "?", missing: str≤200}][, truncated]}`

Either live shape may carry `truncated` — a list of partial-view notes (an input side over its cap), present
only when an input was cut. On a parse failure it names the likely cause of the unparseable reply.

**Repo result:** a list of per-pair results, one per pair.

### Invariants (*rules that must always hold*)

| ID | Invariant |
|----|-----------|
| INV-1 | When `nc == 0` or `nd == 0`, the pair is skipped: `sufficiency` is `None`, `gaps` is empty, and no model call occurs. |
| INV-2 | Each parsed gap's `severity` is a lowercased string and `missing` is a string. |
| INV-3 | On a successful parse, `sufficiency` is a float (`0` when the key is absent). |
| INV-4 | On parse failure (no parseable JSON object with the expected keys), `sufficiency` is `None` and the fallback gap's `missing` is truncated to the first 200 characters of the response. |

### Acceptance criteria (*Given / When / Then*)

| ID | Given | When | Then |
|----|-------|------|------|
| AC-1 | A pair whose code globs match 0 files | `sufficiency_pair` runs | Result has `skipped` set, `sufficiency: None`, `gaps: []`, and no model call. |
| AC-2 | A pair whose doc globs match 0 files | `sufficiency_pair` runs | Same as AC-1 (skipped, `sufficiency: None`, empty gaps). |
| AC-3 | Model returns `{"sufficiency":0.8,"gaps":[{"severity":"MAJOR","missing":"x"}]}` | Response is parsed | Result has `sufficiency: 0.8`, `code_files`/`doc_files` populated, and gap `{severity:"major", missing:"x"}`. |
| AC-8 | A gap carries `code_ref: "file.py (fn)"` | Response is parsed | The gap keeps `code_ref` verbatim; a `code_ref` of `null`/`"null"` or a missing key is omitted. |
| AC-4 | Model returns text with no `{...}` span | Response is parsed | Result has `sufficiency: None` and one gap `{severity:"?", missing: first 200 chars}`. |
| AC-5 | Model returns a JSON object missing the `sufficiency` key | Response is parsed | `sufficiency` defaults to `0.0` (float). |
| AC-6 | `config` has no `pairs` key | `sufficiency_repo` runs | Pairs are inferred via `coverage_mod.infer_pairs(repo, config)`. |
| AC-7 | `config` supplies 3 pairs | `sufficiency_repo` runs | A list of 3 per-pair results is returned, in order. |

> Reconstructed intent (confidence: high) — the shared `REVIEW_MAX_TOKENS` budget and `"?"` sentinel severity are inferred as diagnostic/budget choices, not derivable from external spec.
