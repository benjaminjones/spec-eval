"""Layer 1 — the Python floor is stated once and enforced where a human meets it.

`requires-python` lives in pyproject.toml, which pip reads and a source checkout does not. The documented
way to run from a checkout is `python3 -m spec_eval`, so an older interpreter used to fail inside argparse
with an AttributeError naming a stdlib symbol rather than the version. These pin the two copies together
and pin the floor to the newest feature actually relied on.
"""
import re
import os

import spec_eval

_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")


def test_the_floor_matches_pyproject():
    """Two copies of one number: the guard a human hits, and the metadata pip reads."""
    text = open(os.path.join(_ROOT, "pyproject.toml")).read()
    m = re.search(r'requires-python\s*=\s*"[><=]*\s*(\d+)\.(\d+)"', text)
    assert m, "pyproject.toml no longer declares requires-python in a form this test can read"
    assert spec_eval.MIN_PYTHON == (int(m.group(1)), int(m.group(2))), (
        f"spec_eval.MIN_PYTHON {spec_eval.MIN_PYTHON} != pyproject's requires-python {m.group(1)}.{m.group(2)}")


def test_the_floor_covers_the_newest_feature_relied_on():
    """`argparse.BooleanOptionalAction` is 3.9+, and it is what actually broke on 3.8. If the floor is ever
    lowered, this fails rather than the user finding out through a stdlib AttributeError."""
    import argparse
    assert hasattr(argparse, "BooleanOptionalAction")
    assert spec_eval.MIN_PYTHON >= (3, 9), "BooleanOptionalAction needs 3.9; the floor cannot go below it"
