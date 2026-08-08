"""spec-eval — portable code↔doc drift audit + fingerprint."""
import sys

__version__ = "0.3.0"   # THE single source of version truth; pyproject.toml reads this via dynamic version

MIN_PYTHON = (3, 9)     # KEEP IN SYNC: pyproject.toml's `requires-python`; tests/contract/test_python_floor.py pins them

if sys.version_info < MIN_PYTHON:
    # pip enforces `requires-python`, and the documented way to run this from a source checkout
    # (`python3 -m spec_eval …`) never consults it. Without this, an older interpreter fails deep in
    # argparse with an AttributeError that names a stdlib symbol and not the actual problem.
    raise SystemExit(
        f"spec-eval needs Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or newer — this is "
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} at {sys.executable}.\n"
        f"Run it with a newer interpreter, e.g.  python3.{MIN_PYTHON[1]} -m spec_eval …")
