"""Spec AUTHORING — generate intent-led specs from code.

The generator that pairs with the drift/sufficiency checkers: point it at a repo and, for each spec-worthy code
file with no governing spec yet, author a spec. The layout is chosen by config (`authoring.layout`):

  per-file (default) — one spec BESIDE each code file (`src/x.py` -> `src/x.md`).
  per-dir            — one spec per directory (`src/parser/*.py` -> `src/parser/parser.md`), synthesised from the
                       per-module intents (map -> reduce) so a big folder never blows the char cap.
  per-pair           — author the `docs` file of each explicit config pair from its `code` glob.

An optional `authoring.overview` (none | repo | per-dir | both) adds a navigation index (a repo-level
`OVERVIEW.md` and/or a per-directory `README.md`) that links down to the specs the layout produced. Each
overview call is fed the deterministic system-context scan (`syscontext.py`), so the index's '## System
context' section can only carry OBSERVED external systems — none observed, no section. The built-in
per-module rubric can be swapped with `authoring.template`; the built-in authoring DISCIPLINE is always appended
so a swapped template still yields specs the drift/sufficiency checkers can grade.

Nothing is ever clobbered: a target that already has a file is skipped (no model call) unless `overwrite`.
Authored specs are ordinary new files in the working tree — review them like code (`git diff`) and drop any you
don't want (`git checkout --`). See skills/spec-authoring/SKILL.md.
"""
import os
import re
import glob
from . import providers, audit, coverage as coverage_mod, syscontext

# The built-in rubric is split so a custom template can replace the STRUCTURE while the authoring DISCIPLINE
# (the quality rules the checkers rely on) is always applied.
# KEEP IN SYNC: `skills/spec-authoring/SKILL.md` carries the agent-session copy of this rubric, and the shipped
# templates (`skills/spec-authoring/templates/spec-template.md`, `configs/spec-template.example.md`) carry its
# skeleton markers — `tests/contract/test_rubric_sync.py` pins the shared load-bearing phrases so a change to
# one copy without the others fails loudly. (`templates/OVERVIEW-template.md` is the skill's richer
# project-overview; it is the SOURCE OF TRUTH for which sections the repo-level OVERVIEW carries —
# `tests/contract/test_overview_sections_sync.py` pins REPO_OVERVIEW_RUBRIC below to the template's exact
# section set and order — though the two are not otherwise verbatim copies.)
AUTHORING_STRUCTURE = (
    "You author an INTENT-LED specification (markdown) for ONE code module. A reviewer must be able to grasp the "
    "full intent and contract from the spec ALONE. Follow this structure and these rules exactly:\n"
    "- '## 1. Purpose' — open with a bold one-liner: '**In one line:** <the capability in <=20 words>'. Then 1-2 "
    "sentences of WHAT + WHY, before any type or signature, and the governing constraint stated DIRECTLY as a "
    "checkable consequence (e.g. 'decode(encode(x)) == x for all UTF-8 input') — never as meta-phrasing like "
    "'the one governing constraint a reviewer can check'.\n"
    "- '## 2. Definitions' — a short table of the domain vocabulary (term -> meaning, with bounds/units).\n"
    "- '## 3. Behavior' — EXPLANATION ONLY: the rules / modes / flows over that vocabulary; NOT a per-method "
    "walkthrough. Do NOT inline exhaustive reference material (full option/enum sets, every directory or "
    "extension name, complete rule tables) mid-rule — put it in a §4 table or a §2 term and reference it by "
    "name. When behavior enumerates 3+ cases / conditions / branches, write a bulleted list or a table — never "
    "a comma/semicolon chain. Attach a one-line '**Why:**' ONLY where the rationale is non-obvious or "
    "load-bearing — an obvious Why is padding (confidence-tagged '> Reconstructed intent' rationale always "
    "stays). Load-bearing BEHAVIORS (e.g. generation/sampling policy, weight-loading, "
    "optimizer/decay policy, defaults, error semantics) ARE behavior — specify them; do NOT drop them as 'detail'.\n"
    "- '## 4. Contracts' (REFERENCE, demoted to the end) — open the section with the italic line "
    "'*Reference — consult when implementing or reviewing a change; skip on a first read for intent.*': "
    "SEMANTIC shapes (e.g. `(B, T, vocab)`) with meaning and "
    "bounds — NOT language types; a table headed '### Invariants (*rules that must always hold*)' with IDs "
    "INV-1.. — assert an INV ONLY if the code ENFORCES it (an assert / clamp / validation / raised error); do NOT "
    "state a plausible-but-unenforced range or property, that is drift not an invariant. A table headed "
    "'### Acceptance criteria (*Given / When / Then*)' with IDs AC-1.. and concrete numbers.\n"
)
AUTHORING_DISCIPLINE = (
    "RULES: Organize headings by CAPABILITY, never by the function/symbol tree. NEVER make a function signature or "
    "a language type a heading. DROP code trivia (empty-input errors, slicing tricks, a bare except, 'no caching "
    "in that branch'). DESCRIBE what a capability IS and does — never define it by what it ISN'T ('not a X', "
    "'unlike Y'); state it on its own terms. SENTENCE DISCIPLINE: one idea per sentence; split any sentence past "
    "~30 words; at most "
    "one dash-aside or parenthetical per sentence; no nested parentheses. RIGHT-SIZE to the module: collapse to "
    "one sentence — or omit — any section that would carry <=1 real row; empty scaffolding and N/A rows are "
    "noise, not rigor (a small utility module gets a short spec). Every table row must be FILLED — never emit an "
    "empty INV-*/AC- row; omit an id rather than "
    "leave it blank. LABEL any inferred rationale not determinable from the code alone: "
    "'> Reconstructed intent (confidence: low/med/high) — inferred from the code.'\n"
    "Output ONLY the finished markdown document — no preamble, no title-line meta-note about sources of truth, "
    "and do NOT wrap the whole document in a code fence."
)
AUTHORING_RUBRIC = AUTHORING_STRUCTURE + AUTHORING_DISCIPLINE   # built-in default (per-module authoring)

