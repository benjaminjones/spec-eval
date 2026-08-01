"""Fail a pull request that leaks something the repository should not publish.

spec-eval's contributing guide and PR template both say a change must be described in the repo's own terms, with
no references to other projects, private repos, or the session that produced it. Both are advisory, so the rule
held only as long as everyone remembered it. This script makes it mechanical.

WHAT IS SCANNED
  the PR title, the PR body, the branch name, every commit message on the branch, and the diff's ADDED lines and
  newly introduced PATHS. Added lines only: a pre-existing line is not this PR's doing, and failing on one would
  redden an unrelated change. Paths matter too — a name in a filename is permanent in git history, and a rename
  or a binary addition carries no added lines at all.

TWO CLASSES OF RULE
  Structural rules (below) are generic and live in this file. They catch categories: a path from someone's
  machine, a phrase narrating the chat, a private network address.

  Name rules come from the ARTIFACT_DENYLIST environment variable, one entry per line. They are deliberately NOT
  stored in the repository: a denylist naming the private projects would publish exactly what it exists to hide.
  Set it as a repository secret. A term is matched normalised, so listing `project-x` also catches `project x`,
  `project_x`, `ProjectX` and a line-wrapped `project-\\nx`.

TWO ESCAPE HATCHES, both leaving a visible record
  `HYGIENE_EXEMPT_PATHS` — files that must contain leak-shaped literals to do their job. This script and its
  tests are the whole list; a rule's own regex necessarily contains the phrase it forbids.
  An inline `hygiene: allow` pragma on the offending line, for a one-off the author judges intentional.

KNOWN LIMITS, stated rather than implied
  A denylisted name spelled with homoglyphs (Cyrillic `о` for Latin `o`) passes. So does a leak reaching the
  repository through a channel this script never sees: PR review comments, issue text, or a force-push that
  rewrites a scanned commit after the check ran. This catches the mistakes people actually make, not a
  determined author.

USAGE
  python .github/scripts/check_artifact_hygiene.py <dir>

  <dir> holds title.txt, body.txt, head_ref.txt, commits.txt and diff.txt. Exit 0 clean, 1 findings, 2 the check
  could not run — which is never a pass.
"""
import os
import re
import sys
import unicodedata

SURFACES = ("title", "body", "head_ref", "commits", "diff")
DENYLIST_ENV = "ARTIFACT_DENYLIST"
FORK_ENV = "IS_FORK"

# Files exempt from the ADDED-LINE scan because their job requires leak-shaped literals. Deliberately a short
# explicit tuple rather than a directory skip, so the exemption stays auditable in review.
HYGIENE_EXEMPT_PATHS = (
    ".github/scripts/check_artifact_hygiene.py",
    "tests/contract/test_artifact_hygiene.py",
)

_PRAGMA = re.compile(r"hygiene:\s*allow", re.I)

# Automation home directories. A pasted CI traceback names a machine nobody owns.
_CI_USERS = {"runner", "vsts", "vsts_agent", "circleci", "travis", "ubuntu", "ec2-user", "jenkins", "root"}

_UNIX_HOME = re.compile(r"(?:/Users|/home)/([A-Za-z0-9._-]+)")
_WIN_HOME = re.compile(r"[A-Za-z]:\\{1,2}Users\\{1,2}([A-Za-z0-9._-]+)")
_NARRATION = re.compile(
    r"\b(?:as (?:we|you) (?:discussed|agreed|asked)|you asked me to|as (?:requested|discussed) above"
    r"|in (?:our|this) (?:chat|conversation|session)|per your request|the previous (?:message|turn)"
    r"|(?:earlier|previously) in this (?:chat|thread|session))\b",
    re.I,
)
# RFC1918 only. `localhost` names nobody's machine and appears legitimately in developer docs.
_PRIVATE_NET = re.compile(r"\b(?:192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}"
                          r"|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b")


def _home_paths(text):
    """Personal home paths, with the username masked. The rule name tells the author what to fix; reprinting
    their username into a log that outlives the branch would leak a second thing to fix it."""
    out = []
    for pattern in (_UNIX_HOME, _WIN_HOME):
        for m in pattern.finditer(text):
            user = m.group(1)
            if user.casefold() in _CI_USERS:
                continue
            out.append(m.group(0).replace(user, "<user>"))
    return out


def _matcher(pattern):
    return lambda text: [m.group(0) for m in pattern.finditer(text)]


STRUCTURAL_RULES = (
    ("absolute path from a personal machine", _home_paths,
     "Use a repo-relative path, or a placeholder like <repo>."),
    ("narration of the session that produced the change", _matcher(_NARRATION),
     "Describe what the code does now, not the conversation that produced it."),
    ("private network address", _matcher(_PRIVATE_NET),
     "Point at a placeholder host, not a machine on someone's network."),
)


def _normalize(s):
    """Fold the variations that are typing, not evasion: compatibility forms, zero-width and other format
    characters, and case."""
    s = unicodedata.normalize("NFKC", s)
    return "".join(ch for ch in s if unicodedata.category(ch) != "Cf").casefold()


def _term_pattern(term):
    """A denylist term as a separator-tolerant pattern, so one entry covers how the name is actually written:
    `project-x` also finds `project x`, `project_x`, `projectX`, and a line-wrapped `project-\\nx`."""
    parts = [re.escape(p) for p in re.split(r"[-_\s]+", _normalize(term)) if p]
    return re.compile(r"[-_\s]*".join(parts)) if parts else None


