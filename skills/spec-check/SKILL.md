---
name: spec-check
description: Keep code and its spec/doc in agreement — whether you're writing them TOGETHER for new work or auditing an EXISTING project. Find places where the code does X but the spec claims Y, and decide which side to fix, before you commit. No API key needed; runs in your coding-agent session.
---

# spec-check — keep code and spec in agreement

Check that code and its specification/documentation say the same thing, so a reviewer can often **read the spec
instead of the diff**. This runs two ways:

- **Building something new (spec + code together).** As you draft a spec and write the code in the same session,
  check after each change that they still agree — so the spec is *born accurate*, not reconstructed weeks later.
  When they disagree, you decide which side is right and fix that one.
- **Auditing or backfilling an existing project.** Find where the code and an older spec have *drifted* apart,
  and what the spec is now missing.

It runs in your coding-agent session (Claude Code, Copilot, Cursor, …) — **no API key, no separate billing, no
setup**. For hands-off CI or a cross-vendor second opinion, pair it with a dedicated spec-audit CLI.

## When to use
- **While building a feature with a spec** (e.g. you're drafting `src/x.md` and writing `src/x.py` together):
  after a change, confirm the code and spec still match — catch the gap immediately, not in review.
- **Before a commit / PR:** check that the changed code still matches the spec/doc that governs it.
- **Auditing existing code:** when asked "does this spec match the code?", "did the code drift from the doc?",
  or "is this spec still accurate?"

> To **author** an intent-led spec (not just check agreement), use the sibling **spec-authoring** skill; then run
> spec-check to confirm the new spec matches the code. Authoring generates the artifact; spec-check guards it.

## How to run it
1. **Find the pairs.** The code + the spec/doc that governs it. **By default that's the co-located `<stem>.md`
   beside the code** (`src/x.py` ↔ `src/x.md`) — the same pairing the CLI uses; it can also be a folder spec, a
   design doc, or a README section that describes it. When building new, that's the spec you're drafting
   *alongside* the code. If the project has a pairs config (e.g. a YAML/JSON listing `code` globs → `docs`), use
   it. If a code file has **no** governing spec yet, say so — missing-spec is itself a coverage finding (decide
   whether it needs one).
2. **Apply the rubric below** to each (code, spec) pair — strictly, one pair at a time.
3. **Report** a short table per pair: `severity · summary · code ref · doc ref · suggested fix`, then a one-line
   verdict (✓ in agreement / ⚠ N findings). Quote the conflicting code + doc as evidence. The fix can go
   **either direction** — update the spec to match the code, or the code to match the spec — whichever is the
   intended behaviour. When you're co-authoring both, that's a call you make on the spot.

<!-- KEEP IN SYNC: this rubric mirrors `spec_eval/rubric.py` (DRIFT_RUBRIC) — same severity tiers, same
     do-not-flag list. If the principles change in one place, change both;
     `tests/contract/test_rubric_sync.py` asserts the load-bearing phrases match. -->
## The agreement rubric (apply strictly)
A finding = the code does X but the doc/spec claims Y (or vice versa). Severity is **reserved**:
- **high** — the doc states a MEASURABLE GUARANTEE the code breaks: a numeric value/threshold/default that
  disagrees with code, an explicit signature, a named event/message, a CLI flag default, or a violated
  invariant/acceptance criterion. If you must paraphrase the doc to see the violation, it is **not** high.
- **medium** — misleading but not load-bearing: a renamed function that still does the same thing, a stale
  example, a field in code missing from a spec table, mechanism described differently.
- **low** — cosmetic / trivially-fixable wording.

**Do NOT flag:** stylistic differences; trivial restatements; missing-but-implied behaviour where a doc could
plausibly be silent (**silence is not drift**); a doc describing a **broader system** of which this file is one
part (**scope is not drift**); comments inside code that disagree with each other (only code-vs-doc); drift you
can only verify by **running** the code.

**Prefer false negatives over false positives.** An empty result ("✓ in agreement") is a perfectly valid answer.

## Honesty (the load-bearing part)
Report only **real, defensible** disagreements, with the evidence quoted. If you are unsure a finding is real,
**stay quiet** rather than over-flag — a noisy check gets ignored, which is worse than no check. This is a
single-model check with no second opinion, so be conservative; for high-stakes or ambiguous calls, recommend a
cross-vendor review as the next step.

## System context reconciliation (when an overview has a `## System context` section)
An `OVERVIEW.md` is a conventional doc, so it is **not** one of the code↔spec pairs above — its System context
table (the external systems the code talks to) would otherwise go unchecked. When the tree you're checking has
an overview or README with a `## System context` section, reconcile it against the deterministic scanner: run
`spec-eval context <dir>` (or read an existing `spec-reports/system-context.json`) and compare the observed
systems to the table's rows. The **containment contract** sets the direction — the scanner is the floor, the
author's reading is the ceiling — so the severity is **asymmetric**:

- **high** — a table row whose cited `file:line` evidence does not exist or does not show that system. Fabricated
  or stale evidence breaks the one promise the table makes (every row is verifiable against the code).
- **medium** — a system the scanner observes that is **missing** from the table. The table under-reports; the
  scanner is the floor and the table must include every system it reports.
- **not a finding** — a table row the scanner does **not** observe but that carries valid cited `file:line`
  evidence (the author legitimately saw something the tables miss — an internal wrapper SDK, a niche vendor);
  the table may exceed the scan, never fall short of it.

Also check freshness: if the overview carries a `<!-- system-context-fingerprint: … -->` stamp and
`spec-eval context --check` reports it stale (or the stamp's digest no longer matches a fresh scan), note that
the overview needs regenerating — a **medium** staleness finding, fixable by `generate --overview`, not by hand.

## Save the results as files (optional)
<!-- KEEP IN SYNC: the report filenames below mirror the CLI's outputs (spec_eval/cli.py writes coverage.md /
     report.md / sufficiency.md); tests/contract/test_caps_sync.py pins them so a rename can't silently diverge.
     SPEC-HEALTH.md is authored here / by hand, not by the CLI. -->
By default this check reports **in the chat**. If the user asks to **save** or **write** the results (e.g.
*"…and save the results to `spec-reports/`"*), also mirror the run into a `spec-reports/` folder so it leaves
durable, reviewable receipts — the same files the `spec-eval` CLI produces:

- `spec-reports/coverage.md` — which spec-worthy code files have a governing spec, and which don't.
- `spec-reports/report.md` — the drift findings (per pair: `severity · summary · code ref · doc ref · fix`),
  with the conflicting code and doc quoted as evidence.
- `spec-reports/sufficiency.md` *(only if the user also wants a completeness score)* — a `0.0–1.0` score per
  pair answering *"could a developer rebuild this behavior from the spec alone?"*, worst pair first, listing the
  missing behaviors (each pointing at `file.py (symbol)`).
- `spec-reports/SPEC-HEALTH.md` — a dated one-page rollup of coverage / drift / sufficiency at a glance. This is
  also the project's **standing scorecard**: if one already exists, refresh the scores and date but **preserve
  the human-written verdict and run-history rows** (append a row — never clobber them).

Two rules for writing these:
- **State the honesty caveat in the files, not just the chat** — they are a single-model read, dated; the exact,
  deterministic coverage % and an append-only run history come from the `spec-eval` CLI.
- **Only ever write under `spec-reports/`** — never edit a spec or any source file to "fix" a finding unless the
  user explicitly asks; the fix direction is theirs to choose.