# Synthesis (reduce) rubrics: fed the per-module INTENT SPECS, never the raw code, so a whole directory's specs
# fit under the cap where the raw code would not.
FOLDER_SPEC_RUBRIC = (
    "You author ONE intent-led specification for a whole DIRECTORY, given the intent specs of the modules it "
    "contains. The reader has ONLY this file (the per-module specs may not exist), so make it SELF-CONTAINED:\n"
    "- '## 1. Purpose' — what capability this directory provides as a unit, and why.\n"
    "- '## 2. Modules' — a table: module -> its one-line responsibility (summarise inline).\n"
    "- '## 3. How it fits together' — the data / control flow across these modules, in prose.\n"
    "- '## 4. Shared contract' — invariants and definitions that span modules (cross-module only; do not restate "
    "every per-module detail).\n"
    + AUTHORING_DISCIPLINE
)
# The System-context section instruction — SINGLE-SOURCED so the repo and per-dir overview rubrics carry the
# SAME honesty rules (rows only from observed evidence, unknowable cells say so, never invent a row). Pinned by
# tests/contract/test_rubric_sync.py against the skill + template + scanner; splitting it into one constant keeps
# the two rubrics below from drifting the honesty phrases apart.
_OV_SYSTEM_CONTEXT = (
    "- '## System context' — ONLY when the input carries an 'OBSERVED SYSTEM EVIDENCE' block: a table "
    "'| External system | Direction | What flows | Evidence |' with one row per listed system, keeping the "
    "block's order. NEVER invent a row or add a system the block does not list. 'What flows' is the "
    "domain-level payload inferred from the module intents; when the intents do not say, write 'unknown from "
    "this repo'. Copy each row's evidence reference (file:line) from the block verbatim. Close the section "
    "with the fixed line: '> Derived from this repository's code — rows are evidence of capability in the "
    "code, not proof of runtime traffic. Inbound callers and partner-system behavior "
    "are not observable from this repo — confirm asserted context with the owning teams.' When there is no "
    "evidence block, OMIT the section entirely. If the block ends with a 'Not scanned:' line, reproduce that "
    "line verbatim beneath the table — a language gap must stay visible. These System-context rules take "
    "precedence over the general "
    "RULES below: while an evidence block is present, render the full table even if it carries a single row — "
    "an evidence-backed row is a real row, and 'unknown from this repo' is a filled cell, not an N/A; never "
    "right-size this section away.\n"
)

# The module-map imperative — the canonical one-liner is COPIED verbatim, never paraphrased. Shared by the
# per-dir '## Map' and the repo '## Module map' so the anti-drift rule can't be lost in the rename.
_OV_MODULE_MAP_IMPERATIVE = (
    "a table linking each module's spec (by its given path) to its one-line purpose. REUSE that "
    "spec's '**In one line:**' sentence VERBATIM as the purpose — it is the canonical one-liner; copy it, do "
    "not paraphrase (a paraphrase is a second version that drifts). If a spec has no such line, write one short "
    "line.\n"
)

