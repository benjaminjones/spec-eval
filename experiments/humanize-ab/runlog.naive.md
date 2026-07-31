## 1. Purpose

`runlog` gives the system a durable, append-only history of every check it runs. When a check completes, the module records one self-contained line holding a timestamp, the git commit of the repo under inspection, the command and detector used, and whatever summary numbers that run produced. A user can then track how scores move over time and trace any result back to the exact commit that produced it.

The log is only ever added to, never rewritten. Running a check again leaves all previous lines intact and adds exactly one new line at the end.

## 2. Definitions

A run record is one JSON object describing a single completed check, serialized as one line. The `date` field holds the local timestamp the record was written, ISO 8601 to the second (`YYYY-MM-DDTHH:MM:SS`), so multiple same-day runs stay distinguishable by clock time rather than by append order alone. `git_sha` holds the short git commit hash of the inspected repo's HEAD, or `null` when that is unavailable. `command` and `detector` are both caller-supplied free-form string labels, the first naming what was run and the second naming which detector produced the stats. `stats` is a dict of summary numbers that the writer merges flat into the record. The log file is `<out_dir>/runs.jsonl`, newline-delimited JSON with one record per line.

## 3. Behavior

A record always carries `date`, `git_sha`, `command`, and `detector`, and then the writer merges every key and value from `stats` in at the top level. Each line is meant to stand on its own, so a reader can analyze it without joining against other files.

Because the writer merges `stats` last, a key in `stats` that collides with `date`, `git_sha`, `command`, or `detector` overwrites the built-in value. Reconstructed intent (confidence: low), inferred from the code: the merge order is explicit, but the code alone does not say whether collisions are intended or simply unguarded.

The module obtains the SHA by shelling out to `git -C <repo> rev-parse --short HEAD` with a 5-second timeout. If the directory is not a git repo, if git is not installed, if the command errors, or if it times out, the module records `git_sha` as `null` instead of failing the write. Logging must not depend on a working git environment, and a run with an unknown commit is still worth recording.

The module creates the output directory if it is absent, appends the record as a JSON line to `runs.jsonl`, never reads or modifies existing content, and returns the file path to the caller. It takes the date from the local clock at write time, ISO 8601 to the second, as defined in section 2.

## 4. Contracts

Record shape (one JSON line):

```
{ "date": str, "git_sha": str|null, "command": str, "detector": str, ...stats }
```

`git_sha` is a short hash string or `null`, and `...stats` is zero or more caller-supplied summary fields merged flat.

Three rules always hold. The module creates the output directory before writing, using `makedirs(..., exist_ok=True)`, so a missing directory never fails the write. Git SHA resolution never raises, and any failure or timeout yields `git_sha = null`. Each call writes exactly one line terminated by `\n` and appended in mode `"a"`, so prior lines are never altered.

The acceptance criteria cover six cases. When `out_dir` does not exist and a caller runs `append_run(out_dir, repo, "scan", "d1", {"score": 0.9})`, the module creates `out_dir` and `runs.jsonl` contains one line with `command="scan"`, `detector="d1"`, and `score=0.9`. When `repo` is not a git repository, the written record has `"git_sha": null` and nothing raises. When `runs.jsonl` already holds 3 lines and a caller runs `append_run(...)` once, the file holds exactly 4 lines and the first 3 are unchanged. When `git rev-parse` hangs, resolution aborts at 5 seconds and the module records `git_sha` as `null`. On any successful call, `append_run(...)` returns a value equal to `os.path.join(out_dir, "runs.jsonl")`. When `stats={"date": "2000-01-01"}`, the record's `date` field is `"2000-01-01"`, because stats override built-ins.
