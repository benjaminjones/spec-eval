"""Contract: every provenance claim a written artifact makes must be checkable, and every artifact that
appears on disk must be accounted for.

These pin the four trust signals that a validation run against a real repo found unreliable — a chat reply
recorded as an authored spec, a file written outside the declared targets, a `scanner-verified` label citing a
file the scanner never read, and links that resolve from the repo root but not from the document. Each is a
DETERMINISTIC check: no model call, no key.
"""
from spec_eval import authoring, coverage as coverage_mod, syscontext


# --- the document guard: a reply ABOUT the work is not the work ---------------------------------------------

_REAL_SPEC = """## 1. Purpose

**In one line:** Look up one artifact type from the catalog.

## 2. Definitions

| Term | Meaning |
|---|---|
| Entry | One artifact type. |
"""

# the shape a tool-using provider returns when it wrote the file itself and reported back
_WROTE_IT_REPLY = ("I've authored the spec at `/tmp/probe/specs/catalog-show.md`. Summary of what I did:\n\n"
                   "- Read `show.ts` plus its collaborators to pin down exact error strings.\n")

_CHATTY_WITH_HEADINGS = "I've authored the spec at /tmp/x.md.\n\n## Summary\n\n- did a thing\n"


def test_a_real_spec_passes_the_guard():
    md, note = authoring._document_or_none(_REAL_SPEC, None)
    assert md is _REAL_SPEC and note is None


def test_a_heading_free_reply_is_not_a_document():
    md, note = authoring._document_or_none(_WROTE_IT_REPLY, None)
    assert md is None and "heading" in note


def test_a_reply_that_reports_having_authored_is_rejected_even_with_headings():
    """The dangerous case: it has a heading, so a shape floor alone accepts it and records it `authored`."""
    md, note = authoring._document_or_none(_CHATTY_WITH_HEADINGS, None)
    assert md is None and "instead of returning it" in note


def test_the_guard_does_not_fire_on_a_spec_that_merely_mentions_authoring():
    """A spec is allowed to USE these words — only an opening report of having written something is a reply."""
    md, _ = authoring._document_or_none("## 1. Purpose\n\nThis module has authored specs since v2.\n", None)
    assert md is not None


# --- scanner-verified labels: a closed set, so membership is decidable ---------------------------------------

_EP = {"entrypoints": [{"evidence": {"file": "src/cli.py", "line": 12}}]}


def test_a_label_citing_an_observed_site_survives():
    md, n = authoring.verify_scanner_labels("Note over A: scanner-verified entry point (src/cli.py:12)\n", _EP)
    assert n == 0 and "scanner-verified" in md


def test_a_label_citing_an_unobserved_site_is_downgraded():
    md, n = authoring.verify_scanner_labels("Note over B: scanner-verified entry point (tests/x.py:9)\n", _EP)
    assert n == 1
    assert "scanner-verified" not in md
    assert "conventional invocation (per the module intents, not scanner-detected)" in md


def test_an_empty_scan_downgrades_every_label():
    """The load-bearing case: the scanner found NO entry points, so no note may claim it verified one."""
    md, n = authoring.verify_scanner_labels(
        "Note over L: scanner-verified entry point (tests/cli.test.ts:301)\n"
        "Note over S: scanner-verified entry point (src/commands/catalog/show.ts:23)\n", {"entrypoints": []})
    assert n == 2 and "scanner-verified" not in md


def test_verified_sites_is_the_scan_and_nothing_else():
    assert syscontext.verified_entry_sites(_EP) == {"src/cli.py:12"}
    assert syscontext.verified_entry_sites({}) == set()


# --- links resolve from the DOCUMENT, not from the repo root -------------------------------------------------

def test_a_repo_root_relative_link_is_repaired_to_document_relative(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "list.md").write_text("x")
    md = "| [list.md](src/list.md) | purpose |\n"
    out, fixed, broken = authoring.repair_links(md, str(tmp_path), "src/OVERVIEW.md")
    assert fixed == 1 and broken == []
    assert "(list.md)" in out


def test_a_link_that_resolves_from_the_document_is_left_alone(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "list.md").write_text("x")
    out, fixed, broken = authoring.repair_links("[l](list.md)\n", str(tmp_path), "src/OVERVIEW.md")
    assert (fixed, broken, out) == (0, [], "[l](list.md)\n")


def test_an_unresolvable_link_is_reported_and_never_rewritten_to_a_guess(tmp_path):
    out, fixed, broken = authoring.repair_links("[h](SPEC-HEALTH.md)\n", str(tmp_path), "OVERVIEW.md")
    assert fixed == 0 and broken == ["SPEC-HEALTH.md"]
    assert out == "[h](SPEC-HEALTH.md)\n"


