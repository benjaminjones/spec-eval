---
name: spec-authoring
description: Author intent-led specs — plus a project-overview and a health/metrics layer — that a reviewer can TRUST to carry the intent, leading with the spec that is aligned with the code. Lead with feature/intent/why; demote signatures to reference. The generator that pairs with the spec-check skill (the checker). No API key needed; runs in your coding-agent session.
---

# spec-authoring — write specs a reviewer can trust to carry the intent

A spec earns its keep when a reviewer can rely on it to carry the intent and contract — often enough to review
from the spec alone, and reach for the code when they choose. That trust comes
from **layering** and **intent-first writing** — not from volume, and not from restating the code as prose. This
skill produces that. It **generates** the spec artifact; the sibling **spec-check** skill then **guards** it
(drift + sufficiency). Author here → check there.

Runs in your coding-agent session (Claude Code, Copilot, Cursor) — no API key, no setup.

## The three layers (produce all three)
Trust you can lead with — often working from the spec, reaching for the code when you choose — comes from **layering**, where each doc names its source of truth and defers downward. **By default every file is co-located** — a spec sits *beside* its code (`src/x.py` → `src/x.md`); a separate folder (`spec/`, `docs/`) is an explicit choice the user names, never a default you invent (see "Where the files go" below):

1. **OVERVIEW — the *shape*** (`OVERVIEW.md`, at the top of the path you spec): a navigation root — module map +
   a data-flow diagram + system context (the observed external seams) + glossary + reading order. Lets a reader
   orient from the map before opening a module. Links down; never restates a value.
2. **Per-module intent specs — the *contract*** (`<module>.md`, beside each code file): each leads with Purpose
   (what + why), states invariants and acceptance criteria as *claims*, and demotes signatures to a reference appendix.
3. **SPEC-HEALTH — the *measurement*** (`spec-reports/SPEC-HEALTH.md`, with the check reports it rolls up): the
   dated, SHA-pinned coverage/drift/sufficiency fingerprint that *lets you verify* layer 2 still matches the
   code — "check me," not "trust me."

**For a small project these three are enough** — no constitution or ADRs required. Every doc states its
**boundary** (the deference contract): *"the code/spec is the source of truth; if this and the spec disagree, the
spec wins."* So no single file has to be trusted for everything — and the top layer can't drift into a lie
because it links instead of restating.

