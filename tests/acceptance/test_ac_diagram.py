"""Layer 2 — acceptance criteria for the `diagram` subcommand. Model-backed via the fake provider (no API
key). Default mode is a pure read → STDOUT that touches nothing; --write is replace-only against an EXISTING
'## Architecture (data flow)' section and re-stamps ONLY the architecture fingerprint (never the
system-context stamp); it refuses to create or corrupt a doc."""
import os

import pytest

from spec_eval import authoring, cli, providers, syscontext


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


def test_acd003_write_errors_when_the_doc_has_no_architecture_section(tmp_path, fake_model, monkeypatch):
    """ACD-003. Given a README with no Architecture section, When `diagram --write` runs (replace-only), Then
    it errors and points at --add-section/generate — it never injects a section into an arbitrary doc, and it
    refuses BEFORE synthesising (no wasted model calls)."""
    (tmp_path / "a.py").write_text("x = 1\n")
    (tmp_path / "README.md").write_text("# Proj\n\n## Install\nrun it\n")
    synthesised = []
    monkeypatch.setattr(authoring, "diagram_block", lambda *a, **k: synthesised.append(1))
    with pytest.raises(SystemExit) as ex:
        cli.main(["diagram", str(tmp_path), "--write", "-m", fake_model])
    assert "--add-section" in str(ex.value)
    assert synthesised == []                                   # failed fast — diagram_block never ran
    assert (tmp_path / "README.md").read_text() == "# Proj\n\n## Install\nrun it\n"   # left intact


def test_acd009_add_section_appends_a_diagram_to_an_existing_doc_that_lacks_one(tmp_path, fake_model):
    """ACD-009. Given an existing README with no Architecture section, When `diagram --write --add-section`
    runs, Then the section is APPENDED and architecture-stamped — the explicit opt-in for a first-time add
    (e.g. a lean per-directory README)."""
    (tmp_path / "a.py").write_text("x = 1\n")
    (tmp_path / "README.md").write_text("# Proj\n\n## Install\nrun it\n")
    cli.main(["diagram", str(tmp_path), "--write", "--add-section", "-m", fake_model])
    md = (tmp_path / "README.md").read_text()
    assert "## Install\nrun it" in md                          # original content preserved
    assert "## Architecture (data flow)" in md and "```mermaid" in md    # section appended
    assert syscontext.read_arch_stamp(md) is not None


def test_acd010_add_section_still_never_creates_a_doc(tmp_path, fake_model, monkeypatch):
    """ACD-010. Given no OVERVIEW.md/README.md, When `diagram --write --add-section` runs, Then it still errors
    to `generate` — the opt-in relaxes 'section must exist', never 'doc must exist' — and fails fast."""
    (tmp_path / "a.py").write_text("x = 1\n")
    synthesised = []
    monkeypatch.setattr(authoring, "diagram_block", lambda *a, **k: synthesised.append(1))
    with pytest.raises(SystemExit) as ex:
        cli.main(["diagram", str(tmp_path), "--write", "--add-section", "-m", fake_model])
    assert "generate" in str(ex.value)
    assert synthesised == []                                   # no target doc -> refused before synthesis
    assert not (tmp_path / "README.md").exists() and not (tmp_path / "OVERVIEW.md").exists()


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


def test_acd011_a_second_write_replaces_the_section_it_wrote(tmp_path, fake_model):
    """ACD-011. Given a doc `diagram --write` already wrote (so its Architecture body is two '###'
    subsections), When `--write` runs again, Then the section is REPLACED — the doc does not accumulate a
    second copy of the diagrams on every regeneration."""
    (tmp_path / "a.py").write_text("x = 1\n")
    (tmp_path / "OVERVIEW.md").write_text("# Proj\n\n## Architecture (data flow)\nold\n\n## System context\n| x |\n")
    cli.main(["diagram", str(tmp_path), "--write", "-m", fake_model])
    first = (tmp_path / "OVERVIEW.md").read_text()
    cli.main(["diagram", str(tmp_path), "--write", "-m", fake_model])
    second = (tmp_path / "OVERVIEW.md").read_text()
    assert second.count("### How it is invoked") == 1 and second.count("### Data flow") == 1
    assert second == first                                     # same code + same reply -> byte-identical doc


