"""Layer 1 — authoring OUTPUT assertions.

test_rubric_sync pins the authoring rules as PHRASES in the skill/rubric text — but nothing checked that an
authored spec actually OBEYS them. These are the crisp, judge-free authoring rules as pass/fail on a spec's
markdown: the readability one-liner, the DON'T-list (no signature/type headings), and no metric inside a spec
(scores live in SPEC-HEALTH). Rule phrases live in spec_eval/authoring.py's AUTHORING_STRUCTURE/DISCIPLINE."""
import glob
import os
import re

_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
_HEADING = re.compile(r'^#{2,4}\s+(.+)$', re.M)
# AUTHORING_STRUCTURE requires the governing constraint "stated DIRECTLY as a checkable consequence … never as
# meta-phrasing like 'the one governing constraint a reviewer can check'". Matches the singular and plural forms
# ("Two governing rules a reviewer can check:") so a rename cannot slip the rule.
_META_CONSTRAINT = re.compile(r'governing (?:constraint|rule)s?[^.\n]{0,40}?reviewer can check', re.I)


def authoring_violations(md):
    """Machine-checkable authoring-rule violations in a spec's markdown (empty list = obeys the rules)."""
    v = []
    if "**In one line:**" not in md:
        v.append("missing the '**In one line:**' capability headline (readability rubric)")
    if _META_CONSTRAINT.search(md):
        v.append("governing constraint stated as meta-phrasing; state it directly as a checkable consequence")
    for h in _HEADING.findall(md):
        t = h.strip().strip('`').strip('*')
        # a heading must name a CAPABILITY — never a function signature or a language type (the DON'T list).
        # `name(` (identifier immediately followed by a paren) is a call/signature; a parenthetical aside has a
        # space before the paren ("Model presets (model_type -> dimensions)") and is fine.
        if re.search(r'\b[A-Za-z_]\w*\(', t):
            v.append(f"heading is a signature, not a capability: {h.strip()!r}")
        elif re.search(r'\b(?:dict|list|set|tuple|Optional|List|Dict|Tuple|torch|np|pd)\[', t) or 'torch.' in t:
            v.append(f"heading is a language type, not a capability: {h.strip()!r}")
    # a metric/score belongs in SPEC-HEALTH, never inside a spec (matches a 0.x score, not '= 1.0' definitions).
    # Table rows are exempt: an INV/AC row saying "pairs with sufficiency 0.4, 0.9" is illustrative test DATA,
    # not a claim about this repo's score. Only a score asserted in prose is the violation.
    prose = "\n".join(ln for ln in md.splitlines() if not ln.lstrip().startswith("|"))
    if re.search(r'\bsufficiency\s+0?\.\d', prose) or re.search(r'\bcoverage:?\s+\d{1,3}\s*%', prose):
        v.append("a metric/score appears inside the spec (belongs in SPEC-HEALTH)")
    return v


_COMPLIANT = """## 1. Purpose
**In one line:** Turn UTF-8 text into token ids and back.

Gives the model a compact integer vocabulary. Governing constraint: decode(encode(x)) == x for valid UTF-8.

## 3. Behavior
- Encode: split into chunks, then merge by rank.

## 4. Contracts
### Invariants (*rules that must always hold*)
| ID | Invariant |
|----|-----------|
| INV-1 | Every produced id is in [0, vocab_size). |

### Acceptance criteria (*Given / When / Then*)
| ID | Given | When | Then |
|----|-------|------|------|
| AC-1 | pairs with sufficiency 0.4 and 0.9 | the report renders | the average shown is 0.65. |
"""

_VIOLATING = """## 1. Purpose
Turns text into ids (no one-liner headline).

The one governing constraint a reviewer can check: **ids round-trip.**

## bytes_to_unicode()
A signature heading — forbidden.

## The config as dict[str, int]
A language-type heading — forbidden.

## 3. Behavior
This module scored sufficiency 0.42 last run.
"""


def test_checker_passes_a_compliant_spec():
    assert authoring_violations(_COMPLIANT) == []


def test_checker_flags_every_violation_class():
    v = authoring_violations(_VIOLATING)
    assert any("In one line" in x for x in v), "missed the absent one-liner"
    assert any("meta-phrasing" in x for x in v), "missed the meta-phrased governing constraint"
    assert any("signature" in x for x in v), "missed the signature heading"
    assert any("type" in x for x in v), "missed the language-type heading"
    assert any("metric" in x for x in v), "missed the in-spec metric"


def test_shipped_specs_obey_the_authoring_rules():
    """The OUTPUT obeys the rules, not just the skill text: every spec this repo ships must pass the checker.

    Graded over `spec_eval/*.md` — spec-eval holds its own specs to the rule it publishes, and grades ALL of
    them. An earlier version pointed at an `examples/` tree that no longer exists and skipped any spec without
    the one-liner, so it iterated nothing and passed while nine of ten shipped specs violated the rules. The
    non-empty assertion below is what makes that failure mode impossible to repeat: a glob that matches nothing
    is now a test failure, not a silent pass."""
    specs = sorted(glob.glob(os.path.join(_ROOT, "spec_eval", "*.md")))
    assert specs, "no specs matched spec_eval/*.md — the glob is stale, not the repo clean"
    for f in specs:
        md = open(f).read()
        assert authoring_violations(md) == [], f"{os.path.relpath(f, _ROOT)} violates: {authoring_violations(md)}"
