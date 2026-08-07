"""Layer 1 — health-contract parity: skills/spec-authoring/templates/SPEC-HEALTH-template.md is the SOURCE OF
TRUTH for WHICH fields the pipeline contract carries. The template calls that field set FROZEN, which only
means something if a receipt that drops or invents a field fails.

This exists because the dogfood receipt drifted from it twice in one cycle: once carrying a single `audit_sha`
for three measurements taken at three commits, and once attributing the audit to the fix that followed it. A
receipt that names the wrong commit is worse than one that names none, since it reads as provenance.

Only WHICH keys appear is pinned. The VALUES differ by definition — the template holds placeholders and a real
receipt holds a measurement.
"""
import os
import re

import yaml

_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
TEMPLATE = os.path.join(_ROOT, "skills", "spec-authoring", "templates", "SPEC-HEALTH-template.md")
RECEIPT = os.path.join(_ROOT, "spec-reports", "SPEC-HEALTH.md")


def _contract(path):
    """The `## Pipeline contract` section's yaml block, parsed. Comment lines carry the rationale and are
    dropped by the yaml parser, which is what we want — this pins fields, not prose."""
    md = open(path).read()
    section = md.split("## Pipeline contract", 1)[1]
    block = re.search(r"```yaml\n(.*?)```", section, re.S)
    assert block, f"no yaml block under '## Pipeline contract' in {path}"
    return yaml.safe_load(block.group(1))


def test_receipt_carries_the_templates_field_set():
    t, r = _contract(TEMPLATE), _contract(RECEIPT)
    assert set(r) == set(t), (
        f"receipt/template top-level mismatch — missing {set(t) - set(r)}, unknown {set(r) - set(t)}"
    )
    assert set(r["rollup"]) == set(t["rollup"])
    assert set(r["modules"][0]) == set(t["modules"][0])


def test_one_sha_field_per_measuring_command():
    """coverage, audit and sufficiency are three separate runs and the tree can move between them, so one
    pinned commit cannot say where each number came from. Each command gets its own field."""
    t = _contract(TEMPLATE)
    for cmd in ("coverage", "audit", "sufficiency"):
        assert f"{cmd}_sha" in t, f"the contract lost {cmd}_sha — a number with no commit is not evidence"


def test_receipts_shas_are_short_hashes_or_null():
    """A placeholder or a prose sentence in a SHA field would render the provenance unreadable while still
    parsing as yaml. Null is allowed and meaningful: that command was not run this cycle."""
    r = _contract(RECEIPT)
    for cmd in ("coverage", "audit", "sufficiency"):
        sha = r[f"{cmd}_sha"]
        assert sha is None or re.fullmatch(r"[0-9a-f]{7,40}", str(sha)), \
            f"{cmd}_sha is {sha!r} — expected a git hash or null"
