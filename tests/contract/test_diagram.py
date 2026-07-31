"""Layer 1 — architecture diagram: the entry-point scanner (a deterministic sibling of the system-context
scan) and the diagram freshness stamp. The entry-point scan feeds the repo overview's Architecture (data flow)
'Entry points' cluster; like the system-context scan it reports only OBSERVED, file:line-backed entries and
never fabricates a node. Its provenance is kept SEPARATE from the system-context scanner, and the diagram's
architecture-fingerprint stamp is distinct from the system-context-fingerprint stamp.
"""
import json

from spec_eval import authoring, providers, syscontext
from spec_eval.authoring import ARCH_DIAGRAM_RUBRIC


def _write(root, files):
    for rel, body in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body)
    return root


# --- entry-point detection: one assertion per class -------------------------------------------------------

def _kinds(root):
    ep = syscontext.scan_entrypoints(str(root), {})
    return {e["kind"]: e for e in ep["entrypoints"]}


def test_bare_main_guard_is_a_module_main(tmp_path):
    _write(tmp_path, {"run.py": "def main():\n    print('hi')\n\nif __name__ == '__main__':\n    main()\n"})
    k = _kinds(tmp_path)
    assert "module-main" in k and k["module-main"]["name"] == "run"


def test_argparse_main_is_a_cli_main(tmp_path):
    _write(tmp_path, {"cli.py": "import argparse\n\ndef main():\n    argparse.ArgumentParser()\n\n"
                                 "if __name__ == '__main__':\n    main()\n"})
    k = _kinds(tmp_path)
    assert "cli-main" in k and "module-main" not in k        # argparse promotes it above a bare guard


def test_dunder_main_is_a_package_main(tmp_path):
    _write(tmp_path, {"pkg/__main__.py": "from . import cli\ncli.main()\n"})
    k = _kinds(tmp_path)
    assert "package-main" in k and k["package-main"]["target"] == "python -m pkg"


def test_project_scripts_manifest_is_a_declared_script(tmp_path):
    _write(tmp_path, {"pyproject.toml": '[project.scripts]\nmytool = "pkg.cli:main"\n',
                      "pkg/cli.py": "def main():\n    pass\n"})
    k = _kinds(tmp_path)
    assert "script" in k and k["script"]["name"] == "mytool" and k["script"]["target"] == "pkg.cli:main"


def test_framework_app_object_is_an_observed_capability_not_the_entry_point(tmp_path):
    _write(tmp_path, {"web.py": "from flask import Flask\napp = Flask(__name__)\n"})
    k = _kinds(tmp_path)
    assert "web-app" in k
    # labeled as construction (a capability), never asserted as THE served entry point
    assert "constructed" in k["web-app"]["target"] and "Flask" in k["web-app"]["target"]


# --- honesty: prose and excluded code are never entry points ----------------------------------------------

def test_a_main_guard_inside_a_docstring_is_not_an_entry_point(tmp_path):
    _write(tmp_path, {"lib.py": '"""Example:\n\n    if __name__ == \'__main__\':\n        main()\n"""\n'
                                "def f():\n    return 1\n"})
    assert syscontext.scan_entrypoints(str(tmp_path), {})["entrypoints"] == []


def test_tests_and_example_dirs_are_never_scanned_for_entry_points(tmp_path):
    _write(tmp_path, {"tests/test_x.py": "if __name__ == '__main__':\n    run()\n",
                      "examples/demo.py": "if __name__ == '__main__':\n    demo()\n"})
    assert syscontext.scan_entrypoints(str(tmp_path), {})["entrypoints"] == []


def test_module_main_cluster_is_capped(tmp_path):
    files = {f"m{i}.py": "if __name__ == '__main__':\n    go()\n" for i in range(syscontext.EP_MODULE_MAIN_CAP + 4)}
    _write(tmp_path, files)
    eps = syscontext.scan_entrypoints(str(tmp_path), {})["entrypoints"]
    assert sum(1 for e in eps if e["kind"] == "module-main") == syscontext.EP_MODULE_MAIN_CAP


def test_a_capped_module_main_tier_is_reported_not_silently_dropped(tmp_path):
    """A cap that drops evidence must leave a receipt, like coverage's '… and N more' — the block states the
    held-back count, and the count feeds the architecture digest so the (N+1)th guard still trips staleness."""
    n = syscontext.EP_MODULE_MAIN_CAP
    _write(tmp_path, {f"m{i}.py": "if __name__ == '__main__':\n    go()\n" for i in range(n + 2)})
    ep = syscontext.scan_entrypoints(str(tmp_path), {})
    assert ep["module_mains_capped"] == 2
    assert "2 further bare `__main__` guard(s) observed but not listed" in syscontext.entrypoints_block(ep)

    at_cap = dict(ep, module_mains_capped=0)                    # the same repo with the cap exactly met
    assert (syscontext.architecture_digest({}, ep, ["a.py"])
            != syscontext.architecture_digest({}, at_cap, ["a.py"]))


