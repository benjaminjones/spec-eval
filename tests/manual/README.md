# Skill evals

*The one eval here is manual (model-in-the-loop) and not run in CI; its deterministic CI counterparts live in
`tests/contract/`.*

Two checks that the two skills *fire* and *produce* what the rubric promises — the gaps `test_rubric_sync`
(which pins skill BODY text) can't cover.

| Eval | What it guards | Where | How it runs |
|------|----------------|-------|-------------|
| **Output assertions** | An authored spec OBEYS the readability rules — one-liner present, no signature/type headings, no metric inside a spec | `tests/contract/test_authoring_output.py` | CI unit test (deterministic, judge-free) — also grades the real example specs |
| **Trigger routing** | The frontmatter `description:`s ACTIVATE correctly and don't MIS-ROUTE between the two overlapping siblings ("check the spec" vs "write the spec") | `tests/manual/run_trigger_eval.py` + `trigger-cases.jsonl` | Manual (model-in-the-loop) — needs the `claude` CLI or an API key |

## Trigger routing — run it

```bash
python tests/manual/run_trigger_eval.py                # 1 pass via the claude-code bridge (no API key)
python tests/manual/run_trigger_eval.py --reps 3       # 3 passes → majority vote, for a stable rate
python tests/manual/run_trigger_eval.py --model anthropic:claude-opus-4-8   # or an API-key model
```

The runner reads the two descriptions **verbatim** from the `SKILL.md` files, so it can't drift from what ships.
It's not in CI because it's model-in-the-loop and costs a few calls per rep; run it after editing either
`description:`. Last manual run: **16/16, 0 sibling mis-routes** (claude-code bridge).

`trigger-cases.jsonl` is the fixture set — one JSON object per line, `{"prompt": ..., "expect": "spec-check" |
"spec-authoring" | "none"}`. `none` = plain code work (refactor / rename / bug-fix / tests) that must NOT pull in
a spec skill. Add a case whenever a real request routes wrong.
