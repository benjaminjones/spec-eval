## 1. Purpose

**In one line:** this module holds the fixed rubric that defines *drift* — a place where the code and its doc contradict each other; in a report these findings are **counted** (0 = clean).

This module gives the system a **fixed, portable auditing standard** for detecting *drift* — places where a codebase's implementation and its documentation contradict each other. It exists so the product can run drift-detection independently, without depending on any external rubric file: the rubric text is bundled directly in the package.

**The rubric is deliberately conservative — it prefers to miss a real drift rather than raise a false one.** In practice this means an empty result ("no drift found") is always an acceptable answer; a disagreement you could only surface by guessing or by running the code must NOT be reported, and one that needs the doc paraphrased to see is disqualified from **high** severity (reportable at most as medium/low, not silenced).

> Reconstructed intent (confidence: high) — inferred from the docstring and rubric text: the conservatism exists to protect reviewer trust; loosening it "trades trust for noise."

## 2. Definitions

| Term | Meaning (bounds / units) |
|------|--------------------------|
| Drift | A real mismatch where code does X but the doc claims Y (or vice versa). |
| Pair | Exactly ONE unit of review: the source file(s) plus the doc(s)/spec(s) meant to describe them. |
| Severity | A reserved 3-value tier — `high`, `medium`, or `low` — set by the *doc's claim*, not by reviewer preference. |
| Finding | One reported drift instance: severity, optional code/doc references, summary, evidence, suggestion. |
| Silence | A doc omitting behaviour it could plausibly leave unstated — NOT drift. |
| Scope | A doc describing a broader system of which the reviewed file is only one part — NOT drift. |

## 3. Behavior

The module exposes a single constant string, `DRIFT_RUBRIC`, that instructs a technical reviewer how to audit one code↔doc pair and emit findings.

**Reviewing scope.** The reviewer is shown exactly one pair (source + docs) and must find *real* mismatches within it only.

**Severity is reserved and doc-driven.** The tier is chosen by what the DOC claims, not by how bad the reviewer feels the issue is:
- **high** — the doc states a *measurable guarantee* the code breaks: a numeric value/threshold/default disagreeing with code, an explicit function/class/method signature, a named event/message never emitted, a CLI flag default, or a violated invariant/acceptance criterion. If the violation is only visible after paraphrasing the doc, it is **not** high.
- **medium** — misleading but not load-bearing: a renamed-but-equivalent function, a stale example, a field present in code but missing from a spec table, or a mechanism described differently.
- **low** — cosmetic or trivially-fixable wording.

> **Why:** Anchoring severity to the doc's own claim keeps grading objective and prevents severity inflation.

**Conservatism / prefer false negatives.** The reviewer must NOT flag:
- stylistic differences or trivial restatements;
- missing-but-implied behaviour where a doc could plausibly be silent (silence is not drift);
- a doc describing a broader system of which this file is only one part (scope is not drift);
- code comments that disagree with each other (only code-vs-doc counts);
- drift verifiable only by RUNNING the code.

> **Why:** The rubric is tuned to protect trust — a false positive costs more than a missed low-severity issue. An empty findings list is explicitly valid.

**Output format.** The reviewer must emit strict JSON with no preamble: an object with a `findings` array. Each finding carries `severity`, `code_ref`, `doc_ref`, `summary`, `evidence`, and `suggestion`. When no drift exists, the output is `{"findings": []}`.

## 4. Contracts

**Rubric shape** — `DRIFT_RUBRIC` is a single self-contained instruction string; it embeds no external file reference.

**Sync contract (maintenance / CI, not runtime).** The same principles — the severity tiers and the do-not-flag list — are mirrored in `skills/spec-check/SKILL.md`, the copy an agent loads in-session, with a `KEEP IN SYNC` marker in each file naming the other. `tests/contract/test_rubric_sync.py` pins the shared load-bearing phrases so the two copies can't silently drift. At runtime the rubric stays self-contained (INV-1); the mirror is a hand-maintained duplicate kept aligned by that test.

**Expected reviewer output shape** (as instructed by the rubric):
```
{"findings": [
  {"severity": "high|medium|low",
   "code_ref": "file:Lxx or null",
   "doc_ref":  "file:Lxx or null",
   "summary":  "one sentence",
   "evidence": "quoted conflicting code and doc snippets",
   "suggestion": "the fix"}
]}
```

### Invariants (*rules that must always hold*)

| ID | Invariant |
|----|-----------|
| INV-1 | `DRIFT_RUBRIC` is a module-level string constant with no dependency on any external file. |

> Note: the rubric constrains reviewer *output* (severity enum, JSON shape, empty-list validity), but the module itself enforces none of these at runtime — they are instructions, not code-enforced checks, and so are not asserted as invariants here.

### Acceptance criteria (*Given / When / Then*)

| ID | Given | When | Then |
|----|-------|------|------|
| AC-1 | The module is imported | `DRIFT_RUBRIC` is read | It is a non-empty string requiring strict-JSON output. |
| AC-2 | A doc states a default `X=0.9` and code uses `X=0.5` | The rubric is applied | This qualifies as a **high**-severity finding (numeric default disagreement). |
| AC-3 | A doc omits a behaviour the code implements, and the doc could plausibly be silent | The rubric is applied | No finding is produced (silence is not drift). |
| AC-4 | A code↔doc mismatch is only detectable by executing the code | The rubric is applied | No finding is produced. |
| AC-5 | No real mismatches exist in the pair | The rubric is applied | Output is exactly `{"findings": []}`. |
| AC-6 | A function is renamed but still behaves identically to its doc description | The rubric is applied | This qualifies as at most **medium**, never high. |
