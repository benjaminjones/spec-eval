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
   a data-flow diagram + glossary + reading order. Lets a reader orient from the map before opening a module.
   Links down; never restates a value.
2. **Per-module intent specs — the *contract*** (`<module>.md`, beside each code file): each leads with Purpose
   (what + why), states invariants and acceptance criteria as *claims*, and demotes signatures to a reference appendix.
3. **SPEC-HEALTH — the *measurement*** (`SPEC-HEALTH.md`, at the top of the path you spec): the dated, SHA-pinned
   coverage/drift/sufficiency fingerprint that *lets you verify* layer 2 still matches the code — "check me," not "trust me."

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
- `OVERVIEW-template.md` — the project-overview (module map + data-flow diagram + glossary).
- `SPEC-HEALTH-template.md` — the health/metrics layer.

**Read the template file before writing — don't reproduce it from this skill's description.** The heading
annotations (e.g. `### Invariants (*rules that must always hold*)`) are part of the contract, not decoration:
they tell a reader what the section means without consulting this skill.

## Then check it
Authoring produces the artifact; run **spec-check** afterward to confirm the new spec matches the code (drift),
and a sufficiency pass to score how completely the spec captures the behavior (an indicator you still validate, not a guarantee).
Check in a **fresh session** where you can: a checker that remembers its authoring decisions tends to echo them
instead of re-reading the code.
