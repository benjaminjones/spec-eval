"""The process-wide call ceiling — the guard that makes an unattended paid run safe to leave alone."""
import pytest

from spec_eval import providers


@pytest.fixture(autouse=True)
def _reset():
    before = dict(providers.USAGE)
    providers.set_max_calls(None)
    yield
    providers.set_max_calls(None)
    providers.USAGE.update(before)


def test_unset_ceiling_never_blocks():
    providers.USAGE["calls"] = 10_000
    providers._guard()                       # no exception


def test_guard_fires_at_the_ceiling_not_after_it():
    """The ceiling is the number of calls MADE. Checked before the request, so N means N, never N+1."""
    providers.set_max_calls(3)
    for made in (0, 1, 2):
        providers.USAGE["calls"] = made
        providers._guard()                   # the 1st, 2nd and 3rd calls are allowed
    providers.USAGE["calls"] = 3
    with pytest.raises(providers.CallBudgetExceeded):
        providers._guard()                   # the 4th is not


def test_the_error_names_the_spend_so_far():
    """A ceiling that aborts without saying what it already spent leaves you guessing at the bill."""
    providers.set_max_calls(1)
    providers.USAGE.update({"calls": 1, "in": 72045, "out": 10874})
    with pytest.raises(providers.CallBudgetExceeded) as e:
        providers._guard()
    assert "72,045" in str(e.value) and "10,874" in str(e.value)
    assert "1 of 1" in str(e.value)


def test_zero_and_none_both_mean_unlimited():
    for v in (0, None):
        providers.set_max_calls(v)
        assert providers.MAX_CALLS is None


def test_the_guard_is_wired_into_gen(monkeypatch):
    """A guard that exists but is not called is the benjamini_hochberg defect. Pin the wiring."""
    providers.set_max_calls(1)
    providers.USAGE["calls"] = 1
    with pytest.raises(providers.CallBudgetExceeded):
        providers.gen("claude-code", "sys", "user")     # must raise BEFORE any subprocess or HTTP call
