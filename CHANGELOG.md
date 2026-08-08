# Changelog

Notable changes per release. Dates are the PyPI upload date.

The version lives in `spec_eval/__init__.py` and nowhere else; `pyproject.toml` reads it, and
`.github/workflows/release.yml` refuses a tag that disagrees with it.

## 0.3.0

Two new commands, one new check, and three failures that used to be hard to read.

### Added
- **`audit --verify`** — an opt-in second pass that re-reads the document a finding was raised on and
  withdraws the finding only on one of four named grounds, each settled by quoting a line that exists. A
  `not-asserted` withdrawal is additionally checked **without a model**: the quoted line must be present in
  the document. A withdrawn finding is kept and shown struck through with its ground, never deleted, because
  a withdrawal is a claim a reader may disagree with. Off by default; costs one extra call per pair that
  produced findings.
- **`context`** — an inventory of the external systems a repo actually talks to, with `file:line` evidence,
  fed into an overview's System context section. **`context --check`** diffs a stored baseline against a
  fresh scan by key set, and exits non-zero only on real drift.
- **`diagram`** — scanner-derived Mermaid architecture diagrams: an invocation sequence and a data-flow
  pipeline. Prints to stdout by default; `--write` replaces an existing Architecture section and
  `--add-section` is the explicit opt-in for a first-time add. Neither ever creates a document.
- Findings now carry the **`evidence`** the rubric asks for — the quoted code and doc snippets — through to
  the report, so a finding can be checked rather than taken on trust.

### Fixed
- A failing verification pass no longer discards a completed audit. The audit is written the moment it
  finishes; a failure prints the reason and keeps the unverified findings.
- The `claude -p` bridge reports the reason it failed rather than the first 400 characters of its telemetry,
  which used to hide the actual error.
- An older interpreter fails with its own version and path rather than with an `argparse` symbol. `pip`
  enforces `requires-python`, but running from a source checkout never consults it.

### Changed
- The health receipt records **one commit per measuring command** (`coverage_sha`, `audit_sha`,
  `sufficiency_sha`). The three checks are separate runs and the tree can move between them, so a single
  pinned commit could attribute a measurement to a commit it was not taken at.

## 0.2.2 — 2026-07-22
Prompt-chat release: self-contained option lists, standing prompts, and the health receipt moved into
`spec-reports/`.

## 0.2.1 — 2026-07-17
Packaging follow-up to the first public release.

## 0.2.0 — 2026-07-17
First public release: `coverage`, `audit`, `sufficiency`, `generate`.
