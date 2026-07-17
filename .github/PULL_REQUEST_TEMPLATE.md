<!--
Guidelines (they apply to this description, not just the code):
- Describe the change in spec-eval's own terms — what the code/docs do before and after.
  No references to other projects, private repos, or the session/chat that produced the change.
- Write for a cold reader: someone with no context beyond this repo should follow every sentence
  (see CONTRIBUTING → "Writing docs").
- One concern per PR — split unrelated changes.
-->

## Problem

<!-- What is wrong or missing. Link the issue if one exists: Closes #NN -->

## Change

<!-- What this PR does, and why this shape — the smallest fix that holds. -->

## Reproduce / verify

<!-- Before: the command or prompt that shows the problem. After: how to confirm the fix.
     Prefer runnable commands; "not reproducible, docs-only" is a valid answer. -->

## Validation

- [ ] `uv run --extra dev pytest` passes
- [ ] `uv run --extra dev ruff check .` is clean
- [ ] Changed `spec_eval/*.py`? Its co-located `<module>.md` is updated in the same commit (the self-audit grades them)
- [ ] Changed docs? Cold-read pass done (CONTRIBUTING → "Writing docs")
