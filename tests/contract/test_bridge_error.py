"""Layer 1 — the claude-code bridge reports the CLI's reason, not the head of its telemetry.

A real failure surfaced as `duration_api_ms: 0, num_turns: 1, usage: {input_tokens: 0, ...}` with the cause
cut off: the envelope requested by `--output-format json` puts `usage` before `result`, so truncating the
first 400 characters removed the only field worth reading.
"""
import json

from spec_eval.providers import _bridge_error


def test_the_reason_is_pulled_from_the_envelope_not_the_counters():
    env = json.dumps({"is_error": True, "duration_api_ms": 0, "num_turns": 1,
                      "usage": {"input_tokens": 0, "output_tokens": 0},
                      "result": "Credit balance is too low"})
    assert _bridge_error(env, "") == "Credit balance is too low"


def test_usage_is_dropped_when_no_named_field_carries_the_reason():
    """Some envelopes carry no result/error/message. The counters are still the least useful part."""
    env = json.dumps({"is_error": True, "subtype": "auth_error",
                      "usage": {"input_tokens": 0, "cache_read_input_tokens": 0}})
    out = _bridge_error(env, "")
    assert "auth_error" in out and "input_tokens" not in out


def test_non_json_output_is_passed_through():
    assert _bridge_error("claude: command failed", "") == "claude: command failed"


def test_stderr_is_used_when_stdout_is_empty():
    assert _bridge_error("", "not logged in") == "not logged in"


def test_no_output_says_so_rather_than_returning_empty():
    assert _bridge_error("", "") == "no output"
