# SPEC-HEALTH — `<project>`

> **The measurement layer. REGENERATED, never hand-edited** (only the verdict line + changelog are human-written).
> Specs carry *intent*; this file carries the dated, SHA-pinned *evidence* that the specs still match the code.
> **Litmus:** a fact true regardless of who audited it or when → a spec. A score with a model + date + SHA that
> changes on re-run without the code changing → here.

## Verdict
> <one human-written sentence, read before scrolling — e.g. "Average sufficiency 0.NN across N modules
> (1.0 = no gaps found — an indicator, not a guarantee); M high-severity drift findings open at `<project>` SHA `<sha>`.">

## Pipeline contract  *(machine-written/parsed; field names + types are FROZEN — changes need a changelog entry)*
```yaml
audit_sha: <pinned commit>          # dashboard is known-stale the instant code moves past this
audit_date: <YYYY-MM-DD>
detector: <provider:model>
rollup:
  avg_sufficiency: 0.0
  total_high_drift: 0
  modules_covered: 0
  modules_total: 0
modules:
  - name: <module>
    coverage_status: spec-worthy | excluded-glue | missing-spec
    drift_high: 0
    drift_med: 0
    drift_low: 0
    sufficiency: 0.0
```

## Fingerprint  *(the standing scorecard — one markdown row per module)*
**Coverage** — <N>/<M> spec-worthy modules covered.

**Drift**  *(high+med findings verbatim from `findings.json` — click-to-verify, not "trust me")*

| Module | Sev | Summary | code_ref | doc_ref | fix |
|---|---|---|---|---|---|
| <module> | high | <one line> | `<ref>` | `<ref>` | <suggestion> |

**Sufficiency**  *(unicode bars — a full row = 1.0)*

| Module | Spec completeness | Score | Weakest gap |
|---|---|---|---|
| <module> | `██████████████░░░░░░` | 0.00 | <one line> |

*(The full run — markdown reports — sits beside this file.)*

## Gaps / sufficiency misses  *(per-module, from `sufficiency.json` — the author's backlog)*
- **`<module>`** — **[major]** <the one-sentence missing behavior>
- **`<module>`** — **[minor]** <…>

## How this stays living
Regenerate (never hand-edit the numbers):
```bash
python -m spec_eval coverage    <repo> --config pairs.yml                                   # free
python -m spec_eval audit       <repo> --config pairs.yml --model <p:m> --env .env          # drift
python -m spec_eval sufficiency <repo> --config pairs.yml --model <p:m> --env .env          # sufficiency
```

## Changelog
| Date | SHA | Change |
|---|---|---|
| <YYYY-MM-DD> | <sha> | <what moved> |
