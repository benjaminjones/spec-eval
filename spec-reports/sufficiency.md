# Spec sufficiency — `spec-eval`
detector: `claude-code` · 9/9 pairs scored · 9 model call(s)

**Average sufficiency 0.91** — how completely does the spec capture the code's behavior? (1.0 = no gaps found; gaps = behavior in the code but not the spec. An indicator, not a guarantee.)

## Sufficiency fingerprint  *(at a glance — worst first)*

| Pair | Spec completeness | Score |
|---|---|---|
| `authoring` | `█████████████████░░░` | 0.87 |
| `audit` | `██████████████████░░` | 0.88 |
| `cli` | `██████████████████░░` | 0.90 |
| `coverage` | `██████████████████░░` | 0.90 |
| `report` | `██████████████████░░` | 0.90 |
| `sufficiency` | `██████████████████░░` | 0.90 |
| `providers` | `██████████████████░░` | 0.92 |
| `rubric` | `███████████████████░` | 0.95 |
| `runlog` | `███████████████████░` | 0.95 |

## Per-module gaps  *(worst first)*

### authoring — sufficiency 0.87
- **[minor]** The numeric defaults are never given — REDUCE_CAP=48000 chars, _MAX_LEVELS=4 synthesis passes, AUTHOR_MAX_TOKENS=5000 output tokens — so a rebuild would have to guess all three budgets. · `spec_eval/authoring.py (REDUCE_CAP / _MAX_LEVELS / AUTHOR_MAX_TOKENS)`
- **[minor]** An unknown `authoring.layout` value raises a ValueError naming the three valid layouts; the spec never states the error semantics for a bad layout. · `spec_eval/authoring.py (_layout_targets)`
- **[minor]** Several load-bearing per-module rubric rules are absent from the spec: an INV may be asserted only if the code enforces it, acceptance criteria use Given/When/Then IDs with concrete numbers, shapes must be semantic not language types, the one-liner is capped at ~20 words, headings organize by capability never by symbol tree, and output must carry no preamble or title-line meta-note. · `spec_eval/authoring.py (AUTHORING_STRUCTURE)`
- **[minor]** The section structures of the two synthesis rubrics are unspecified — folder spec: Purpose / Modules table / How it fits together / Shared contract (self-contained, reader has only this file); overview: Map / How it fits together / Shared contract. · `spec_eval/authoring.py (FOLDER_SPEC_RUBRIC)`
- **[minor]** Progress events also fire once per sub-group during a multi-pass synthesis ('synthesis pass L: group i/N'), not only per module map call and per target as the spec states. · `spec_eval/authoring.py (_synthesize)`
- **[minor]** The force-fit slice gives each item max(200, cap // n_items - 40) chars — the per-item floor and header allowance behind 'an equal share of the cap' are unstated. · `spec_eval/authoring.py (_synthesize)`
- **[minor]** The rubric text is a synchronized contract — SKILL.md and the shipped templates carry copies whose shared phrases are pinned by a contract test, so editing one copy alone must fail loudly; the spec never mentions this cross-artifact sync obligation. · `spec_eval/authoring.py`

### audit — sufficiency 0.88
- **[minor]** The model-reply output-token budget default (REVIEW_MAX_TOKENS = 3000) is never stated — the spec says a token cap exists but a rebuilder would have to guess the value, and would not know it is a shared constant the sufficiency check also reads to keep both review budgets coupled. · `spec_eval/audit.py (REVIEW_MAX_TOKENS)`
- **[minor]** Files are opened with errors="ignore", so binary or badly-encoded files are included lossily (bad bytes dropped) rather than skipped — the spec only says unreadable files are skipped silently, which a rebuilder could implement as skip-on-decode-error instead. · `spec_eval/audit.py (_read_globs)`
- **[minor]** Reported file counts and the skip decision are based on contributing files (readable, non-empty), not glob matches — a side whose globs match only empty files yields count 0 and the pair is skipped as "no files matched", a distinction the spec's contracts leave ambiguous. · `spec_eval/audit.py (_read_globs)`
- **[minor]** first_json_object and truncation_notes are generic, exported helpers with contracts beyond this module's use (arbitrary key sets; pair-level notes explicitly shared with the sufficiency check) — a rebuild from the spec would inline them and break the cross-module reuse. · `spec_eval/audit.py (first_json_object)`
- **[minor]** The reply-truncation note is derived from provider-global state of the most recent call (providers.LAST["truncated"]), meaning truncation_notes must be invoked immediately after the generation call — an ordering constraint the spec does not convey. · `spec_eval/audit.py (truncation_notes)`

### cli — sufficiency 0.90
- **[minor]** The terminal list cap for uncovered files and orphaned specs is 25 entries (UNCOVERED_LIST_CAP); the spec says only 'capped' so a rebuild would have to guess the threshold. · `spec_eval/cli.py (UNCOVERED_LIST_CAP)`
- **[minor]** Single-file scoping falls back to the per-dir folder spec only when the co-located <stem>.md does not exist on disk; the spec's 'or' phrasing leaves this precedence rule (existing <stem>.md wins even under per-dir layout) ambiguous. · `spec_eval/cli.py (_file_scope)`
- **[minor]** The synthesized pair's label is the code file's stem (which surfaces in report labels and the run log's per_module keys), and the folder-spec name is read from the config key authoring.dir_spec_name with default '<dir>' — neither is specified. · `spec_eval/cli.py (_file_scope)`
- **[minor]** The orphaned-spec list truncates silently with no '… and N more' overflow note, unlike the uncovered list; the spec's 'also capped' implies symmetric treatment. · `spec_eval/cli.py (main)`

### coverage — sufficiency 0.90
- **[minor]** The exact membership of CONVENTIONAL_DOC_STEMS (20 stems including testing, faq, security, todo, authors, maintainers, install, upgrading, contributing, notice, changes, getting-started/getting_started, code_of_conduct) and the fact that the stem match is case-insensitive (stem.lower()) are only exemplified with an ellipsis, so a rebuild would guess which doc names are exempt from orphan flagging. · `spec_eval/coverage.py (CONVENTIONAL_DOC_STEMS)`
- **[minor]** The full PRUNE_DIRS set is elided ('caches, IDE dirs, …') — a rebuild would miss entries like venv, env, .tox, htmlcov, .eggs, .idea, .vscode, thirdparty, jspm_packages, changing which trees are walked. · `spec_eval/coverage.py (PRUNE_DIRS)`
- **[minor]** dir_spec_path's edge rules are unspecified: a repo-root code file's folder spec resolves to <repo_name>.md, and a literal dir_spec_name (e.g. 'README') maps to <dir>/README.md rather than <dir>/<dir>.md, with '<dir>' as the sentinel default. · `spec_eval/coverage.py (dir_spec_path)`
- **[minor]** format_report renders the headline percentage with zero decimals (:.0f) even though the returned dict stores pct rounded to one decimal, and prefixes the report with the repo basename as a title. · `spec_eval/coverage.py (format_report)`

### report — sufficiency 0.90
- **[minor]** The bar fill count uses round-to-nearest (`int(round(v * width))`), so a rebuild could plausibly floor/ceil and render visibly different bars for the same score. · `spec_eval/report.py (_bar)`
- **[minor]** Drift-report per-pair sections render in input order (results iterated as given, skipped inline), whereas the sufficiency report sorts worst-first — the spec never states the drift detail ordering, so a rebuilder might sort it by analogy. · `spec_eval/report.py (write_markdown)`
- **[minor]** In the sufficiency detail sort, skipped pairs (which lack a `sufficiency` value) fall into the same trailing 'None' group as unscored pairs and interleave with them in stable input order; the spec only places unscored pairs last and leaves skipped-pair position unstated. · `spec_eval/report.py (write_sufficiency_markdown)`
- **[minor]** Per-pair sufficiency scores are rendered to exactly two decimal places (`:.2f`) in both the fingerprint table and section headers; the spec pins two decimals only for the headline average via AC-5. · `spec_eval/report.py (write_sufficiency_markdown)`
- **[minor]** The drift fingerprint is an h3 heading (`### Drift fingerprint`) while the sufficiency fingerprint is an h2 with an italic tagline, and fingerprint rows wrap labels/bars in inline-code backticks — heading levels and exact column titles ('Spec completeness', 'High+med findings') are unstated. · `spec_eval/report.py (sufficiency_fingerprint)`

### sufficiency — sufficiency 0.90
- **[minor]** Pair inference is triggered by any falsy `config["pairs"]` (the code uses `or`), so an explicitly present but empty pairs list also falls back to `infer_pairs` — the spec's AC-6 only covers the key being absent. · `spec_eval/sufficiency.py (sufficiency_repo)`
- **[minor]** The fallback record is produced on ANY exception during result normalization (e.g., a non-numeric `sufficiency` value failing float coercion, or `gaps` entries that aren't dicts), not only when no JSON span is found — the spec's 'JSON parsing raises' phrasing would let a rebuilder skip wrapping the normalization loop in try/except. · `spec_eval/sufficiency.py (sufficiency_pair)`
- **[minor]** `code_ref` dropping is a truthiness-plus-case-insensitive check: empty-string refs and any casing of "null" (e.g., "NULL", "Null") are dropped, beyond the spec's stated null/"null"/missing cases. · `spec_eval/sufficiency.py (sufficiency_pair)`
- **[minor]** The skipped record's explanation string has a specific shape embedding both match counts — `no files matched (code=N, docs=N)` — which the spec types only as `skipped: str`. · `spec_eval/sufficiency.py (sufficiency_pair)`
- **[minor]** A pair missing its `code` or `docs` key entirely is tolerated (`pair.get(..., [])` defaults to an empty glob list, yielding a skip) rather than raising KeyError. · `spec_eval/sufficiency.py (sufficiency_pair)`

### providers — sufficiency 0.92
- **[minor]** The concrete value of DEFAULT_MODEL ("anthropic:claude-opus-4-8") is not stated — the spec describes the constant's role but a rebuild would have to guess which model string is the default. · `spec_eval/providers.py (DEFAULT_MODEL)`
- **[minor]** The claude-code bridge runs the CLI subprocess with a 600-second timeout, which the spec never mentions — a rebuild would either hang indefinitely or guess a bound. · `spec_eval/providers.py (_gen_claude_code)`
- **[minor]** Bridge error messages embed a snippet of the child's stderr (falling back to stdout) truncated to 400 characters — the spec only says the call 'fails loudly', leaving the diagnostic-payload shape unspecified. · `spec_eval/providers.py (_gen_claude_code)`

### rubric — sufficiency 0.95
- **[minor]** The docstring's maintenance note that rubric.md itself is the module's own spec and is guarded by spec-eval's self-audit is not captured in the spec's sync contract (which only covers the SKILL.md mirror and test_rubric_sync.py). · `spec_eval/rubric.py (module docstring)`

### runlog — sufficiency 0.95
- **[minor]** git_sha is a standalone public helper (callable independently of append_run) with its own contract (short SHA string or None); the spec folds SHA resolution into append_run's behavior, so a rebuild would likely inline it rather than expose it. · `spec_eval/runlog.py (git_sha)`
- **[minor]** A git invocation that succeeds but prints empty/whitespace-only output is coerced to null (`out.stdout.strip() or None`) — the spec only maps failures and timeouts to null, leaving the empty-success case to be guessed. · `spec_eval/runlog.py (git_sha)`
- **[minor]** git's stdout/stderr are captured and suppressed (capture_output=True), so failed or missing-repo invocations emit no console noise as an observable side effect. · `spec_eval/runlog.py (git_sha)`
