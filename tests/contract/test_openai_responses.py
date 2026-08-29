"""The v1/responses fallback — newer OpenAI models are served only from that endpoint."""
from spec_eval import providers


class _Err(Exception):
    def __init__(self, msg, status):
        super().__init__(msg)
        self.status_code = status


def test_only_the_specific_404_triggers_the_fallback():
    """A blanket retry would re-issue a call after a rate limit or an auth failure — one billable error
    becoming two. Match the API's own words, nothing broader."""
    assert providers._wants_responses_endpoint(
        _Err("This model is not supported in the v1/chat/completions endpoint. Use the v1/responses "
             "endpoint instead.", 404)) is True
    # everything else must NOT retry
    assert providers._wants_responses_endpoint(_Err("model not found", 404)) is False
    assert providers._wants_responses_endpoint(_Err("rate limit exceeded", 429)) is False
    assert providers._wants_responses_endpoint(_Err("invalid api key", 401)) is False
    assert providers._wants_responses_endpoint(_Err("use the v1/responses endpoint", 400)) is False
    assert providers._wants_responses_endpoint(ValueError("boom")) is False


class _Usage:
    input_tokens, output_tokens = 1234, 56


class _Resp:
    usage, status, output_text, output = _Usage(), "completed", "hello", None


class _Client:
    class responses:
        @staticmethod
        def create(**kw):
            _Client.seen = kw
            return _Resp()


def test_responses_path_maps_the_differently_named_token_fields():
    """responses reports input/output_tokens; chat reports prompt/completion_tokens. Mixing them up
    silently under-reports the spend a paid run is budgeted against."""
    before = dict(providers.USAGE)
    try:
        providers.USAGE.update({"in": 0, "out": 0, "calls": 0, "truncated": 0})
        out = providers._gen_openai_responses(_Client(), "m", "sys", "usr", 900)
        assert out == "hello"
        assert providers.USAGE["in"] == 1234 and providers.USAGE["out"] == 56
        assert _Client.seen["instructions"] == "sys" and _Client.seen["input"] == "usr"
        assert _Client.seen["max_output_tokens"] == 900
    finally:
        providers.USAGE.update(before)


def test_incomplete_status_is_recorded_as_truncated():
    class _Trunc(_Resp):
        status = "incomplete"

    class _C:
        class responses:
            @staticmethod
            def create(**kw): return _Trunc()

    before = dict(providers.USAGE)
    try:
        providers.USAGE.update({"in": 0, "out": 0, "calls": 0, "truncated": 0})
        providers._gen_openai_responses(_C(), "m", "s", "u", 100)
        assert providers.USAGE["truncated"] == 1
    finally:
        providers.USAGE.update(before)


def test_text_is_assembled_when_output_text_is_absent():
    class _Part:
        text = "wor"

    class _Part2:
        text = "ld"

    class _Item:
        content = [_Part(), _Part2()]
    class _NoConvenience(_Resp):
        output_text, output = None, [_Item()]

    class _C:
        class responses:
            @staticmethod
            def create(**kw): return _NoConvenience()

    before = dict(providers.USAGE)
    try:
        assert providers._gen_openai_responses(_C(), "m", "s", "u", 100) == "world"
    finally:
        providers.USAGE.update(before)
