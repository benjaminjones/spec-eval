"""Layer 2 — acceptance criteria for the `diagram` subcommand. Model-backed via the fake provider (no API
key). Default mode is a pure read → STDOUT that touches nothing; --write is replace-only against an EXISTING
'## Architecture (data flow)' section and re-stamps ONLY the architecture fingerprint (never the
system-context stamp); it refuses to create or corrupt a doc."""
import os

import pytest

from spec_eval import cli, syscontext


def test_acd001_stdout_prints_a_mermaid_block_and_touches_nothing(tmp_path, fake_model, capsys):
    """ACD-001. Given a repo, When `diagram <dir>` runs, Then a ```mermaid block is printed to stdout and NO
    file is created or changed."""
    (tmp_path / "a.py").write_text("x = 1\n")
    before = set(os.listdir(tmp_path))
    cli.main(["diagram", str(tmp_path), "-m", fake_model])
    out = capsys.readouterr().out
    assert "```mermaid" in out and "flowchart" in out
    assert set(os.listdir(tmp_path)) == before                   # touched nothing, created nothing


def test_acd002_write_updates_the_architecture_section_and_restamps_only_the_diagram(tmp_path, fake_model):
    """ACD-002. Given an OVERVIEW with an Architecture section and a system-context stamp, When
    `diagram <dir> --write` runs, Then the section body is replaced with the mermaid block, the architecture
    fingerprint is (re)stamped fresh, and the system-context stamp is left BYTE-IDENTICAL (no laundering)."""
    (tmp_path / "a.py").write_text("x = 1\n")
    (tmp_path / "OVERVIEW.md").write_text(
        "# Proj\n\n## Architecture (data flow)\nold ascii flow\n\n## System context\n| x |\n\n"
        "<!-- system-context-fingerprint: abc123abc123 -->\n")
    cli.main(["diagram", str(tmp_path), "--write", "-m", fake_model])
    md = (tmp_path / "OVERVIEW.md").read_text()
    assert "```mermaid" in md and "old ascii flow" not in md      # section body replaced
    assert "## System context" in md                             # neighbouring section preserved
    assert syscontext.read_stamp(md) == "abc123abc123"           # system-context stamp untouched (not re-blessed)
    ctx = syscontext.scan(str(tmp_path), {})
    ep = syscontext.scan_entrypoints(str(tmp_path), {})
    from spec_eval import authoring
    assert syscontext.diagram_stale(md, ctx, ep, authoring.module_set(str(tmp_path), {})) is False


def test_acd003_write_errors_when_the_doc_has_no_architecture_section(tmp_path, fake_model):
    """ACD-003. Given a README with no Architecture section, When `diagram --write` runs, Then it errors and
    points at `generate` — it never injects a section into an arbitrary doc."""
    (tmp_path / "a.py").write_text("x = 1\n")
    (tmp_path / "README.md").write_text("# Proj\n\n## Install\nrun it\n")
    with pytest.raises(SystemExit) as ex:
        cli.main(["diagram", str(tmp_path), "--write", "-m", fake_model])
    assert "generate" in str(ex.value)
    assert (tmp_path / "README.md").read_text() == "# Proj\n\n## Install\nrun it\n"   # left intact


def test_acd004_write_errors_when_no_overview_markdown_exists(tmp_path, fake_model):
    """ACD-004. Given no OVERVIEW.md/README.md at the scope, When `diagram --write` runs, Then it errors to
    `generate` rather than creating an orphan doc."""
    (tmp_path / "a.py").write_text("x = 1\n")
    with pytest.raises(SystemExit) as ex:
        cli.main(["diagram", str(tmp_path), "--write", "-m", fake_model])
    assert "generate" in str(ex.value)
    assert not (tmp_path / "OVERVIEW.md").exists()


def test_acd005_a_file_argument_diagrams_its_directory(tmp_path, fake_model, capsys):
    """ACD-005. Given a file path, When `diagram <file>` runs, Then the file's DIRECTORY is diagrammed (a
    single file has no meaningful data flow) — mirrors the file-or-dir scoping of the other commands."""
    (tmp_path / "a.py").write_text("x = 1\n")
    (tmp_path / "b.py").write_text("y = 2\n")
    cli.main(["diagram", str(tmp_path / "a.py"), "-m", fake_model])
    assert "```mermaid" in capsys.readouterr().out


def test_acd006_write_preserves_the_system_context_stamp_when_architecture_is_last(tmp_path, fake_model):
    """ACD-006. Given an OVERVIEW where Architecture is the LAST heading with a trailing system-context stamp,
    When `diagram --write` runs, Then the system-context stamp is left byte-identical (never re-blessed)."""
    (tmp_path / "a.py").write_text("x = 1\n")
    (tmp_path / "OVERVIEW.md").write_text(
        "# Proj\n\n## System context\n| x |\n\n## Architecture (data flow)\nold ascii\n\n"
        "<!-- system-context-fingerprint: abc123abc123 -->\n")
    cli.main(["diagram", str(tmp_path), "--write", "-m", fake_model])
    md = (tmp_path / "OVERVIEW.md").read_text()
    assert syscontext.read_stamp(md) == "abc123abc123"         # untouched — stale-table detection stays alive
    assert "```mermaid" in md and syscontext.read_arch_stamp(md) is not None


def test_acd007_diagram_on_a_directory_with_no_code_errors_cleanly(tmp_path, fake_model):
    """ACD-007. Given a directory with no spec-worthy code files, When `diagram` runs, Then it exits with a
    clean message rather than a traceback."""
    (tmp_path / "notes.txt").write_text("just notes\n")
    with pytest.raises(SystemExit) as ex:
        cli.main(["diagram", str(tmp_path), "-m", fake_model])
    assert "nothing to diagram" in str(ex.value)


def test_acd008_check_warns_for_a_stale_readme_diagram(tmp_path, fake_model, capsys):
    """ACD-008. Given a README (no OVERVIEW.md) that `diagram --write` architecture-stamped, When the code's
    systems change and `context --check` runs, Then it warns on the stale README diagram — the freshness check
    reads whichever doc got stamped, not only OVERVIEW.md."""
    (tmp_path / "a.py").write_text("import psycopg2\n")
    (tmp_path / "README.md").write_text("# P\n\n## Architecture (data flow)\nflow\n\n## System context\n| x |\n")
    out = tmp_path / "reports"
    cli.main(["diagram", str(tmp_path), "--write", "-m", fake_model])      # stamps README.md
    cli.main(["context", str(tmp_path), "--out", str(out)])                # baseline (psycopg2 only)
    (tmp_path / "b.py").write_text("import redis\n")                       # a new system -> diagram now stale
    capsys.readouterr()
    with pytest.raises(SystemExit):
        cli.main(["context", str(tmp_path), "--check", "--out", str(out)])
    assert "README.md architecture diagram is stale" in capsys.readouterr().out