# KEEP IN SYNC: DIR_OVERVIEW_RUBRIC (per-directory README) is the LEAN index — the legacy 4-section set, and it
# NEVER carries the Architecture diagram. REPO_OVERVIEW_RUBRIC (the repo-root OVERVIEW.md) is the FULL project
# overview whose section set is pinned to templates/OVERVIEW-template.md. Both include _OV_SYSTEM_CONTEXT.
DIR_OVERVIEW_RUBRIC = (
    "You author a navigation OVERVIEW for a set of modules, given each module's intent spec and its spec path. "
    "This is an INDEX a reader orients from before opening any module — not a restatement:\n"
    "- '## Map' — " + _OV_MODULE_MAP_IMPERATIVE +
    "- '## How it fits together' — the flow across these modules, in prose.\n"
    "- '## Shared contract' — only invariants / definitions that span modules; DEFER all module detail to the "
    "linked specs, never restate them.\n"
    + _OV_SYSTEM_CONTEXT
    + AUTHORING_DISCIPLINE
)

# The Architecture (data flow) section instruction — TWO scanner-fed Mermaid diagrams (an invocation sequence
# and a pure data-flow pipeline: the arc42/C4 static-vs-runtime split, so each diagram answers ONE question).
# ONLY the repo overview embeds it, so a per-dir README can never emit a diagram (repo-only by construction).
# Shared verbatim with the `diagram` subcommand's diagram-only rubric; its load-bearing phrases are pinned
# across the skill + template by tests/contract/test_rubric_sync.py (DIAGRAM_LOAD_BEARING).
ARCH_DIAGRAM_RUBRIC = (
    "- '## Architecture (data flow)' — TWO mermaid diagrams, each answering one question, in this order:\n"
    "  (a) '### How it is invoked' — a fenced sequenceDiagram: `actor U as User` plus at most 5 participants — "
    "every entry in the OBSERVED ENTRY POINTS block, plus (only when the module intents name them) the "
    "conventional entry scripts and the config loader. Depict the PRIMARY end-to-end workflow a user runs — "
    "not just the first step: for a multi-stage pipeline draw the whole run path (e.g. prepare -> train -> "
    "sample/serve), one message per stage's main entry script, and INCLUDE the primary run/serve entry even "
    "when it is a conventional (not scanner-detected) invocation — the scanner floor is a minimum, not the "
    "whole story. At most 10 messages; each workflow starts with its "
    "literal shell command as the message text; a dashed reply (-->>) only for an artifact returned to the "
    "user. Every scanner entry MUST carry 'Note over X: scanner-verified entry point (file:line)'; an "
    "invocation the block does NOT list may appear ONLY with 'Note over X: conventional invocation (per the "
    "module intents, not scanner-detected)' — NEVER present an unscanned invocation as verified, and never "
    "invent a call order the intents do not state. No block and no documented invocation -> omit (a).\n"
    "  (b) '### Data flow' — a fenced `flowchart LR` of the producer->consumer pipeline ONLY: sources left, "
    "outputs right. It MUST span the FULL pipeline end to end — from the source nodes to the terminal OUTPUT "
    "node: the USER-FACING RESULT the invocation diagram (a) shows the User receiving (generated samples, a "
    "served response, a written report). If (a) shows a run/sample/serve step producing that result by "
    "consuming a pipeline artifact, that producing script AND its output node MUST appear here too — an "
    "intermediate artifact (a checkpoint, an index, a cache) is NOT the terminal output when a later stage "
    "consumes it to make the user's result. NEVER truncate before that final output; the terminal output node "
    "is mandatory and (a) and (b) must agree on it. NO entry-points cluster and NO CLI/config/loader nodes — "
    "invocation lives in (a). External "
    "systems come ONLY from the OBSERVED SYSTEM EVIDENCE block, at the boundary, joined by dashed -.-> edges "
    "labeled with the transfer; NEVER invent one. BUDGET: at most 12 nodes and 18 edges (subgraph containers "
    "don't count). The terminal produce-the-result stage is PROTECTED — when over budget, make room by folding "
    "UPSTREAM/intermediate detail FIRST, in this order: merge same-role sibling sources/artifacts into one node "
    "labeled 'Role<br/>glob-path', then merge an artifact into its sole producer, then drop only nodes NOT on "
    "any source-to-output path (e.g. a profiler/benchmark). Fold intermediate stages before ever touching the "
    "final stage; NEVER drop the produce-the-result step to keep upstream detail, and never meet the "
    "budget by shrinking labels. State each folded fact in a one-line note under the diagram. Group into 2-5 "
    "lifecycle-stage subgraphs (subgraph id[\"Label\"] ... end), "
    "each styled stroke-only (style id fill:none,stroke:#94a3b8,stroke-dasharray:4 4); never a `direction` "
    "statement inside a subgraph. SHAPES: stadium ([\"...\"]) = invocation surface, rect = runnable script, "
    "[[\"...\"]] = imported library, [(\"...\")] = data artifact, [/\"...\"/] = external system or terminal "
    "output. COLOR: exactly these classDefs, applied with ::: to every node — each sets fill+stroke+color "
    "together so GitHub's dark mode cannot break contrast; no theme, no %%{init}%%, no linkStyle: "
    "classDef process fill:#dbeafe,stroke:#2563eb,color:#1e3a5f; "
    "classDef artifact fill:#fef9c3,stroke:#ca8a04,color:#713f12; "
    "classDef external fill:#fae8ff,stroke:#9333ea,color:#581c87. "
    "EDGES: solid --> = produces/consumes, -.-> = network or optional, exactly one ==> chain marking the "
    "primary pipeline; label at most a third of edges with a 1-2 word verb; never draw an edge implied by "
    "transitivity. Node labels: a role noun phrase, then the bare file path after <br/> — never line numbers "
    "or mechanics in a label.\n"
    "  Close the section with EXACTLY this one-sentence caveat line, verbatim, with nothing appended: '> The "
    "invocation entries and external systems are scanner-derived (file:line-observed) where noted; the "
    "internal edges are inferred from the module intents, not verified against a call graph.' It states "
    "provenance and nothing else — never restate it in other words, never append regeneration or stamp "
    "mechanics, and never fold a budget-driven omission into it; those go in the SEPARATE one-line note.\n"
)
REPO_OVERVIEW_RUBRIC = (
    "You author the repository-level project OVERVIEW — the page a newcomer reads to understand the whole "
    "project before opening any spec, given each module's intent spec and its spec path. It is an INDEX that "
    "points, never a restatement. Emit these sections in THIS ORDER, using these EXACT headings:\n"
    "- '## What it is' — in 2-4 sentences, what the project does, its core job, and what it optimizes for "
    "(clarity, speed, fidelity), so a newcomer grasps the point before opening any spec.\n"
    "- '## Governing principles' — the intent root: the few 'why' principles the whole spec-set serves, each a "
    "bolded one-liner. Fold in only cross-module invariants that govern the whole set; DEFER per-module detail "
    "to the linked specs.\n"
    + ARCH_DIAGRAM_RUBRIC
    + _OV_SYSTEM_CONTEXT
    + "- '## Module map' — " + _OV_MODULE_MAP_IMPERATIVE +
    "- '## Glossary' — plain-English one-liners for the project's domain terms, each pointing to its defining "
    "spec section. Omit the section if the project carries no cross-module vocabulary worth a newcomer's "
    "glance.\n"
    "- '## Health receipt' — a fixed pointer, no scores on this page: the spec-set trust signal (coverage / "
    "drift / sufficiency, dated and SHA-pinned) lives in SPEC-HEALTH.md.\n"
    "- '## Reading order' — the path through the set: this overview, then the module specs, then SPEC-HEALTH.md "
    "to confirm the specs still match the code.\n"
    + AUTHORING_DISCIPLINE
)

