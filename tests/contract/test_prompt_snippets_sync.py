"""Layer 1 — code↔doc value sync for the README's two prompt-chat snippets (and the skills they point at).
The snippets hand a coding agent the SAME defaults the CLI uses — the layout, the overview values, the reports
folder, the co-located spec path — but those are re-typed by hand into README / FAQ / skill prose, where they
drift silently (none of them are in the self-audit set). Same pattern as `test_caps_sync.py`: each doc mention
is pinned to its code source, so a real change fails loudly here and reminds you to update the snippets.

Scope on purpose: code-DERIVED facts only (defaults, enum values, paths). Prose claims are NOT pinned here —
a test is the wrong, too-brittle tool for those (see CONTRIBUTING)."""
import os
import re

from spec_eval.authoring import spec_path_for

_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")


def _read(rel):
    return open(os.path.join(_ROOT, rel)).read()


def test_readme_snippet_defaults_match_the_authoring_fallbacks():
    """The write-specs block states `layout: per-file` and `overview: none` as defaults — they must equal
    authoring.py's config fallbacks (source-grep, the same style as the shared-token-budget pin)."""
    src = _read("spec_eval/authoring.py")
    readme = _read("README.md")
    assert 'authoring.get("layout", "per-file")' in src, \
        "authoring's default layout moved/changed — update this pin + the README snippet"
    assert 'authoring.get("overview", "none")' in src, \
        "authoring's default overview moved/changed — update this pin + the README snippet"
    assert "layout:   per-file" in readme, "README write-specs snippet no longer states the per-file default"
    assert "overview: none" in readme, "README write-specs snippet no longer states the overview-none default"


def test_overview_values_in_the_snippet_match_the_cli_choices():
    """The snippet's comment lists the overview values in CLI order; build the line from cli.py's choices."""
    m = re.search(r'"--overview",\s*choices=\[([^\]]*)\]', _read("spec_eval/cli.py"))
    assert m, "cli.py's --overview choices moved — update this test"
    legend = " | ".join(re.findall(r'"([^"]+)"', m.group(1)))
    assert legend in _read("README.md"), \
        f"README snippet's overview legend != CLI choices ({legend}); update the snippet + tip"


def test_overview_min_files_prose_matches_the_default():
    """Docs say per-dir overviews appear in folders of 'N+ modules'; N = the code default, because the code
    writes an overview for a directory with AT LEAST overview_min_files files (a true minimum — pin the
    comparison too, since the prose formula depends on it)."""
    src = _read("spec_eval/authoring.py")
    assert "len(dfiles) < overview_min_files" in src, \
        "the threshold comparison changed — the 'N+ modules' doc formula no longer holds; update both"
    m = re.search(r'"overview_min_files", (\d+)', src)
    assert m, "overview_min_files default moved — update this test"
    n_plus = f"{int(m.group(1))}+ modules"
    for doc in ("README.md", "FAQ.md", "skills/spec-authoring/SKILL.md"):
        assert n_plus in _read(doc), f"{doc}'s per-dir threshold prose != '{n_plus}' (default bumped?)"


def test_colocated_spec_path_claim_matches_spec_path_for():
    """README + both skills state the co-located pairing with the same example; it must match the function."""
    assert spec_path_for("src/x.py") == "src/x.md"
    assert "src/x.py -> src/x.md" in _read("README.md"), \
        "README write-specs snippet dropped the co-located src/x.py -> src/x.md example"
    assert "`src/x.py` → `src/x.md`" in _read("skills/spec-authoring/SKILL.md"), \
        "spec-authoring skill dropped the co-located example"
    assert "`src/x.py` ↔ `src/x.md`" in _read("skills/spec-check/SKILL.md"), \
        "spec-check skill dropped the co-located default pairing"


def test_snippets_and_skill_name_the_same_reports_folder():
    """Both snippets' save line and the spec-check skill point at the folder the CLI writes."""
    save_line = "save the results to spec-reports/"
    assert _read("README.md").count(save_line) >= 2, \
        "a README snippet dropped its 'save the results to spec-reports/' line"
    assert save_line in _read("skills/spec-check/SKILL.md").replace("`", ""), \
        "the spec-check skill's save-trigger example no longer matches the snippets"
    assert "spec-reports" in _read("spec_eval/cli.py"), \
        "cli.py's default reports folder moved — update the snippets + skill"
