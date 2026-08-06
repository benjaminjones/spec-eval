## 1. Purpose

**In one line:** render drift and sufficiency results into two markdown reports whose headline counts match their contents.

This module turns the raw results of a spec-vs-code audit into the **legible product output**: two human-readable markdown reports — a *drift report* (where code and docs disagree) and a *spec-sufficiency report* (whether the spec fully captures the code's behavior). It exists so the audit's findings become something a reviewer can read, diff in version control, and search — not a JSON blob.

**Every number in a report's headline is a faithful count of what follows it.** If the header says "*3 high/medium drift finding(s) across 2 audited pair(s)*", then exactly 2 non-skipped pairs appear below and their high+medium findings total exactly 3. Skipped pairs are shown as skipped and never counted.

> Reconstructed intent (confidence: high) — the module docstrings state the "legible product output" and "fingerprint" goals explicitly.

## 2. Definitions

| Term | Meaning (bounds / units) |
|---|---|
| **Pair** | One audited unit (a code/doc module pairing), carried as a result record with a `label`. |
| **Finding** | A drift item on a pair: `severity` ∈ {high, medium, low, ...}, `summary`, optional `code_ref`, `doc_ref`, `evidence`, `suggestion`. |
| **Evidence block** | The finding's quoted code and doc snippets, rendered as a four-space-indented fenced block so a multi-line quote stays inside its list item. Fences inside the quote are neutralized so they cannot close the block early. |
| **Drift load** | Count of a pair's findings whose severity is `high` or `medium` **and which were not withdrawn by the verification pass**. Integer ≥ 0. |
| **Withdrawn finding** | A finding the optional second pass judged not supported by its document. It carries a `verification` verdict naming the ground and quoting the doc line. Kept in the report, struck through, and excluded from the drift load. |
| **Skipped pair** | A result carrying a truthy `skipped` reason string; excluded from all counts and fingerprints. |
| **Sufficiency** | Per-pair score in `0.0..1.0`: how fully the spec captures the code's behavior (1.0 = fully). May be absent (`None`) → "not scored". |
| **Gap** | A sufficiency shortfall on a pair: `severity`, `missing` (behavior present in code, absent from spec), optional `code_ref` (searchable file+symbol pointer). |
| **Fingerprint** | An at-a-glance markdown table summarizing all pairs; toggled by `include_fingerprint`. The sufficiency fingerprint is ordered **worst first**; the drift fingerprint stays in **input order**. |
| **Unicode bar** | A 20-cell bar of `█` (filled) / `░` (empty) rendering a `0..1` value. |

## 3. Behavior

### Drift report
Renders a markdown document headed with the repo's basename, the detector model, an audited-pair count (`audited/total`) and the provider call count, then a bold headline of total high/medium findings across audited pairs.

Each pair is a section:
- **Skipped** pairs → `## {label} — _skipped: {reason}_` and nothing more.
- **Audited** pairs → header marked `✓ clean` (drift load 0) or `⚠ N drift`; a ⚠ *partial view* line follows when the pair carries `truncated` notes (findings may be incomplete); then one bullet per finding: `**[severity]** summary`, appending a `` (`code_ref` vs `doc_ref`) `` suffix only when at least one ref exists (missing side shown as `?`), an indented `*evidence:*` fenced block when the finding quotes evidence, and an indented `*fix:*` line when a suggestion exists. A finding with empty evidence emits no block at all. A **withdrawn** finding renders its summary struck through, followed by its ground and the doc line that settles it, and proposes no fix.

> **Why keep a withdrawn finding visible:** a withdrawal is a claim in its own right. Deleting it would hide a judgement the reader may disagree with; counting it would defeat the pass.

**Why:** clean pairs still appear so the reader sees coverage, not just problems.

If `include_fingerprint`, a **Drift fingerprint** table (`✓ clean` / `⚠ count` per non-skipped pair) is appended at the end. The function writes the file and returns `total`.

### Sufficiency report
Renders a document headed with basename, detector line (`scored/total` pairs), and a bold **average sufficiency** across scored pairs, framed as "*how completely does the spec capture the code's behavior?*" with an explicit "indicator, not a guarantee" caveat.

That headline average is a **two-level** number:
```
sufficiencyᵢ = the grader's score for pair i          (from sufficiency.py — 0.0..1.0, or None = not scored)
avg          = mean(sufficiencyᵢ over scored pairs)    (this module; 0 when no pair is scored)
```
The inner term is the model's per-pair judgment; only the outer `mean` is computed here.

**Why fingerprint first:** unlike the drift report, the sufficiency fingerprint is placed *before* the per-module detail — the reader sees the overall shape before drilling in.

Per-module detail is ordered **worst first**, with unscored (`None`) pairs sorted last. Skipped pairs show as `_skipped: {reason}_`; unscored pairs (an unparseable model reply) show `### {label} — not scored (unparseable model reply)` with the raw-excerpt gap beneath, so one bad reply never loses the whole report; scored pairs show `### {label} — sufficiency {score}` and one bullet per gap (`**[severity]** missing`, with a ` · \`code_ref\`` suffix as plain inline code when the gap carries one, so the pointer can be searched for in any viewer or editor. The ` · ` separator is used because em dashes occur naturally inside gap prose; the dot marks the ref unambiguously). A pair carrying `truncated` notes gets a ⚠ *partial view* line under its header — for an unscored pair it names the likely cause (e.g. the reply hit the token cap). The function writes the file and returns `avg`.

### Ordering & empties
- **Sufficiency fingerprint:** scored pairs only, ascending score (worst first). Empty input → empty string (table omitted).
- **Drift fingerprint:** non-skipped pairs only, in input order. Empty → empty string.
- **Average** when no pairs are scored is `0`.

### Usage line
Both reports read `providers.USAGE['calls']` at render time — the header states how many model calls the run made. Exact token totals print to the terminal; no dollar figure is rendered.

## 4. Contracts

### Shapes
| Shape | Meaning |
|---|---|
| `results: [pair]` | list of result records; each has `label`, either `skipped` or (`findings` / `sufficiency`+`gaps`). |
| `sufficiency` | float in `0.0..1.0` or `None` (not scored). |
| `_bar(v) → str` | length-20 string of `█`/`░`; `v` clamped to `0..1` before rendering. |
| return of `write_markdown` | `total` = integer count of high/medium findings across audited pairs. |
| return of `write_sufficiency_markdown` | `avg` = mean sufficiency of scored pairs, or `0`. |

### Invariants (*rules that must always hold*)
| ID | Invariant |
|---|---|
| INV-1 | The bar value is clamped to `0.0..1.0` before rendering (`max(0.0, min(1.0, v))`), so the bar never over/underflows its 20 cells. |

### Acceptance criteria (*Given / When / Then*)
| ID | Given | When | Then |
|---|---|---|---|
| AC-1 | 3 pairs, 1 skipped, remaining two with 2 and 0 high/medium findings | `write_markdown` | headline reads "**2 high/medium drift finding(s) across 2 audited pair(s).**"; skipped pair shown as `_skipped: …_`; return value = 2. |
| AC-2 | a finding with `code_ref` set, `doc_ref` absent | render drift bullet | bullet suffix is `` (`<code_ref>` vs `?`) ``. |
| AC-3 | a finding with no `code_ref` and no `doc_ref` | render drift bullet | no ref suffix appended. |
| AC-11 | a pair with one upheld and one withdrawn high-severity finding | `write_markdown` | the headline counts 1; the withdrawn finding appears struck through with its ground and doc line, and proposes no fix. |
| AC-8 | a finding whose `evidence` is two lines | render drift bullet | an `*evidence:*` fenced block follows the bullet, every line indented four spaces, and the `*fix:*` line still renders after it. |
| AC-9 | a finding whose `evidence` itself contains a ``` fence | render drift bullet | the rendered block contains exactly two fences — its own — so the report cannot spill into a code block. |
| AC-10 | a finding whose `evidence` is the empty string | render drift bullet | no `*evidence:*` block is emitted. |
| AC-4 | pairs with sufficiency 0.4, 0.9, and one `None` | `write_sufficiency_markdown` | per-module detail order is 0.4, 0.9, then the `None` pair last; average = 0.65. |
| AC-5 | no scored pairs | `write_sufficiency_markdown` | average = 0.00; sufficiency fingerprint omitted. |
| AC-6 | `sufficiency = 1.0` | `_bar(1.0)` | returns 20 `█` and 0 `░`. |
| AC-7 | `include_fingerprint=False` | either report | no fingerprint table appears in output. |
