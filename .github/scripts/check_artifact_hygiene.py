"""Fail a pull request that leaks something the repository should not publish.

spec-eval's contributing guide and PR template both say a change must be described in the repo's own terms, with
no references to other projects, private repos, or the session that produced it. Both are advisory, so the rule
held only as long as everyone remembered it. This script makes it mechanical.

WHAT IS SCANNED
  the PR title, the PR body, every commit message on the branch, and the ADDED lines of the diff. Added lines
  only: a pre-existing line is not this PR's problem, and failing on one would make an unrelated change red.

TWO CLASSES OF RULE
  Structural rules (below) are generic and live in this file. They catch whole categories: a path from someone's
  machine, a phrase that narrates the chat that produced the change.

  Name rules come from the ARTIFACT_DENYLIST environment variable, one entry per line, matched case-insensitively
  as a literal substring. They are deliberately NOT stored in the repository: a denylist naming the private
  projects would publish exactly what it exists to hide. Set it as a repository secret. When it is unset (a fork
  PR, or a checkout with no secret configured) the structural rules still run and the script says so rather than
  passing silently.

OUTPUT
  A denylist hit is reported REDACTED — the location is named precisely, the matched text is not reproduced,
  because CI logs outlive the branch and may be public. A structural hit is shown in full: it is generic by
  construction and the author needs to see it to fix it.

USAGE
  python .github/scripts/check_artifact_hygiene.py <dir>

  where <dir> holds title.txt, body.txt, commits.txt and diff.txt. Exit 0 = clean, 1 = something to fix.
"""
import os
import re
import sys

# Generic leaks, safe to name in a public file because they describe a SHAPE, not a project.
STRUCTURAL_RULES = [
    (
        "absolute path from a personal machine",
        re.compile(r"(?:/Users/|/home/|[A-Za-z]:\\Users\\)[A-Za-z0-9._-]+", re.I),
        "Use a repo-relative path, or a placeholder like <repo>.",
    ),
    (
        "narration of the session that produced the change",
        re.compile(
            r"\b(?:as (?:we|you) (?:discussed|agreed|asked)|you asked me to|as (?:requested|discussed) above"
            r"|in (?:our|this) (?:chat|conversation|session)|per your request|the previous (?:message|turn)"
            r"|(?:earlier|previously) in this (?:chat|thread|session))\b",
            re.I,
        ),
        "Describe what the code does now, not the conversation that produced it.",
    ),
    (
        "local network address",
        re.compile(r"\b(?:localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}):\d+"),
        "Point at a placeholder host, not a machine on someone's network.",
    ),
]

DENYLIST_ENV = "ARTIFACT_DENYLIST"


def _redact(text):
    """First character, then asterisks. Enough for the author to recognise, not enough to republish."""
    return text[0] + "*" * max(len(text) - 1, 1) if text else "*"


def _added_lines(diff):
    """The diff's added lines, paired with the file they land in. `+++ b/path` sets the current file; a `+` line
    that is not the `+++` header is an addition. Removed and context lines are ignored — this PR is answerable
    for what it introduces, not for what was already there."""
    out, path = [], "(unknown file)"
    for line in diff.splitlines():
        if line.startswith("+++ "):
            path = line[4:].strip()
            path = path[2:] if path.startswith("b/") else path
        elif line.startswith("+") and not line.startswith("+++"):
            out.append((path, line[1:]))
    return out


def _sources(directory):
    """Yield (source-label, text) for every surface a PR can leak through."""
    def read(name):
        p = os.path.join(directory, name)
        return open(p, encoding="utf-8", errors="replace").read() if os.path.exists(p) else ""

    yield "PR title", read("title.txt")
    yield "PR body", read("body.txt")
    yield "commit messages", read("commits.txt")
    for path, text in _added_lines(read("diff.txt")):
        yield f"added line in {path}", text


def _denylist():
    """Literal names from the environment. Blank lines and `#` comments are skipped so the secret can be
    annotated by whoever maintains it."""
    raw = os.environ.get(DENYLIST_ENV, "")
    return [t for t in (ln.strip() for ln in raw.splitlines()) if t and not t.startswith("#")]


def scan(directory):
    """Return a list of (source, rule, detail, hint) findings across every surface."""
    terms, findings = _denylist(), []
    for source, text in _sources(directory):
        if not text:
            continue
        for rule, pattern, hint in STRUCTURAL_RULES:
            for m in dict.fromkeys(pattern.findall(text)):        # de-duplicate, keep first-seen order
                findings.append((source, rule, repr(m), hint))
        low = text.lower()
        for term in terms:
            if term.lower() in low:
                findings.append((source, "denylisted name", _redact(term),
                                 "Describe the evidence by its characteristics instead of naming the project."))
    return findings


def main(argv):
    if len(argv) != 1:
        print(__doc__)
        return 2
    directory = argv[0]
    findings = scan(directory)

    if not _denylist():
        print(f"note: {DENYLIST_ENV} is unset, so only the structural rules ran. Fork pull requests cannot read "
              f"repository secrets; this is expected there and is not a failure.")

    if not findings:
        print("Artifact hygiene: clean. Nothing in the title, body, commit messages or added lines is a leak.")
        return 0

    print(f"Artifact hygiene: {len(findings)} finding(s).\n")
    for source, rule, detail, hint in findings:
        print(f"  [{rule}] in {source}")
        print(f"      {detail}")
        print(f"      {hint}\n")
    print("A published artifact describes what the code does, in this repository's own terms. Rewrite the text "
          "above and push again; editing the PR title or body re-runs this check.")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