REDUCE_CAP = 48000   # char budget for the per-module intents concatenated into one synthesis (reduce) call;
                     # ~8 real intents (~6k chars each) = p85-p90 directory fan-out in a single pass, with the
                     # recursion below absorbing larger folders at depth ~2 (widen fan-in, don't deepen the tree)
_MAX_LEVELS = 4      # recursion bound for multi-pass synthesis; past it, remaining items are force-fitted
AUTHOR_MAX_TOKENS = 5000   # output-token budget for authoring a spec (map or synthesis) — one source for all four call sites


def _rubric(template_path):
    """The per-module authoring instruction: the built-in structure, or a custom template file. The built-in
    DISCIPLINE is always appended so a swapped template still yields specs the checkers can grade."""
    if template_path:
        return open(template_path).read().strip() + "\n\n" + AUTHORING_DISCIPLINE
    return AUTHORING_RUBRIC


def _unfence(md):
    """Strip an accidental outer ``` fence so the written .md is raw markdown."""
    md = md.strip()
    if md.startswith("```"):
        md = md.split("\n", 1)[1] if "\n" in md else md
        if md.rstrip().endswith("```"):
            md = md.rstrip()[:-3].rstrip()
    return md


def spec_path_for(code_path):
    """Co-located per-file spec path: the .md beside the code file (`src/x.py` -> `src/x.md`)."""
    base, _ = os.path.splitext(code_path)
    return base + ".md"


