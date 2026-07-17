"""Layer 2 — acceptance criteria for orphaned-spec detection and third-party pruning. The orphan check is a
free, advisory heuristic: it never moves the coverage percentage, and conventional docs are never flagged."""
from spec_eval import coverage


def test_aco001_orphan_flagged_when_its_code_file_is_gone(tmp_path):
    """ACO-001. Given a dir with code and a spec-shaped .md whose same-stem code file no longer exists,
    When coverage runs, Then the .md is listed under orphans and the percentage is unaffected."""
    (tmp_path / "a.py").write_text("x = 1\n")
    (tmp_path / "a.md").write_text("## 1. Purpose\nA.\n")
    (tmp_path / "b.md").write_text("## 1. Purpose\nB — but b.py was moved away.\n")
    cov = coverage.coverage(str(tmp_path), {})
    assert cov["orphans"] == ["b.md"]
    assert cov["pct"] == 100.0                                   # advisory only — pct untouched


def test_aco002_conventional_docs_and_folder_specs_are_never_orphans(tmp_path):
    """ACO-002. Given a README and a folder spec beside code, When coverage runs, Then neither is flagged."""
    pkg = tmp_path / "src" / "pkg"
    pkg.mkdir(parents=True)
    (pkg / "a.py").write_text("x = 1\n")
    (pkg / "README.md").write_text("docs\n")
    (pkg / "pkg.md").write_text("folder spec\n")
    cov = coverage.coverage(str(tmp_path), {})
    assert cov["orphans"] == []


def test_aco003_docs_only_dirs_and_pair_docs_are_never_orphans(tmp_path):
    """ACO-003. Given a docs-only directory and a pair-declared doc beside code, When coverage runs,
    Then neither is flagged (docs-only dirs hold docs; a paired doc is governed wherever its code lives)."""
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "design.md").write_text("free-floating docs\n")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("x = 1\n")
    (tmp_path / "src" / "notes.md").write_text("declared in pairs\n")
    cfg = {"pairs": [{"label": "a", "code": ["src/a.py"], "docs": ["src/notes.md"]}]}
    cov = coverage.coverage(str(tmp_path), cfg)
    assert cov["orphans"] == []


def test_aco004_vendored_dirs_and_minified_bundles_are_not_spec_worthy(tmp_path):
    """ACO-004. Given vendored third-party code and a minified bundle, When coverage runs, Then neither is a
    spec-worthy candidate (vendor/ is pruned; *.min.js classifies as generated)."""
    (tmp_path / "vendor" / "lib").mkdir(parents=True)
    (tmp_path / "vendor" / "lib" / "pico.py").write_text("x = 1\n")
    (tmp_path / "static").mkdir()
    (tmp_path / "static" / "app.min.js").write_text("!function(){}();\n")
    (tmp_path / "app.py").write_text("x = 1\n")
    cov = coverage.coverage(str(tmp_path), {})
    assert cov["uncovered"] == ["app.py"]                        # the only spec-worthy file
    assert "static/app.min.js" in (cov["excluded"].get("generated") or [])


def test_aco005_user_excluded_paths_are_never_orphans(tmp_path):
    """ACO-005. Given an .md under a user-excluded tree (with code beside it), When coverage runs,
    Then it is not flagged — the repo's own `exclude:` scoping governs the orphan scan too."""
    (tmp_path / "examples").mkdir()
    (tmp_path / "examples" / "demo.py").write_text("x = 1\n")
    (tmp_path / "examples" / "_notes.md").write_text("a method note, not an orphan\n")
    cov = coverage.coverage(str(tmp_path), {"exclude": ["examples/*"]})
    assert cov["orphans"] == []
