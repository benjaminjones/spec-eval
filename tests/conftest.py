"""Shared fixtures. The provider double lets the model-backed commands run with no API key."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))          # make `doubles` importable
from doubles.fake_provider import install as _install_fake_gen  # noqa: E402


@pytest.fixture
def repo(tmp_path):
    """A tiny repo: one covered module (spec beside it), one uncovered, plus glue + a test (both excluded)."""
    (tmp_path / "widget.py").write_text("def add(a, b):\n    return a + b\n")
    (tmp_path / "widget.md").write_text("## 1. Purpose\nAdds two numbers.\n")
    (tmp_path / "helper.py").write_text("def noop():\n    pass\n")                 # spec-worthy, NO spec
    (tmp_path / "__init__.py").write_text("")                                      # glue → excluded
    (tmp_path / "test_widget.py").write_text("def test_x():\n    assert True\n")   # test → excluded
    return tmp_path


@pytest.fixture
def fake_model(monkeypatch):
    """Patch the model boundary; return a model spec string the commands accept."""
    _install_fake_gen(monkeypatch)
    return "fake:model"


@pytest.fixture(autouse=True)
def _reset_provider_last():
    """LAST is deliberately module-global (read right after gen()); tests must not leak it across files."""
    from spec_eval import providers
    providers.LAST["truncated"] = False
    yield
    providers.LAST["truncated"] = False
