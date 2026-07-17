#!/usr/bin/env python3
"""Trigger / description routing eval (manual — model-in-the-loop).

A skill fires only if its frontmatter DESCRIPTION routes to it. test_rubric_sync pins the skill BODY; nothing
checks the descriptions ACTIVATE correctly — or, the specific risk, don't MIS-ROUTE between the two overlapping
siblings ("check the spec" vs "write the spec"). This routes each labelled case in trigger-cases.jsonl through
the descriptions (read verbatim from the two SKILL.md files, so it can't drift) and reports accuracy + every
mis-route. It is NOT a CI unit test — it needs the `claude` CLI (or an API key) and costs a few calls per rep.

    python tests/manual/run_trigger_eval.py                 # 1 pass, via the claude-code bridge (no API key)
    python tests/manual/run_trigger_eval.py --reps 3        # 3 passes for a reliable rate
    python tests/manual/run_trigger_eval.py --model anthropic:claude-opus-4-8   # or an API-key model
"""
import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))          # tests/manual/ -> repo root
SKILLS = os.path.join(ROOT, "skills")                  # the two shipped skills live at <repo>/skills/


def _description(skill):
    fm = open(os.path.join(SKILLS, skill, "SKILL.md")).read().split("---", 2)[1]
    return re.search(r'^description:\s*(.+)$', fm, re.M).group(1).strip()


def _route(model, prompt, descs):
    system = ("You are a router. Given a user request and two available skills, reply with EXACTLY one token: "
              "the skill name that best applies, or 'none' if neither is the right tool (e.g. plain code edits, "
              "refactors, bug fixes, or tests are 'none'). Do not explain.\n"
              + "\n".join(f"- {name}: {d}" for name, d in descs.items()))
    user = f"User request: {prompt!r}\nReply with one of: {', '.join(descs)}, none"
    if model == "claude-code":
        exe = subprocess.run(["claude", "-p", "--output-format", "json", "--system-prompt", system],
                             input=user, capture_output=True, text=True, timeout=120)
        out = json.loads(exe.stdout).get("result", "")
    else:                                                  # API-key path via spec-eval's provider layer
        sys.path.insert(0, ROOT)
        from spec_eval import providers
        out = providers.gen(model, system, user, max_tokens=20)
    for name in list(descs) + ["none"]:
        if name in out.lower():
            return name
    return out.strip().lower()[:20]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="claude-code")
    ap.add_argument("--reps", type=int, default=1)
    args = ap.parse_args()
    descs = {"spec-check": _description("spec-check"), "spec-authoring": _description("spec-authoring")}
    cases = [json.loads(line) for line in open(os.path.join(HERE, "trigger-cases.jsonl")) if line.strip()]

    hits = 0
    total = 0
    misroutes = []
    for c in cases:
        got = [_route(args.model, c["prompt"], descs) for _ in range(args.reps)]
        agree = max(set(got), key=got.count)              # majority label across reps
        ok = agree == c["expect"]
        hits += ok
        total += 1
        mark = "✓" if ok else "✗"
        print(f"  {mark} {c['expect']:14} got {agree:14} — {c['prompt']}")
        if not ok:
            misroutes.append((c["prompt"], c["expect"], agree, got))
    print(f"\nrouting accuracy: {hits}/{total} = {hits/total:.0%}  (model={args.model}, reps={args.reps})")
    sib = [m for m in misroutes if {m[1], m[2]} <= {"spec-check", "spec-authoring"}]
    if sib:
        print(f"⚠ {len(sib)} sibling MIS-ROUTE(s) (check<->authoring) — the highest-risk failure:")
        for p, exp, got, _ in sib:
            print(f"    '{p}' expected {exp}, routed {got}")
    return 0 if hits == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
