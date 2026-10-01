"""A transient model-call failure must not discard a run's completed work.

A 12-pair audit lost all 12 calls to a single `Request timed out`, twice in a row, because `gen` had
no retry: the first failure propagated out of the per-pair list comprehension and nothing was written.

The fix has to distinguish two failure modes that were previously treated alike:

  · PERMANENT — a missing CLI, an unknown model, the call ceiling. These fail identically on every
    attempt. Retrying wastes time and buries the cause.
  · TRANSIENT — a timeout, a 429, a 5xx. A property of the moment, and worth one more try.

Layer 1, per `TESTING.md`: contract checks on a pure function, with the model boundary replaced by a
double. No API key, no network.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from spec_eval import providers                                        # noqa: E402


def _reset():
    providers.USAGE.update({"in": 0, "out": 0, "calls": 0, "truncated": 0, "retries": 0})
    providers.set_max_calls(None)


# --- which failures are transient -----------------------------------------------------------------

def test_a_timeout_is_transient_and_a_missing_cli_is_not():
    """PRECONDITION on the retry decision. The bridge raises `RuntimeError` for every failure mode, so
    the exception type carries no information and the message is the only signal available."""
    assert providers._is_transient(RuntimeError("`claude -p` failed (exit 1): Request timed out"))
    assert providers._is_transient(RuntimeError("429 rate limit exceeded"))
    assert providers._is_transient(RuntimeError("503 service unavailable"))
    assert not providers._is_transient(RuntimeError("model 'x' needs the Claude Code CLI on PATH"))
    assert not providers._is_transient(RuntimeError("unknown provider 'q'"))


def test_the_call_ceiling_is_never_treated_as_transient():
    """If it were, a run at its ceiling would retry until it exhausted the attempt budget instead of
    stopping — turning a deliberate limit into a delay."""
    assert not providers._is_transient(RuntimeError("call ceiling reached: 5 of 5 already made"))


# --- retry behaviour ------------------------------------------------------------------------------

def test_a_transient_failure_is_retried_and_the_retry_is_counted(monkeypatch):
    """POSTCONDITION: the call succeeds, and `USAGE['retries']` records that it needed help.

    The counting is not decoration. A run that silently retried is indistinguishable from a clean one,
    and a flaky bridge would then look like a healthy one.
    """
    _reset()
    calls = {"n": 0}

    def flaky(*a, **k):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("`claude -p` failed (exit 1): Request timed out")
        return "ok"

    monkeypatch.setattr(providers, "_gen_once", flaky)
    monkeypatch.setattr(providers.time if hasattr(providers, "time") else providers,
                        "sleep", lambda s: None, raising=False)
    import time as _t
    monkeypatch.setattr(_t, "sleep", lambda s: None)

    assert providers.gen("claude-code", "sys", "user") == "ok"
    assert calls["n"] == 2
    assert providers.USAGE["retries"] == 1


def test_a_permanent_failure_is_not_retried(monkeypatch):
    """One attempt, and the original error reaches the caller unchanged — a wrapped or delayed
    "CLI not on PATH" is strictly worse than an immediate one."""
    _reset()
    calls = {"n": 0}

    def broken(*a, **k):
        calls["n"] += 1
        raise RuntimeError("model 'claude-code' needs the Claude Code CLI on PATH")

    monkeypatch.setattr(providers, "_gen_once", broken)
    try:
        providers.gen("claude-code", "sys", "user")
        raise AssertionError("expected the permanent failure to propagate")
    except RuntimeError as e:
        assert "on PATH" in str(e)
    assert calls["n"] == 1, "a permanent failure must not be retried"
    assert providers.USAGE["retries"] == 0


def test_retries_are_bounded_and_the_last_error_propagates(monkeypatch):
    """INVARIANT: a bridge that is down does not hang the run. Attempts stop at RETRY_ATTEMPTS and the
    real error surfaces rather than a generic one."""
    _reset()
    calls = {"n": 0}

    def always_timeout(*a, **k):
        calls["n"] += 1
        raise RuntimeError("Request timed out")

    monkeypatch.setattr(providers, "_gen_once", always_timeout)
    import time as _t
    monkeypatch.setattr(_t, "sleep", lambda s: None)
    try:
        providers.gen("claude-code", "sys", "user")
        raise AssertionError("expected exhaustion to raise")
    except RuntimeError as e:
        assert "timed out" in str(e)
    assert calls["n"] == providers.RETRY_ATTEMPTS
    assert providers.USAGE["retries"] == providers.RETRY_ATTEMPTS - 1


def test_the_call_ceiling_counts_logical_calls_not_attempts(monkeypatch):
    """`--max-calls` limits the questions asked, not the packets sent. A retried call must consume one
    unit of budget, or a flaky connection would silently halve a user's stated ceiling."""
    _reset()
    providers.set_max_calls(2)
    calls = {"n": 0}

    def flaky(*a, **k):
        calls["n"] += 1
        if calls["n"] in (1, 3):
            raise RuntimeError("Request timed out")
        providers.USAGE["calls"] += 1          # what a real provider path does via _track
        return "ok"

    monkeypatch.setattr(providers, "_gen_once", flaky)
    import time as _t
    monkeypatch.setattr(_t, "sleep", lambda s: None)
    assert providers.gen("claude-code", "s", "u") == "ok"
    assert providers.gen("claude-code", "s", "u") == "ok"
    assert providers.USAGE["retries"] == 2, "both logical calls needed one retry each"
    _reset()
