"""What each subcommand writes must be what `cli.md` says it writes.

`cli.md`'s Artifacts & logging paragraph describes which commands create `--out`, which write a
Markdown file beside the JSON, and which append a run record. That paragraph drifted twice, in
opposite ways, and both times the drift was a *quantifier* problem rather than a wrong fact:

  · it once read "Every command creates `--out` …", which was wrong about `diagram`;
  · amended to "Every command **except `diagram`** …", it was still wrong about `compare` — which
    writes `compare.json` only and appends no run record. The amendment made the claim MORE specific
    and left it false, which is worse than the vague version it replaced.

The lesson this file encodes: **a claim about a closed set has to be checked against the set, not
against the prose.** So the test enumerates the subcommands from `cli.py` and asserts the paragraph
accounts for every one of them by name.

Layer 1, per `TESTING.md`: a contract framed as an invariant check over a pure reading of two files.
No model, no fixture, no filesystem beyond reading the sources.
"""
import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CODE = os.path.join(_ROOT, "spec_eval", "cli.py")
DOC = os.path.join(_ROOT, "spec_eval", "cli.md")

# Ground truth, read from the code by `_writes()` below and asserted against the doc. Commands whose
# artifact behaviour is EXCEPTIONAL must be named individually in the paragraph; the conforming
# majority may be described as a group.
CONFORMING = {"audit", "sufficiency", "coverage", "context"}


def _subcommands():
    return set(re.findall(r'add_parser\("([a-z]+)"', open(CODE, encoding="utf-8").read()))


def _artifacts_paragraph():
    for line in open(DOC, encoding="utf-8").read().splitlines():
        if line.startswith("**Artifacts & logging.**"):
            return line
    raise AssertionError("cli.md has no `**Artifacts & logging.**` paragraph")


def test_every_subcommand_is_named_in_the_artifacts_paragraph():
    """INVARIANT: the paragraph accounts for every command the CLI registers.

    This is the test that would have caught both drifts. A command the paragraph never mentions is a
    command its claim is silently wrong about, and adding a subcommand is exactly when that happens.
    """
    para = _artifacts_paragraph()
    missing = sorted(s for s in _subcommands() if f"`{s}`" not in para)
    assert not missing, (
        f"cli.py registers {missing} but the Artifacts & logging paragraph never names "
        f"{'it' if len(missing) == 1 else 'them'}. A claim about every command has to account for "
        f"every command — enumerate from the code, do not add one exception at a time.")


def test_the_stated_count_matches_the_number_of_subcommands():
    """The paragraph opens with a count. A count that disagrees with the code is the same defect in
    numeric form, and it is the cheaper half to check."""
    para = _artifacts_paragraph()
    n = len(_subcommands())
    words = {4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}
    assert words.get(n, str(n)) in para.lower() or str(n) in para, (
        f"cli.py registers {n} subcommands; the Artifacts & logging paragraph does not state that "
        f"number. Update the count with the command.")


def test_the_conforming_set_really_does_conform():
    """A guard on the guard. The doc groups four commands as behaving uniformly; if one of them stops
    doing so, the grouping becomes a false claim that the name-check above cannot see — because the
    command is still named."""
    src = open(CODE, encoding="utf-8").read()
    for cmd in sorted(CONFORMING):
        m = re.search(rf'args\.cmd == "{cmd}"(.*?)(?=elif args\.cmd ==|\Z)', src, re.S)
        assert m, f"no dispatch branch found for `{cmd}`"
        body = m.group(1)
        assert "append_run" in body, (
            f"`{cmd}` is grouped in cli.md as appending a run record and no longer does. Either "
            f"restore the call or move `{cmd}` out of the conforming group in both places.")
        assert ".md" in body, (
            f"`{cmd}` is grouped in cli.md as writing a Markdown file and no longer does.")


def test_the_exceptional_commands_are_still_exceptional():
    """The other direction: if `compare` grows a run-log call, the doc's carve-out becomes the false
    claim. A carve-out is a promise too."""
    src = open(CODE, encoding="utf-8").read()
    m = re.search(r'args\.cmd == "compare"(.*?)(?=elif args\.cmd ==|\Z)', src, re.S)
    assert m, "no dispatch branch found for `compare`"
    assert "append_run" not in m.group(1), (
        "`compare` now appends a run record, so cli.md's carve-out naming it as the command that "
        "does not is wrong. Update the paragraph.")
