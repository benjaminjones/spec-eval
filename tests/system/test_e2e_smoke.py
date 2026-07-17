"""Layer 4 — e2e smoke: the full CLI pipeline on a fresh repo, zero config, no API key (fake provider)."""
from spec_eval import cli


def test_e2e_smoke_generate_coverage_audit_sufficiency(tmp_path, fake_model):
    """Given a fresh one-module repo, When generate → coverage → audit → sufficiency run via the CLI with no
    config, Then a spec is authored beside the code, coverage reaches 100%, and both reports are written."""
    (tmp_path / "calc.py").write_text("def add(a, b):\n    return a + b\n")
    out = str(tmp_path / "spec-reports")

    cli.main(["generate", str(tmp_path), "--model", fake_model, "--out", out])
    assert (tmp_path / "calc.md").exists()                               # authored beside the code

    cli.main(["coverage", str(tmp_path), "--out", out, "--min", "100"])  # co-located → 100%, no exit(1)

    cli.main(["audit", str(tmp_path), "--model", fake_model, "--out", out])
    cli.main(["sufficiency", str(tmp_path), "--model", fake_model, "--out", out])

    import os
    assert os.path.exists(os.path.join(out, "report.md"))
    assert os.path.exists(os.path.join(out, "sufficiency.md"))
    assert os.path.exists(os.path.join(out, "runs.jsonl"))          # every run is logged
