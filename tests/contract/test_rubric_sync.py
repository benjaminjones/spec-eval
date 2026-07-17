"""Layer 1 — rubric sync: the CLI rubrics and their agent-session copies are hand-maintained mirrors of the
same principles. These tests pin the load-bearing phrases so a change to one copy without the others fails
loudly instead of drifting silently. Two mirror pairs are guarded:
  drift     — `spec_eval/rubric.py` (DRIFT_RUBRIC)       <-> `skills/spec-check/SKILL.md`
  authoring — `spec_eval/authoring.py` (AUTHORING_RUBRIC) <-> `skills/spec-authoring/SKILL.md` + shipped templates
(SUFFICIENCY_RUBRIC has no agent-side mirror; its description lives in `spec_eval/sufficiency.md`, which the
self-dogfood audit guards. `OVERVIEW-template.md` is intentionally NOT a copy of OVERVIEW_RUBRIC.)"""
import os

from spec_eval.authoring import AUTHORING_RUBRIC
from spec_eval.rubric import DRIFT_RUBRIC

_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
SKILL_PATH = os.path.join(_ROOT, "skills", "spec-check", "SKILL.md")
AUTHORING_SKILL_PATH = os.path.join(_ROOT, "skills", "spec-authoring", "SKILL.md")
SKILL_TEMPLATE_PATH = os.path.join(_ROOT, "skills", "spec-authoring", "templates", "spec-template.md")
EXAMPLE_TEMPLATE_PATH = os.path.join(_ROOT, "configs", "spec-template.example.md")

# The principles both rubrics must state (severity anchor + the conservatism rules).
LOAD_BEARING = [
    "MEASURABLE GUARANTEE",
    "silence is not drift",
    "scope is not drift",
    "false negatives",
]


def test_drift_rubric_and_spec_check_skill_share_the_load_bearing_phrases():
    skill = open(SKILL_PATH).read()
    for phrase in LOAD_BEARING:
        assert phrase in DRIFT_RUBRIC, f"rubric.py lost the principle: {phrase!r}"
        assert phrase in skill, f"skills/spec-check/SKILL.md lost the principle: {phrase!r}"


def test_both_rubrics_carry_the_sync_pointer():
    """Each copy names the other, so an editor landing in either file learns the sync rule."""
    import spec_eval.rubric as rubric_mod
    assert "KEEP IN SYNC" in open(rubric_mod.__file__).read()
    assert "KEEP IN SYNC" in open(SKILL_PATH).read()


# --- authoring rubric: spec_eval/authoring.py <-> skills/spec-authoring/SKILL.md + shipped templates ---

# The principles both authoring copies must state (added by the readability pass; each phrase appears verbatim
# in the code rubric AND the skill — pin the exact shared substring, not the surrounding prose).
AUTHORING_LOAD_BEARING = [
    "**In one line:**",                      # the front-loaded capability headline
    "Reconstructed intent (confidence:",     # inferred rationale is always labeled
    "skip on a first read for intent",       # §4's visible reference cue
    "one idea per sentence",                 # sentence discipline
    "non-obvious or load-bearing",           # the earned-Why rule
    "collapse to one sentence",              # right-sizing
    "CAPABILITY",                            # headings by capability, never the symbol tree
    "what it ISN'T",                         # describe a capability on its own terms, never by negation
]


def test_authoring_rubric_and_skill_share_the_load_bearing_phrases():
    skill = open(AUTHORING_SKILL_PATH).read()
    for phrase in AUTHORING_LOAD_BEARING:
        assert phrase in AUTHORING_RUBRIC, f"authoring.py rubric lost the principle: {phrase!r}"
        assert phrase in skill, f"skills/spec-authoring/SKILL.md lost the principle: {phrase!r}"


def test_shipped_templates_carry_the_structural_markers():
    """The templates are skeletons, not rubric copies — pin only the markers a generated spec and a templated
    spec must share so the two authoring paths keep telling one story."""
    skill_tpl = open(SKILL_TEMPLATE_PATH).read()
    for phrase in ["**In one line:**", "skip on a first read for intent", "Reconstructed intent (confidence:"]:
        assert phrase in skill_tpl, f"skill spec-template lost the marker: {phrase!r}"
    assert "**In one line:**" in open(EXAMPLE_TEMPLATE_PATH).read(), "example config template lost the headline marker"


def test_authoring_copies_carry_the_sync_pointer():
    import spec_eval.authoring as authoring_mod
    assert "KEEP IN SYNC" in open(authoring_mod.__file__).read()
    assert "KEEP IN SYNC" in open(AUTHORING_SKILL_PATH).read()
