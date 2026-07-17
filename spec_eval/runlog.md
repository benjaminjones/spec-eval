## 1. Purpose

`runlog` gives the system a durable, append-only history of every check it runs. Each time a check completes, the module records a single self-contained line — a timestamp, the git commit of the repo under inspection, the command and detector used, and whatever summary numbers that run produced. This lets a user track how scores move over time and trace any result back to the exact commit that produced it.

The one governing constraint a reviewer can check: **the log is only ever added to, never rewritten.** Running a check again leaves all previous lines intact and adds exactly one new line at the end.

## 2. Definitions

| Term | Meaning (bounds / units) |
|------|--------------------------|
| run record | One JSON object describing a single completed check; serialized as one line. |
| `date` | Local timestamp the record was written, ISO 8601 to the second (`YYYY-MM-DDTHH:MM:SS`) — so multiple same-day runs are distinguishable by clock time, not just append order. |
| `git_sha` | Short git commit hash of the inspected repo's HEAD, or `null` if unavailable. |
| `command` | Caller-supplied label for what was run (free-form string). |
| `detector` | Caller-supplied label for which detector produced the stats (free-form string). |
| `stats` | Dict of summary numbers for the run; merged flat into the record. |
| log file | `<out_dir>/runs.jsonl` — newline-delimited JSON, one record per line. |

## 3. Behavior

**Record assembly.** A record always carries `date`, `git_sha`, `command`, and `detector`, then all key/value pairs from `stats` merged in at the top level.
> **Why:** each line is meant to be self-contained — readable and analyzable without joining against other files.

**Key precedence.** `stats` is merged last, so a key in `stats` that collides with `date`/`git_sha`/`command`/`detector` overwrites the built-in value.
> Reconstructed intent (confidence: low) — the merge order is explicit in the code, but whether collisions are intended or simply unguarded is not determinable from the code alone.

**Git SHA resolution.** The SHA is obtained by shelling out to `git -C <repo> rev-parse --short HEAD` with a 5-second timeout. If the directory is not a git repo, git is not installed, the command errors, or it times out, `git_sha` is recorded as `null` rather than failing the write.
> **Why:** logging must not be blocked by a missing or broken git environment; a run with an unknown commit is still worth recording.

**Append semantics.** The output directory is created if absent. The record is appended as a JSON line to `runs.jsonl`; existing content is never read or modified. The file path is returned to the caller.

**Date.** Uses the local date and time at write time, ISO 8601 to the second (`YYYY-MM-DDTHH:MM:SS`) — as defined in §2.

## 4. Contracts

Record shape (one JSON line):

```
{ "date": str, "git_sha": str|null, "command": str, "detector": str, ...stats }
```

- `git_sha`: short hash string, or `null`.
- `...stats`: zero or more caller-supplied summary fields merged flat.

### Invariants (*rules that must always hold*)

| ID | Invariant |
|----|-----------|
| INV-1 | The output directory is created before writing (`makedirs(..., exist_ok=True)`); a missing directory never fails the write. |
| INV-2 | Git SHA resolution never raises; any failure or timeout yields `git_sha = null`. |
| INV-3 | Each call writes exactly one line terminated by `\n`, appended (mode `"a"`) — prior lines are never altered. |

### Acceptance criteria (*Given / When / Then*)

| ID | Given | When | Then |
|----|-------|------|------|
| AC-1 | `out_dir` does not exist | `append_run(out_dir, repo, "scan", "d1", {"score": 0.9})` | `out_dir` is created and `runs.jsonl` contains one line with `command="scan"`, `detector="d1"`, `score=0.9`. |
| AC-2 | `repo` is not a git repository | `append_run(...)` is called | the written record has `"git_sha": null` and no exception is raised. |
| AC-3 | `runs.jsonl` already has 3 lines | `append_run(...)` is called once | the file has exactly 4 lines; the first 3 are unchanged. |
| AC-4 | `git rev-parse` hangs | `append_run(...)` is called | resolution aborts at 5 seconds and `git_sha` is recorded as `null`. |
| AC-5 | any successful call | `append_run(...)` returns | the return value equals `os.path.join(out_dir, "runs.jsonl")`. |
| AC-6 | `stats={"date": "2000-01-01"}` | `append_run(...)` is called | the record's `date` field is `"2000-01-01"` (stats override built-ins). |
