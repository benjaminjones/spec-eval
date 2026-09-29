"""The `status` vocabulary: what `authoring.py` emits must be what `authoring.md` enumerates.

`authoring.md`'s Definitions table names the values a `generate` record's `status` can take, and
`generate_repo` emits them. Nothing tied the two together, and they drifted: the table listed
`authored`, `skipped` and `failed` while the code also emits `stray` for markdown that appeared on
disk without being a declared target (INV-15, AC-18).

A prose enumeration with no executable form is a claim, not a contract. This is its executable form,
and it fails in both directions — a value added to the code without the table, or removed from the
code while the table still promises it.

Layer 1, per `TESTING.md`: a contract framed as an invariant check over a pure reading of the two
files, no model and no filesystem fixture required.
"""
import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CODE = os.path.join(_ROOT, "spec_eval", "authoring.py")
DOC = os.path.join(_ROOT, "spec_eval", "authoring.md")


def _emitted_statuses():
    """Every literal assigned to a `status` key in the authoring module."""
    src = open(CODE, encoding="utf-8").read()
    return set(re.findall(r'"status":\s*"([a-z]+)"', src))


def _documented_statuses():
    """The values the Definitions table's `status` row enumerates, read as backticked literals."""
    doc = open(DOC, encoding="utf-8").read()
    row = next((ln for ln in doc.splitlines()
                if ln.startswith("| status |") or ln.startswith("| `status` |")), None)
    assert row, "authoring.md has no `status` row in its Definitions table"
    return set(re.findall(r"`([a-z]+)`", row))


def test_the_status_row_enumerates_every_status_the_code_emits():
    """INVARIANT: no status reaches a consumer that the document does not name.

    The failure this pins actually happened: `stray` was emitted by `generate_repo` and absent from the
    Definitions row, so a reader taking the row as the closed set would not have handled it.
    """
    missing = _emitted_statuses() - _documented_statuses()
    assert not missing, (
        f"authoring.py emits {sorted(missing)} but authoring.md's Definitions row does not name "
        f"{'it' if len(missing) == 1 else 'them'}. Add to the row, or stop emitting.")


def test_the_status_row_promises_nothing_the_code_cannot_emit():
    """INVARIANT: the document does not name a status no code path produces.

    The other direction, which no previous test covered. A row naming a value the code stopped
    emitting is as misleading as one omitting a value it does emit, and is the likelier drift once a
    branch is removed.
    """
    phantom = _documented_statuses() - _emitted_statuses()
    assert not phantom, (
        f"authoring.md's Definitions row names {sorted(phantom)} but no code path emits "
        f"{'it' if len(phantom) == 1 else 'them'}.")


def test_stray_is_among_them():
    """A guard on the guard: if the extraction above silently matched nothing, both set comparisons
    would pass vacuously. `stray` is the value the drift was about, so its presence on both sides is
    asserted directly rather than inferred from two empty differences."""
    assert "stray" in _emitted_statuses(), "extraction from authoring.py found no `stray`"
    assert "stray" in _documented_statuses(), "extraction from authoring.md found no `stray`"
    assert len(_emitted_statuses()) >= 4, "extraction looks broken — fewer than four statuses found"
