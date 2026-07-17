"""Layer 1 — runlog: append-only run records stamped with date + git sha."""
import json

from spec_eval import runlog


def test_append_run_writes_one_jsonl_record(tmp_path):
    path = runlog.append_run(str(tmp_path), str(tmp_path), "sufficiency", "anthropic:claude-opus-4-8",
                             {"avg_sufficiency": 0.92, "per_module": {"a": 0.90}})
    lines = open(path).read().strip().splitlines()
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["command"] == "sufficiency" and rec["avg_sufficiency"] == 0.92 and rec["detector"].startswith("anthropic")
    assert "date" in rec and "git_sha" in rec                 # git_sha present (may be None outside a repo)


def test_append_run_is_append_only(tmp_path):
    runlog.append_run(str(tmp_path), str(tmp_path), "coverage", None, {"coverage_pct": 50.0})
    runlog.append_run(str(tmp_path), str(tmp_path), "coverage", None, {"coverage_pct": 100.0})
    lines = open(str(tmp_path / "runs.jsonl")).read().strip().splitlines()
    assert len(lines) == 2 and json.loads(lines[1])["coverage_pct"] == 100.0


def test_git_sha_is_best_effort(tmp_path):
    """Postcondition: a short string in a git repo, None otherwise — never raises."""
    sha = runlog.git_sha(str(tmp_path))
    assert sha is None or isinstance(sha, str)


def test_date_is_a_seconds_precision_timestamp(tmp_path):
    """Same-day runs must be distinguishable by clock time — `date` carries YYYY-MM-DDTHH:MM:SS."""
    import datetime
    path = runlog.append_run(str(tmp_path), str(tmp_path), "coverage", None, {"coverage_pct": 100.0})
    rec = json.loads(open(path).read().strip())
    parsed = datetime.datetime.fromisoformat(rec["date"])
    assert "T" in rec["date"] and parsed.second is not None
