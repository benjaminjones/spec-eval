# `<project>` — Project Overview

> **About the TARGET project — not the process that specced it.**
> This page describes the *shape* of `<project>`; the specs describe the *contract*.
> If this page and a spec disagree, **the spec wins**. This page never restates a value — it points.

## What `<project>` is
<2–4 sentences: what the project does, its core job, and what it optimizes for (clarity? speed? fidelity?).
Written so a newcomer understands the point before opening any spec.>

## Governing principles  *(the intent root — the "why" the whole set serves)*
- **<Principle 1>** — <one line>.
- **<Principle 2>** — <one line>.
<!-- If reverse-engineered: > Reconstructed intent (confidence: …) — inferred from the code, not stated by the author. -->

## Architecture (data flow)
```
<input> --[<component>]--> <intermediate (shape)> --[<component>]--> <output>
                                                          |
                            <the one seam / abstraction that threads through everything>
```
*(For internal component diagrams and stateful flows, see the relevant module spec's §3 Behavior.)*

## Module map  *(src → canonical spec → one-line intent; the navigation layer)*
| Module | Canonical spec | Intent (not signatures) |
|---|---|---|
| `<src/a.py>` | [a.md](./a.md) | <the spec's **In one line:** sentence, copied verbatim — not a paraphrase> |
| `<src/b.py>` | [b.md](./b.md) | <the spec's **In one line:** sentence, verbatim> |

## Glossary  *(plain-English one-liners, each → its spec section)*
- **<term>** — <meaning> → [<a.md §N>](./a.md)
- **<term>** — <meaning> → [<b.md §N>](./b.md)

## Health receipt
Spec-set trust signal (coverage / drift / sufficiency, dated + SHA-pinned): see
[SPEC-HEALTH.md](./spec-reports/SPEC-HEALTH.md). **This page carries no scores.**

## Reading order
1. This overview → 2. the module specs (`<a>` → `<b>` → …) → 3. [SPEC-HEALTH.md](./spec-reports/SPEC-HEALTH.md)
   to confirm the specs still match the code.
