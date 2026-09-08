"""The rubric override is a contract: it reaches the model, or it fails loudly. Never silently default.

A run that quietly grades against the wrong rubric is indistinguishable from one that works — the report
is well-formed, the score is plausible, and nothing errors. So every test here asserts on the SYSTEM
PROMPT ACTUALLY SENT rather than on a return value, and the failure cases assert that the tool exits
rather than falling back.
"""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from spec_eval import audit, sufficiency  # noqa: E402


CUSTOM = "CUSTOM RUBRIC MARKER — quote a verbatim span into code_ref.\n"


@pytest.fixture()
def project(tmp_path):
    (tmp_path / "a.md").write_text("The total was 42 units across three sites.\n", encoding="utf-8")
    (tmp_path / "b.md").write_text("The total was 42 units.\n", encoding="utf-8")
    (tmp_path / "custom.md").write_text(CUSTOM, encoding="utf-8")
    return tmp_path


def capture(monkeypatch):
    seen = []

    def fake_gen(model, system, user, **kw):
        seen.append(system)
        return '{"sufficiency":1.0,"gaps":[]}' if "sufficiency" in system.lower() else '{"findings":[]}'

    monkeypatch.setattr(audit.providers, "gen", fake_gen)
    return seen


def pairs_cfg(**extra):
    return {"pairs": [{"label": "p", "code": ["a.md"], "docs": ["b.md"]}], **extra}


def test_default_rubric_is_unchanged(project, monkeypatch):
    seen = capture(monkeypatch)
    sufficiency.sufficiency_repo(str(project), pairs_cfg(), "stub:stub")
    audit.audit_repo(str(project), pairs_cfg(), "stub:stub")
    assert seen[0] == sufficiency.SUFFICIENCY_RUBRIC
    assert seen[1] == audit.DRIFT_RUBRIC


def test_override_reaches_the_sufficiency_prompt(project, monkeypatch):
    seen = capture(monkeypatch)
    sufficiency.sufficiency_repo(str(project), pairs_cfg(rubric={"sufficiency": "custom.md"}),
                                 "stub:stub")
    assert seen[0] == CUSTOM.strip()


def test_override_reaches_the_audit_prompt(project, monkeypatch):
    seen = capture(monkeypatch)
    audit.audit_repo(str(project), pairs_cfg(rubric={"drift": "custom.md"}), "stub:stub")
    assert seen[0] == CUSTOM.strip()


def test_overriding_one_check_leaves_the_other_alone(project, monkeypatch):
    """The commonest way to get this wrong is a shared binding that swaps both at once."""
    seen = capture(monkeypatch)
    cfg = pairs_cfg(rubric={"sufficiency": "custom.md"})
    sufficiency.sufficiency_repo(str(project), cfg, "stub:stub")
    audit.audit_repo(str(project), cfg, "stub:stub")
    assert seen[0] == CUSTOM.strip()
    assert seen[1] == audit.DRIFT_RUBRIC


def test_absolute_path_is_accepted(project, monkeypatch):
    seen = capture(monkeypatch)
    sufficiency.sufficiency_repo(
        str(project), pairs_cfg(rubric={"sufficiency": str(project / "custom.md")}), "stub:stub")
    assert seen[0] == CUSTOM.strip()


def test_missing_file_exits_rather_than_defaulting(project):
    with pytest.raises(SystemExit) as e:
        audit.rubric_from({"rubric": {"drift": "nope.md"}}, "drift", audit.DRIFT_RUBRIC, str(project))
    assert "no such file" in str(e.value)


def test_empty_file_exits_rather_than_defaulting(project):
    (project / "empty.md").write_text("   \n", encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        audit.rubric_from({"rubric": {"drift": "empty.md"}}, "drift", audit.DRIFT_RUBRIC, str(project))
    assert "empty" in str(e.value)


def test_absent_config_returns_the_default():
    for cfg in (None, {}, {"rubric": None}, {"rubric": {}}):
        assert audit.rubric_from(cfg, "drift", audit.DRIFT_RUBRIC) == audit.DRIFT_RUBRIC
