"""Append-only run log — one JSON line per check, stamped with a seconds-precision timestamp and the repo's git SHA.

Lets you track scores over time and trace a fingerprint back to the commit that produced it. Writes
`<out>/runs.jsonl`; each line is a self-contained record (date, git_sha, command, detector, plus per-run stats).
"""
import os
import json
import subprocess
import datetime


def git_sha(repo):
    """Short git SHA of `repo`'s HEAD, or None if it isn't a git repo / git is unavailable."""
    try:
        out = subprocess.run(["git", "-C", repo, "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True, timeout=5)
        return out.stdout.strip() or None
    except Exception:
        return None


def append_run(out_dir, repo, command, detector, stats):
    """Append one run record to `<out_dir>/runs.jsonl`. `stats` is a dict of summary numbers. Returns the path."""
    rec = {"date": datetime.datetime.now().isoformat(timespec="seconds"), "git_sha": git_sha(repo),   # to the second: same-day runs stay distinguishable by clock time, not just line order
           "command": command, "detector": detector, **stats}
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "runs.jsonl")
    with open(path, "a") as f:
        f.write(json.dumps(rec) + "\n")
    return path
