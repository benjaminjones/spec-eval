"""spec-eval CLI — portable spec coverage + code↔doc drift + sufficiency + spec authoring.

  spec-eval coverage    <repo> --config pairs.yml                             # free, no key
  spec-eval context     <repo> [--config pairs.yml]                           # free, no key
  spec-eval generate    <repo> [--config pairs.yml] --model … --env .env      # author specs beside the code
  spec-eval audit       <repo> --config pairs.yml --model … --env .env        # drift
  spec-eval sufficiency <repo> --config pairs.yml --model … --env .env        # sufficiency
  spec-eval diagram     <path> [--model … --env .env] [--write]               # architecture (data flow) diagrams

Keys come from the environment (ANTHROPIC_API_KEY / OPENAI_API_KEY / GOOGLE_API_KEY); --env loads a .env file.
"""
import argparse
import os
import sys
import json
from . import providers, audit, report, coverage as coverage_mod, sufficiency as sufficiency_mod, authoring, runlog, syscontext

UNCOVERED_LIST_CAP = 25   # cap the per-line uncovered list printed to the terminal; full list always lands in coverage.md


def _load_keys(env, config):
    providers.load_env(env)
    if config:
        providers.load_env(os.path.join(os.path.dirname(os.path.abspath(config)), ".env"))
    providers.load_env(".env")


def _file_scope(path, cfg):
    """PROJECT_DIR may be a single code FILE (audit / sufficiency / generate): narrow to the file's directory
    with ONE synthesized pair — its co-located `<stem>.md`, or the folder spec under a per-dir layout — so no
    pairs config is needed to scope a check to the file you just changed. Overviews are forced off."""
    repo = os.path.dirname(os.path.abspath(path))
    rel = os.path.basename(path)
    stem = os.path.splitext(rel)[0]
    doc = stem + ".md"
    authoring_cfg = cfg.get("authoring", {})
    if not os.path.exists(os.path.join(repo, doc)) and authoring_cfg.get("layout") == "per-dir":
        doc = os.path.basename(coverage_mod.dir_spec_path(rel, os.path.basename(repo),
                                                          authoring_cfg.get("dir_spec_name", "<dir>")))
    return repo, {**cfg, "pairs": [{"label": stem, "code": [rel], "docs": [doc]}],
                  "authoring": {**authoring_cfg, "overview": "none"}}