# --- determinism + evidence -------------------------------------------------------------------------------

def test_entrypoint_scan_is_deterministic(tmp_path):
    _write(tmp_path, {"pyproject.toml": '[project.scripts]\nt = "p.c:main"\n',
                      "p/__main__.py": "x = 1\n", "run.py": "if __name__ == '__main__':\n    go()\n"})
    a = syscontext.scan_entrypoints(str(tmp_path), {})
    b = syscontext.scan_entrypoints(str(tmp_path), {})
    assert a == b and json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_every_entry_point_carries_file_line_evidence(tmp_path):
    _write(tmp_path, {"run.py": "if __name__ == '__main__':\n    go()\n"})
    for e in syscontext.scan_entrypoints(str(tmp_path), {})["entrypoints"]:
        assert e["evidence"]["file"] and e["evidence"]["line"] >= 1 and e["evidence"]["match"]


# --- the block marker agrees with the rubric --------------------------------------------------------------

def test_entrypoints_block_marker_agrees_with_the_rubric(tmp_path):
    _write(tmp_path, {"run.py": "if __name__ == '__main__':\n    go()\n"})
    ep = syscontext.scan_entrypoints(str(tmp_path), {})
    block = syscontext.entrypoints_block(ep)
    assert "OBSERVED ENTRY POINTS" in block
    assert "OBSERVED ENTRY POINTS" in ARCH_DIAGRAM_RUBRIC       # rubric renders the block the scanner emits
    assert "scanner-verified entry point" in ARCH_DIAGRAM_RUBRIC   # ...as provenance-noted sequence entries


# --- provenance is separate from the system-context scanner -----------------------------------------------

def test_entrypoint_knowledge_never_rebaselines_the_system_context_fingerprint(monkeypatch):
    """The entry-point detection tables are deliberately absent from `_tables_digest`: teaching the scanner a
    new framework or moving the module-main cap must never make a stored system-context baseline read as a
    scanner re-baseline."""
    base = syscontext._tables_digest()
    monkeypatch.setattr(syscontext, "FRAMEWORK_APP_FACTORIES", syscontext.FRAMEWORK_APP_FACTORIES + ("Litestar",))
    monkeypatch.setattr(syscontext, "EP_MODULE_MAIN_CAP", syscontext.EP_MODULE_MAIN_CAP + 1)
    assert syscontext._tables_digest() == base


# --- architecture digest / stamp: distinct from the system-context stamp ----------------------------------

def _ctx(entries):
    return {"entries": [{"system": s, "direction": d} for s, d in entries]}


def _ep(keys):
    return {"entrypoints": [{"kind": k, "name": n, "target": t} for k, n, t in keys]}


def test_architecture_digest_moves_on_system_entrypoint_or_module_change():
    base = syscontext.architecture_digest(_ctx([("Redis", "outbound")]),
                                          _ep([("script", "t", "p:main")]), ["a.py", "b.py"])
    assert base == syscontext.architecture_digest(_ctx([("Redis", "outbound")]),      # stable input -> stable
                                                  _ep([("script", "t", "p:main")]), ["b.py", "a.py"])
    assert base != syscontext.architecture_digest(_ctx([("Redis", "outbound"), ("S3", "outbound")]),
                                                  _ep([("script", "t", "p:main")]), ["a.py", "b.py"])
    assert base != syscontext.architecture_digest(_ctx([("Redis", "outbound")]),
                                                  _ep([("cli-main", "t", "cli")]), ["a.py", "b.py"])
    assert base != syscontext.architecture_digest(_ctx([("Redis", "outbound")]),      # a module added
                                                  _ep([("script", "t", "p:main")]), ["a.py", "b.py", "c.py"])


def test_architecture_stamp_is_distinct_from_the_system_context_stamp():
    ctx, ep = _ctx([("Redis", "outbound")]), _ep([("script", "t", "p:main")])
    md = syscontext.stamp_comment(ctx) + "\n" + syscontext.architecture_stamp_comment(ctx, ep, ["a.py"])
    assert syscontext.read_stamp(md) != syscontext.read_arch_stamp(md)     # two disjoint digests
    assert syscontext.read_stamp(md) == syscontext.fingerprint_digest(ctx)
    assert syscontext.read_arch_stamp(md) == syscontext.architecture_digest(ctx, ep, ["a.py"])