def denylist():
    """Literal names from the environment. Blank lines and `#` comments are skipped so whoever maintains the
    secret can annotate it."""
    raw = os.environ.get(DENYLIST_ENV, "")
    return [t for t in (ln.strip() for ln in raw.splitlines()) if t and not t.startswith("#")]


def _redact(term):
    """A fixed-width mask. Length and initial are themselves identifying for a short project name, and the
    location in the report is what the author actually needs."""
    return "*" * 8


_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")
_BINARY = re.compile(r"^Binary files .* and b/(.+?) differ$")


def diff_surfaces(diff):
    """Yield (label, text) for everything a diff INTRODUCES: added lines, and paths that did not exist before.

    Parsed as the state machine git's output actually is, not by line prefix. A source line beginning with `++`
    becomes `+++...` in a diff and would otherwise be mistaken for a file header and dropped — silently, which is
    the worst way for a check like this to fail."""
    path, new_file, in_hunk, lineno = None, False, False, 0
    for raw in diff.splitlines():
        if raw.startswith("diff --git "):
            path, new_file, in_hunk = None, False, False
            continue
        if not in_hunk:
            if raw.startswith("new file mode") or raw == "--- /dev/null":
                new_file = True
            elif raw.startswith(("rename to ", "copy to ")):
                yield "new file path", raw.split(" ", 2)[2]
            elif raw.startswith("+++ "):
                p = raw[4:].strip()
                path = p[2:] if p.startswith("b/") else p
                if new_file and path != "/dev/null":
                    yield "new file path", path
            elif _BINARY.match(raw):
                yield "new file path", _BINARY.match(raw).group(1)
            else:
                m = _HUNK.match(raw)
                if m:
                    in_hunk, lineno = True, int(m.group(1))
            continue
        m = _HUNK.match(raw)
        if m:
            lineno = int(m.group(1))
        elif raw.startswith("+"):
            yield f"added line {lineno} in {path}", raw[1:]
            lineno += 1
        elif raw.startswith(" ") or raw == "":
            lineno += 1
        elif not raw.startswith(("-", "\\")):
            in_hunk = False


def _sources(directory):
    """Yield (label, text) for every surface a PR can leak through."""
    def read(name):
        p = os.path.join(directory, f"{name}.txt")
        return open(p, encoding="utf-8", errors="replace").read() if os.path.exists(p) else ""

    yield "PR title", read("title")
    yield "PR body", read("body")
    yield "branch name", read("head_ref")
    yield "commit messages", read("commits")
    exempt = set(HYGIENE_EXEMPT_PATHS)
    for label, text in diff_surfaces(read("diff")):
        if label.startswith("added line") and label.split(" in ", 1)[-1] in exempt:
            continue
        if label == "new file path" and text in exempt:
            continue
        yield label, text


def scan(directory, terms=None):
    """Return a list of (source, rule, detail, hint) findings across every surface."""
    terms = denylist() if terms is None else terms
    patterns = [(t, _term_pattern(t)) for t in terms]
    findings = []
    for source, text in _sources(directory):
        if not text or _PRAGMA.search(text):
            continue
        for rule, find, hint in STRUCTURAL_RULES:
            for hit in dict.fromkeys(find(text)):
                findings.append((source, rule, repr(hit), hint))
        normalized = _normalize(text)
        for term, pattern in patterns:
            if pattern and pattern.search(normalized):
                findings.append((source, "denylisted name", _redact(term),
                                 "Describe the evidence by its characteristics instead of naming the project."))
    return findings


def _group(findings):
    """One entry per distinct (rule, detail), with the places it occurs. A term repeated down a file is one
    thing to fix, not twelve."""
    grouped = {}
    for source, rule, detail, hint in findings:
        grouped.setdefault((rule, detail, hint), []).append(source)
    return grouped


def main(argv):
    if len(argv) != 1:
        print(__doc__)
        return 2
    directory = argv[0]

    if not os.path.isdir(directory):
        print(f"::error::hygiene inputs missing — {directory!r} is not a directory. The check did not run.")
        return 2
    if not [n for n in SURFACES if os.path.exists(os.path.join(directory, f"{n}.txt"))]:
        print(f"::error::hygiene inputs missing — none of {', '.join(n + '.txt' for n in SURFACES)} exists in "
              f"{directory!r}. The check did not run.")
        return 2

    terms = denylist()
    is_fork = os.environ.get(FORK_ENV, "").casefold() == "true"
    if not terms:
        if is_fork:
            print(f"::warning::{DENYLIST_ENV} is unavailable to a fork pull request, so only the structural "
                  f"rules ran. A maintainer should re-check the name rules before merging.")
        else:
            print(f"::error::{DENYLIST_ENV} is not configured, so the name rules could not run. Add it as a "
                  f"repository secret (Settings → Secrets and variables → Actions), one name per line.")
            return 2

    grouped = _group(scan(directory, terms))
    if not grouped:
        print("Artifact hygiene: clean. Nothing in the title, body, branch name, commit messages, added lines "
              "or new paths is a leak.")
        return 0

    print(f"Artifact hygiene: {len(grouped)} finding(s).\n")
    for (rule, detail, hint), sources in grouped.items():
        shown = sources[:3]
        more = f" (+{len(sources) - len(shown)} more)" if len(sources) > len(shown) else ""
        print(f"  [{rule}] {detail}")
        print(f"      in {'; '.join(shown)}{more}")
        print(f"      {hint}\n")
    print("A published artifact describes what the code does, in this repository's own terms. Rewrite the text "
          "above and push again; editing the PR title or body re-runs this check. If an occurrence is "
          "deliberate, add a `hygiene: allow` pragma on that line.")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