def _diagram_target(repo):
    """The existing overview markdown `diagram --write` updates: OVERVIEW.md (canonical) then README.md, or
    None if neither exists at the scope root — `--write` never creates a doc."""
    for name in ("OVERVIEW.md", "README.md"):
        p = os.path.join(repo, name)
        if os.path.exists(p):
            return p
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(prog="spec-eval",
                                 description="Portable spec coverage + drift + sufficiency + authoring.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def model_args(p):
        p.add_argument("repo", metavar="PROJECT_DIR", help="path to the project — a repo root, a subdirectory, or a single code file")
        p.add_argument("--config", "-c", default=None,
                       help="pairs config (YAML/JSON); optional — co-located `<file>.md` specs are auto-paired")
        p.add_argument("--model", "-m", default=providers.DEFAULT_MODEL,
                       help="provider:model (e.g. openai:gpt-5.5, google:gemini-3.5-flash), or claude-code "
                            "(no API key — your Claude subscription via the claude CLI)")
        p.add_argument("--out", "-o", default="spec-reports", help="output directory")
        p.add_argument("--env", default=None, help="path to a .env file with API keys")
        p.add_argument("--fingerprint", action=argparse.BooleanOptionalAction, default=True,
                       help="include the markdown unicode-bar fingerprint (default: on)")

    model_args(sub.add_parser("audit", help="DRIFT: do the pairs CONTRADICT their specs? (needs a model)"))
    model_args(sub.add_parser("sufficiency", help="SUFFICIENCY: how completely do the specs capture the code's "
                                                  "behavior? (needs a model)"))

    g = sub.add_parser("generate", help="AUTHOR an intent-led spec BESIDE each spec-worthy code file with no spec (needs a model)")
    g.add_argument("repo", metavar="PROJECT_DIR", help="path to the project — a repo root, a subdirectory, or a single code file")
    g.add_argument("--config", "-c", default=None, help="optional config (YAML/JSON) for code_ext / exclude; defaults to sensible excludes")
    g.add_argument("--model", "-m", default=providers.DEFAULT_MODEL,
                   help="provider:model, or claude-code (no API key — your Claude subscription via the claude CLI)")
    g.add_argument("--out", "-o", default="spec-reports", help="output directory (run summary)")
    g.add_argument("--env", default=None, help="path to a .env file with API keys")
    g.add_argument("--overwrite", action="store_true", help="re-author specs that already exist")
    g.add_argument("--layout", choices=["per-file", "per-dir", "per-pair"], default=None,
                   help="spec granularity: per-file (default) | per-dir | per-pair")
    g.add_argument("--overview", choices=["none", "repo", "per-dir", "both"], default=None,
                   help="also write a navigation index (default: none)")
    g.add_argument("--template", default=None,
                   help="path to a custom authoring template (replaces the built-in structure)")

    c = sub.add_parser("coverage", help="COVERAGE: which code files have NO governing spec? (free; no API key)")
    c.add_argument("repo", metavar="PROJECT_DIR", help="path to the project — a repo root or any subdirectory")
    c.add_argument("--config", "-c", default=None,
                   help="pairs config (YAML/JSON); optional — co-located `<file>.md` specs count as covered")
    c.add_argument("--out", "-o", default="spec-reports", help="output directory")
    c.add_argument("--min", type=float, default=None, help="fail (exit 1) if coverage %% is below this")

    x = sub.add_parser("context", help="SYSTEM CONTEXT: what external systems does the code observably talk "
                                       "to? (free; no API key)")
    x.add_argument("repo", metavar="PROJECT_DIR", help="path to the project — a repo root or any subdirectory")
    x.add_argument("--config", "-c", default=None,
                   help="optional config (YAML/JSON) for code_ext / exclude rules")
    x.add_argument("--out", "-o", default="spec-reports", help="output directory")
    x.add_argument("--check", action="store_true",
                   help="compare a fresh scan against the stored system-context.json baseline in --out and "
                        "exit 1 if any external system was added or removed (a scanner change is a re-baseline, "
                        "not drift); does not overwrite the baseline")

    d = sub.add_parser("diagram", help="DIAGRAM: print the repo's Mermaid architecture diagrams (an invocation "
                                       "sequence + the data-flow pipeline) to stdout; --write updates the "
                                       "Architecture section of an EXISTING OVERVIEW/README")
    d.add_argument("repo", metavar="PROJECT_DIR",
                   help="path to the project — a repo root, a subdirectory, or a file (its directory is diagrammed)")
    d.add_argument("--config", "-c", default=None, help="optional config (YAML/JSON) for code_ext / exclude rules")
    d.add_argument("--model", "-m", default=providers.DEFAULT_MODEL,
                   help="provider:model, or claude-code (no API key — used only to derive any missing module intents)")
    d.add_argument("--env", default=None, help="path to a .env file with API keys")
    d.add_argument("--write", action="store_true",
                   help="update the '## Architecture (data flow)' section of an EXISTING OVERVIEW.md/README.md at "
                        "PROJECT_DIR and re-stamp the architecture fingerprint; REPLACE-ONLY — errors if no such "
                        "section exists (see --add-section)")
    d.add_argument("--add-section", action="store_true",
                   help="write, and if the target doc has no '## Architecture (data flow)' section, APPEND one "
                        "instead of erroring — an explicit opt-in; the doc must already exist (never creates a file)")

    args = ap.parse_args(argv)

    if args.cmd == "audit":
        _load_keys(args.env, args.config)
        cfg = audit.load_config(args.config) if args.config else {}
        if os.path.isfile(args.repo):
            args.repo, cfg = _file_scope(args.repo, cfg)
        os.makedirs(args.out, exist_ok=True)
        results = audit.audit_repo(args.repo, cfg, args.model)
        json.dump(results, open(os.path.join(args.out, "findings.json"), "w"), indent=2)
        total = report.write_markdown(results, args.repo, args.model, os.path.join(args.out, "report.md"), args.fingerprint)
        audited = sum(1 for r in results if not r.get("skipped"))
        print(f"{total} high/medium drift finding(s) across {audited}/{len(results)} audited pair(s).")
        truncated = sum(1 for r in results if r.get("truncated"))
        if truncated:
            print(f"⚠ {truncated} pair(s) graded on a partial view (input cap or reply token cap) — "
                  f"flagged per pair in report.md")
        print(f"wrote report.md + findings.json → {os.path.abspath(args.out)}")
        print(f"{providers.USAGE['calls']} model call(s), "
              f"{providers.USAGE['in']:,} in + {providers.USAGE['out']:,} out tokens")
        runlog.append_run(args.out, args.repo, "audit", args.model,
                          {"high_med_drift": total, "pairs_audited": audited, "pairs_truncated": truncated,
                           "per_module": {r["label"]: report.drift_load(r) for r in results if not r.get("skipped")}})

    elif args.cmd == "sufficiency":
        _load_keys(args.env, args.config)
        cfg = audit.load_config(args.config) if args.config else {}
        if os.path.isfile(args.repo):
            args.repo, cfg = _file_scope(args.repo, cfg)
        os.makedirs(args.out, exist_ok=True)
        results = sufficiency_mod.sufficiency_repo(args.repo, cfg, args.model)
        json.dump(results, open(os.path.join(args.out, "sufficiency.json"), "w"), indent=2)
        avg = report.write_sufficiency_markdown(results, args.repo, args.model, os.path.join(args.out, "sufficiency.md"), args.fingerprint)
        scored = sum(1 for r in results if r.get("sufficiency") is not None)
        print(f"average spec sufficiency {avg:.2f} across {scored}/{len(results)} pairs (1.0 = no gaps found — an "
              f"indicator, not a guarantee)")
        truncated = sum(1 for r in results if r.get("truncated"))
        if truncated:
            print(f"⚠ {truncated} pair(s) scored on a partial view (input cap or reply token cap) — "
                  f"flagged per pair in sufficiency.md")
        print(f"wrote sufficiency.md + sufficiency.json → {os.path.abspath(args.out)}")
        print(f"{providers.USAGE['calls']} model call(s), {providers.USAGE['in']:,} in + {providers.USAGE['out']:,} out tokens")
        runlog.append_run(args.out, args.repo, "sufficiency", args.model,
                          {"avg_sufficiency": round(avg, 2), "pairs_scored": scored, "pairs_truncated": truncated,
                           "per_module": {r["label"]: r["sufficiency"] for r in results if r.get("sufficiency") is not None}})

    elif args.cmd == "generate":
        _load_keys(args.env, args.config)
        cfg = audit.load_config(args.config) if args.config else {"pairs": []}
        authoring_cfg = dict(cfg.get("authoring", {}))        # CLI flags override the config's authoring block
        if args.layout:
            authoring_cfg["layout"] = args.layout
        if args.overview:
            authoring_cfg["overview"] = args.overview
        if args.template:
            authoring_cfg["template"] = args.template
        cfg = {**cfg, "authoring": authoring_cfg}             # coverage() (called inside generate_repo) reads this too
        if os.path.isfile(args.repo):
            args.repo, cfg = _file_scope(args.repo, cfg)
            cfg["authoring"]["layout"] = "per-pair"           # author exactly that file's spec
        os.makedirs(args.out, exist_ok=True)
        print("generating specs — one model call per module; progress below (Ctrl-C is safe)…", file=sys.stderr, flush=True)
        res = authoring.generate_repo(args.repo, cfg, args.model, overwrite=args.overwrite,
                                      on_progress=lambda m: print(f"  … {m}", file=sys.stderr, flush=True))
        json.dump(res, open(os.path.join(args.out, "generated.json"), "w"), indent=2)
        for r in res:
            note = f"  — {r['note']}" if r.get("note") else ""
            print(f"  {r['status']:10} {r['spec']}{note}")
        authored = sum(1 for r in res if r["status"] == "authored")
        print(f"authored {authored} spec(s) beside the code; {len(res)-authored} skipped. "
              f"Review with `git diff`; drop any you don't want with `git checkout --`.")
        print(f"{providers.USAGE['calls']} model call(s), {providers.USAGE['in']:,} in + {providers.USAGE['out']:,} out tokens")
        runlog.append_run(args.out, args.repo, "generate", args.model,
                          {"authored": authored, "skipped": len(res) - authored,
                           "flagged": sum(1 for r in res if r.get("note"))})

    elif args.cmd == "coverage":
        if os.path.isfile(args.repo):
            parent = os.path.dirname(args.repo) or "."
            raise SystemExit(f"coverage reports on directories — try `spec-eval coverage {parent}`. "
                             "(audit / sufficiency / generate do accept a single file.)")
        cfg = audit.load_config(args.config) if args.config else {}
        os.makedirs(args.out, exist_ok=True)
        cov = coverage_mod.coverage(args.repo, cfg)
        json.dump(cov, open(os.path.join(args.out, "coverage.json"), "w"), indent=2)
        open(os.path.join(args.out, "coverage.md"), "w").write(coverage_mod.format_report(cov, args.repo))
        print(f"spec coverage: {cov['pct']:.0f}% — {len(cov['covered'])}/{cov['spec_worthy']} spec-worthy files covered")
        if cov["uncovered"]:
            print(f"  uncovered ({len(cov['uncovered'])}) — spec-worthy files with no governing spec:")
            for f in cov["uncovered"][:UNCOVERED_LIST_CAP]:
                print(f"    - {f}")
            if len(cov["uncovered"]) > UNCOVERED_LIST_CAP:
                print(f"    … and {len(cov['uncovered']) - UNCOVERED_LIST_CAP} more (full list in coverage.md)")
        if cov.get("orphans"):
            print(f"  possible orphaned spec(s) ({len(cov['orphans'])}) — spec-shaped .md with no same-stem code file; review or remove:")
            for f in cov["orphans"][:UNCOVERED_LIST_CAP]:
                print(f"    - {f}")
        print(f"wrote coverage.md + coverage.json → {os.path.abspath(args.out)}  (free; no API key)")
        runlog.append_run(args.out, args.repo, "coverage", None,
                          {"coverage_pct": cov["pct"], "covered": len(cov["covered"]),
                           "spec_worthy": cov["spec_worthy"], "orphans": len(cov.get("orphans", []))})
        if args.min is not None and cov["pct"] < args.min:
            print(f"FAIL: coverage {cov['pct']:.0f}% < --min {args.min:.0f}%")
            raise SystemExit(1)

    elif args.cmd == "context":
        if os.path.isfile(args.repo):
            parent = os.path.dirname(args.repo) or "."
            raise SystemExit(f"context scans directories — try `spec-eval context {parent}`.")
        cfg = audit.load_config(args.config) if args.config else {}
        os.makedirs(args.out, exist_ok=True)
        ctx = syscontext.scan(args.repo, cfg)

        if args.check:
            baseline_path = os.path.join(args.out, "system-context.json")
            if not os.path.exists(baseline_path):
                print(f"no baseline at {baseline_path} — run `spec-eval context {args.repo}` first to store one")
                raise SystemExit(0)
            try:
                baseline = json.load(open(baseline_path))
                assert isinstance(baseline, dict)
            except (ValueError, AssertionError, OSError):     # corrupt/empty/non-dict → re-baseline, don't crash
                print(f"unreadable baseline at {baseline_path} — re-run `spec-eval context {args.repo}` to re-store")
                raise SystemExit(0)
            d = syscontext.diff(baseline, ctx)
            print(syscontext.diff_receipt(d, sha=runlog.git_sha(args.repo)))
            overview_path = _diagram_target(args.repo)                       # OVERVIEW.md, else README.md — the doc
            overview_md = open(overview_path, errors="ignore").read() if overview_path else ""   # diagram --write stamps
            doc = os.path.basename(overview_path) if overview_path else "OVERVIEW.md"
            overview_stale = bool(overview_md) and syscontext.overview_stale(overview_md, ctx)   # second edge
            if overview_stale:
                print(f"⚠ {doc} system context is stale — regenerate its overview (`generate --overview`)")
            ep = syscontext.scan_entrypoints(args.repo, cfg)                 # third edge: fingerprint -> diagram
            modules = authoring.module_set(args.repo, cfg)
            diagram_stale = bool(overview_md) and syscontext.diagram_stale(overview_md, ctx, ep, modules)
            if diagram_stale:
                print(f"⚠ {doc} architecture diagram is stale — regenerate it "
                      "(`spec-eval diagram . --write`, or `generate --overview`)")
            runlog.append_run(args.out, args.repo, "context-check", None,
                              {"outcome": d["outcome"], "added": len(d["added"]), "removed": len(d["removed"]),
                               "overview_stale": overview_stale, "diagram_stale": diagram_stale})
            if d["outcome"] == "drift":
                raise SystemExit(1)                # gate: a system was added or removed (overview staleness warns)
            raise SystemExit(0)

        json.dump(ctx, open(os.path.join(args.out, "system-context.json"), "w"), indent=2)
        open(os.path.join(args.out, "system-context.md"), "w").write(syscontext.format_report(ctx, args.repo) + "\n")
        print(f"system context: {len(ctx['entries'])} external system(s) observed across "
              f"{ctx['files_scanned']} scanned code file(s)")
        for rec in ctx["entries"]:
            e = rec["evidence"][0]
            print(f"  - {rec['system']}  ({rec['kind']}, {rec['direction']}; {e['file']}:{e['line']})")
        note = syscontext.unscanned_note(ctx)
        if note:
            print(f"⚠ {note}")
        print(f"wrote system-context.md + system-context.json → {os.path.abspath(args.out)}  (free; no API key)")
        runlog.append_run(args.out, args.repo, "context", None,
                          {"systems_observed": len(ctx["entries"]), "files_scanned": ctx["files_scanned"],
                           "files_unscanned": sum(ctx["unscanned"].values())})

    elif args.cmd == "diagram":
        _load_keys(args.env, args.config)
        cfg = audit.load_config(args.config) if args.config else {}
        if os.path.isfile(args.repo):
            args.repo = os.path.dirname(os.path.abspath(args.repo)) or "."   # a file -> its directory's diagram
        target, original = None, None
        if args.write or args.add_section:                        # validate the write target BEFORE synthesising,
            target = _diagram_target(args.repo)                   # so a doc we'll refuse fails fast (no model calls)
            if target is None:                                    # both flags update an EXISTING doc — never create one
                raise SystemExit(
                    f"diagram --write updates an EXISTING overview — none found at {args.repo} (looked for "
                    f"OVERVIEW.md, README.md). Run `spec-eval generate {args.repo} --overview repo` to author "
                    f"one, or pipe in `spec-eval diagram {args.repo}`.")
            original = open(target, errors="ignore").read()
            if not args.add_section and not authoring.has_architecture_section(original):   # replace-only, no section
                raise SystemExit(
                    f"{os.path.relpath(target)} has no '## Architecture (data flow)' section — pass --add-section to "
                    f"append one, pipe in `spec-eval diagram {args.repo}`, or run "
                    f"`spec-eval generate {args.repo} --overview repo`.")
        block, ctx, ep, modules = authoring.diagram_block(
            args.repo, cfg, args.model,
            on_progress=lambda m: print(f"  … {m}", file=sys.stderr, flush=True))
        if not modules:
            raise SystemExit(f"no spec-worthy code files under {args.repo} — nothing to diagram.")
        if target is None:
            print(block)                                          # STDOUT only — touches nothing, creates nothing
        else:
            md = authoring.set_architecture_section(original, block, create=args.add_section)
            md = syscontext.restamp_architecture(md, ctx, ep, modules)   # refresh ONLY the architecture stamp
            open(target, "w").write(md.rstrip() + "\n")
            print(f"wrote the Architecture (data flow) section + re-stamped → {os.path.abspath(target)}",
                  file=sys.stderr)
        print(f"{providers.USAGE['calls']} model call(s), {providers.USAGE['in']:,} in + "
              f"{providers.USAGE['out']:,} out tokens", file=sys.stderr)


if __name__ == "__main__":
    main()
