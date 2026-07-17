"""Layer 1 — code↔doc value sync: the docs quote a few code-derived NUMBERS and IDENTIFIERS (the input caps,
the default model). Those have one objective source — the code constant — but are re-typed by hand into the FAQ,
the example config, and the CLI spec, where they drift silently (the FAQ + example config are outside the
self-audit set, so nothing else catches them). This pins each doc mention to its code source, the same way
`test_rubric_sync.py` pins the rubric phrases: a real bump fails loudly here and reminds you to update the docs.

Scope on purpose: code-DERIVED facts only (numbers/identifiers with a single objective source). Prose claims and
wobbling scores are NOT pinned here — a test is the wrong, too-brittle tool for those (see CONTRIBUTING)."""
import os

from spec_eval.audit import CODE_CAP, DOC_CAP
from spec_eval.authoring import REDUCE_CAP
from spec_eval.providers import DEFAULT_MODEL

_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")


def _read(rel):
    return open(os.path.join(_ROOT, rel)).read()


# The per-run report files the CLI writes (spec_eval/cli.py). README, the FAQ, and now the spec-check skill all
# NAME them, so a rename must not silently leave the docs/skill stale. (SPEC-HEALTH.md is authored by the
# skill / by hand, not the CLI — not pinned here.)
REPORT_FILES = ("coverage.md", "report.md", "sufficiency.md")


def test_report_filenames_consistent_across_cli_skill_and_readme():
    cli = _read("spec_eval/cli.py")
    skill = _read("skills/spec-check/SKILL.md")
    readme = _read("README.md")
    for f in REPORT_FILES:
        assert f in cli, f"cli.py no longer writes {f} — update REPORT_FILES + every doc/skill that names it"
        assert f in skill, f"the spec-check skill's 'Save the results' section dropped {f}"
        assert f in readme, f"README's 'What it creates' no longer names {f}"


def test_drift_and_sufficiency_share_one_review_token_budget():
    """The two review checks must use the SAME output-token budget (a truncated JSON list is unparseable). This
    is structural — sufficiency references `audit.REVIEW_MAX_TOKENS` rather than re-typing 3000 — so the pin is a
    source-grep: no bare literal may re-appear in sufficiency's model call."""
    suff = _read("spec_eval/sufficiency.py")
    assert "audit.REVIEW_MAX_TOKENS" in suff, "sufficiency must reference the shared audit.REVIEW_MAX_TOKENS budget"
    assert "max_tokens=3000" not in suff, "sufficiency re-hardcoded the review budget instead of sharing the constant"


def test_example_config_cap_literals_match_the_code():
    """configs/spec-eval.example.yml documents the default caps as literals — keep them equal to the constants."""
    cfg = _read("configs/spec-eval.example.yml")
    for name, value in [("code", CODE_CAP), ("docs", DOC_CAP), ("reduce", REDUCE_CAP)]:
        assert f"{name}: {value}" in cfg, f"example config's caps.{name} != code ({value}); update the config comment"


def test_faq_cap_prose_matches_the_code():
    """The FAQ quotes the caps in 'k' shorthand ('~64k characters of code, ~28k of spec') — pin those too."""
    faq = _read("FAQ.md")
    assert f"{CODE_CAP // 1000}k" in faq, f"FAQ code-cap shorthand != CODE_CAP ({CODE_CAP})"
    assert f"{DOC_CAP // 1000}k" in faq, f"FAQ doc-cap shorthand != DOC_CAP ({DOC_CAP})"


def test_cli_spec_states_the_actual_default_model():
    """spec_eval/cli.md documents the default model as a literal; it must equal providers.DEFAULT_MODEL."""
    assert DEFAULT_MODEL in _read("spec_eval/cli.md"), \
        f"cli.md's stated default model != DEFAULT_MODEL ({DEFAULT_MODEL}); update the spec"
