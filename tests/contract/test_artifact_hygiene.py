"""Layer 1 — the artifact-hygiene check's own contract.

`.github/scripts/check_artifact_hygiene.py` enforces the rule CONTRIBUTING and the PR template state in prose:
a published artifact describes the change in this repository's own terms. A checker that is itself unchecked is
the failure mode this repo exists to catch, so its behaviour is pinned here.

The load-bearing assertions are the ones that would let a leak through silently — diff parsing, path scanning,
name normalisation — and the two that would make the check unusable: the repo's own tracked text must pass the
structural rules, and a check that cannot run must never report clean.
"""
import importlib.util
import os
import subprocess
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_SCRIPT = os.path.join(_ROOT, ".github", "scripts", "check_artifact_hygiene.py")


def _load():
    """Import the checker by path — it lives under .github/, which is not an importable package."""
    spec = importlib.util.spec_from_file_location("check_artifact_hygiene", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


hygiene = _load()


def _surfaces(tmp_path, **texts):
    tmp_path.mkdir(parents=True, exist_ok=True)
    for name in hygiene.SURFACES:
        (tmp_path / f"{name}.txt").write_text(texts.get(name, ""), encoding="utf-8")
    return str(tmp_path)


def _scan(tmp_path, denylist=(), **texts):
    return hygiene.scan(_surfaces(tmp_path, **texts), list(denylist))


def _rules(findings):
    return {f[1] for f in findings}


def _git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def _real_diff(repo, build):
    """A genuine `git diff` from a throwaway repo. Hand-written diff fixtures cannot catch a parser that
    mismodels git's actual output, which is exactly the bug class this guards."""
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q", ".")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")
    (repo / "seed.md").write_text("seed\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "base")
    build(repo)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "change")
    return subprocess.run(["git", "-C", str(repo), "diff", "HEAD~1", "HEAD"],
                          check=True, capture_output=True, text=True).stdout


# --- structural rules -----------------------------------------------------------------------------------------

def test_clean_text_produces_no_findings(tmp_path):
    assert _scan(tmp_path, title="Add a coverage gate", body="Closes #12.", commits="Add a coverage gate") == []


def test_personal_paths_are_flagged_on_every_platform(tmp_path):
    for path in ("/Users/someone/scratch", "/home/someone/scratch",
                 r"C:\Users\someone\scratch", r"C:\\Users\\someone\\scratch"):
        assert "absolute path from a personal machine" in _rules(_scan(tmp_path, body=f"see {path}")), path


def test_personal_path_report_masks_the_username(tmp_path):
    """The rule name says what to fix. Reprinting the username into a log that outlives the branch would leak a
    second thing in the course of reporting the first."""
    findings = _scan(tmp_path, body="see /Users/someone/scratch")
    assert findings and "someone" not in findings[0][2], findings
    assert "<user>" in findings[0][2]


def test_ci_home_directories_are_not_personal_machines(tmp_path):
    """A pasted CI traceback is not a leak, and failing on one would train people to ignore the check."""
    for path in ("/home/runner/work/spec-eval", "/Users/runner/hostedtoolcache", "/home/ubuntu/build"):
        assert _scan(tmp_path, body=f"traceback from {path}") == [], path


def test_session_narration_is_flagged(tmp_path):
    for phrase in ("As we discussed, the scanner is Python-only.",
                   "You asked me to split this.",
                   "Fixed the case from the previous message."):
        assert "narration of the session that produced the change" in _rules(_scan(tmp_path, body=phrase)), phrase


def test_private_network_addresses_are_flagged_but_localhost_is_not(tmp_path):
    for addr in ("192.168.1.10", "10.0.0.5", "172.16.4.4"):
        assert "private network address" in _rules(_scan(tmp_path, body=f"see http://{addr}:8080")), addr
    for ok in ("http://localhost:8080", "http://127.0.0.1:8000"):
        assert _scan(tmp_path, body=ok) == [], f"{ok} names nobody's machine and is normal in developer docs"


def test_structural_rules_have_no_capturing_groups():
    """`finditer` + `group(0)` is used throughout; a capturing group would silently change `findall` semantics
    for anyone who reaches for it later."""
    for name, _find, _hint in hygiene.STRUCTURAL_RULES:
        assert isinstance(name, str)
    for pattern in (hygiene._NARRATION, hygiene._PRIVATE_NET):
        assert pattern.groups == 0, pattern.pattern


def test_every_surface_is_scanned(tmp_path):
    leak = "/Users/someone/x"
    for surface in ("title", "body", "head_ref", "commits"):
        assert _scan(tmp_path / surface, **{surface: leak}), f"{surface} was not scanned"
    assert _scan(tmp_path / "d", diff=f"+++ b/a.md\n@@ -0,0 +1 @@\n+{leak}\n"), "added lines were not scanned"


