"""Layer 1 — overview × system context: the OBSERVED SYSTEM EVIDENCE block reaches the overview synthesis
call (and ONLY its final pass), scoped per directory, and is absent when nothing was observed — pins
authoring.md AC-10/AC-11 and the extra-block plumbing of `_synthesize`."""
import pytest

from spec_eval import authoring, providers


@pytest.fixture
def recording_gen(monkeypatch):
    """Patch the model boundary with a recorder; returns the call list [(system, user), ...]."""
    calls = []

    def fake_gen(model, system, user, max_tokens=1200):
        calls.append((system, user))
        return "## 1. Purpose\n\n**In one line:** A fixture.\n"

    monkeypatch.setattr(providers, "gen", fake_gen)
    return calls


def _integration_repo(tmp_path):
    (tmp_path / "store.py").write_text("import boto3\nboto3.client('s3')\n")
    (tmp_path / "logic.py").write_text("def run():\n    pass\n")
    return tmp_path


def test_repo_overview_call_carries_the_evidence_block(tmp_path, recording_gen):
    repo = _integration_repo(tmp_path)
    authoring.generate_repo(str(repo), {"authoring": {"overview": "repo"}}, "fake:model")
    overview_calls = [(s, u) for s, u in recording_gen if "Repository overview" in u]
    assert overview_calls, "no overview call was made"
    ((system, user),) = overview_calls
    assert "OBSERVED SYSTEM EVIDENCE" in user and "AWS S3" in user
    assert "## System context" in system                       # the rubric knows how to render the block
    assert "NEVER invent" in system


def test_no_observed_systems_means_no_evidence_block(tmp_path, recording_gen):
    (tmp_path / "pure.py").write_text("def add(a, b):\n    return a + b\n")
    (tmp_path / "more.py").write_text("def sub(a, b):\n    return a - b\n")
    authoring.generate_repo(str(tmp_path), {"authoring": {"overview": "repo"}}, "fake:model")
    assert not any("OBSERVED SYSTEM EVIDENCE" in u for _, u in recording_gen)


def test_per_dir_overview_gets_only_its_directory_evidence(tmp_path, recording_gen):
    (tmp_path / "a").mkdir(), (tmp_path / "b").mkdir()
    (tmp_path / "a" / "s3.py").write_text("import boto3\nboto3.client('s3')\n")
    (tmp_path / "a" / "x.py").write_text("def x():\n    pass\n")
    (tmp_path / "b" / "db.py").write_text("import psycopg2\n")
    (tmp_path / "b" / "y.py").write_text("def y():\n    pass\n")
    authoring.generate_repo(str(tmp_path), {"authoring": {"overview": "per-dir"}}, "fake:model")
    a_calls = [u for _, u in recording_gen if "Directory overview — `a`" in u]
    b_calls = [u for _, u in recording_gen if "Directory overview — `b`" in u]
    assert a_calls and "AWS S3" in a_calls[0] and "PostgreSQL" not in a_calls[0]
    assert b_calls and "PostgreSQL" in b_calls[0] and "AWS S3" not in b_calls[0]


def test_extra_reaches_only_the_final_synthesis_pass(recording_gen):
    """Force a multi-pass reduce with a tiny cap: intermediates must NOT carry the block; the final call must."""
    items = [(f"m{i}", "x" * 400) for i in range(6)]
    authoring._synthesize("fake:model", "rubric", items, "Repository overview",
                          reduce_cap=900, extra="## OBSERVED SYSTEM EVIDENCE\n- AWS S3")
    assert len(recording_gen) > 1, "the tiny cap should have forced a multi-pass synthesis"
    *intermediate, final = recording_gen
    assert all("OBSERVED SYSTEM EVIDENCE" not in u for _, u in intermediate)
    assert "OBSERVED SYSTEM EVIDENCE" in final[1]
