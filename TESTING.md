# Testing

Adapted **by analogy** from a layered testing strategy (the strategy's own guidance: *"push verification as low as
it can meaningfully go"* and *"adapt the worked examples to your domain"*), scaled to a small CLI.

## Which layers apply here

| Layer | Applied? | Where |
|---|---|---|
| **0 — Static analysis** | ✅ ruff + type hints | `ruff check .` |
| **1 — Contract / property** | ✅ **the core** — the pure functions | `tests/contract/` |
| **2 — Acceptance (GWT)** | ✅ command-level, GWT-named | `tests/acceptance/` |
| **3 — System / e2e smoke** | ✅ the full CLI on a fixture repo | `tests/system/test_e2e_smoke.py` |
| **Manual — skill trigger routing** | ✅ model-in-the-loop, **not in CI** (needs the `claude` CLI or a key) | `tests/manual/` — see its [README](tests/manual/README.md) |

## Conventions kept
- **Design by Contract** — the contract tests are framed as precondition / postcondition / invariant checks.
- **GWT acceptance criteria** — `test_ac<NNN>_<scenario>` names, Given/When/Then in the docstring.
- **Property-based testing** (Hypothesis) for the pure, total functions (`_bar`, `classify_exclude`) — a
  *proportionate* budget, not the 10,000-per-invariant a large system's safety invariants warrant.
- **Test doubles for the model boundary** — `tests/doubles/fake_provider.py` monkeypatches `providers.gen`, so
  `drift` / `sufficiency` / `generate` are tested **with no API key**.
- Production and test code are never co-located; every test name is interpretable without its body.

## Run
```bash
pip install -e ".[dev]"
ruff check .          # Layer 0
pytest                # Layers 1, 2, 3 — no API key needed
```

Layers 0 through 3 also run in CI on every pull request and on `main`
([`tests.yml`](.github/workflows/tests.yml)), against the `requires-python` floor and a current release, so the
version claim in `pyproject.toml` stays true rather than aspirational. The manual layer stays local by design:
it needs a model.
