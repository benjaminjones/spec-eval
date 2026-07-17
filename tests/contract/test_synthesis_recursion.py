"""Layer 1 — recursive synthesis: a folder whose per-module intents exceed REDUCE_CAP is synthesised in
sub-group passes — modules are NEVER dropped. (The old behavior dropped overflow modules with a note, so a
folder spec synthesised from only some of its modules could ship as if complete.)"""

from spec_eval import authoring, providers


def test_pack_keeps_every_item_and_respects_the_cap():
    items = [("a", "x" * 80), ("b", "y" * 80), ("c", "z" * 80)]
    groups = authoring._pack(items, 200)
    assert sum(len(g) for g in groups) == 3                     # nothing dropped, ever
    assert len(groups) >= 2                                     # the cap actually split them


def test_pack_slices_a_lone_oversized_intent_instead_of_looping():
    groups = authoring._pack([("big", "q" * 500)], 100)
    assert len(groups) == 1 and len(groups[0]) == 1
    assert groups[0][0][1].endswith("[truncated]")              # sliced with a visible marker


def test_synthesize_single_group_is_one_call_level_one(monkeypatch):
    calls = []
    monkeypatch.setattr(providers, "gen", lambda *a, **k: (calls.append(1), "## doc")[1])
    md, levels, capped = authoring._synthesize("fake:m", "RUBRIC", [("a", "short")], "H")
    assert md == "## doc" and levels == 1 and capped is False and len(calls) == 1


def test_synthesize_recurses_and_every_module_is_seen(monkeypatch):
    monkeypatch.setattr(authoring, "REDUCE_CAP", 200)
    seen = []

    def fake_gen(model, system, user, max_tokens=1200):
        seen.append(user)
        return "## intermediate\nshort"
    monkeypatch.setattr(providers, "gen", fake_gen)
    items = [(f"m{i}", "x" * 150) for i in range(6)]            # each block alone nearly fills the cap
    md, levels, capped = authoring._synthesize("fake:m", "RUBRIC", items, "H")
    assert levels >= 2                                          # it recursed instead of dropping
    joined = "\n".join(seen)
    for i in range(6):
        assert f"m{i}" in joined                                # every module reached a synthesis pass


def test_synthesize_terminates_when_intermediates_never_shrink(monkeypatch):
    """Regression (caught in development): synthesis replies that stay near cap size repacked into the same
    group count forever. Past the no-progress point the items are force-fitted into one final, marked call."""
    monkeypatch.setattr(authoring, "REDUCE_CAP", 200)
    calls = []

    def fake_gen(model, system, user, max_tokens=1200):
        calls.append(user)
        return "z" * 180                                        # every reply nearly fills the cap — no shrinkage
    monkeypatch.setattr(providers, "gen", fake_gen)
    items = [(f"m{i}", "x" * 180) for i in range(3)]
    md, levels, capped = authoring._synthesize("fake:m", "RUBRIC", items, "H")
    assert levels <= authoring._MAX_LEVELS and len(calls) < 30  # bounded work, no runaway
    assert "...[truncated]" in calls[-1]                        # the force-fit final call is visibly marked


def test_generate_folder_note_reports_multipass_nothing_dropped(tmp_path, monkeypatch):
    """Uses the user-facing `caps.reduce` config override (not a monkeypatch), proving the plumbing end-to-end."""
    pkg = tmp_path / "src" / "pkg"
    pkg.mkdir(parents=True)
    for name in ("a", "b", "c"):
        (pkg / f"{name}.py").write_text(f"def {name}():\n    return 1\n")
    monkeypatch.setattr(providers, "gen",
                        lambda *a, **k: "## 1. Purpose\n" + "w" * 250)   # long intents force multi-pass
    cfg = {"authoring": {"layout": "per-dir"}, "caps": {"reduce": 300}}
    res = authoring.generate_repo(str(tmp_path), cfg, "fake:m")
    folder = next(r for r in res if r["spec"].endswith("pkg.md"))
    assert folder["status"] == "authored"
    assert "passes" in folder["note"] and "nothing dropped" in folder["note"]