# --- denylist -------------------------------------------------------------------------------------------------

def test_denylist_matches_separator_and_case_variants(tmp_path):
    """One secret entry has to cover how a name is actually written in prose, or half the check is decorative."""
    for text in ("project-x", "Project X", "project_x", "ProjectX", "PROJECT-X", "project-\nx"):
        assert _scan(tmp_path, denylist=["project-x"], body=text), repr(text)


def test_denylist_ignores_zero_width_padding(tmp_path):
    assert _scan(tmp_path, denylist=["project-x"], body="project\u200b-x")


def test_denylist_match_is_redacted_in_the_report(tmp_path):
    """CI logs outlive the branch. Naming the thing in the failure message would republish it, and the length
    and initial of a short project name are themselves identifying."""
    findings = _scan(tmp_path, denylist=["project-x"], body="built against project-x")
    assert findings
    detail = findings[0][2]
    assert "project" not in detail.lower() and "x" not in detail.lower()
    assert set(detail) == {"*"}


def test_denylist_skips_comments_and_blanks(tmp_path):
    """The comment's own words must not become a term. Paired with a positive control so the test can fail."""
    deny = ["# project-x was the old name", "", "   ", "lemma"]
    assert _scan(tmp_path, denylist=deny, body="the old name still applies") == []
    assert _scan(tmp_path, denylist=deny, body="built on lemma")


def test_absent_denylist_still_runs_structural_rules(tmp_path):
    findings = _scan(tmp_path, denylist=[], body="/Users/someone/x")
    assert "absolute path from a personal machine" in _rules(findings)
    assert "denylisted name" not in _rules(findings)


# --- diff scoping and parsing ---------------------------------------------------------------------------------

def test_only_added_lines_are_scanned(tmp_path):
    """A pre-existing leak is not this PR's doing; failing on one would redden an unrelated change."""
    diff = ("+++ b/requirements.txt\n@@ -1,3 +1,3 @@\n"
            "-# removed line naming project-x\n"
            " # context line naming project-x\n"
            "+anthropic>=0.40\n")
    assert _scan(tmp_path, denylist=["project-x"], diff=diff) == []


def test_added_line_is_attributed_to_its_file_and_line_number(tmp_path):
    diff = "+++ b/docs/notes.md\n@@ -0,0 +1,2 @@\n+clean\n+see /Users/someone/x\n"
    findings = _scan(tmp_path, diff=diff)
    assert findings and "docs/notes.md" in findings[0][0]
    assert "added line 2 " in findings[0][0], findings[0][0]


def test_added_content_starting_with_plus_plus_is_still_scanned(tmp_path):
    """A source line beginning with `++` becomes `+++...` in a diff. Treating that as a file header drops the
    line from every rule — silently, which is the worst way for this check to fail."""
    diff = _real_diff(
        tmp_path / "repo",
        lambda r: (r / "seed.md").write_text("seed\n++ b/decoy.md\n++leak /Users/someone/private\n",
                                             encoding="utf-8"),
    )
    findings = hygiene.scan(_surfaces(tmp_path / "s", diff=diff), [])
    assert "absolute path from a personal machine" in _rules(findings), diff


def test_a_new_file_whose_path_names_a_denylisted_project_is_caught(tmp_path):
    """A name in a filename is permanent in git history — the exact durability this check exists for."""
    diff = _real_diff(tmp_path / "repo",
                      lambda r: (r / "project-x-notes.md").write_text("clean content\n", encoding="utf-8"))
    assert hygiene.scan(_surfaces(tmp_path / "s", diff=diff), ["project-x"])


def test_a_rename_into_a_leaky_path_is_caught(tmp_path):
    """A pure rename carries no added lines at all."""
    diff = _real_diff(tmp_path / "repo", lambda r: os.rename(r / "seed.md", r / "project-x.md"))
    assert hygiene.scan(_surfaces(tmp_path / "s", diff=diff), ["project-x"]), diff


def test_a_binary_addition_with_a_leaky_path_is_caught(tmp_path):
    diff = _real_diff(tmp_path / "repo",
                      lambda r: (r / "shot-project-x.png").write_bytes(b"\x00\x01binary\x00"))
    assert hygiene.scan(_surfaces(tmp_path / "s", diff=diff), ["project-x"]), diff