def test_diagram_stale_flips_when_an_entry_point_changes():
    ctx, ep = _ctx([("Redis", "outbound")]), _ep([("script", "t", "p:main")])
    md = f"## Architecture (data flow)\n\n{syscontext.architecture_stamp_comment(ctx, ep, ['a.py'])}\n"
    assert syscontext.diagram_stale(md, ctx, ep, ["a.py"]) is False
    ep2 = _ep([("script", "t", "p:main"), ("cli-main", "u", "cli")])
    assert syscontext.diagram_stale(md, ctx, ep2, ["a.py"]) is True


# --- the generate flow stamps the repo overview (and only the repo overview) ------------------------------

def test_generate_stamps_the_repo_overview_with_an_architecture_fingerprint(tmp_path, monkeypatch):
    monkeypatch.setattr(providers, "gen", lambda m, s, u, max_tokens=1200: "## Architecture (data flow)\n\n| x |\n")
    _write(tmp_path, {"a.py": "x = 1\n", "run.py": "if __name__ == '__main__':\n    go()\n"})
    authoring.generate_repo(str(tmp_path), {"authoring": {"overview": "repo"}}, "fake:model")
    overview = (tmp_path / "OVERVIEW.md").read_text()
    assert syscontext.read_arch_stamp(overview) is not None
    ctx = syscontext.scan(str(tmp_path), {})
    ep = syscontext.scan_entrypoints(str(tmp_path), {})
    modules = authoring.module_set(str(tmp_path), {})           # the same code-file set the stamp binds to
    assert syscontext.diagram_stale(overview, ctx, ep, modules) is False


def test_a_non_document_reply_is_never_written_or_stamped(tmp_path, monkeypatch):
    """A stamp is a RECEIPT. When the model answers with a question or a refusal instead of a document, the
    overview must not be written and must carry no fingerprint — a stamped non-document reads as FRESH to
    `context --check`, which is worse than no overview at all. Not writing also keeps the next run from
    skipping the target as already-existing."""
    monkeypatch.setattr(providers, "gen", lambda m, s, u, max_tokens=1200:
                        "I need the module specs to build this. Could you paste them, or give me a path?")
    _write(tmp_path, {"a.py": "import redis\n"})
    res = authoring.generate_repo(str(tmp_path), {"authoring": {"overview": "repo"}}, "fake:model")
    rec = next(r for r in res if r["spec"] == "OVERVIEW.md")
    assert rec["status"] == "failed" and "not an overview" in rec["note"]
    assert not (tmp_path / "OVERVIEW.md").exists()          # nothing written -> the next run retries it


def test_per_dir_readme_is_not_architecture_stamped(tmp_path, monkeypatch):
    monkeypatch.setattr(providers, "gen", lambda m, s, u, max_tokens=1200: "## Map\n\n| x |\n")
    _write(tmp_path, {"pkg/a.py": "x = 1\n", "pkg/b.py": "y = 2\n"})
    authoring.generate_repo(str(tmp_path), {"authoring": {"overview": "per-dir"}}, "fake:model")
    readme = (tmp_path / "pkg" / "README.md").read_text()
    assert syscontext.read_arch_stamp(readme) is None          # the diagram + its stamp are repo-level only


# --- regressions from the implementation review -----------------------------------------------------------

def test_manifest_scripts_decode_as_utf8_not_the_host_locale(tmp_path):
    """A non-ASCII console-script target must decode as UTF-8 regardless of the host locale, or the same tree
    fingerprints differently across machines (a determinism break). Pins the UTF-8 read."""
    (tmp_path / "pyproject.toml").write_bytes('[project.scripts]\nt = "pkg.café:main"\n'.encode("utf-8"))
    (tmp_path / "pkg" / "café.py").parent.mkdir(exist_ok=True)
    scripts = {e["name"]: e["target"] for e in syscontext.scan_entrypoints(str(tmp_path), {})["entrypoints"]}
    assert scripts.get("t") == "pkg.café:main"


def test_toml_scripts_header_with_a_trailing_comment_is_recognized(tmp_path):
    _write(tmp_path, {"pyproject.toml": '[project.scripts]  # console entry points\nfoo = "pkg.cli:main"\n'})
    names = {e["name"] for e in syscontext.scan_entrypoints(str(tmp_path), {})["entrypoints"]}
    assert "foo" in names                                      # the trailing comment must not hide the section