def author_file(repo, code_path, model, rubric=AUTHORING_RUBRIC, code_cap=None):
    """Author (map) an intent-led spec markdown for a single code file (path relative to `repo`).
    Returns (markdown, note|None) — the note flags a partial view: code input over the cap, or a model reply
    cut off at the token cap (either can silently produce a spec that ends mid-section)."""
    code_cap = audit.CODE_CAP if code_cap is None else code_cap
    raw = open(os.path.join(repo, code_path), errors="ignore").read()
    code = raw[:code_cap]
    stem = os.path.splitext(os.path.basename(code_path))[0]
    user = f"# Author a spec for module `{stem}`\n\n## Code (`{code_path}`)\n```\n{code}\n```\n"
    md = _unfence(providers.gen(model, rubric, user, max_tokens=AUTHOR_MAX_TOKENS))
    notes = ([f"code input capped at ~{code_cap:,} chars — authored from a partial view"]
             if len(raw) > code_cap else []) \
        + (["reply hit the token cap — the spec may end mid-section"] if providers.LAST["truncated"] else [])
    return md, ("; ".join(notes) or None)


def _pack(items, cap):
    """Group (label, intent-md) items into consecutive groups whose rendered blocks each fit under `cap`.
    A single block larger than `cap` is sliced to fit (with a marker) so packing always terminates."""
    groups, cur, used = [], [], 0
    for label, md in items:
        block = f"### {label}\n{(md or '').strip()}\n"
        if len(block) > cap:
            block = block[:cap] + "\n...[truncated]"           # a lone oversized intent: slice, never loop
        if cur and used + len(block) > cap:
            groups.append(cur)
            cur, used = [], 0
        cur.append((label, block))
        used += len(block)
    if cur:
        groups.append(cur)
    return groups


