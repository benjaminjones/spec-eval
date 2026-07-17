"""Layer 2 — acceptance criteria for the authoring LAYOUTS (per-dir / per-pair / overview) and the swappable
template. Model-backed via the fake provider (no API key). Layouts are explicit: default stays per-file, and a
folder spec is never clobbered without --overwrite."""
import os

from spec_eval import authoring, coverage


def _mkpkg(root):
    """Two spec-worthy modules under src/pkg/ (no co-located specs)."""
    (root / "src" / "pkg").mkdir(parents=True)
    (root / "src" / "pkg" / "a.py").write_text("def a():\n    return 1\n")
    (root / "src" / "pkg" / "b.py").write_text("def b():\n    return 2\n")


def test_acl001_per_dir_writes_one_spec_per_directory(tmp_path, fake_model):
    """ACL-001. Given a directory of modules and layout=per-dir, When generate runs, Then one folder spec
    `<dir>/<dir>.md` is authored and no per-file specs are littered beside the code."""
    _mkpkg(tmp_path)
    res = authoring.generate_repo(str(tmp_path), {"authoring": {"layout": "per-dir"}}, fake_model)
    authored = {r["spec"] for r in res if r["status"] == "authored"}
    assert os.path.join("src", "pkg", "pkg.md") in authored
    assert (tmp_path / "src" / "pkg" / "pkg.md").exists()
    assert not (tmp_path / "src" / "pkg" / "a.md").exists()          # per-file specs NOT written under per-dir


def test_acl002_coverage_counts_a_folder_spec_under_per_dir(tmp_path):
    """ACL-002. Given layout=per-dir, When a folder spec exists, Then coverage counts every file in that
    directory as covered (parity with generate — no separate pairs entry needed)."""
    _mkpkg(tmp_path)
    cfg = {"authoring": {"layout": "per-dir"}}
    assert coverage.coverage(str(tmp_path), cfg)["pct"] == 0.0        # no folder spec yet
    (tmp_path / "src" / "pkg" / "pkg.md").write_text("## 1. Purpose\npkg\n")
    cov = coverage.coverage(str(tmp_path), cfg)
    assert cov["pct"] == 100.0 and cov["uncovered"] == []


def test_acl003_per_dir_skips_an_existing_folder_spec(tmp_path, fake_model):
    """ACL-003. Given a hand-written folder spec and no --overwrite, When generate runs, Then it is skipped and
    left byte-for-byte intact (no surprises)."""
    _mkpkg(tmp_path)
    (tmp_path / "src" / "pkg" / "pkg.md").write_text("HAND WRITTEN\n")
    res = authoring.generate_repo(str(tmp_path), {"authoring": {"layout": "per-dir"}}, fake_model)
    assert any(r["spec"] == os.path.join("src", "pkg", "pkg.md") and r["status"] == "skipped" for r in res)
    assert (tmp_path / "src" / "pkg" / "pkg.md").read_text() == "HAND WRITTEN\n"


def test_acl004_overview_repo_writes_a_top_level_index(tmp_path, fake_model):
    """ACL-004. Given overview=repo, When generate runs, Then a repo-level OVERVIEW.md index is authored."""
    (tmp_path / "a.py").write_text("x = 1\n")
    res = authoring.generate_repo(str(tmp_path), {"authoring": {"overview": "repo"}}, fake_model)
    assert any(r["spec"] == "OVERVIEW.md" and r["status"] == "authored" for r in res)
    assert (tmp_path / "OVERVIEW.md").exists()


def test_acl005_per_pair_authors_the_pair_doc_from_its_code_glob(tmp_path, fake_model):
    """ACL-005. Given explicit pairs and layout=per-pair, When generate runs, Then the pair's `docs` file is
    authored from its `code` glob (one spec governing many files)."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("x = 1\n")
    (tmp_path / "src" / "b.py").write_text("y = 2\n")
    cfg = {"pairs": [{"label": "core", "code": ["src/**/*.py"], "docs": ["docs/core.md"]}],
           "authoring": {"layout": "per-pair"}}
    res = authoring.generate_repo(str(tmp_path), cfg, fake_model)
    assert any(r["spec"] == "docs/core.md" and r["status"] == "authored" for r in res)
    assert (tmp_path / "docs" / "core.md").exists()


def test_acl006_custom_template_replaces_structure_but_keeps_discipline(tmp_path):
    """ACL-006. Given a custom template, When the rubric is built, Then the template's text is used AND the
    built-in authoring discipline is still appended (so the checkers can grade the result)."""
    tpl = tmp_path / "tpl.md"
    tpl.write_text("MY CUSTOM STRUCTURE — one section only.")
    r = authoring._rubric(str(tpl))
    assert "MY CUSTOM STRUCTURE" in r
    assert "Output ONLY the finished markdown document" in r          # discipline appended
    assert authoring._rubric(None) == authoring.AUTHORING_RUBRIC       # default unchanged
