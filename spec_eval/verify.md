## 1. Purpose

**In one line:** re-read the document a drift finding was raised on and withdraw the finding if the document does not assert what it claims.

The audit asks *does the code contradict the doc?* This module asks a different question — *does the doc assert the thing this finding contradicts?* — and answering it requires reading the document again rather than instructing the first reader more firmly. The governing constraint is that a finding may be withdrawn **only** on one of four named grounds, each settled by quoting one line that exists; a finding that cannot be withdrawn on a named ground with a quote is upheld.

> Reconstructed intent (confidence: high) — inferred from the module's own comments and a recorded run: a measured two-arm comparison found that strengthening the drift rubric's paraphrase guard made the model quote more fully without reducing findings, and that a claim two blind readers judged a false positive was raised on six runs of six under both rubric versions. A reproducible misreading is systematic, and a systematic misreading is not addressed by re-instructing the reader who made it.

## 2. Definitions

| Term | Meaning |
|---|---|
| **Verdict** | Per finding: `{verdict, ground, doc_quote, why}`, where `verdict` ∈ {`upheld`, `withdrawn`}. |
| **Ground** | The named reason a finding was withdrawn, from a closed set of four. A withdrawal without a ground from that set is not a withdrawal. |
| **not-asserted** | The line the finding *itself cites* does not carry the claim at the strength the finding needs — a quantifier the line lacks, or a clause it has that the finding dropped. |
| **stated-elsewhere** | The same document states the rule correctly in another passage, commonly a contract table below the narrative being graded. |
| **not-normative** | The graded sentence is rationale or commentary, not a claim about behaviour. |
| **scoped** | The document scoped its statement to a named case, and the finding applies it to a case the document excluded. |
| **Upheld set** | The findings that survive verification, and every finding when the pass did not run. Only these are counted. |

## 3. Behavior

The pass is **off by default** and runs only under `--verify`. It costs one extra model call per pair that produced findings, so a run with findings on a third of its pairs pays roughly a third again in calls.

Verification is **per pair, not per finding**. One call carries the whole document plus every finding raised on that pair, because the question is *does this document say it* and half a document cannot answer that.

Every ground is a **positive existential** — each is settled by quoting one line that is present.
> **Why:** an earlier form let `not-asserted` mean "the document does not say this", which no quote can establish. A run withdrew a finding about little-endian serialization on that ground, quoting a line that omitted the property while three other lines, including an invariant row, asserted it outright. The outcome was right and the reason was false. Scoping the ground to the line the finding cites makes it a claim a quote can settle.

Two properties make the pass safe to add, and both are failure-direction choices:

- **An unusable verifier is a no-op.** A response that is empty, unparseable, or missing an index leaves those findings upheld. Silently deleting real findings is the one harm this pass could do that the audit alone cannot, so every degradation path resolves toward keeping findings.
- **A withdrawn finding is kept and uncounted, never deleted.** It renders struck through with its ground and the document line that settles it. A withdrawal is a claim in its own right and stays reviewable.

A `not-asserted` withdrawal is additionally checked **without a model**: the quoted line must appear in the document at all, and — when the finding cited a line — within a small window of it. Presence is checked either way, because a finding's `doc_ref` may be null and those are exactly the withdrawals with no line to check a position against. A quote found nowhere is rejected outright — a wholly invented quote is stronger evidence of fabrication than a misplaced one. The check applies to that ground alone — `stated-elsewhere` quotes a line that is by definition *not* the cited one, so the same check would reject every correct use of it.

## 4. Contracts

*Reference — consult when implementing or reviewing a change; skip on a first read for intent.*

Verdict shape: `{verdict: "upheld"|"withdrawn", ground: <one of four>|null, doc_quote: str, why: str}`, one per finding, positionally aligned with the findings given.

### Invariants (*rules that must always hold*)

| ID | Invariant |
|---|---|
| INV-1 | A verdict is `withdrawn` only if its `ground` is one of the four named grounds; any other value yields `upheld`. |
| INV-2 | `parse_verdicts(resp, n)` returns exactly `n` verdicts for any input, including empty or unparseable text. |
| INV-3 | A finding with no parseable verdict, or an out-of-range index, is `upheld`. |
| INV-4 | A `not-asserted` withdrawal whose quote is empty, absent from the document, or found only outside the window around a cited line, is converted to `upheld`. Presence is checked whether or not a line was cited; the window only when one was. |
| INV-5 | The position check is applied to `not-asserted` alone and never alters a verdict on another ground. |
| INV-6 | A withdrawn finding is retained in the results and excluded from the drift count. |

### Acceptance criteria (*Given / When / Then*)

| ID | Given | When | Then |
|---|---|---|---|
| AC-1 | A verdict `withdrawn` with ground `not-asserted` and a quote | parsed | The finding is withdrawn with that ground recorded. |
| AC-2 | A verdict `withdrawn` with no ground, or ground `seems-wrong` | parsed | The finding is `upheld` and `ground` is `null`. |
| AC-3 | An empty response, prose with no JSON, or `{"nope": []}`, for 3 findings | parsed | 3 verdicts returned, all `upheld`. |
| AC-4 | Verdicts for index 0 and index 9, with 2 findings | parsed | Finding 0 takes its verdict; finding 1 is `upheld`. |
| AC-5 | A finding citing `prepare.md:L50`, withdrawn `not-asserted`, quoting a line found at 56 | checked | Converted to `upheld`, with the why naming the position mismatch. |
| AC-6 | The same finding withdrawn `stated-elsewhere`, quoting a line at 1 | checked | The withdrawal stands — the position check does not apply. |
| AC-7 | One upheld and one withdrawn high-severity finding on a pair | rendered | The drift count is 1; the withdrawn finding appears struck through with its ground and doc line, and proposes no fix. |
| AC-8 | A pair whose findings list is empty | verified | No model call is made and the pair is returned unchanged. |
| AC-9 | A `not-asserted` withdrawal quoting text that appears nowhere in the document | checked | Converted to `upheld`, with the why naming the absent quote. |
| AC-10 | The same withdrawal where the finding's `doc_ref` is null or carries no line number | checked | Still converted to `upheld` — presence does not depend on a cited line. |

## 5. Open questions / Out of scope

- The withdrawal grounds are pinned to `skills/spec-check/SKILL.md` by the rubric-sync test; the agent-session path describes the same four grounds in prose.
- The pass has been exercised on one repository. Withdrawal rates observed there are a property of that subject and are not a rate for any other.
- The intermittency of the `not-asserted` misquotation is unmeasured: the position check is unit-tested against a captured instance, and how often that instance recurs in live runs is not established.
