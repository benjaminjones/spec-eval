"""Layer 1 — providers: model-spec parsing, the non-overriding .env loader, and the claude-code CLI bridge."""
import os
import subprocess

import pytest

from spec_eval import providers


def test_parse_model_explicit_provider():
    assert providers.parse_model("openai:gpt-5.5") == ("openai", "gpt-5.5")


def test_parse_model_bare_name_defaults_provider():
    prov, model = providers.parse_model("claude-opus-4-8")
    assert prov == "anthropic" and model == "claude-opus-4-8"


def test_load_env_sets_missing_key(tmp_path, monkeypatch):
    monkeypatch.delenv("SPEC_EVAL_TEST_K", raising=False)
    (tmp_path / ".env").write_text("SPEC_EVAL_TEST_K=v1\n# a comment\n\n")
    providers.load_env(str(tmp_path / ".env"))
    assert os.environ["SPEC_EVAL_TEST_K"] == "v1"


def test_load_env_does_not_override_existing(tmp_path, monkeypatch):
    monkeypatch.setenv("SPEC_EVAL_TEST_K", "already")
    (tmp_path / ".env").write_text("SPEC_EVAL_TEST_K=v2\n")
    providers.load_env(str(tmp_path / ".env"))
    assert os.environ["SPEC_EVAL_TEST_K"] == "already"                   # non-overriding


def test_load_env_absent_is_safe():
    providers.load_env("/no/such/path/.env")                            # postcondition: no raise


def test_parse_model_bare_claude_code_is_the_bridge():
    assert providers.parse_model("claude-code") == ("claude-code", "")


def test_parse_model_claude_code_with_model_override():
    assert providers.parse_model("claude-code:haiku") == ("claude-code", "haiku")


def test_claude_code_bridge_calls_the_cli_and_tracks_usage(monkeypatch):
    """The bridge shells out to `claude -p --output-format json`, feeds the user prompt on stdin, strips
    ANTHROPIC_API_KEY from the child env (subscription billing can never silently become API billing), returns
    the envelope's `result`, and records exact token usage."""
    seen = {}

    def fake_run(cmd, input=None, capture_output=None, text=None, env=None, timeout=None):
        seen.update(cmd=cmd, input=input, env=env)
        return subprocess.CompletedProcess(
            cmd, 0, stdout='{"result": "SPEC TEXT", "usage": {"input_tokens": 7, "output_tokens": 3}}', stderr="warn")

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-must-not-leak")
    monkeypatch.setattr("shutil.which", lambda name: "/usr/local/bin/claude")
    monkeypatch.setattr(subprocess, "run", fake_run)
    before = dict(providers.USAGE)

    out = providers.gen("claude-code:haiku", "SYSTEM RUBRIC", "USER PROMPT")

    assert out == "SPEC TEXT"
    assert seen["cmd"][0].endswith("claude") and "-p" in seen["cmd"]
    assert "SYSTEM RUBRIC" in seen["cmd"] and seen["cmd"][seen["cmd"].index("--model") + 1] == "haiku"
    assert seen["input"] == "USER PROMPT"
    assert "ANTHROPIC_API_KEY" not in seen["env"]                       # the key never reaches the child
    assert providers.USAGE["in"] == before["in"] + 7
    assert providers.USAGE["out"] == before["out"] + 3
    assert providers.USAGE["calls"] == before["calls"] + 1
    assert providers.LAST["truncated"] is False                         # the envelope has no stop reason — never flags


def test_anthropic_reply_truncation_is_flagged(monkeypatch):
    """stop_reason == max_tokens → the call is recorded as truncated (LAST for the caller, USAGE as a tally)."""
    from types import SimpleNamespace as NS
    resp = NS(usage=NS(input_tokens=5, output_tokens=7), stop_reason="max_tokens",
              content=[NS(type="text", text="partial")])
    monkeypatch.setitem(providers._clients, "anthropic", NS(messages=NS(create=lambda **kw: resp)))
    before = dict(providers.USAGE)
    assert providers.gen("anthropic:m", "s", "u") == "partial"
    assert providers.LAST["truncated"] is True
    assert providers.USAGE["truncated"] == before["truncated"] + 1


def test_anthropic_normal_stop_is_not_flagged(monkeypatch):
    from types import SimpleNamespace as NS
    resp = NS(usage=NS(input_tokens=5, output_tokens=7), stop_reason="end_turn",
              content=[NS(type="text", text="done")])
    monkeypatch.setitem(providers._clients, "anthropic", NS(messages=NS(create=lambda **kw: resp)))
    before = dict(providers.USAGE)
    providers.gen("anthropic:m", "s", "u")
    assert providers.LAST["truncated"] is False
    assert providers.USAGE["truncated"] == before["truncated"]


def test_openai_length_finish_is_flagged(monkeypatch):
    from types import SimpleNamespace as NS
    resp = NS(usage=NS(prompt_tokens=3, completion_tokens=4),
              choices=[NS(finish_reason="length", message=NS(content="cut"))])
    monkeypatch.setitem(providers._clients, "openai", NS(chat=NS(completions=NS(create=lambda **kw: resp))))
    assert providers.gen("openai:gpt-x", "s", "u") == "cut"
    assert providers.LAST["truncated"] is True


def test_google_max_tokens_finish_is_flagged(monkeypatch):
    from types import SimpleNamespace as NS
    resp = NS(usage_metadata=NS(prompt_token_count=2, candidates_token_count=3),
              candidates=[NS(finish_reason=NS(name="MAX_TOKENS"))], text="g")
    monkeypatch.setitem(providers._clients, "google", NS(models=NS(generate_content=lambda **kw: resp)))
    assert providers.gen("google:gemini-x", "s", "u") == "g"
    assert providers.LAST["truncated"] is True


def test_claude_code_bridge_missing_cli_raises(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: None)
    with pytest.raises(RuntimeError, match="claude-code"):
        providers.gen("claude-code", "s", "u")
