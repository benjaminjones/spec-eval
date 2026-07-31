"""Layer 1 — overview section parity: skills/spec-authoring/templates/OVERVIEW-template.md is the SOURCE OF
TRUTH for WHICH sections the repo-level OVERVIEW carries. The CLI's REPO_OVERVIEW_RUBRIC must emit that exact
section set, in that exact order, or a user standardizing against the template and a user running the CLI get
different overviews. The per-directory README overview (DIR_OVERVIEW_RUBRIC) stays a LEAN, distinct index and
never carries the Architecture (data flow) diagram — this file pins both facts.

Only WHICH sections appear is pinned here (the section headings). HOW each section is filled may differ between
the template (a skeleton a human copies) and the rubric (an instruction the model follows) — that is by design.
"""
import os
import re

from spec_eval.authoring import DIR_OVERVIEW_RUBRIC, REPO_OVERVIEW_RUBRIC

_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
OVERVIEW_TEMPLATE_PATH = os.path.join(_ROOT, "skills", "spec-authoring", "templates", "OVERVIEW-template.md")

# The 4 legacy headings the per-directory README index carries — the lean subset, unchanged by the split.
DIR_SECTIONS = ["## Map", "## How it fits together", "## Shared contract", "## System context"]


def _normalize(heading):
    """A template heading may carry a trailing ' *(annotation)*' and backtick-wrapped placeholders; the rubric
    pins the bare heading. Strip both so the two sides compare on the section NAME only."""
    heading = re.sub(r"\s*\*\(.*\)\*\s*$", "", heading)   # drop a trailing  *(annotation)*
    return heading.replace("`", "").strip()


def _template_sections(md):
    """Ordered level-2 ('## ') headings from the template — the source of truth for the section set."""
    return ["## " + _normalize(m.group(1)) for m in re.finditer(r"^## +(.+)$", md, re.M)]


def _rubric_sections(rubric):
    """The '## <heading>' tokens the rubric instructs the model to emit, in order."""
    return re.findall(r"'(## [^']+)'", rubric)


def test_repo_overview_sections_match_the_template_in_order():
    """The CLI repo overview emits the SAME sections as the template, identically and in order — the template
    is the WHICH-sections source of truth (parity is enforced here, not by importing markdown at runtime)."""
    template = open(OVERVIEW_TEMPLATE_PATH).read()
    assert _rubric_sections(REPO_OVERVIEW_RUBRIC) == _template_sections(template), (
        "REPO_OVERVIEW_RUBRIC has drifted from OVERVIEW-template.md's section set/order"
    )


def test_per_dir_overview_is_the_lean_legacy_subset_with_no_diagram():
    """The per-dir README index stays the 4 legacy sections and NEVER gains the Architecture diagram; the two
    rubrics are distinct constants whose only shared section is System context."""
    dir_sections = _rubric_sections(DIR_OVERVIEW_RUBRIC)
    repo_sections = _rubric_sections(REPO_OVERVIEW_RUBRIC)
    assert dir_sections == DIR_SECTIONS
    assert "## Architecture (data flow)" in repo_sections
    assert "## Architecture (data flow)" not in dir_sections
    assert set(dir_sections) & set(repo_sections) == {"## System context"}
