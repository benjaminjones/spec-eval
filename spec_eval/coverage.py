"""Spec coverage — which code files have NO governing spec? Pure filesystem set-arithmetic: NO API key, NO
model call, free + CI-fast. The spec analogue of test coverage.

COVERED   = files matched by any pair's `code` globs in the config.
CANDIDATE = repo code files (.py) minus the EXCLUDES taxonomy (tests / config / generated / glue / skills/docs
            / user `exclude:` pragmas) — the classes that are impractical to spec (each would create a second
            source of truth with no independent representation to cross-check, the exact drift the tool sells
            against). 'Missing spec' (coverage) is a SEPARATE finding type from 'drift' (accuracy).
UNCOVERED = spec-worthy code files with no governing pair.
"""
import os
import glob
import fnmatch

# the code universe — language-agnostic by default; override per-repo via the config's `code_ext:` list.
DEFAULT_CODE_EXT = (".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".go", ".rs", ".java", ".rb",
                    ".kt", ".kts", ".swift", ".php", ".cs")


def classify_exclude(rel, user_excludes):
    """Return the exclusion tier for a path, or None if it is spec-worthy. Language-agnostic conventions."""
    base = os.path.basename(rel)
    stem = base.rsplit(".", 1)[0]
    ext = os.path.splitext(base)[1]
    parts = set(rel.split(os.sep))
    if any(fnmatch.fnmatch(rel, p) or fnmatch.fnmatch(base, p) for p in (user_excludes or [])):
        return "user"
    # tests (py/ts/js/go/rust conventions): test_x, x_test, x.test.*, x.spec.*, in a tests dir
    if (base.startswith("test_") or stem.endswith("_test") or ".test." in base or ".spec." in base
            or {"tests", "__tests__", "test", "spec", "__mocks__"} & parts):
        return "test"
    # glue / trivial entrypoints across languages
    if base in ("__init__.py", "__main__.py", "conftest.py", "setup.py", "index.ts", "index.js",
                "index.tsx", "index.jsx", "main.go", "mod.rs", "lib.rs"):
        return "glue"
    if {"scripts", "tools", "tooling"} & parts:
        return "tooling"
    if {"__pycache__", "build", "dist", ".venv", "node_modules", "mutants", "formal"} & parts:
        return "generated"
    if base.endswith(".min.js") or base.endswith(".min.mjs"):
        return "generated"                              # minified vendor bundles are build output, not source
    if ext in (".yml", ".yaml", ".toml", ".cfg", ".ini", ".txt", ".lock"):
        return "config"
    if ext == ".md" or base == "SKILL.md":
        return "skill/doc"
    return None


# doc names that are never co-located specs — a `README.md` beside code is a doc, not an orphaned spec
CONVENTIONAL_DOC_STEMS = {"readme", "overview", "changelog", "changes", "contributing", "license", "notice",
                          "spec-health", "testing", "faq", "getting-started", "getting_started", "security",
                          "code_of_conduct", "skill", "todo", "authors", "maintainers", "install", "upgrading"}

# directories never worth walking into (vendored deps, build output, caches, generated test artifacts)
PRUNE_DIRS = {".git", ".venv", "venv", "env", "build", "dist", "target", "node_modules", "__pycache__",
              ".mypy_cache", ".pytest_cache", ".ruff_cache", ".tox", "htmlcov", "site-packages",
              "mutants", ".idea", ".vscode", ".eggs",
              "vendor", "vendored", "third_party", "thirdparty", "bower_components", "jspm_packages"}


def dir_spec_path(code_path, repo_name, dir_spec_name="<dir>"):
    """Per-directory spec path for the directory containing `code_path`. `<dir>` -> the directory's own name
    (`src/parser/lexer.py` -> `src/parser/parser.md`); a literal like `README` -> `src/parser/README.md`. A
    repo-root file uses `repo_name`. Shared with `authoring` so `coverage` and `generate` agree on the layout."""
    d = os.path.dirname(code_path)
    dirname = os.path.basename(d) if d else repo_name
    name = dirname if dir_spec_name == "<dir>" else dir_spec_name
    return os.path.join(d, name + ".md")


def infer_pairs(repo, config):
    """Co-located pairs — each spec-worthy code file + its sibling `<stem>.md`, when the `.md` exists.

    Used when the config declares no explicit `pairs`: the "specs live beside the code" convention, so
    `audit`/`sufficiency` need no `pairs.yml` — a `model.md` next to `model.py` is auto-paired.
    """
    repo = os.path.abspath(repo)
    exts = tuple(config.get("code_ext") or DEFAULT_CODE_EXT)
    user_excludes = config.get("exclude", [])
    pairs = []
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in PRUNE_DIRS]
        for fn in sorted(files):
            if not fn.endswith(exts):
                continue
            rel = os.path.relpath(os.path.join(root, fn), repo)
            if classify_exclude(rel, user_excludes):
                continue
            md = os.path.splitext(rel)[0] + ".md"
            if os.path.isfile(os.path.join(repo, md)):
                pairs.append({"label": os.path.splitext(os.path.basename(rel))[0], "code": [rel], "docs": [md]})
    return sorted(pairs, key=lambda p: p["label"])


