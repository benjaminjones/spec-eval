# Spec sufficiency — `spec-eval`
detector: `claude-code` · 10/10 pairs scored · 10 model call(s)

**Average sufficiency 0.88** — how completely does the spec capture the code's behavior? (1.0 = no gaps found; gaps = behavior in the code but not the spec. An indicator, not a guarantee.)

## Sufficiency fingerprint  *(at a glance — worst first)*

| Pair | Spec completeness | Score |
|---|---|---|
| `authoring` | `████████████████░░░░` | 0.80 |
| `audit` | `█████████████████░░░` | 0.83 |
| `syscontext` | `█████████████████░░░` | 0.85 |
| `cli` | `█████████████████░░░` | 0.86 |
| `report` | `██████████████████░░` | 0.88 |
| `coverage` | `██████████████████░░` | 0.90 |
| `providers` | `██████████████████░░` | 0.90 |
| `rubric` | `██████████████████░░` | 0.90 |
| `sufficiency` | `██████████████████░░` | 0.90 |
| `runlog` | `███████████████████░` | 0.93 |

## Per-module gaps  *(worst first)*

### authoring — sufficiency 0.80
- **[major]** The built-in authored-spec skeleton the map rubric enforces — §1 Purpose with a bold '**In one line:** <=20-word' headline and a directly-checkable governing constraint, §2 Definitions table, §3 Behavior (explanation-only, no per-method walkthrough), §4 Contracts opening with the italic reference cue, semantic (not language) shapes, an Invariants table (INV-* asserted only when the code enforces it) and a Given/When/Then Acceptance-criteria table (AC-*) — is only gestured at, not specified enough to reproduce. · `spec_eval/authoring.py (AUTHORING_STRUCTURE)`
- **[minor]** Default numeric constants are named but never valued: REDUCE_CAP defaults to 48000 chars, _MAX_LEVELS to 4 recursion passes, and AUTHOR_MAX_TOKENS to 5000 output tokens (the single budget for all four call sites). · `spec_eval/authoring.py (module constants)`
- **[minor]** The folder synthesis rubric's produced section structure is undescribed: ## 1 Purpose, ## 2 Modules (module→one-line-responsibility table), ## 3 How it fits together (prose data/control flow), ## 4 Shared contract (cross-module invariants only). · `spec_eval/authoring.py (FOLDER_SPEC_RUBRIC)`
- **[minor]** When the evidence block ends with a 'Not scanned:' line, the overview must reproduce that line verbatim beneath the System-context table so a language-coverage gap stays visible. · `spec_eval/authoring.py (OVERVIEW_RUBRIC)`
- **[minor]** The System-context section must render the full table even for a single evidence row (an evidence-backed row and an 'unknown from this repo' cell count as real, not N/A) — an explicit override of the general right-sizing rule. · `spec_eval/authoring.py (OVERVIEW_RUBRIC)`
- **[minor]** An unrecognized layout value raises ValueError('unknown layout ... use per-file | per-dir | per-pair'). · `spec_eval/authoring.py (_layout_targets)`
- **[minor]** per-pair edge behavior: a pair with no docs entry is skipped, its first docs entry is the target, code globs are matched with recursive=True keeping only files (relpath'd, deduped, sorted), and a pair whose globs match nothing produces no target. · `spec_eval/authoring.py (_layout_targets)`
- **[minor]** Force-fit sizing detail: past the recursion bound each remaining intent is sliced to max(200, cap//len(items) - 40) chars, and _pack emits blocks as '### <label>\n<intent>' with a lone oversized block sliced to cap and marked '...[truncated]'. · `spec_eval/authoring.py (_synthesize / _pack)`

### audit — sufficiency 0.83
- **[minor]** The output-token budget passed to the provider (REVIEW_MAX_TOKENS = 3000) is never given a value; a rebuild would know a token cap exists (via the 'reply hit the token cap' note) but must guess 3000. · `audit.py (REVIEW_MAX_TOKENS / audit_pair)`
- **[minor]** The provider interface contract is unspecified: audit calls providers.gen(model, DRIFT_RUBRIC, user, max_tokens) returning raw text, and reads the module-global providers.LAST['truncated'] after each call to decide the reply-cut-off note. · `audit.py (truncation_notes / audit_pair)`
- **[minor]** The exact user-message template is not given — label header '# Drift review: {label}', code wrapped in triple-backtick fences under '## Code', docs left unfenced under '## Docs / spec'. · `audit.py (audit_pair)`
- **[minor]** Field-level normalization defaults in the primary parse are unstated: code_ref/doc_ref default to None, suggestion defaults to "", and severity/summary are coerced via str(). · `audit.py (parse_findings)`
- **[minor]** Truncation-note number formatting uses comma-grouped digits (e.g. '~64,000 chars'), not the bare integer. · `audit.py (truncation_notes)`
- **[minor]** caps_from coerces each override via int() and falls back per-key to the default when caps or an individual key is absent/null. · `audit.py (caps_from)`

### syscontext — sufficiency 0.85
- **[minor]** The exact numeric caps are not given: EVIDENCE_CAP=8 sites per entry per directory, LINE_CAP=160 chars per evidence match, FILE_CAP=2,000,000 bytes read per file. · `syscontext.py (module constants)`
- **[minor]** The SDK_IMPORTS table is only partially enumerated; several recognized systems are unspecified (Celery broker, Yahoo Finance/yfinance, ccxt crypto exchanges, Alpaca, Interactive Brokers, LDAP directory, Oracle via cx_Oracle/oracledb, Elasticsearch/OpenSearch, Cassandra, Memcached, SMTP/smtplib). · `syscontext.py (SDK_IMPORTS)`
- **[minor]** The full SCHEME_SYSTEMS scheme→system map is not enumerated; nats→NATS, mqtt→MQTT broker, ftp/sftp→FTP/SFTP server, gs→Google Cloud Storage, smtp→SMTP are missing. · `syscontext.py (SCHEME_SYSTEMS)`
- **[minor]** AWS SDK plumbing namespaces (runtime, extensions, util, core, config, auth) are explicitly skipped and never reported as services. · `syscontext.py (_scan_file)`
- **[minor]** The display-name fallback formatting rules are unspecified: an unknown AWS service id ≤4 chars is upper-cased else title-cased, and hyphens/underscores become spaces before title-casing (also applied to Google Cloud service names). · `syscontext.py (_scan_file)`
- **[minor]** Which file extensions receive C-style (/*…*/, //) vs hash-style (#) comment stripping (C_FAMILY vs HASH_FAMILY), and that extensions in neither family get no comment stripping at all, is not specified. · `syscontext.py (C_FAMILY / HASH_FAMILY)`
- **[minor]** The exact OTHER_SOURCE_EXT set that determines which unsupported-language files are counted into `unscanned` (vs ignored entirely) is not enumerated. · `syscontext.py (OTHER_SOURCE_EXT)`
- **[minor]** The full SKIP_HOST_SUFFIXES documentation-domain list is only partially enumerated (missing pypi.org, npmjs.com, shields.io, readthedocs.io, stackoverflow.com, opensource.org, creativecommons.org, schema.org, json-schema.org). · `syscontext.py (SKIP_HOST_SUFFIXES)`

### cli — sufficiency 0.86
- **[minor]** The per-line terminal list of uncovered files (and orphans) is capped at exactly 25 entries (UNCOVERED_LIST_CAP); the spec says 'capped' but never states the numeric threshold. · `spec_eval/cli.py (UNCOVERED_LIST_CAP)`
- **[minor]** Orphaned specs are sliced to the cap but printed with NO '… and N more' overflow note (unlike uncovered files), so overflow orphans are silently dropped from the terminal output. · `spec_eval/cli.py (main, coverage branch)`
- **[minor]** When a single-file scope has no co-located <stem>.md under a per-dir layout, the doc name is derived via coverage_mod.dir_spec_path using the authoring 'dir_spec_name' default of '<dir>' — the folder-spec filename derivation and its default are not specified. · `spec_eval/cli.py (_file_scope)`
- **[minor]** generate defaults its config to {"pairs": []} (not {}) when no --config is given, and _file_scope for generate additionally forces layout to 'per-pair' — the exact config default and layout override value are unstated. · `spec_eval/cli.py (main, generate branch)`
- **[minor]** The context (non-check) per-system console line uses only the first evidence entry (rec['evidence'][0]) in the exact format '{system} ({kind}, {direction}; {file}:{line})' — the evidence-shape fields (kind, direction, file, line) are not enumerated in the spec. · `spec_eval/cli.py (main, context branch)`

### report — sufficiency 0.88
- **[minor]** The drift report lists a bullet for EVERY finding regardless of severity (not just high/medium), so a pair headed `✓ clean` (drift load 0) can still render low-severity finding bullets — the spec ties bullets to "per finding" but never makes the clean-header-yet-nonempty interaction explicit. · `report.py (write_markdown)`
- **[minor]** `_bar` computes filled cells as `int(round(v*width))` (nearest-integer rounding); the spec specifies clamping and the 1.0→20 boundary but not the rounding rule, so a rebuild could use floor and produce different bars for non-boundary values. · `report.py (_bar)`
- **[minor]** The drift report's per-pair sections are emitted in input order (the loop iterates `results` directly, not sorted by drift load); the spec specifies ordering for the fingerprints and sufficiency detail but is silent on drift-body order. · `report.py (write_markdown)`
- **[minor]** The sufficiency detail sort key `(sufficiency is None, sufficiency or 0)` also sinks skipped pairs (whose sufficiency is absent/None) into the last bucket alongside unscored pairs; the spec doesn't state where skipped pairs land in the sufficiency detail ordering. · `report.py (write_sufficiency_markdown)`
- **[minor]** The sufficiency fingerprint's concrete table layout — three columns `Pair | Spec completeness | Score`, a `_bar` in the middle column, and score to 2 decimals — is not fully pinned down by the spec's loose Fingerprint definition. · `report.py (sufficiency_fingerprint)`

### coverage — sufficiency 0.90
- **[minor]** The full PRUNE_DIRS membership is not enumerated (spec gives only a representative subset with '…'), so a rebuild would guess which directory names like `env`, `target`, `.mypy_cache`, `.pytest_cache`, `.ruff_cache`, `.tox`, `htmlcov`, `.eggs`, `thirdparty`, `jspm_packages` are pruned. · `coverage.py (PRUNE_DIRS)`
- **[minor]** The conventional-doc-stem match is case-insensitive (`stem.lower() in CONVENTIONAL_DOC_STEMS`) and the full stem set (changes, contributing, notice, testing, faq, getting-started, security, code_of_conduct, skill, todo, authors, maintainers, install, upgrading, …) is not enumerated in the spec. · `coverage.py (coverage / CONVENTIONAL_DOC_STEMS)`
- **[minor]** dir_spec_path's exact rules — a repo-root code file (empty dirname) uses repo_name as the folder name, and a literal (non-`<dir>`) dir_spec_name produces `<dir>/<literal>.md` — are only partially implied. · `coverage.py (dir_spec_path)`
- **[minor]** format_report renders the headline percentage with `:.0f` (integer rounding), not the one-decimal float that `pct` stores, so the displayed number can differ from the contract value. · `coverage.py (format_report)`
- **[minor]** infer_pairs iterates files in sorted order within the walk before the final label sort, and its pair label is the basename stem — the precise emitted pair shape/label derivation is only loosely described. · `coverage.py (infer_pairs)`

### providers — sufficiency 0.90
- **[minor]** The exact default model value `anthropic:claude-opus-4-8` is not given; the spec only says DEFAULT_MODEL holds a default provider:model string and its examples even use a different name (`claude-opus-4`), so a rebuild would guess the wrong constant. · `providers.py (DEFAULT_MODEL)`
- **[minor]** The claude-code bridge subprocess uses a fixed 600-second timeout; the spec never states any timeout for the CLI call. · `providers.py (_gen_claude_code)`
- **[minor]** OpenAI truncation detection guards against an empty `choices` list (defaults truncated to False when no choices), an edge case not captured in the spec. · `providers.py (gen)`
- **[minor]** RuntimeError messages from the bridge truncate the CLI's stderr/stdout to 400 characters, an error-shape detail the spec omits. · `providers.py (_gen_claude_code)`
- **[minor]** Google's finish-reason check normalizes an enum via `fr.name` or `str(fr)` before matching 'MAX_TOKENS'; the spec states the marker but not this reason-object handling. · `providers.py (gen)`

### rubric — sufficiency 0.90
- **[minor]** The docstring states this module's own spec (rubric.md) is itself checked by "spec-eval's self-audit"; the spec describes the sync test but not that the module↔spec relationship is guarded by a self-audit mechanism. · `rubric.py (module docstring)`
- **[minor]** The rubric opens by casting the reviewer as "a careful technical reviewer auditing a codebase" shown "ONE pair" and told to "Find real mismatches" — the exact persona/instruction framing that shapes the emitted string is only partially reflected. · `rubric.py (DRIFT_RUBRIC)`

### sufficiency — sufficiency 0.90
- **[minor]** When a pair omits the "code" or "docs" key entirely, the globs default to an empty list (via pair.get(key, [])), which yields nc/nd of 0 and a skip rather than an error — the spec never states the missing-key default. · `sufficiency.py (sufficiency_pair)`
- **[minor]** The exact user-prompt template is unspecified: the code fences the concatenated code in a triple-backtick block but leaves the spec/doc text unfenced, under literal headings `# Sufficiency review: {label}`, `## Code`, `## Spec`. · `sufficiency.py (sufficiency_pair)`
- **[minor]** At repo level, caps are derived once via audit.caps_from(config) and threaded into every pair call; the spec names caps.code/caps.docs defaults but not the caps_from extraction mechanism. · `sufficiency.py (sufficiency_repo)`
- **[minor]** A non-numeric `sufficiency` value that fails float() coercion falls through the try/except into the parse-failure fallback (None score, "?" gap) rather than defaulting to 0.0. · `sufficiency.py (sufficiency_pair)`

### runlog — sufficiency 0.93
- **[minor]** The exact JSON serialization is unspecified: records are written with `json.dumps` defaults (ensure_ascii=True, so non-ASCII in labels/stats is \uXXXX-escaped; default separators), which fixes the on-disk byte form. · `runlog.py (append_run)`
- **[minor]** git_sha never checks the subprocess return code; it derives the result purely from `stdout.strip() or None`, so a non-zero git exit that still emitted stray stdout would be recorded as the SHA rather than null. · `runlog.py (git_sha)`
