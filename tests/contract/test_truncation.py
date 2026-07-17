"""Layer 1 — truncation transparency: input caps and reply token-caps are SURFACED, never silent. Found live:
a generate run shipped a spec ending mid-table with no warning, and a capped sufficiency reply read as a generic
parse failure — these pin the fix (notes on pair records / authored records, flags from the provider layer)."""
import pytest

from spec_eval import audit, authoring, providers, sufficiency


@pytest.fixture(autouse=True)
def _reset_last():
    providers.LAST["truncated"] = False
    yield
    providers.LAST["truncated"] = False


def test_read_globs_reports_the_input_cap(tmp_path):
    (tmp_path / "big.py").write_text("x = 1\n" * 200)
    text, n, capped = audit._read_globs(str(tmp_path), ["big.py"], 50)
    assert n == 1 and capped is True and text.endswith("[truncated]")
    text2, _, capped2 = audit._read_globs(str(tmp_path), ["big.py"], 10_000)
    assert capped2 is False and "[truncated]" not in text2


def test_audit_pair_flags_input_and_reply_caps(tmp_path, monkeypatch):
    (tmp_path / "big.py").write_text("x = 1\n" * 12000)         # 72k chars > CODE_CAP (64k)
    (tmp_path / "doc.md").write_text("## 1. Purpose\nsmall\n")

    def fake_gen(model, system, user, max_tokens=1200):
        providers.LAST["truncated"] = True                      # simulate a reply cut at the token cap
        return '{"findings": []}'
    monkeypatch.setattr(providers, "gen", fake_gen)
    r = audit.audit_pair(str(tmp_path), {"label": "p", "code": ["big.py"], "docs": ["doc.md"]}, "fake:m")
    assert any("code input capped" in n for n in r["truncated"])
    assert any("reply hit the token cap" in n for n in r["truncated"])
    assert not any("docs input capped" in n for n in r["truncated"])   # the small side is not flagged


def test_audit_pair_clean_run_has_no_truncated_key(tmp_path, monkeypatch):
    (tmp_path / "a.py").write_text("x = 1\n")
    (tmp_path / "a.md").write_text("## 1. Purpose\n")
    monkeypatch.setattr(providers, "gen", lambda *a, **k: '{"findings": []}')
    r = audit.audit_pair(str(tmp_path), {"label": "p", "code": ["a.py"], "docs": ["a.md"]}, "fake:m")
    assert "truncated" not in r


def test_sufficiency_unparseable_reply_names_the_token_cap(tmp_path, monkeypatch):
    """The exact live failure shape: a reply cut mid-JSON. The record now says WHY it couldn't be scored."""
    (tmp_path / "a.py").write_text("x = 1\n")
    (tmp_path / "a.md").write_text("## 1. Purpose\n")

    def fake_gen(model, system, user, max_tokens=1200):
        providers.LAST["truncated"] = True
        return '{"sufficiency": 0.15, "gaps": [{"sever'
    monkeypatch.setattr(providers, "gen", fake_gen)
    r = sufficiency.sufficiency_pair(str(tmp_path), {"label": "p", "code": ["a.py"], "docs": ["a.md"]}, "fake:m")
    assert r["sufficiency"] is None
    assert any("reply hit the token cap" in n for n in r["truncated"])


def test_config_caps_override_the_defaults(tmp_path, monkeypatch):
    """A config `caps: {code: N}` tightens (or raises) the input caps — honored end-to-end, and the
    partial-view note names the ACTIVE cap, not the default."""
    (tmp_path / "a.py").write_text("x = 1\n" * 50)                  # 300 chars — far under the default cap
    (tmp_path / "a.md").write_text("## 1. Purpose\n")
    monkeypatch.setattr(providers, "gen", lambda *a, **k: '{"findings": []}')
    cfg = {"pairs": [{"label": "p", "code": ["a.py"], "docs": ["a.md"]}], "caps": {"code": 100}}
    r = audit.audit_repo(str(tmp_path), cfg, "fake:m")[0]
    assert any("capped at ~100 chars" in n for n in r["truncated"])


def test_author_file_notes_input_cap_and_reply_cap(tmp_path, monkeypatch):
    (tmp_path / "big.py").write_text("x = 1\n" * 12000)

    def fake_gen(model, system, user, max_tokens=1200):
        providers.LAST["truncated"] = True
        return "## 1. Purpose\npartial spec"
    monkeypatch.setattr(providers, "gen", fake_gen)
    md, note = authoring.author_file(str(tmp_path), "big.py", "fake:m")
    assert md.startswith("## 1. Purpose")
    assert "code input capped" in note and "token cap" in note


def test_author_file_clean_run_has_no_note(tmp_path, monkeypatch):
    (tmp_path / "a.py").write_text("x = 1\n")
    monkeypatch.setattr(providers, "gen", lambda *a, **k: "## 1. Purpose\nok")
    md, note = authoring.author_file(str(tmp_path), "a.py", "fake:m")
    assert note is None


def test_generate_repo_carries_the_note_into_the_record(tmp_path, monkeypatch):
    """The end-to-end path of the live bug: an authored spec built from capped input is FLAGGED in its record
    (generated.json / the console line), not shipped as if complete."""
    (tmp_path / "big.py").write_text("x = 1\n" * 12000)
    monkeypatch.setattr(providers, "gen", lambda *a, **k: "## 1. Purpose\nok")
    res = authoring.generate_repo(str(tmp_path), {"pairs": []}, "fake:m")
    rec = next(r for r in res if r["spec"] == "big.md")
    assert rec["status"] == "authored" and "code input capped" in rec["note"]
