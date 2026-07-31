"""A fake `providers.gen` — returns canned output keyed on the rubric, so `drift` / `sufficiency` / `generate`
can be exercised with NO API key. Honors the shape each caller parses (findings JSON / sufficiency JSON /
intent-led markdown). Written for the Layer-2 acceptance tests and the Layer-4 e2e smoke.

ROUTING RULE: match each rubric on a phrase from its OPENING SENTENCE, which is unique by construction. Topic
words are a trap — every rubric talks about the others. 'drift' appears in the AUTHORING rubric ('that is drift
not an invariant') and in both overview rubrics ('a paraphrase is a second version that drifts'); 'sufficiency'
appears in the repo overview's Health receipt line. Keying on those silently fed authoring and overview calls a
findings/score JSON, and the tests still passed because they asserted the file EXISTED, not that it was a spec.
Each reply below is the shape its caller actually has to parse.
"""
from spec_eval import providers

_SPEC = ("## 1. Purpose\n\n**In one line:** A fixture module.\n\n## 2. Definitions\n\n| Term | Meaning |\n"
         "|---|---|\n| widget | a fixture |\n\n## 3. Behavior\n\nIt holds.\n\n## 4. Contracts\n"
         "### Invariants (*rules that must always hold*)\n\n| ID | Invariant |\n|---|---|\n| INV-1 | It holds. |\n")

_FOLDER_SPEC = ("## 1. Purpose\n\nWhat this directory provides.\n\n## 2. Modules\n\n| Module | Responsibility |\n"
                "|---|---|\n| a.py | holds |\n\n## 3. How it fits together\n\nFlow.\n\n## 4. Shared contract\n\n"
                "Cross-module invariant.\n")

_DIR_OVERVIEW = ("## Map\n\n| Module | Purpose |\n|---|---|\n| a.md | A fixture module. |\n\n"
                 "## How it fits together\n\nFlow across the modules.\n\n## Shared contract\n\nOne invariant.\n\n"
                 "## System context\n\n| External system | Direction | What flows | Evidence |\n|---|---|---|---|\n"
                 "| Redis | outbound | cache entries | `a.py:1` |\n")

_REPO_OVERVIEW = ("## What it is\n\nA fixture project.\n\n## Governing principles\n\n- **Determinism** — it holds.\n\n"
                  "## Architecture (data flow)\n\n### How it is invoked\n\n```mermaid\nsequenceDiagram\n"
                  "    actor U as User\n    participant R as run.py\n    U->>R: python run.py\n```\n\n"
                  "### Data flow\n\n```mermaid\nflowchart LR\n    A[\"a.py\"] ==> OUT[/\"stdout\"/]\n```\n"
                  "> scanner-derived; internal edges not verified against a call graph.\n\n"
                  "## System context\n\n| External system | Direction | What flows | Evidence |\n|---|---|---|---|\n"
                  "| Redis | outbound | cache entries | `a.py:1` |\n\n"
                  "## Module map\n\n| Module | Spec | Intent |\n|---|---|---|\n| a.py | a.md | A fixture module. |\n\n"
                  "## Glossary\n\n- **widget** — a fixture.\n\n## Health receipt\n\nSee SPEC-HEALTH.md.\n\n"
                  "## Reading order\n\n1. This overview → 2. the specs → 3. SPEC-HEALTH.md\n")

_DIAGRAM_BODY = ("### How it is invoked\n\n```mermaid\nsequenceDiagram\n    actor U as User\n"
                 "    participant R as run.py\n    U->>R: python run.py\n"
                 "    Note over R: scanner-verified entry point (run.py:1)\n```\n\n"
                 "### Data flow\n\n```mermaid\nflowchart LR\n    A[\"a.py\"] ==> OUT[/\"stdout\"/]\n```\n"
                 "> scanner-derived; internal edges not verified against a call graph.\n")


def fake_gen(model, system, user, max_tokens=1200):
    s = system.lower()
    if "you assess whether a spec is sufficient" in s:        # SUFFICIENCY_RUBRIC
        return ('{"sufficiency": 0.90, "gaps": [{"severity": "minor", "missing": "a default value", '
                '"code_ref": "widget.py (add)"}]}')
    if "auditing a codebase for drift" in s:                  # DRIFT_RUBRIC
        return '{"findings": []}'
    if "output only the architecture section body" in s:      # ARCH_DIAGRAM_ONLY_RUBRIC (the `diagram` command)
        return _DIAGRAM_BODY
    if "you author the repository-level project overview" in s:   # REPO_OVERVIEW_RUBRIC
        return _REPO_OVERVIEW
    if "you author a navigation overview" in s:               # DIR_OVERVIEW_RUBRIC
        return _DIR_OVERVIEW
    if "for a whole directory" in s:                          # FOLDER_SPEC_RUBRIC
        return _FOLDER_SPEC
    return _SPEC                                              # AUTHORING_RUBRIC → an intent-led spec


def install(monkeypatch):
    """Patch `providers.gen` (used by audit / sufficiency / authoring) with the fake."""
    monkeypatch.setattr(providers, "gen", fake_gen)
