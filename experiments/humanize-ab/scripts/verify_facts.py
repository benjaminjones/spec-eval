"""Fact-preservation guard for the humanize A/B variants.

The experiment asks one question: does the sufficiency grader score CONTENT or SHAPE? That question is only
answerable if every variant carries the same facts as the baseline and differs only in presentation. This script
enforces that precondition BEFORE any model call is spent.

It extracts the baseline's checkable literals — backticked code spans, bare numbers, and quoted strings — and
asserts each one survives into every variant. A variant that drops a literal is rejected: a sufficiency drop on
such a variant would be explained by the missing fact, not by the lost shape, and the run would prove nothing.

Deliberately one-directional. A variant may ADD text (prose needs connective tissue the tables did not); it may
not LOSE a literal. Run it with no arguments from this directory.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # the experiment dir, one level up from scripts/
BASELINE = os.path.join(HERE, "runlog.baseline.md.variant")
VARIANTS = ["runlog.frozen.md.variant", "runlog.naive.md.variant"]

# Literals the grader can check a spec against. Markdown table pipes and heading marks are SHAPE, not fact, so
# they are deliberately not extracted — losing them is the very thing the experiment is measuring.
_CODE_SPAN = re.compile(r"`([^`\n]+)`")
# Trailing punctuation must not hide a number: `as defined in §2.` carries the fact `2`. The guard therefore
# rejects only a following word character, not a following period.
_NUMBER = re.compile(r"(?<![\w.])(\d+(?:\.\d+)*)(?!\w)")

# INV-1 / AC-6 are structural IDs, and their digits are not facts about the module. The naive variant dissolves
# the tables that carry them BY CONSTRUCTION, so they are stripped before number extraction and tracked
# separately — otherwise the guard would fail the naive variant for the very shape change under test.
_STRUCTURAL_ID = re.compile(r"\b((?:INV|AC)-\d+)\b")


def literals(text):
    """The baseline's checkable facts: backticked spans plus bare numbers, normalised for whitespace.
    Structural IDs are removed before number extraction and returned as their own set."""
    ids = {m.group(1) for m in _STRUCTURAL_ID.finditer(text)}
    stripped = _STRUCTURAL_ID.sub(" ", text)
    spans = {" ".join(m.group(1).split()) for m in _CODE_SPAN.finditer(stripped)}
    numbers = {m.group(1) for m in _NUMBER.finditer(stripped)}
    return spans, numbers, ids


def main():
    base = open(BASELINE, encoding="utf-8").read()
    base_spans, base_numbers, base_ids = literals(base)
    failed = False

    for name in VARIANTS:
        path = os.path.join(HERE, name)
        text = open(path, encoding="utf-8").read()
        var_spans, var_numbers, var_ids = literals(text)
        flat = " ".join(text.split())

        missing_spans = sorted(s for s in base_spans if s not in flat)
        missing_numbers = sorted(base_numbers - var_numbers)
        dropped_ids = sorted(base_ids - var_ids)

        status = "FAIL" if (missing_spans or missing_numbers) else "ok"
        print(f"[{status}] {name}")
        print(f"       code spans {len(base_spans) - len(missing_spans)}/{len(base_spans)} preserved, "
              f"numbers {len(base_numbers) - len(missing_numbers)}/{len(base_numbers)} preserved, "
              f"structural IDs {len(base_ids) - len(dropped_ids)}/{len(base_ids)} retained")
        if dropped_ids:
            print(f"       IDs dropped (SHAPE, the variable under test): {', '.join(dropped_ids)}")
        if missing_spans:
            print(f"       MISSING code spans: {', '.join(missing_spans)}")
        if missing_numbers:
            print(f"       MISSING numbers: {', '.join(missing_numbers)}")
        if status == "FAIL":
            failed = True

    if failed:
        print("\nA variant lost a fact. Fix it before spending model calls — the A/B is not interpretable "
              "while a variant differs from the baseline in content as well as shape.")
        return 1
    print("\nAll variants preserve the baseline's facts. The only difference is presentation, which is the "
          "variable under test.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