def test_external_and_anchor_links_are_untouched(tmp_path):
    md = "[a](https://x.test/y) [b](#section) [c](mailto:x@y.test)\n"
    out, fixed, broken = authoring.repair_links(md, str(tmp_path), "OVERVIEW.md")
    assert (out, fixed, broken) == (md, 0, [])


def test_links_inside_a_fenced_block_are_not_rewritten(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "list.md").write_text("x")
    md = "```\n[list.md](src/list.md)\n```\n"
    out, fixed, _ = authoring.repair_links(md, str(tmp_path), "src/OVERVIEW.md")
    assert fixed == 0 and out == md


# --- stray writes: what appeared on disk vs what the run declared --------------------------------------------

def test_a_file_written_outside_the_declared_targets_is_reported():
    before = {"a.md": (1, 10)}
    after = {"a.md": (2, 20), "specs/catalog-show.md": (2, 40)}
    assert authoring._stray_writes(before, after, ["a.md"]) == ["specs/catalog-show.md"]


def test_an_untouched_file_is_not_a_stray():
    sig = (1, 10)
    assert authoring._stray_writes({"a.md": sig, "b.md": sig}, {"a.md": sig, "b.md": sig}, ["a.md"]) == []


def test_the_inventory_skips_pruned_directories(tmp_path):
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "dep.md").write_text("x")
    (tmp_path / "real.md").write_text("x")
    assert set(authoring._md_inventory(str(tmp_path))) == {"real.md"}


# --- unmodeled markdown: the percentage is scoped, and says so ------------------------------------------------

def _cov(tmp_path):
    return coverage_mod.coverage(str(tmp_path), {})


def test_a_requirement_id_spec_tree_is_reported_as_unmodeled(tmp_path):
    """A spec tree keyed by requirement id has no same-stem code sibling, so pairing cannot see it. It must be
    NAMED rather than silently absent — otherwise 0% reads as 'this project has no specs'."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("x = 1\n")
    (tmp_path / "spec").mkdir()
    for i in (1, 2, 3):
        (tmp_path / "spec" / f"FR-00{i}-does-a-thing.md").write_text("# FR\n")
    cov = _cov(tmp_path)
    assert cov["pct"] == 0.0                                   # the number is unchanged — this never scores
    assert [g["dir"] for g in cov["unmodeled"]] == ["spec"]
    assert cov["unmodeled"][0]["files"] == 3


def test_markdown_implemented_behavior_is_reported_as_unmodeled(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("x = 1\n")
    for name in ("one", "two", "three"):
        d = tmp_path / "skills" / name
        d.mkdir(parents=True)
        (d / "reference.md").write_text("# behavior\n")
    cov = _cov(tmp_path)
    assert [g["dir"] for g in cov["unmodeled"]] == ["skills"]


def test_a_couple_of_loose_docs_are_not_reported(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("x = 1\n")
    (tmp_path / "notes").mkdir()
    (tmp_path / "notes" / "one.md").write_text("x")
    assert _cov(tmp_path)["unmodeled"] == []


def test_conventional_docs_never_count_as_an_unmodeled_corpus(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("x = 1\n")
    (tmp_path / "docs").mkdir()
    for n in ("README.md", "CHANGELOG.md", "CONTRIBUTING.md"):
        (tmp_path / "docs" / n).write_text("x")
    assert _cov(tmp_path)["unmodeled"] == []


def test_the_report_scopes_the_percentage_when_a_corpus_exists(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("x = 1\n")
    (tmp_path / "spec").mkdir()
    for i in (1, 2, 3):
        (tmp_path / "spec" / f"FR-00{i}-x.md").write_text("# FR\n")
    report = coverage_mod.format_report(_cov(tmp_path), str(tmp_path))
    assert "## Unmodeled markdown" in report
    assert "spec/" in report


# --- agent-instruction files are docs, never stale specs ------------------------------------------------------

def test_agent_instruction_files_are_not_proposed_for_removal(tmp_path):
    """`CLAUDE.md` / `AGENTS.md` never had a same-stem code file. Advising their removal is always wrong."""
    (tmp_path / "a.py").write_text("x = 1\n")
    for n in ("CLAUDE.md", "AGENTS.md"):
        (tmp_path / n).write_text("# instructions\n")
    assert _cov(tmp_path)["orphans"] == []


def test_a_genuinely_orphaned_spec_is_still_flagged(tmp_path):
    """The orphan heuristic must keep working — widening the doc list must not blind it."""
    (tmp_path / "a.py").write_text("x = 1\n")
    (tmp_path / "removed_module.md").write_text("# spec for code that is gone\n")
    assert _cov(tmp_path)["orphans"] == ["removed_module.md"]
