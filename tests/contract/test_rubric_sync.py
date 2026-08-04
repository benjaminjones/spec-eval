"""Layer 1 — rubric sync: the CLI rubrics and their agent-session copies are hand-maintained mirrors of the
same principles. These tests pin the load-bearing phrases so a change to one copy without the others fails
loudly instead of drifting silently. Two mirror pairs are guarded:
  drift     — `spec_eval/rubric.py` (DRIFT_RUBRIC)       <-> `skills/spec-check/SKILL.md`
  authoring — `spec_eval/authoring.py` (AUTHORING_RUBRIC) <-> `skills/spec-authoring/SKILL.md` + shipped templates
(SUFFICIENCY_RUBRIC has no agent-side mirror; its description lives in `spec_eval/sufficiency.md`, which the
self-dogfood audit guards. `OVERVIEW-template.md` is not a verbatim copy of the overview rubrics, but it is the
SOURCE OF TRUTH for the repo overview's section set — `test_overview_sections_sync.py` pins REPO_OVERVIEW_RUBRIC
to it — and both overview rubrics share the System-context honesty phrases pinned below.)"""
import os

from spec_eval.authoring import (ARCH_CAVEAT, ARCH_DIAGRAM_RUBRIC, AUTHORING_RUBRIC, DIR_OVERVIEW_RUBRIC,
                                 REPO_OVERVIEW_RUBRIC)
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


# --- system context: REPO/DIR_OVERVIEW_RUBRIC <-> spec-authoring SKILL.md + OVERVIEW-template.md + the scanner ---

OVERVIEW_TEMPLATE_PATH = os.path.join(_ROOT, "skills", "spec-authoring", "templates", "OVERVIEW-template.md")

# The honesty rules every System context copy must state: rows come only from observed evidence, unknowable
# cells say so, and the section admits what a single repo cannot see.
SYSTEM_CONTEXT_LOAD_BEARING = [
    "## System context",
    "NEVER invent",
    "unknown from this repo",
    "not observable from this repo",
    "capability in the code, not proof of runtime traffic",
]


def test_system_context_copies_share_the_honesty_phrases():
    skill = open(AUTHORING_SKILL_PATH).read()
    template = open(OVERVIEW_TEMPLATE_PATH).read()
    for phrase in SYSTEM_CONTEXT_LOAD_BEARING:
        assert phrase in REPO_OVERVIEW_RUBRIC and phrase in DIR_OVERVIEW_RUBRIC, (
            f"an overview rubric lost the System-context principle: {phrase!r}")
        assert phrase in skill, f"skills/spec-authoring/SKILL.md lost the principle: {phrase!r}"
        assert phrase in template, f"OVERVIEW-template.md lost the principle: {phrase!r}"


def test_system_context_wins_over_right_sizing_in_both_copies():
    """AUTHORING_DISCIPLINE's right-size rule (collapse sections with <=1 real row) is appended AFTER the
    System context bullet — without an explicit precedence, a 1-system repo loses its table. Both copies must
    carry the exemption."""
    phrase = "even if it carries a single row"
    assert phrase in REPO_OVERVIEW_RUBRIC and phrase in DIR_OVERVIEW_RUBRIC, (
        "an overview rubric lost the right-sizing exemption")
    assert phrase in open(AUTHORING_SKILL_PATH).read(), "spec-authoring SKILL.md lost the right-sizing exemption"


def test_rubric_triggers_on_the_exact_block_marker_the_scanner_emits():
    """The rubric renders the section ONLY when the scanner's block is present — the two sides must agree on
    the marker string, or the section silently never renders."""
    from spec_eval import syscontext
    result = {"entries": [{"system": "X", "kind": "infra", "direction": "outbound", "via": ["sdk"],
                           "evidence": [{"file": "a.py", "line": 1, "match": "import x"}],
                           "evidence_total": 1}]}
    block = syscontext.evidence_block(result)
    assert "OBSERVED SYSTEM EVIDENCE" in block
    assert "OBSERVED SYSTEM EVIDENCE" in REPO_OVERVIEW_RUBRIC and "OBSERVED SYSTEM EVIDENCE" in DIR_OVERVIEW_RUBRIC
    # the language-gap line's marker must also agree between scanner and rubric
    assert syscontext.unscanned_note({"unscanned": {".cpp": 1}}).startswith("Not scanned:")
    assert "'Not scanned:'" in REPO_OVERVIEW_RUBRIC and "'Not scanned:'" in DIR_OVERVIEW_RUBRIC


