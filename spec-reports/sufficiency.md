# Spec sufficiency — `spec-eval`
detector: `claude-code` · 10/10 pairs scored · 10 model call(s)

**Average sufficiency 0.86** — how completely does the spec capture the code's behavior? (1.0 = no gaps found; gaps = behavior in the code but not the spec. An indicator, not a guarantee.)

## Sufficiency fingerprint  *(at a glance — worst first)*

| Pair | Spec completeness | Score |
|---|---|---|
| `authoring` | `████████████████░░░░` | 0.80 |
| `audit` | `████████████████░░░░` | 0.82 |
| `cli` | `█████████████████░░░` | 0.85 |
| `coverage` | `█████████████████░░░` | 0.85 |
| `report` | `█████████████████░░░` | 0.85 |
| `providers` | `██████████████████░░` | 0.88 |
| `syscontext` | `██████████████████░░` | 0.88 |
| `rubric` | `██████████████████░░` | 0.90 |
| `runlog` | `██████████████████░░` | 0.90 |
| `sufficiency` | `██████████████████░░` | 0.90 |

## Per-module gaps  *(worst first)*

### authoring — sufficiency 0.80
- **[major]** When a system-context evidence block is present, the repo OVERVIEW.md gets a syscontext fingerprint stamp appended (via stamp_comment) so a later `--check` can detect staleness — this staleness-stamp feature is entirely absent from the spec. · `spec_eval/authoring.py (generate_repo._repo_overview)`
- **[minor]** An unrecognized layout value raises ValueError('unknown layout ...') rather than being ignored or defaulted. · `spec_eval/authoring.py (_layout_targets)`
- **[minor]** FOLDER_SPEC_RUBRIC's authored-document section structure (## 1 Purpose, ## 2 Modules table, ## 3 How it fits together, ## 4 Shared contract) is not specified. · `spec_eval/authoring.py (FOLDER_SPEC_RUBRIC)`
- **[minor]** If the evidence block ends with a 'Not scanned:' language-gap line, the overview must reproduce that line verbatim beneath the System-context table; also the OVERVIEW section headings (## Map, ## How it fits together, ## Shared contract) are unspecified. · `spec_eval/authoring.py (OVERVIEW_RUBRIC)`
- **[minor]** per-pair targets use only the pair's first `docs` entry, silently skip pairs with no docs, and deduplicate the code files matched across globs. · `spec_eval/authoring.py (_layout_targets)`
- **[minor]** The default numeric constants REDUCE_CAP=48000, _MAX_LEVELS=4, and AUTHOR_MAX_TOKENS=5000 are named but their concrete values (thresholds/budgets) are not stated. · `spec_eval/authoring.py`

### audit — sufficiency 0.82
- **[minor]** The model call is bounded to a fixed output-token budget of 3000 (REVIEW_MAX_TOKENS) passed as max_tokens to the provider; the spec references a 'token cap' but never states the value or that audit sets it. · `audit.py (audit_pair / REVIEW_MAX_TOKENS)`
- **[minor]** Files are read with errors="ignore" so encoding-bad bytes are dropped and the file is still included; only files that raise OSError are silently skipped — the spec's 'unreadable files skipped silently' omits this encoding-tolerance behavior. · `audit.py (_read_globs)`
- **[minor]** Reply-truncation detection depends on a stateful provider contract providers.LAST["truncated"] read immediately after providers.gen(model, system, user, max_tokens); the spec doesn't specify this provider interface or the read-after-call ordering. · `audit.py (truncation_notes / audit_pair)`
- **[minor]** caps_from coerces config overrides with int(), and truncation notes render the cap with comma-thousands formatting (e.g. 'code input capped at ~64,000 chars'); the exact note wording/format is unspecified. · `audit.py (caps_from / truncation_notes)`
- **[minor]** In parse_findings, missing code_ref/doc_ref default to None while summary/suggestion default to "" (empty string), and all fields are stringified; the per-field default/normalization behavior is not stated. · `audit.py (parse_findings)`
- **[minor]** Shared helpers (REVIEW_MAX_TOKENS, truncation_notes, and first_json_object's generic *keys) are also consumed by a separate sufficiency check; the audit-only spec omits this cross-module coupling. · `audit.py (first_json_object / truncation_notes)`
- **[minor]** The user prompt uses a specific template where the code block is fenced in triple backticks but the doc block is left unfenced under '## Docs / spec'; exact prompt layout is unspecified. · `audit.py (audit_pair)`
- **[minor]** The actual content of DRIFT_RUBRIC (the system prompt that governs what findings the model produces) is imported from .rubric and not captured, so review behavior cannot be reproduced from the spec alone. · `rubric.py (DRIFT_RUBRIC)`

### cli — sufficiency 0.85
- **[minor]** The terminal-print cap for uncovered/orphan lists is a fixed value of 25 (UNCOVERED_LIST_CAP); the spec says the list is 'capped' but never states the numeric threshold. · `cli.py (UNCOVERED_LIST_CAP)`
- **[minor]** The orphaned-spec list is capped at 25 but, unlike the uncovered list, prints no '… and N more' overflow note when it exceeds the cap — an asymmetry a rebuild would not reproduce. · `cli.py (main, coverage branch)`
- **[minor]** The synthesized single-file pair has a specific shape — label = file stem, code=[basename], docs=[<stem>.md] — and the per-dir fallback resolves the folder spec via coverage_mod.dir_spec_path using dir_spec_name default '<dir>'. · `cli.py (_file_scope)`
- **[minor]** The context --check receipt is stamped with the repo's git sha via runlog.git_sha(args.repo), and OVERVIEW.md is read with errors='ignore'; these provenance/robustness details are not specified. · `cli.py (main, context branch)`
- **[minor]** Printed numeric formats are unspecified: coverage pct as integer (.0f), sufficiency avg as .2f, token counts thousands-separated (:,), and generate status left-padded to width 10. · `cli.py (main)`

### coverage — sufficiency 0.85
- **[minor]** The full CONVENTIONAL_DOC_STEMS set (~24 stems: testing, faq, getting-started, security, code_of_conduct, todo, authors, maintainers, install, upgrading, notice, changes, contributing, overview, spec-health, etc.) is only partially given with '…', so a rebuild would flag/skip a different set of orphan specs. · `coverage.py (CONVENTIONAL_DOC_STEMS)`
- **[minor]** The exact PRUNE_DIRS membership is only exemplified ('…') — a rebuild would miss specific entries like venv, env, .mypy_cache, .pytest_cache, .ruff_cache, .tox, htmlcov, .eggs, thirdparty, jspm_packages, .idea, .vscode. · `coverage.py (PRUNE_DIRS)`
- **[minor]** format_report renders the headline percent with integer formatting ({pct:.0f}%) despite pct being stored to 1 decimal, and prefixes Uncovered with '⚠'; the display-vs-stored precision and exact section markers aren't specified. · `coverage.py (format_report)`
- **[minor]** dir_spec_path edge cases: a repo-root code file (no directory) falls back to repo_name for its folder-spec name, and a literal dir_spec_name yields <dir>/<literal>.md — not spelled out in the spec. · `coverage.py (dir_spec_path)`
- **[minor]** Orphan detection only skips a doc when classify_exclude returns exactly the 'user' tier (not other exclusion tiers), and the .md candidate set (mds) is gathered only from non-pruned directories during the same walk. · `coverage.py (coverage)`

### report — sufficiency 0.85
- **[minor]** The bar's fractional-to-cell mapping (`filled = int(round(v * width))`, i.e. round-half rounding of v*20) is unspecified, so bars for non-boundary values (e.g. 0.4 → 8 filled cells) can't be reproduced exactly. · `report.py (_bar)`
- **[minor]** Exact fingerprint table titles/column headers are not given — sufficiency uses '## Sufficiency fingerprint *(at a glance — worst first)*' with columns 'Pair | Spec completeness | Score', drift uses '### Drift fingerprint' with 'Pair | High+med findings', and pair labels are wrapped in backticks. · `report.py (sufficiency_fingerprint / drift_fingerprint)`
- **[minor]** Where skipped pairs land in the sufficiency per-module ordering is unspecified; the sort key `(sufficiency is None, sufficiency or 0)` groups skipped (None) pairs with the unscored group at the end. · `report.py (write_sufficiency_markdown)`
- **[minor]** The literal '## Per-module gaps *(worst first)*' detail section heading and the markdown heading levels (## for drift sections vs ### for sufficiency sections) are not stated. · `report.py (write_sufficiency_markdown)`
- **[minor]** The sufficiency fingerprint is inserted between the head and the detail via `"\n".join(head) + summary + "\n" + ...` (and the drift fingerprint is concatenated with no leading blank join), so exact blank-line/spacing composition of the documents isn't fully specified. · `report.py (write_sufficiency_markdown)`

### providers — sufficiency 0.88
- **[minor]** The spec never states DEFAULT_MODEL's actual value ("anthropic:claude-opus-4-8"), which is the single default the CLI's --model reads, so a rebuild would guess the constant. · `providers.py (DEFAULT_MODEL)`
- **[minor]** The claude-code bridge runs the CLI subprocess with a 600-second timeout, so a hung CLI aborts the call; this threshold is absent from the spec. · `providers.py (_gen_claude_code)`
- **[minor]** The bridge's RuntimeError messages have a specific shape — non-zero exit includes the exit code and prefers stderr over stdout, and error text is truncated to 400 chars. · `providers.py (_gen_claude_code)`
- **[minor]** Anthropic reply assembly concatenates only content blocks whose type is exactly "text" (skipping non-text blocks), rather than all blocks. · `providers.py (gen)`

### syscontext — sufficiency 0.88
- **[minor]** The exact default constant values are unspecified — EVIDENCE_CAP=8 sites per entry per directory, LINE_CAP=160 chars, FILE_CAP=2,000,000 bytes — so a rebuild would have to guess the thresholds. · `spec_eval/syscontext.py (module constants)`
- **[minor]** AWS SDK plumbing namespaces (runtime, extensions, util, core, config, auth) matched by the ecosystem regexes are filtered out and never produce a service entry. · `spec_eval/syscontext.py (_scan_file)`
- **[minor]** Unresolved AWS service-id display naming uses a length rule: ids of ≤4 chars are upper-cased, longer ids are dash-split and title-cased — the spec only says 'title-cased'. · `spec_eval/syscontext.py (_scan_file)`
- **[minor]** AWS resolution also fires on `.resource("...")` calls (not just `.client(...)`), and a known service id resolves even without a boto3 import while an unknown id only resolves when `import boto3` is present in the file. · `spec_eval/syscontext.py (_scan_file / _AWS_CLIENT)`
- **[minor]** Google Gemini API is detected via `from google import genai` and the `google.genai` import key — Gemini detection is absent from the spec (only Google Cloud and Azure are named). · `spec_eval/syscontext.py (_GOOGLE_GENAI_RE / SDK_IMPORTS)`
- **[minor]** The full documentation-domain skip list (schema.org, json-schema.org, pypi.org, npmjs.com, opensource.org, creativecommons.org, shields.io, readthedocs.io, stackoverflow.com) is broader than the spec's examples. · `spec_eval/syscontext.py (SKIP_HOST_SUFFIXES)`
- **[minor]** The unscanned language-gap note has a fixed exact wording ('Not scanned: … source file(s) — language(s) outside the scan's support … Add the extension(s) to `code_ext` …') that the spec paraphrases but does not pin down. · `spec_eval/syscontext.py (unscanned_note)`

### rubric — sufficiency 0.90
- **[minor]** The docstring notes that this module's own spec `rubric.md` is itself guarded by 'spec-eval's self-audit' — the spec omits that it is an audited artifact of the same drift system. · `rubric.py (module docstring)`
- **[minor]** The sync test's exact mechanism — that it asserts the load-bearing phrases (severity tiers + do-not-flag list) *match* between rubric.py and SKILL.md — is only partially conveyed; the spec says phrases are 'pinned' but doesn't state the assertion is bidirectional phrase-equality guarding against silent divergence in either copy. · `rubric.py (module docstring, KEEP IN SYNC)`

### runlog — sufficiency 0.90
- **[minor]** git_sha uses stdout.strip() or None without checking the subprocess return code, so a nonzero git exit that still prints to stdout would be recorded rather than yielding null; the spec asserts errors always produce null. · `runlog.py (git_sha)`
- **[minor]** Serialization details are unspecified: json.dumps defaults (ensure_ascii=True, default separators) and the file opened in text mode with default encoding determine the exact on-disk line format. · `runlog.py (append_run)`

### sufficiency — sufficiency 0.90
- **[minor]** The exact skip explanation string format `"no files matched (code={nc}, docs={nd})"` (embedding the two match counts) is not specified — the spec only says a 'skipped explanation string' is returned. · `sufficiency.py (sufficiency_pair)`
- **[minor]** `sufficiency_pair` accepts `code_cap`/`doc_cap` keyword args that default to `None` and are resolved to `audit.CODE_CAP`/`audit.DOC_CAP` only when `None`, letting a caller override the caps per call — this parameter-level None→default resolution is not captured. · `sufficiency.py (sufficiency_pair)`
- **[minor]** The parse-failure fallback also fires when a JSON object WAS found but gap normalization or the `float(...)` coercion raises (e.g. a non-numeric `sufficiency` value), not only when no JSON span is found — INV-4 frames it solely as 'no parseable JSON object'. · `sufficiency.py (sufficiency_pair)`
- **[minor]** An empty-string `code_ref` is dropped too (the guard `if ref and str(ref).lower() != "null"` treats falsy refs as absent), beyond the `null`/`"null"`/missing cases the spec enumerates. · `sufficiency.py (sufficiency_pair)`
