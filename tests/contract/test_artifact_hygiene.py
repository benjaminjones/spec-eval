"""Layer 1 — the artifact-hygiene check's own contract.

`.github/scripts/check_artifact_hygiene.py` enforces the rule CONTRIBUTING and the PR template state in prose:
a published artifact describes the change in this repository's own terms. A checker that is itself unchecked is
the failure mode this repo exists to catch, so its behaviour is pinned here.

The load-bearing assertions are the ones that would let a leak through (added-lines scoping, case folding) and
the one that would make the check unusable (the repo's own docs must pass it).
"""
import importlib.util
import os
import subprocess
import sys

_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
_SCRIPT = os.path.join(_ROOT, ".github", "scripts", "check_artifact_hygiene.py")


def _load():
    """Import the checker by path — it lives under .github/, which is not an importable package."""
    spec = importlib.util.spec_from_file_location("check_artifact_hygiene", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


hygiene = _load()


def _surfaces(tmp_path, title="", body="", commits="", diff=""):
    for name, text in (("title", title), ("body", body), ("commits", commits), ("diff", diff)):
        (tmp_path / f"{name}.txt").write_text(text, encoding="utf-8")
    return str(tmp_path)


def _scan(tmp_path, denylist=None, **surfaces):
    """Run scan() with ARTIFACT_DENYLIST set (or explicitly absent) — the env is global, so restore it."""
    before = os.environ.get(hygiene.DENYLIST_ENV)
    if denylist is None:
        os.environ.pop(hygiene.DENYLIST_ENV, None)
    else:
        os.environ[hygiene.DENYLIST_ENV] = denylist
    try:
        return hygiene.scan(_surfaces(tmp_path, **surfaces))
    finally:
        os.environ.pop(hygiene.DENYLIST_ENV, None)
        if before is not None:
            os.environ[hygiene.DENYLIST_ENV] = before


def _rules(findings):
    return {f[1] for f in findings}


# --- structural rules -----------------------------------------------------------------------------------------

def test_clean_text_produces_no_findings(tmp_path):
    assert _scan(tmp_path, title="Add a coverage gate", body="Closes #12.", commits="Add a coverage gate") == []


def test_personal_paths_are_flagged_on_every_platform(tmp_path):
    for path in ("/Users/someone/scratch", "/home/someone/scratch", r"C:\Users\someone\scratch"):
        assert "absolute path from a personal machine" in _rules(_scan(tmp_path, body=f"see {path}")), path


def test_session_narration_is_flagged(tmp_path):
    for phrase in ("As we discussed, the scanner is Python-only.",
                   "You asked me to split this.",
                   "Fixed the case from the previous message."):
        assert "narration of the session that produced the change" in _rules(_scan(tmp_path, body=phrase)), phrase


def test_every_surface_is_scanned(tmp_path):
    leak = "/Users/someone/x"
    for surface in ("title", "body", "commits"):
        assert _scan(tmp_path, **{surface: leak}), f"{surface} was not scanned"
    assert _scan(tmp_path, diff=f"+++ b/a.md\n+{leak}\n"), "diff added lines were not scanned"


# --- denylist -------------------------------------------------------------------------------------------------

def test_denylist_matches_are_case_insensitive(tmp_path):
    for text in ("project-x", "Project-X", "PROJECT-X"):
        assert _scan(tmp_path, denylist="project-x", body=text), text


def test_denylist_match_is_redacted_in_the_report(tmp_path):
    """CI logs outlive the branch. Naming the thing in the failure message would republish it."""
    findings = _scan(tmp_path, denylist="project-x", body="built against project-x")
    assert findings
    detail = findings[0][2]
    assert "project-x" not in detail.lower(), f"the denylisted name was reproduced verbatim: {detail!r}"
    assert detail.startswith("p") and set(detail[1:]) == {"*"}


def test_denylist_skips_comments_and_blanks(tmp_path):
    findings = _scan(tmp_path, denylist="# a note\n\n  \nproject-x\n", body="mentions nothing sensitive")
    assert findings == [], "a comment or blank line was treated as a term to match"


def test_unset_denylist_still_runs_structural_rules(tmp_path):
    """A fork PR cannot read secrets. It must not therefore pass everything. `_scan(denylist=None)` removes the
    variable entirely, so this is the fork case exactly."""
    findings = _scan(tmp_path, denylist=None, body="/Users/someone/x")
    assert "absolute path from a personal machine" in _rules(findings)
    assert "denylisted name" not in _rules(findings)               # nothing to match against, and no crash


# --- diff scoping ---------------------------------------------------------------------------------------------

def test_only_added_lines_are_scanned(tmp_path):
    """A pre-existing leak is not this PR's doing; failing on one would redden an unrelated change."""
    diff = ("+++ b/requirements.txt\n"
            "-# removed line naming project-x\n"
            " # context line naming project-x\n"
            "+anthropic>=0.40\n")
    assert _scan(tmp_path, denylist="project-x", diff=diff) == []


def test_added_line_is_attributed_to_its_file(tmp_path):
    diff = "+++ b/docs/notes.md\n+see /Users/someone/x\n"
    findings = _scan(tmp_path, diff=diff)
    assert findings and "docs/notes.md" in findings[0][0]


def test_diff_header_lines_are_not_treated_as_additions(tmp_path):
    """`+++ b/path` is a header, not content. Counting it would attribute the path to itself as a leak."""
    assert _scan(tmp_path, denylist="project-x", diff="+++ b/project-x/notes.md\n+clean line\n") == []


# --- the repo's own corpus ------------------------------------------------------------------------------------

def test_the_repos_own_published_docs_pass_the_structural_rules(tmp_path):
    """A rule the repository itself violates would be turned off within a week. This asserts the structural
    rules are compatible with the prose spec-eval actually ships."""
    docs = ["README.md", "FAQ.md", "GETTING-STARTED.md", "CONTRIBUTING.md", "TESTING.md",
            "skills/spec-authoring/SKILL.md", "skills/spec-check/SKILL.md",
            ".github/PULL_REQUEST_TEMPLATE.md"]
    offenders = []
    for rel in docs:
        path = os.path.join(_ROOT, rel)
        if not os.path.exists(path):
            continue
        text = open(path, encoding="utf-8").read()
        for rule, pattern, _hint in hygiene.STRUCTURAL_RULES:
            hits = pattern.findall(text)
            if hits:
                offenders.append(f"{rel}: [{rule}] {hits[:3]}")
    assert not offenders, "the structural rules fire on this repo's own docs:\n  " + "\n  ".join(offenders)


# --- the script as a program ----------------------------------------------------------------------------------

def _run(directory):
    return subprocess.run([sys.executable, _SCRIPT, directory], capture_output=True, text=True)


def test_exit_codes(tmp_path):
    clean, dirty = tmp_path / "clean", tmp_path / "dirty"
    clean.mkdir()
    dirty.mkdir()
    assert _run(_surfaces(clean, body="nothing to see")).returncode == 0
    assert _run(_surfaces(dirty, body="/Users/someone/x")).returncode == 1


def test_failure_output_names_the_surface_and_the_fix(tmp_path):
    """The message is the whole product when a check fails — an author who cannot find the leak will disable it."""
    out = _run(_surfaces(tmp_path, body="see /Users/someone/x")).stdout
    assert "PR body" in out and "repo-relative path" in out


def test_wrong_arity_is_a_usage_error_not_a_pass(tmp_path):
    """Exit 2, never 0: a misconfigured workflow step must not read as a clean bill of health."""
    assert subprocess.run([sys.executable, _SCRIPT], capture_output=True).returncode == 2