def coverage(repo, config):
    repo = os.path.abspath(repo)
    exts = tuple(config.get("code_ext") or DEFAULT_CODE_EXT)   # language-agnostic; override per repo
    authoring = config.get("authoring", {})                    # the authoring layout decides what "covered" means
    layout = authoring.get("layout", "per-file")
    dir_spec_name = authoring.get("dir_spec_name", "<dir>")
    repo_name = os.path.basename(repo)
    covered = set()
    for p in config.get("pairs", []):
        for pat in p.get("code", []):
            for f in glob.glob(os.path.join(repo, pat), recursive=True):
                if os.path.isfile(f):
                    covered.add(os.path.relpath(f, repo))

    candidate = set()
    mds = set()
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in PRUNE_DIRS]   # don't descend into vendored/generated/cache dirs
        for fn in files:
            if fn.endswith(exts):
                candidate.add(os.path.relpath(os.path.join(root, fn), repo))
            elif fn.endswith(".md"):
                mds.add(os.path.relpath(os.path.join(root, fn), repo))

    for rel in candidate:                                    # a co-located `<stem>.md` counts as coverage
        if os.path.isfile(os.path.join(repo, os.path.splitext(rel)[0] + ".md")):
            covered.add(rel)
        elif layout == "per-dir" and os.path.isfile(os.path.join(repo, dir_spec_path(rel, repo_name, dir_spec_name))):
            covered.add(rel)                                 # per-directory layout: the folder spec governs the file

    user_excludes = config.get("exclude", [])
    excluded = {}
    for rel in candidate:
        tier = classify_exclude(rel, user_excludes)
        if tier:
            excluded[rel] = tier
    spec_worthy = candidate - set(excluded)
    covered_worthy = covered & spec_worthy
    uncovered = sorted(spec_worthy - covered)
    pct = 100 * len(covered_worthy) / max(len(spec_worthy), 1)
    by_tier = {}
    for rel, t in excluded.items():
        by_tier.setdefault(t, []).append(rel)

    # Possible ORPHANED specs (heuristic, advisory only — never affects pct/covered/uncovered): a spec-shaped
    # `.md` sitting in a directory that has code, whose same-stem code file no longer exists. Catches the
    # agentic-dev churn case where code moves and its old spec is left behind. Conventional docs (README, …),
    # folder specs, pair-declared docs, and docs-only directories are never flagged.
    pair_docs = set()
    for p in config.get("pairs", []):
        for pat in p.get("docs", []):
            for f in glob.glob(os.path.join(repo, pat), recursive=True):
                if os.path.isfile(f):
                    pair_docs.add(os.path.relpath(f, repo))
    code_dirs = {os.path.dirname(rel) for rel in candidate}
    orphans = []
    for md in mds:
        d = os.path.dirname(md)
        if d not in code_dirs:
            continue                                     # docs-only dir → docs, not specs
        if classify_exclude(md, user_excludes) == "user":
            continue                                     # respect the repo's own exclude: scoping
        stem = os.path.splitext(os.path.basename(md))[0]
        if stem.lower() in CONVENTIONAL_DOC_STEMS:
            continue
        if stem == (os.path.basename(d) if d else repo_name):
            continue                                     # a folder spec (`<dir>/<dir>.md`), not an orphan
        if dir_spec_name != "<dir>" and stem == dir_spec_name:
            continue
        if md in pair_docs:
            continue                                     # explicitly paired — governed, wherever its code is
        base = os.path.splitext(md)[0]
        if any(os.path.isfile(os.path.join(repo, base + ext)) for ext in exts):
            continue                                     # sibling code exists → a normal co-located spec
        orphans.append(md)

    return {"pct": round(pct, 1), "spec_worthy": len(spec_worthy),
            "covered": sorted(covered_worthy), "uncovered": uncovered, "orphans": sorted(orphans),
            "excluded": {t: sorted(v) for t, v in by_tier.items()}}


def format_report(cov, repo):
    name = os.path.basename(os.path.abspath(repo))
    lines = [f"# Spec coverage — `{name}`",
             f"**{cov['pct']:.0f}%** — {len(cov['covered'])}/{cov['spec_worthy']} spec-worthy code files have a governing spec.", ""]
    if cov["uncovered"]:
        lines.append("## ⚠ Uncovered (spec-worthy, no governing pair)")
        lines += [f"- `{f}`" for f in cov["uncovered"]]
        lines.append("")
    if cov.get("orphans"):
        lines.append("## Possible orphaned specs *(heuristic — a spec-shaped `.md` whose same-stem code file is gone; the code may have moved. Review, then delete or re-pair.)*")
        lines += [f"- `{f}`" for f in cov["orphans"]]
        lines.append("")
    lines.append("## Excluded (impractical to spec — by class)")
    for tier, files in sorted(cov["excluded"].items()):
        lines.append(f"- **{tier}** ({len(files)}): " + ", ".join(f"`{f}`" for f in files[:8]) +
                     (" …" if len(files) > 8 else ""))
    return "\n".join(lines)