# --- architecture diagram: ARCH_DIAGRAM_RUBRIC <-> spec-authoring SKILL.md + OVERVIEW-template.md ---

# The load-bearing phrases every Architecture (data flow) copy must carry: the section heading, the mermaid
# marker, the two subsection names (the invocation/data-flow split), the fact that their order is fixed, the
# two provenance labels a sequence entry must wear, and the inferred-edge honesty (the diagrams' analogue of
# System context's 'capability in the code, not proof of runtime traffic').
DIAGRAM_LOAD_BEARING = [
    "## Architecture (data flow)",
    "mermaid",
    "How it is invoked",
    "Data flow",
    "in this order",
    "scanner-verified entry point",
    "not scanner-detected",
    "scanner-derived",
    "not verified against a call graph",
]


def test_diagram_phrases_shared_across_rubric_skill_and_template():
    skill = open(AUTHORING_SKILL_PATH).read()
    template = open(OVERVIEW_TEMPLATE_PATH).read()
    for phrase in DIAGRAM_LOAD_BEARING:
        assert phrase in ARCH_DIAGRAM_RUBRIC, f"authoring.py ARCH_DIAGRAM_RUBRIC lost the diagram phrase: {phrase!r}"
        assert phrase in skill, f"spec-authoring SKILL.md lost the diagram phrase: {phrase!r}"
        assert phrase in template, f"OVERVIEW-template.md lost the diagram phrase: {phrase!r}"


def test_the_invocation_diagram_precedes_the_data_flow_diagram_in_every_copy():
    """'in this order' is a phrase until something checks the order. Each copy must introduce
    '### How it is invoked' BEFORE '### Data flow' — a reader meets how the project is run before what moves
    through it, whether the page came from the CLI, the skill, or the template."""
    copies = (("ARCH_DIAGRAM_RUBRIC", ARCH_DIAGRAM_RUBRIC),
              ("spec-authoring SKILL.md", open(AUTHORING_SKILL_PATH).read()),
              ("OVERVIEW-template.md", open(OVERVIEW_TEMPLATE_PATH).read()))
    for name, text in copies:
        invoked, data_flow = text.find("### How it is invoked"), text.find("### Data flow")
        assert invoked >= 0 and data_flow >= 0, f"{name} lost one of the two diagram subsections"
        assert invoked < data_flow, f"{name} introduces the data-flow diagram before the invocation diagram"


def test_the_provenance_caveat_is_one_sentence_byte_for_byte():
    """The rubric orders the model to close the section with this line 'verbatim' while the skill tells an
    agent to copy it from the template — so the three copies must be the SAME STRING, not three paraphrases
    that render differently depending on who authored the page. Substring pins can't catch a formatting
    divergence; this compares the whole sentence."""
    assert ARCH_CAVEAT in ARCH_DIAGRAM_RUBRIC                  # the rubric embeds the constant, not a retype
    for path, name in ((OVERVIEW_TEMPLATE_PATH, "OVERVIEW-template.md"), (AUTHORING_SKILL_PATH, "SKILL.md")):
        assert ARCH_CAVEAT in open(path).read(), f"{name} no longer carries the caveat line byte-for-byte"


def test_per_dir_overview_never_carries_the_architecture_diagram():
    """The settled constraint, pinned mechanically: the Architecture diagram is repo-overview only — the lean
    per-directory rubric carries neither the section heading nor a mermaid fence."""
    assert "## Architecture (data flow)" in REPO_OVERVIEW_RUBRIC
    assert "## Architecture (data flow)" not in DIR_OVERVIEW_RUBRIC
    assert "mermaid" not in DIR_OVERVIEW_RUBRIC
