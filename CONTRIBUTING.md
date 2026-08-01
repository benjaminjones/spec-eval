# Contributing

## Keep it DRY — one source of truth per fact

A fact should live in **one** place; everywhere else should link or defer to it. Two kinds of duplication, two
tools:

- **A code-derived value** (a cap number, the default model, a token budget) — put it in a named constant and
  reference the constant. Docs that must quote the literal are pinned by
  [`tests/contract/test_caps_sync.py`](tests/contract/test_caps_sync.py): change the constant and the test tells
  you which docs to update. Add new pinned facts there.
- **A load-bearing phrase** shared between the CLI rubric and a skill — the `KEEP IN SYNC` markers +
  [`tests/contract/test_rubric_sync.py`](tests/contract/test_rubric_sync.py) hold the two copies together.

**Changing a phrase or value that travels?** (`"an indicator, not a guarantee"`, a cap number, a model id, a
rubric rule) — `grep` it across the repo first. If it's a value, prefer making it a constant over adding a
second copy.

**What is *not* a DRY violation:** a nav link, a short teaser that points to a fuller section, an example reused
to teach, a value stated once and linked elsewhere. That's progressive disclosure — good. Don't over-dedup
prose; a reader landing on any one page should get what they need.

## Writing docs

Docs describe **what exists and how it works** — not the conversation that produced them. Two habits:

- **Cold-read pass.** Before committing docs written during a working session, reread the diff as if you never saw
  the discussion. Cut any sentence catching the reader up on something only the chat covered — defensive negation
  ("this is *not* a skill"), a contrast that answers a chat question ("*unlike* sufficiency…"), meta-commentary on
  how it reads, a TL;DR that restates the body, or a stylistic flourish.
- **Describe what a thing IS, never what it isn't** — state it on its own terms. Generated specs enforce this too
  (`AUTHORING_DISCIPLINE`, pinned by [`test_rubric_sync.py`](tests/contract/test_rubric_sync.py)); narrative docs
  like the README have no linter for these qualities, so the cold-read pass is their only guard.
- **Pragmatic wording for trade-offs.** Name a drawback by its mechanism — "goes stale", "changes faster than
  docs can follow", "already maintained elsewhere" — not by a doom word ("rot"). Realistic beats dramatic.

The same rules apply to **commit messages and PR titles/descriptions**: state the change and its logic,
agnostic of the working session that produced it. General use cases are fine; conversation narrative and
references to specific private projects are not.

The mechanical half of that rule runs in CI. [`artifact-hygiene.yml`](.github/workflows/artifact-hygiene.yml)
scans the PR title, the PR body, every commit message on the branch, and the diff's **added** lines, and fails on
a path from a personal machine, a phrase narrating the session, or a name listed in the `ARTIFACT_DENYLIST`
repository secret. The names live in the secret rather than the repo, because a denylist naming the private
projects would publish exactly what it exists to hide — so a fork pull request runs the generic rules only, and
says so. Judgement calls (defensive negation, a chat-shaped contrast, a flourish) are still the cold-read pass's
job; the check catches the categories a reader can name, not the ones they have to feel.

## Tests

`pip install -e ".[dev]"` then `pytest` — see [TESTING.md](TESTING.md). New behavior gets a test; changed
behavior updates its co-located spec (`spec_eval/<module>.md`) in the same commit — the self-audit grades them.

## Releasing (uvx caveat)

`uvx --from <local-checkout> spec-eval` keys its cached build on the **version string, not file contents** — so
after code changes without a version bump, uvx silently serves the *stale* build (`--reinstall`/`--refresh` don't
help). **Bump `__version__` in `spec_eval/__init__.py` every release** — that's the real cache-buster. For a
one-off fresh run from a working checkout, use `uvx --no-cache --from <checkout> spec-eval`.
