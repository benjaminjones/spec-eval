# Spec: `<Feature / capability name>`   *(NOT the module/file name)*

> **This file is the contract for a capability of `<project>`. It leads with intent.**
> Signatures, language types, and control-flow are **not** the subject here — the code owns those.
> If a fact here and the code disagree about *intent*, this file wins; for *signatures*, read the code.

## Metadata
- **Capability:** <one line — the job this gives the system>
- **Source module(s):** `<src/x.py>`   *(pointer only — a reader can orient from this spec, not the source)*
- **Depends on:** <capabilities/specs this consumes>
- **Consumed by:** <capabilities/specs that consume this>
- **Status:** Draft | Accepted
- **Health:** see [SPEC-HEALTH.md](./SPEC-HEALTH.md#<label>)   *(do NOT restate scores here)*

## 1. Purpose  *(prose — WHAT + WHY; nothing above this in reading order)*
**In one line:** <the capability in ≤20 words — a reader can stop here and know what this is.>

<1–2 sentences: what capability this gives the system, and what breaks if it is wrong.>

**Governing constraint:** <the ONE law, stated as a consequence a reviewer can evaluate — e.g.
"decode(encode(text)) == text for all UTF-8 input; any divergence is a spec violation, not an edge case.">

**Why `<the key design choice>`:** <the rationale — the spine, not a side note.>
<!-- If reverse-engineered: > Reconstructed intent (confidence: low/med/high) — inferred from the code. -->

## 2. Definitions  *(ubiquitous language — so the rest speaks in nouns, not variables)*
| Term | Meaning (with bounds / units) |
|---|---|
| <Term> | <plain-English meaning, with bounds> |

## 3. Behavior  *(rules / modes / states / numbered flows keyed to §2 — NOT per-method walkthroughs)*
### 3.1 <The X pipeline / the forward pass / …>
1. <ordered step over the vocabulary> — **Why:** <only when non-obvious; an obvious Why is padding>
2. <3+ enumerable cases → a bulleted list or table, never a comma/semicolon chain>
3. …

### 3.2 <state machine / second capability>
<transition table or numbered flow — name WHO calls it and WHY, then the business rules.>

## 4. Contracts  *(REFERENCE — the last third; semantic, not language types)*
*Reference — consult when implementing or reviewing a change; skip on a first read for intent.*
### 4.1 Shapes
| Value | Shape / semantic type | Notes |
|---|---|---|
| <output> | `(B, T, …)` | <meaning, bounds — NOT `SomeLibType`> |

### 4.2 Invariants  *(stable IDs — laws about the capability, each traceable to a test)*
| ID | Invariant |
|---|---|
| INV-<CAP>-001 | <a law, e.g. "n_embd % n_head == 0" — not a code assert> |

### 4.3 Acceptance criteria  *(Given/When/Then, concrete numbers, testable without reading code)*
- **AC-<CAP>-001** (<name>): Given <state>, when <action>, then <observable outcome>.

## 5. Open questions / Out of scope
- <a decision to be made, or explicitly-excluded behavior>

<!-- DO NOT INCLUDE: function signatures as headings; language return types as contracts; code trivia
     (empty-input errors, slicing tricks, bare except, "no caching in that branch"); any metric/score/drift
     finding (those live in SPEC-HEALTH.md). LEADS: §1 Purpose → §3 Behavior. REFERENCE: §4 Contracts.
     RIGHT-SIZE: collapse or delete any section that would carry ≤1 real row — empty scaffolding is fatigue,
     not rigor. SENTENCES: one idea each; split past ~30 words; no nested parentheses; no meta-phrasing. -->