def test_acd012_a_reply_with_no_mermaid_block_never_overwrites_the_doc(tmp_path, fake_model, monkeypatch):
    """ACD-012. Given a model reply carrying no ```mermaid block (an empty or derailed synthesis), When
    `diagram --write` runs, Then it exits non-zero and the doc is left BYTE-IDENTICAL — a bad reply must not
    blank a good diagram."""
    (tmp_path / "a.py").write_text("x = 1\n")
    original = "# Proj\n\n## Architecture (data flow)\n```mermaid\nflowchart LR\n  A --> B\n```\n> caveat\n"
    (tmp_path / "OVERVIEW.md").write_text(original)
    monkeypatch.setattr(authoring, "diagram_block", lambda *a, **k: ("I could not produce a diagram.", {}, {}, ["a.py"], None))
    with pytest.raises(SystemExit) as ex:
        cli.main(["diagram", str(tmp_path), "--write", "-m", fake_model])
    assert "mermaid" in str(ex.value)
    assert (tmp_path / "OVERVIEW.md").read_text() == original


def test_acd013_a_diagram_is_synthesised_in_exactly_one_pass(tmp_path, fake_model, monkeypatch, capsys):
    """ACD-013. Given module intents far over the reduce cap, When `diagram` runs, Then there is exactly ONE
    synthesis call — a diagram is never drawn from other diagrams — every module still reaches it, and the
    slicing is reported rather than passed off as a full view."""
    monkeypatch.setattr(authoring, "REDUCE_CAP", 400)
    for i in range(6):
        (tmp_path / f"m{i}.py").write_text("x = 1\n")
        (tmp_path / f"m{i}.md").write_text(f"## 1. Purpose\n\n**In one line:** module {i}.\n" + "filler. " * 60)
    seen = []
    real_gen = providers.gen
    monkeypatch.setattr(providers, "gen", lambda m, s, u, **k: (seen.append(u), real_gen(m, s, u, **k))[1])
    cli.main(["diagram", str(tmp_path), "-m", fake_model])
    assert len(seen) == 1                                      # one picture, drawn once
    for i in range(6):
        assert f"m{i}.py" in seen[0]                           # ...over every module, none dropped
    assert "sliced to an equal share" in capsys.readouterr().err   # the partial view is reported


def test_acd014_a_generated_repo_overview_is_a_document_with_its_stamps_last(tmp_path, fake_model):
    """ACD-014. Given `generate --overview repo`, When it writes OVERVIEW.md, Then the file is a real document
    — the rubric's sections survive the write path intact — and BOTH fingerprint receipts sit after the last
    section. The rest of the acceptance layer asserts a file landed with some status; this asserts what landed
    is a page, and that the stamps are a footer rather than something buried mid-document."""
    (tmp_path / "a.py").write_text("import redis\n")
    cli.main(["generate", str(tmp_path), "--overview", "repo", "-m", fake_model, "--out", str(tmp_path / "rep")])
    md = (tmp_path / "OVERVIEW.md").read_text()

    sections = [ln for ln in md.splitlines() if ln.startswith("## ")]
    assert sections[0] == "## What it is" and sections[-1] == "## Reading order"
    assert "```mermaid" in md                                  # the Architecture section survived the write

    last_section = md.rindex("## Reading order")
    for stamp in ("system-context-fingerprint", "architecture-fingerprint"):
        assert md.index(stamp) > last_section, f"{stamp} is buried inside the document"
    assert md.rstrip().endswith("-->")                         # the receipts are the footer


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
