"""A fake `providers.gen` — returns canned output keyed on the rubric, so `drift` / `sufficiency` / `generate`
can be exercised with NO API key. Honors the shape each caller parses (findings JSON / sufficiency JSON /
intent-led markdown). Written for the Layer-2 acceptance tests and the Layer-4 e2e smoke.
"""
from spec_eval import providers


def fake_gen(model, system, user, max_tokens=1200):
    s = system.lower()
    if "sufficien" in s:
        return ('{"sufficiency": 0.90, "gaps": [{"severity": "minor", "missing": "a default value", '
                '"code_ref": "widget.py (add)"}]}')
    if "drift" in s or "contradict" in s:
        return '{"findings": []}'
    # authoring rubric → an intent-led spec
    return ("## 1. Purpose\n\nA fixture module.\n\n## 4. Contracts\n"
            "### Invariants (*rules that must always hold*)\n\n| ID | Invariant |\n|---|---|\n| INV-1 | It holds. |\n")


def install(monkeypatch):
    """Patch `providers.gen` (used by audit / sufficiency / authoring) with the fake."""
    monkeypatch.setattr(providers, "gen", fake_gen)