**Trust is established early.** All three layers can exist from commit 1, *before* the specs are good: stub the
OVERVIEW + SPEC-HEALTH with their boundaries, take a baseline fingerprint (even a low score is trustable because
it's dated + pinned), then let the fingerprint drive the specs toward good.

## Where the files go — layout & overview
Two independent choices decide *where* the markdown lands. **Default to the first value of each** — it matches the
`spec-eval` CLI, so a chat session and the terminal produce the same tree:

- **layout** — the spec *granularity*:
  - `per-file` *(default)* — one spec beside each code file (`src/x.py` → `src/x.md`).
  - `per-dir` — one spec per folder (`src/parser/parser.md` covering `src/parser/*.py`), synthesised from its modules.
  - `per-pair` — author the doc of each explicit `code → docs` entry in a pairs config — the way to put specs
    in a separate folder (`docs/`, `spec/`) when the user names one. If a user asks for a separate folder in
    chat, follow it — and tell them the `spec-eval` CLI checks need a matching pairs config to find those specs.
- **overview** — optional overview files that map the specs (none by default):
  - `none` *(default)* — no overview files.
  - `repo` — one `OVERVIEW.md` at the top of the path you spec (a subfolder path → the top of *that* folder).
  - `per-dir` — a `README.md` overview inside each folder that has **2+ modules** (single-module folders are
    skipped; the `overview_min_files` config adjusts the bar). Specs are never size-gated — only these overviews.
  - `both` — `repo` **and** `per-dir`.

**`layout: per-dir` and `overview: per-dir` are different axes** — `layout` sets where the *specs* go, `overview`
only adds overview files. If the user says just "per-dir" or "both," ask which they mean before writing. Unless the
user asks otherwise, use **`per-file` + `none`** and write nothing but a spec beside each code file.

<!-- KEEP IN SYNC: this rubric mirrors `spec_eval/authoring.py` (AUTHORING_STRUCTURE + AUTHORING_DISCIPLINE);
     the templates in `templates/` carry the same skeleton markers. If a principle changes in one place,
     change both — `tests/contract/test_rubric_sync.py` asserts the load-bearing phrases match. -->
## The authoring rubric (per spec)
- **Open with a one-liner, then §1 Purpose (WHAT + WHY)** — `**In one line:** <capability in ≤20 words>`, then
  1–2 sentences + the governing constraint stated directly (no "a reviewer can check" meta-phrasing) — all
  before any type, signature, or class name.
- Organize headings by **CAPABILITY**, not by the symbol/function tree.
- **NEVER make a function signature or a language type a heading.**
- Write behavior as **rules / modes / states / numbered flows** over a defined vocabulary (§2 Definitions) — not
  per-method walkthroughs. Keep §3 in **explanation mode**: sink exhaustive reference lists (full enum/option
  sets, every path or extension name) into a §4 table or a §2 term and reference them by name; 3+ enumerable
  cases become a **list or table**, never a comma/semicolon chain.
- Contracts are **SEMANTIC** (shapes with meaning/bounds/units, invariants, acceptance criteria) and **demoted to
  the last third** — not language types. Open §4 with the visible cue: *Reference — consult when implementing or
  reviewing a change; skip on a first read for intent.*
- Promote load-bearing asserts to **INV-\*** tables (*rules that must always hold*); write acceptance criteria as
  **AC-\*** — *Given / When / Then* with concrete numbers, testable without reading code.
- **DROP code trivia** the code already owns (empty-input `IndexError`, `[1:-1]` slicing, a bare `except`, "no
  caching in that branch").
- **Describe what it IS, not what it ISN'T** — state each capability on its own terms; never define it by
  negation ("not a X") or by contrast with a sibling ("unlike Y"). Those read as leftover context.
- Attach a one-line **`Why:` only where it's earned** — non-obvious or load-bearing rationale; an obvious Why is
  padding. (Confidence-tagged *Reconstructed intent* rationale always stays — that's the trust-carrying kind.)
- **Sentence discipline** — one idea per sentence; split anything past ~30 words; at most one dash-aside or
  parenthetical per sentence; no nested parentheses; no spec-about-the-spec meta-phrasing.
- **Right-size to the module** — collapse to one sentence, or omit, any section that would carry ≤1 real row;
  empty scaffolding and N/A rows are fatigue, not rigor. A small utility module gets a short spec.

## System context (the observed external seams)
The OVERVIEW's `## System context` section inventories what the project *talks to* — infrastructure services
(S3, databases, queues), partner applications, configured endpoints, and any surface the code exposes to
callers. Three rules keep it trustworthy:
- **Observed only.** A row needs code evidence you actually saw — an SDK/driver import, a client call, a
  literal URL, an endpoint-shaped env var — cited as `file:line` in the Evidence column. NEVER invent a row or
  list a system you cannot point at; when nothing was observed, omit the section entirely.
- **Unknowable cells stay honest.** What flows, and who calls an exposed surface, is often not in this repo:
  write `unknown from this repo`, don't guess. Rows are evidence of capability in the code, not proof of runtime traffic.
  Close the section with the fixed boundary line — inbound
  callers and partner-system behavior are not observable from this repo; confirm asserted context with the
  owning teams.
- **Systems and direction only.** No installed-package lists, no endpoint schemas, no ownership registers —
  those change faster than an overview should, and already have better homes (lockfiles, contracts, catalogs).

These rules take precedence over the right-sizing rule: render the full table even if it carries a single row —
an evidence-backed row is a real row, and `unknown from this repo` is a filled cell, not an N/A.

- **Containment contract.** An authored System context table must be a **superset** of what the deterministic
  scanner observes: it may add a row the scanner missed *only* with cited, verifiable `file:line` evidence, and
  must **never lack a system the scanner reports**. So the scanner is the floor, your reading is the ceiling —
  when the two disagree, reconcile toward the union, never drop a scanner-observed system.

*(CLI equivalent: `spec-eval context` — a free, deterministic scan writing `spec-reports/system-context.md` +
`.json`; `generate --overview` feeds the same observed evidence into `OVERVIEW.md` and stamps it with the
fingerprint it was rendered from, so `spec-eval context --check` can later flag a stale overview.)*

## Architecture diagram (the repo overview's data-flow picture)
The repo `OVERVIEW.md`'s `## Architecture (data flow)` section is a `mermaid` flowchart — top to bottom: an
**Entry points** cluster → the wiring root → the pipeline of components → the external systems. It is a
**repo-overview-only** section: per-directory READMEs stay lean and carry no diagram. Two honesty rules mirror
System context:
- **Entry points are scanner-derived.** Each node in the **Entry points** cluster is one *observed* way the code
  is invoked — a declared console script, a `__main__.py`, a framework app object, a CLI main — labeled with its
  `file:line`. Never add an entry point you cannot point at, and never write entry points into a per-module spec;
  they live only in this cluster.
- **Internal edges are inferred, not verified.** The wiring between components is read from the module intents,
  **not verified against a call graph** — draw it as intended data flow, not proof of runtime wiring, and say so
  in the closing caveat line.

**Asking an agent to add or update the diagram in an existing README** (the chat mirror of
`spec-eval diagram <path> --write`): update the `## Architecture (data flow)` section of an **existing**
`OVERVIEW.md`/`README.md`, touching only that section's body. If the doc has **no** such section, adding one is a
**deliberate** act, never a silent graffiti of a doc that wasn't meant to carry a diagram (e.g. a project's
marketing README) — the CLI gates it behind `--add-section`, and a doc that does not exist is authored by
`generate` first. Re-stamp deterministically by running `spec-eval diagram <path> --write` (or
`spec-eval context`); never hand-write the fingerprint digest. A ready prompt:

> Regenerate the `## Architecture (data flow)` mermaid diagram for `<path>` from the current entry points and
> module intents, and update only that section of its existing `OVERVIEW.md` — keep the scanner-derived Entry
> points cluster (`file:line`-labeled), mark the internal edges as inferred (not verified against a call graph),
> then re-stamp with `spec-eval diagram <path> --write`.

*(CLI equivalent: `spec-eval diagram <path>` prints the fenced ```mermaid block to stdout and touches nothing;
`--write` replaces the Architecture section of an existing doc and re-stamps only the architecture fingerprint;
`--add-section` explicitly appends the section when the doc lacks one. Neither ever creates a doc.)*

## Reconstructed intent (reverse-engineering code you didn't write)
When specifying code with no stated rationale, you may *infer* the "why" — but **label it**:
`> Reconstructed intent (confidence: low/med/high) — inferred from the code, not the author's stated law.`
Never present inferred rationale as fact, and don't mint formal decision records (ADRs) for it.

## The DON'T list (the anti-patterns this replaces)
- ❌ `bytes_to_unicode() -> dict[int, str]` **as a heading** — a signature is not a feature.
- ❌ "Module-level functions / Class X / Method `y()`" **symbol-tree headings**.
- ❌ Language return types as "contracts" (`torch.Tensor`) — use **semantic** shapes (`(B, T, vocab_size)`, with
  meaning + bounds).
- ❌ **Any metric, score, or drift finding inside a spec** — those live in `SPEC-HEALTH.md`.
- ❌ A **Why:** on an obvious rule — noise, not rationale; it restates what the reader already got.

**Litmus for what goes where:** a fact true about the system *regardless of who audited it or when* → a **spec**.
A measurement with a model + date + SHA that would change on re-run without the code changing → **SPEC-HEALTH.md**.
A signature/type (derivable from the code) → **neither**; drop it (or sink it to a tiny reference appendix).

## The fingerprint feedback loop (iterate the specs — and this skill)
One module at a time, so the signal is fast:
1. **Author** the spec intent-led (rubric above).
2. **Fingerprint** it — run the drift + sufficiency checks on that *one* pair.
3. **Read the delta:** sufficiency should **grow** (an intent-led spec captures *more* of the behavior, not less); drift stays
   flat. If sufficiency **drops** when you strip a signature, that gap is a **real behavior** the prose failed to
   carry — add it back as a *semantic* contract, not a signature.
4. **Fold each recurring gap CLASS** back into your rubric (e.g. "always raise `(B,T,*)` shapes as named
   contracts"), not the one-off.
5. **Re-author + compare** — put the two fingerprints (before/after) side by side, one per skill version. Stop
   when sufficiency plateaus high and drift is flat.

*(Caveat on famous/heavily-published subjects: the detector can refill stripped intent from memory, so the
sufficiency number is partly its prior — treat the delta as directional there, and get the clean number from an
obscure or private subject.)*

## Templates (in `templates/`)
- `spec-template.md` — the per-module intent spec.
- `OVERVIEW-template.md` — the project-overview (module map + data-flow diagram + system context + glossary).
- `SPEC-HEALTH-template.md` — the health/metrics layer.

**Read the template file before writing — don't reproduce it from this skill's description.** The heading
annotations (e.g. `### Invariants (*rules that must always hold*)`) are part of the contract, not decoration:
they tell a reader what the section means without consulting this skill.

## Then check it
Authoring produces the artifact; run **spec-check** afterward to confirm the new spec matches the code (drift),
and a sufficiency pass to score how completely the spec captures the behavior (an indicator you still validate, not a guarantee).
Check in a **fresh session** where you can: a checker that remembers its authoring decisions tends to echo them
instead of re-reading the code.
