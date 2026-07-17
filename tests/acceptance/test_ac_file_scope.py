"""Layer 2 — single-file scope: audit / sufficiency / generate accept ONE code file with no config; the pair
is synthesized from its co-located spec (or the folder spec under a per-dir layout). coverage stays
directory-only and says so instead of silently reporting 0/0."""
import json
import os

import pytest

from spec_eval import cli


def test_acf001_audit_a_single_file_grades_exactly_that_pair(repo, fake_model, tmp_path):
    """ACF-001. Given a code file with a co-located spec, When audit runs on the FILE, Then exactly that one
    pair is audited — no config needed."""
    out = str(tmp_path / "out")
    cli.main(["audit", str(repo / "widget.py"), "--model", fake_model, "--out", out])
    results = json.load(open(os.path.join(out, "findings.json")))
    assert len(results) == 1 and results[0]["label"] == "widget" and not results[0].get("skipped")


def test_acf002_sufficiency_a_single_file(repo, fake_model, tmp_path):
    """ACF-002. Given a code file with a co-located spec, When sufficiency runs on the FILE, Then that one
    pair is scored."""
    out = str(tmp_path / "out")
    cli.main(["sufficiency", str(repo / "widget.py"), "--model", fake_model, "--out", out])
    results = json.load(open(os.path.join(out, "sufficiency.json")))
    assert len(results) == 1 and results[0]["label"] == "widget" and results[0]["sufficiency"] == 0.90


def test_acf003_generate_a_single_file_authors_only_its_spec(repo, fake_model, tmp_path):
    """ACF-003. Given an uncovered code file, When generate runs on the FILE, Then exactly its spec is
    authored beside it (and a second run skips it); the covered neighbour is untouched."""
    out = str(tmp_path / "out")
    cli.main(["generate", str(repo / "helper.py"), "--model", fake_model, "--out", out])
    assert (repo / "helper.md").exists()
    res = json.load(open(os.path.join(out, "generated.json")))
    assert [r["status"] for r in res] == ["authored"] and res[0]["spec"] == "helper.md"
    cli.main(["generate", str(repo / "helper.py"), "--model", fake_model, "--out", out])
    res = json.load(open(os.path.join(out, "generated.json")))
    assert [r["status"] for r in res] == ["skipped"]                    # no clobber on re-run


def test_acf004_per_dir_layout_falls_back_to_the_folder_spec(tmp_path, fake_model):
    """ACF-004. Given a per-dir layout and a folder spec, When audit runs on a FILE with no co-located .md,
    Then the synthesized pair uses the folder spec (not a skip)."""
    pkg = tmp_path / "src" / "pkg"
    pkg.mkdir(parents=True)
    (pkg / "a.py").write_text("x = 1\n")
    (pkg / "pkg.md").write_text("## 1. Purpose\nthe folder spec\n")
    cfg = tmp_path / "cfg.yml"
    cfg.write_text("authoring:\n  layout: per-dir\n")
    out = str(tmp_path / "out")
    cli.main(["audit", str(pkg / "a.py"), "--config", str(cfg), "--model", fake_model, "--out", out])
    results = json.load(open(os.path.join(out, "findings.json")))
    assert len(results) == 1 and results[0]["label"] == "a" and not results[0].get("skipped")


def test_acf005_coverage_on_a_file_errors_with_guidance(repo, tmp_path):
    """ACF-005. Given a FILE path, When coverage runs, Then it exits with a message pointing at the directory
    (the old behavior was a silent, useless 0/0 report)."""
    with pytest.raises(SystemExit) as e:
        cli.main(["coverage", str(repo / "widget.py"), "--out", str(tmp_path / "out")])
    assert "directories" in str(e.value)