def test_modified_file_paths_are_not_scanned(tmp_path):
    """Only paths the PR INTRODUCES. A pre-existing leaky path is a separate, already-committed problem."""
    diff = "+++ b/project-x/notes.md\n@@ -1 +1 @@\n-old\n+new\n"
    assert _scan(tmp_path, denylist=["project-x"], diff=diff) == []


# --- escape hatches -------------------------------------------------------------------------------------------

def test_the_checker_and_its_tests_are_exempt_from_the_added_line_scan(tmp_path):
    """Both files must contain leak-shaped literals to do their job — a rule's regex necessarily contains the
    phrase it forbids. Without this, the pull request adding the check fails the check."""
    for path in hygiene.HYGIENE_EXEMPT_PATHS:
        diff = f"+++ b/{path}\n@@ -0,0 +1 @@\n+/Users/someone/x and project-x\n"
        assert _scan(tmp_path / path.replace("/", "_"), denylist=["project-x"], diff=diff) == [], path


def test_an_inline_pragma_declares_an_intentional_occurrence(tmp_path):
    assert _scan(tmp_path, body="documented example: /Users/someone/x  <!-- hygiene: allow -->") == []


# --- the repo's own corpus ------------------------------------------------------------------------------------

def test_the_repos_own_tracked_text_passes_the_structural_rules():
    """A rule the repository itself violates would be switched off within a week. Driven off `git ls-files` so a
    new file is covered automatically — a hardcoded list is what let the checker's own fixtures slip through."""
    listed = subprocess.run(["git", "-C", _ROOT, "ls-files"], capture_output=True, text=True, check=True)
    exts = (".md", ".py", ".txt", ".yml", ".yaml", ".toml", ".cfg")
    paths = [p for p in listed.stdout.split("\n")
             if p.endswith(exts) and p not in hygiene.HYGIENE_EXEMPT_PATHS]
    assert len(paths) > 50, f"the glob found only {len(paths)} files — it is stale, not the repo small"

    offenders = []
    for rel in paths:
        try:
            text = open(os.path.join(_ROOT, rel), encoding="utf-8").read()
        except (OSError, UnicodeDecodeError):
            continue
        for rule, find, _hint in hygiene.STRUCTURAL_RULES:
            hits = [h for h in find(text) if not hygiene._PRAGMA.search(text)]
            if hits:
                offenders.append(f"{rel}: [{rule}] {hits[:2]}")
    assert not offenders, "the structural rules fire on this repo's own tracked text:\n  " + "\n  ".join(offenders)


# --- the script as a program ----------------------------------------------------------------------------------

def _run(directory, **env):
    e = {**os.environ, "ARTIFACT_DENYLIST": "project-x", **env}
    return subprocess.run([sys.executable, _SCRIPT, directory], capture_output=True, text=True, env=e)


def test_exit_codes(tmp_path):
    assert _run(_surfaces(tmp_path / "clean", body="nothing to see")).returncode == 0
    assert _run(_surfaces(tmp_path / "dirty", body="/Users/someone/x")).returncode == 1


def test_a_check_that_cannot_run_never_reports_clean(tmp_path):
    """Exit 2, never 0. A misconfigured step must not read as a clean bill of health."""
    assert subprocess.run([sys.executable, _SCRIPT], capture_output=True).returncode == 2
    assert _run(str(tmp_path / "does-not-exist")).returncode == 2
    (tmp_path / "empty").mkdir()
    assert _run(str(tmp_path / "empty")).returncode == 2


def test_a_missing_denylist_fails_on_a_branch_but_warns_on_a_fork(tmp_path):
    """Fail closed where the secret should have been available; degrade loudly where it cannot be."""
    clean = _surfaces(tmp_path / "c", body="nothing to see")
    branch = _run(clean, ARTIFACT_DENYLIST="", IS_FORK="false")
    assert branch.returncode == 2 and "not configured" in branch.stdout
    fork = _run(clean, ARTIFACT_DENYLIST="", IS_FORK="true")
    assert fork.returncode == 0 and "::warning::" in fork.stdout


def test_failure_output_names_the_surface_and_the_fix(tmp_path):
    """The message is the whole product when a check fails — an author who cannot find the leak will disable it."""
    out = _run(_surfaces(tmp_path, body="see /Users/someone/x")).stdout
    assert "PR body" in out and "repo-relative path" in out and "hygiene: allow" in out


def test_repeated_occurrences_are_reported_once(tmp_path):
    """One name repeated down a file is one thing to fix, not twelve."""
    diff = "+++ b/a.md\n@@ -0,0 +1,3 @@\n" + "".join("+naming project-x again\n" for _ in range(3))
    out = _run(_surfaces(tmp_path, diff=diff)).stdout
    assert "1 finding(s)" in out, out