def test_a_non_script_toml_table_does_not_leak_scripts(tmp_path):
    """A key in an unrelated table (e.g. [tool.foo]) after [project.scripts] must NOT be fabricated as a
    console script — a false entry point would ride the diagram as scanner-verified."""
    _write(tmp_path, {"pyproject.toml": '[project.scripts]\nreal = "pkg.cli:main"\n[tool.foo]\nname = "not-a-script"\n'})
    names = {e["name"] for e in syscontext.scan_entrypoints(str(tmp_path), {})["entrypoints"]}
    assert "real" in names and "name" not in names


def test_a_main_guard_inside_a_string_literal_is_not_an_entry_point(tmp_path):
    """`_visible_lines` preserves string-literal contents (the system-context scan needs literal URLs), so the
    guard match must be anchored to a statement position — a guard-shaped substring in a string is not a root."""
    _write(tmp_path, {"help.py": "HELP = \"run with: if __name__ == '__main__'\"\ndef go():\n    return HELP\n"})
    assert syscontext.scan_entrypoints(str(tmp_path), {})["entrypoints"] == []


def test_has_architecture_section_is_fence_aware():
    """The cheap precondition `diagram --write` checks before synthesising — a real section is present, a
    section-less doc or a fenced example is not."""
    assert authoring.has_architecture_section("# P\n\n## Architecture (data flow)\nx\n")
    assert not authoring.has_architecture_section("# P\n\n## Install\nrun it\n")
    assert not authoring.has_architecture_section("# P\n\n```md\n## Architecture (data flow)\nex\n```\n")


def test_set_architecture_section_ignores_a_heading_inside_a_code_fence(tmp_path):
    md = ("## What it is\nExample of the format:\n```md\n## Architecture (data flow)\nEXAMPLE\n```\n\n"
          "## Architecture (data flow)\nREAL old diagram\n\n## System context\n| x |\n")
    out = authoring.set_architecture_section(md, "```mermaid\nflowchart TD\n  a --> b\n```\n> caveat")
    assert "EXAMPLE" in out                                    # the fenced example is not the section — untouched
    assert "REAL old diagram" not in out and "flowchart TD" in out   # the real section body was replaced


GENERATED_BODY = ("### How it is invoked\n```mermaid\nsequenceDiagram\n    actor U as User\n    U->>R: run\n```\n\n"
                  "### Data flow\n```mermaid\nflowchart LR\n    A --> B\n```\n> caveat\n")


def test_replacing_a_generated_section_is_idempotent_not_cumulative(tmp_path):
    """THE shape the feature itself produces: an Architecture body is two '###' subsections. The section must
    end at the next '##' — ending at a '###' would replace only the first diagram and leave the rest of the
    stale section behind, so every regeneration would append another copy."""
    md = ("# P\n\n## Governing principles\n- **X** — y.\n\n"
          "## Architecture (data flow)\n" + GENERATED_BODY.replace("A --> B", "OLD --> STALE") +
          "\n## System context\n| x |\n")
    once = authoring.set_architecture_section(md, GENERATED_BODY)
    twice = authoring.set_architecture_section(once, GENERATED_BODY)
    for out in (once, twice):
        assert out.count("### How it is invoked") == 1 and out.count("### Data flow") == 1
        assert "OLD --> STALE" not in out                       # the stale diagram is gone, not pushed down
        assert "## Governing principles" in out and "## System context" in out    # neighbours intact
    assert twice == once                                       # regenerating twice changes nothing further


def test_add_section_keeps_the_stamp_footer_at_the_bottom(tmp_path):
    """The receipts are the document's footer: a first-time add goes ABOVE them, never after, so the stamps
    don't end up stranded mid-document."""
    md = "# P\n\n## Install\nrun it\n\n<!-- system-context-fingerprint: aaaa1111bbbb -->\n"
    out = authoring.set_architecture_section(md, GENERATED_BODY, create=True)
    assert out.index("## Architecture (data flow)") < out.index("<!-- system-context-fingerprint")
    assert syscontext.read_stamp(out) == "aaaa1111bbbb"         # and the existing receipt is untouched


def test_set_architecture_section_preserves_a_trailing_system_context_stamp(tmp_path):
    """When Architecture is the LAST heading, its body must stop at the trailing fingerprint receipts, not run
    to EOF — otherwise a diagram update swallows the system-context stamp and re-blesses a stale table."""
    md = ("# P\n\n## System context\n| x |\n\n## Architecture (data flow)\nold\n\n"
          "<!-- system-context-fingerprint: aaaa1111bbbb -->\n"
          "<!-- architecture-fingerprint: cccc2222dddd -->\n")
    out = authoring.set_architecture_section(md, "```mermaid\nflowchart TD\n  a --> b\n```\n> caveat")
    assert "old" not in out and "flowchart TD" in out
    assert syscontext.read_stamp(out) == "aaaa1111bbbb"        # system-context stamp NOT swallowed