def _synthesize(model, rubric, items, header, on_progress=None, _level=1, reduce_cap=None, extra=None, unfence=True):
    """Reduce: synthesise (label, intent-markdown) modules into one document. Returns
    (markdown, levels, reply_capped). When the concatenated intents exceed the reduce cap, the items are packed
    into sub-groups, each sub-group is synthesised into an intermediate intent, and the intermediates are
    reduced in turn (recursively) — modules are NEVER dropped. `levels` counts the stacked synthesis passes
    (1 = a single call); `reply_capped` is True when ANY pass's reply hit the token cap.
    `extra` is an optional evidence block appended to the FINAL call's user message only (intermediate passes
    summarise modules; the final pass is the one that renders sections from it).
    Termination is guaranteed: past _MAX_LEVELS, or when a pass stops reducing the item count, the remaining
    items are force-fitted into one final call (each sliced to an equal share of the cap, visibly marked)."""
    cap = REDUCE_CAP if reduce_cap is None else reduce_cap
    finish = _unfence if unfence else (lambda s: s.strip())     # a mermaid diagram keeps its ```mermaid fence
    tail = f"\n\n{extra}" if extra else ""
    if not items:                                               # nothing to synthesise — no model call, no div-by-zero
        return "", _level, False
    groups = _pack(items, cap)
    if len(groups) == 1:
        user = f"# {header}\n\n" + "\n".join(block for _, block in groups[0]) + tail
        md = finish(providers.gen(model, rubric, user, max_tokens=AUTHOR_MAX_TOKENS))
        return md, _level, providers.LAST["truncated"]
    if _level >= _MAX_LEVELS or (_level > 1 and len(groups) >= len(items)):
        share = max(200, cap // len(items) - 40)
        blocks = [f"### {label}\n{(md or '').strip()[:share]}\n...[truncated]\n" for label, md in items]
        user = f"# {header}\n\n" + "\n".join(blocks) + tail
        md = finish(providers.gen(model, rubric, user, max_tokens=AUTHOR_MAX_TOKENS))
        return md, _level, providers.LAST["truncated"]
    intermediates, capped = [], False
    for i, group in enumerate(groups, 1):
        if on_progress:
            on_progress(f"· synthesis pass {_level}: group {i}/{len(groups)} ({len(group)} modules)")
        user = f"# {header} (part {i}/{len(groups)})\n\n" + "\n".join(block for _, block in group)
        gmd = finish(providers.gen(model, rubric, user, max_tokens=AUTHOR_MAX_TOKENS))
        capped = capped or providers.LAST["truncated"]
        intermediates.append((f"{group[0][0]} … {group[-1][0]}", gmd))
    md, levels, sub_capped = _synthesize(model, rubric, intermediates, header, on_progress, _level + 1, cap, extra,
                                         unfence=unfence)
    return md, levels, capped or sub_capped


def _layout_targets(repo, files, layout, dir_spec_name, config):
    """Group spec-worthy code files into {spec_path: [code files]} per the layout."""
    if layout == "per-file":
        return {spec_path_for(f): [f] for f in files}
    if layout == "per-dir":
        repo_name = os.path.basename(os.path.abspath(repo))
        groups = {}
        for f in files:
            groups.setdefault(coverage_mod.dir_spec_path(f, repo_name, dir_spec_name), []).append(f)
        return {sp: sorted(fs) for sp, fs in groups.items()}
    if layout == "per-pair":
        groups = {}
        for p in config.get("pairs", []):
            doc = (p.get("docs") or [None])[0]
            if not doc:
                continue
            cfs = []
            for pat in p.get("code", []):
                for m in glob.glob(os.path.join(repo, pat), recursive=True):
                    if os.path.isfile(m):
                        cfs.append(os.path.relpath(m, repo))
            if cfs:
                groups.setdefault(doc, []).extend(sorted(set(cfs)))
        return {sp: sorted(set(fs)) for sp, fs in groups.items()}
    raise ValueError(f"unknown layout '{layout}' (use per-file | per-dir | per-pair)")


def generate_repo(repo, config, model, overwrite=False, on_progress=None):
    """Author specs for a repo per the `authoring` config. Returns a list of {code, spec, status[, note]}.

    `authoring.layout` (per-file | per-dir | per-pair) sets the spec granularity; `authoring.overview`
    (none | repo | per-dir | both) adds a navigation index; `authoring.template` swaps the per-module rubric.
    Existing files are skipped (no model call) unless `overwrite` — review the written specs via version control.
    """
    authoring = config.get("authoring", {})
    layout = authoring.get("layout", "per-file")
    dir_spec_name = authoring.get("dir_spec_name", "<dir>")
    overview = authoring.get("overview", "none")
    overview_min_files = int(authoring.get("overview_min_files", 2))
    rubric = _rubric(authoring.get("template"))
    code_cap, _ = audit.caps_from(config)                                # caps: {code, docs, reduce} — config-overridable
    reduce_cap = int((config.get("caps") or {}).get("reduce", REDUCE_CAP))

    cov = coverage_mod.coverage(repo, config)
    files = sorted(cov["covered"] + cov["uncovered"])          # all spec-worthy code files
    targets = _layout_targets(repo, files, layout, dir_spec_name, config)

    results = []
    _intent = {}                                               # code_path -> per-module intent (reused across reduces)

    def module_intent(code_path):
        return _module_intent(repo, code_path, model, rubric, code_cap, _intent, on_progress)

    def target_md(spec_path, code_files):
        dest = os.path.join(repo, spec_path)
        if os.path.exists(dest):
            return open(dest, errors="ignore").read()
        if len(code_files) == 1:
            return module_intent(code_files[0])
        md, _, _ = _synthesize(model, FOLDER_SPEC_RUBRIC,               # INV-4: synthesise, never silently slice
                               [(f, module_intent(f)) for f in code_files],
                               f"Modules in `{os.path.dirname(spec_path) or '.'}`", on_progress,
                               reduce_cap=reduce_cap)
        return md

    def emit(spec_path, code_ref, make_md, label):
        """Skip-existing / write, uniformly for specs and overviews. make_md() -> (markdown, note|None), and is
        called only when a file is actually going to be written (never on a skip)."""
        dest = os.path.join(repo, spec_path)
        if os.path.exists(dest) and not overwrite:
            results.append({"code": code_ref, "spec": spec_path, "status": "skipped"})
            return
        if on_progress:
            on_progress(label)
        md, note = make_md()
        rec = {"code": code_ref, "spec": spec_path, "status": "authored"}
        if note:
            rec["note"] = note
        os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
        open(dest, "w").write(md.rstrip() + "\n")
        results.append(rec)

    def _cap_notes(*parts):
        """Join shortfall notes (drop counts, token-cap flags) into one note string, or None."""
        joined = "; ".join(p for p in parts if p)
        return joined or None

    # 1. Specs — map (single file) or map -> reduce (a directory / pair of files).
    for spec_path, code_files in sorted(targets.items()):
        if len(code_files) == 1:
            code_ref, cf = code_files[0], code_files[0]
            emit(spec_path, code_ref, lambda cf=cf: author_file(repo, cf, model, rubric, code_cap),
                 f"authoring {spec_path}")
        else:
            code_ref = os.path.dirname(spec_path) or "."

            def _folder(sp=spec_path, cfs=code_files):
                md, levels, reply_capped = _synthesize(model, FOLDER_SPEC_RUBRIC,
                                                       [(f, module_intent(f)) for f in cfs],
                                                       f"Modules in `{os.path.dirname(sp) or '.'}`", on_progress,
                                                       reduce_cap=reduce_cap)
                return md, _cap_notes(
                    (f"synthesised in {levels} passes from all {len(cfs)} modules "
                     f"(nothing dropped)") if levels > 1 else None,
                    "reply hit the token cap — the spec may end mid-section" if reply_capped else None)
            emit(spec_path, code_ref, _folder, f"authoring {spec_path} ({len(code_files)} modules)")

    # 2. Overview layer — an index that links down to the specs the layout produced (runs after every spec exists).
    # A deterministic system-context scan (free, no model call) feeds each overview call its OBSERVED SYSTEM
    # EVIDENCE, so the '## System context' section can only ever carry observed, file:line-backed entries.
    ctx = syscontext.scan(repo, config) if overview != "none" else None
    if overview in ("repo", "both"):
        def _repo_overview():
            block = syscontext.evidence_block(ctx) or None
            ep = syscontext.scan_entrypoints(repo, config)               # how the repo is invoked (deterministic)
            ep_block = syscontext.entrypoints_block(ep) or None
            extra = "\n\n".join(b for b in (ep_block, block) if b) or None   # both reach the final synthesis pass
            items = [(sp, target_md(sp, cf)) for sp, cf in sorted(targets.items())]
            md, levels, reply_capped = _synthesize(model, REPO_OVERVIEW_RUBRIC, items, "Repository overview",
                                                   on_progress, reduce_cap=reduce_cap, extra=extra)
            if block:            # stamp the fingerprint this System context section was rendered from, so a
                md = md.rstrip() + "\n\n" + syscontext.stamp_comment(ctx)   # later `--check` can flag staleness
            md = md.rstrip() + "\n\n" + syscontext.architecture_stamp_comment(ctx, ep, files)
            return md, _cap_notes(
                f"index synthesised in {levels} passes over all {len(items)} specs (nothing dropped)" if levels > 1 else None,
                "reply hit the token cap — the index may end mid-section" if reply_capped else None)
        emit("OVERVIEW.md", ".", _repo_overview, f"authoring OVERVIEW.md (index over {len(targets)} spec(s))")

    if overview in ("per-dir", "both"):
        by_dir = {}
        for f in files:
            by_dir.setdefault(os.path.dirname(f), []).append(f)
        for d, dfiles in sorted(by_dir.items()):
            readme = os.path.join(d, "README.md")
            if len(dfiles) < overview_min_files:               # only index directories with at least
                results.append({"code": d or ".", "spec": readme, "status": "skipped",   # min_files modules —
                                "note": f"below overview_min_files ({len(dfiles)} < {overview_min_files})"})
                continue                                       # recorded, never silently omitted
            dtargets = {tp: cf for tp, cf in targets.items() if os.path.dirname(tp) == d}

            def _dir_overview(dtargets=dtargets, d=d):
                items = [(tp, target_md(tp, cf)) for tp, cf in sorted(dtargets.items())]
                md, levels, reply_capped = _synthesize(model, DIR_OVERVIEW_RUBRIC, items,
                                                       f"Directory overview — `{d or '.'}`", on_progress,
                                                       reduce_cap=reduce_cap,
                                                       extra=syscontext.evidence_block(ctx, scope_dir=d) or None)
                return md, _cap_notes(
                    f"index synthesised in {levels} passes (nothing dropped)" if levels > 1 else None,
                    "reply hit the token cap — the index may end mid-section" if reply_capped else None)
            emit(readme, d or ".", _dir_overview, f"authoring {readme} (index)")

    return results


# --- on-demand architecture diagram (the `diagram` subcommand) -----------------------------------------------
# The diagram-only rubric reuses ARCH_DIAGRAM_RUBRIC verbatim, then narrows the output to just the mermaid block
# + its caveat (no heading, no other prose) so the block is pasteable / redirectable and slots into an existing
# '## Architecture (data flow)' section.
ARCH_DIAGRAM_ONLY_RUBRIC = (
    ARCH_DIAGRAM_RUBRIC +
    "OUTPUT ONLY the Architecture section body: the two '###' subsections with their fenced ```mermaid blocks "
    "and the closing '>' caveat line — do not emit the section heading itself, and no other prose before or "
    "after.\n"
)


def _module_intent(repo, code_path, model, rubric, code_cap, cache=None, on_progress=None):
    """The per-module intent — reuse an existing co-located `<stem>.md` if present, else author it IN MEMORY via
    `author_file` WITHOUT writing (an intermediate for a folder spec, an overview, or a diagram). `cache` is an
    optional `code_path -> intent` dict reused across a run so a module is authored at most once."""
    if cache is not None and code_path in cache:
        return cache[code_path]
    colo = os.path.join(repo, spec_path_for(code_path))
    if os.path.exists(colo):
        intent = open(colo, errors="ignore").read()              # reuse the existing per-file spec
    else:
        if on_progress:
            on_progress(f"· module {code_path}")                 # each map call is a model round-trip
        intent = author_file(repo, code_path, model, rubric, code_cap)[0]   # intermediate — not written to disk
    if cache is not None:
        cache[code_path] = intent
    return intent


def module_set(repo, config):
    """The sorted code-file identifiers the architecture diagram is drawn over — the SAME set `generate`,
    `diagram`, and `context --check` stamp/compare with, so the architecture fingerprint is consistent across
    all three. Coverage's spec-worthy files (covered + uncovered)."""
    cov = coverage_mod.coverage(os.path.abspath(repo), config)
    return sorted(cov["covered"] + cov["uncovered"])


def diagram_block(repo, config, model, on_progress=None):
    """Build the repo's Architecture section body — the invocation sequenceDiagram + the data-flow pipeline —
    for the `diagram` subcommand. Reads existing specs; derives any MISSING module intent in memory and writes
    nothing. Returns `(section_body_markdown, ctx, ep, modules)` — the two fenced diagrams plus the two scans
    and the module set it is stamped from."""
    repo = os.path.abspath(repo)
    rubric = _rubric(config.get("authoring", {}).get("template"))
    code_cap, _ = audit.caps_from(config)
    reduce_cap = int((config.get("caps") or {}).get("reduce", REDUCE_CAP))
    modules = module_set(repo, config)
    cache = {}
    items = [(f, _module_intent(repo, f, model, rubric, code_cap, cache, on_progress)) for f in modules]
    ctx = syscontext.scan(repo, config)
    ep = syscontext.scan_entrypoints(repo, config)
    extra = "\n\n".join(b for b in (syscontext.entrypoints_block(ep) or None,
                                    syscontext.evidence_block(ctx) or None) if b) or None
    md, _, _ = _synthesize(model, ARCH_DIAGRAM_ONLY_RUBRIC, items, "Architecture diagram",
                           on_progress, reduce_cap=reduce_cap, extra=extra, unfence=False)  # keep the ```mermaid fence
    return md.strip(), ctx, ep, modules


_ARCH_HEADING_RE = re.compile(r"^##\s+Architecture \(data flow\)")
_MD_HEADING_RE = re.compile(r"^#{1,3}\s")
_MD_FENCE_RE = re.compile(r"^\s*(```|~~~)")
_STAMP_COMMENT_RE = re.compile(r"^\s*<!--\s*(?:system-context|architecture)-fingerprint:")


def _arch_heading_line(lines):
    """Index of the first '## Architecture (data flow)' heading at fence depth 0, or None — FENCE-AWARE, so a
    heading that sits inside a ``` code block (an example) is not the section."""
    in_fence = False
    for i, ln in enumerate(lines):
        if _MD_FENCE_RE.match(ln):
            in_fence = not in_fence
        elif not in_fence and _ARCH_HEADING_RE.match(ln):
            return i
    return None


def has_architecture_section(markdown):
    """True when the document already carries an (unfenced) '## Architecture (data flow)' section. The cheap
    precondition the `diagram --write` path checks BEFORE synthesising, so a replace-only update on a doc that
    has no such section fails fast instead of burning model calls on a diagram it will refuse to write."""
    return _arch_heading_line(markdown.splitlines(keepends=True)) is not None


def set_architecture_section(markdown, body, create=False):
    """Replace the BODY of the existing '## Architecture (data flow)' section with `body` (the fenced mermaid
    block + caveat), keeping the heading line intact. REPLACE-ONLY by default: raises ValueError if the
    document has no such section. When `create` is set (an explicit caller opt-in), APPEND a new section to the
    end of the document instead of raising — the document must already exist; this never invents one.
    FENCE-AWARE: a heading that sits inside a ``` code block is not the section. STAMP-AWARE: the section body
    ends at the next heading OR the first trailing fingerprint receipt, so a diagram update never swallows the
    trailing system-context stamp (which would silently re-bless a stale System context table)."""
    lines = markdown.splitlines(keepends=True)
    start = _arch_heading_line(lines)
    if start is None:
        if not create:
            raise ValueError("no '## Architecture (data flow)' section")
        prefix = markdown.rstrip() + "\n\n" if markdown.strip() else ""      # append; deterministic, at the end
        return prefix + "## Architecture (data flow)\n" + body.strip() + "\n"
    end = len(lines)
    in_fence = False
    for j in range(start + 1, len(lines)):
        ln = lines[j]
        if _MD_FENCE_RE.match(ln):
            in_fence = not in_fence
        elif not in_fence and (_MD_HEADING_RE.match(ln) or _STAMP_COMMENT_RE.match(ln)):
            end = j
            break
    new_section = lines[start].rstrip("\n") + "\n" + body.strip() + "\n\n"
    return "".join(lines[:start]) + new_section + "".join(lines[end:])
