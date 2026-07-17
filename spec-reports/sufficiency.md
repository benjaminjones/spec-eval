# Spec sufficiency — `spec-eval`
detector: `claude-code` · 9/9 pairs scored · 9 model call(s)

**Average sufficiency 0.86** — how completely does the spec capture the code's behavior? (1.0 = no gaps found; gaps = behavior in the code but not the spec. An indicator, not a guarantee.)

## Sufficiency fingerprint  *(at a glance — worst first)*

| Pair | Spec completeness | Score |
|---|---|---|
| `authoring` | `████████████████░░░░` | 0.78 |
| `cli` | `████████████████░░░░` | 0.82 |
| `coverage` | `█████████████████░░░` | 0.83 |
| `audit` | `█████████████████░░░` | 0.85 |
| `report` | `█████████████████░░░` | 0.86 |
| `providers` | `██████████████████░░` | 0.90 |
| `rubric` | `██████████████████░░` | 0.90 |
| `sufficiency` | `██████████████████░░` | 0.90 |
| `runlog` | `███████████████████░` | 0.93 |

## Per-module gaps  *(worst first)*

### authoring — sufficiency 0.78
- **[major]** The exact per-module authoring rubric contract that defines what an authored spec must look like — the §1 Purpose '**In one line:** ≤20 words' headline, §2 Definitions table, §3 Behavior explanation-only rules, §4 Contracts with INV-/AC- ID tables, semantic-shapes-not-language-types, and 'assert an INV only if the code enforces it' — is only paraphrased at a high level, so a rebuild would produce differently-structured specs the downstream checkers rely on. · `spec_eval/authoring.py (AUTHORING_STRUCTURE / AUTHORING_DISCIPLINE)`
- **[minor]** The numeric defaults are named but their values are never given: REDUCE_CAP=48000, _MAX_LEVELS=4, AUTHOR_MAX_TOKENS=5000; a rebuild must guess them. · `spec_eval/authoring.py (module constants)`
- **[minor]** An unknown layout value raises ValueError with a 'use per-file | per-dir | per-pair' message rather than silently proceeding. · `spec_eval/authoring.py (_layout_targets)`
- **[minor]** The load-bearing KEEP-IN-SYNC coupling of the rubric with skills/spec-authoring/SKILL.md, the shipped templates, and test_rubric_sync.py (which pins shared phrases) is not stated. · `spec_eval/authoring.py (AUTHORING_RUBRIC)`
- **[minor]** per-pair details beyond 'first docs entry': a pair with no docs is silently skipped, code globs run with recursive=True filtering to files, and matches are deduped via set. · `spec_eval/authoring.py (_layout_targets)`
- **[minor]** _pack uses greedy consecutive grouping and _synthesize terminates when a pass stops reducing the item count (len(groups) >= len(items)) with a specific per-item share = max(200, cap//len(items)-40) slice; only the 'equal share' idea is captured. · `spec_eval/authoring.py (_synthesize / _pack)`

### cli — sufficiency 0.82
- **[minor]** The terminal uncovered/orphan lists are truncated at a fixed cap of 25 entries (UNCOVERED_LIST_CAP); the spec says 'capped' but never gives the numeric threshold. · `spec_eval/cli.py (module-level UNCOVERED_LIST_CAP / main coverage branch)`
- **[minor]** The orphaned-specs list is capped at the same limit but, unlike the uncovered list, prints NO '… and N more' overflow note; the spec implies symmetric capping. · `spec_eval/cli.py (main, coverage branch)`
- **[minor]** For single-file scope under a per-dir layout, the synthesized doc name falls back to coverage_mod.dir_spec_path using the config's dir_spec_name (default '<dir>'), a resolution rule/default not stated in the spec. · `spec_eval/cli.py (_file_scope)`
- **[minor]** generate defaults its config to {'pairs': []} (not {} like audit/sufficiency) and deep-copies the authoring block before applying CLI overrides. · `spec_eval/cli.py (main, generate branch)`
- **[minor]** All JSON artifacts (findings/sufficiency/generated/coverage.json) are written with indent=2 pretty-printing. · `spec_eval/cli.py (main)`

### coverage — sufficiency 0.83
- **[minor]** The exact `PRUNE_DIRS` set (env, .mypy_cache, .pytest_cache, .ruff_cache, .tox, htmlcov, site-packages, .idea, .vscode, .eggs, vendored, thirdparty, jspm_packages, etc.) is only partially enumerated with examples, so a rebuild would guess which directory names are pruned. · `coverage.py (PRUNE_DIRS)`
- **[minor]** The full `CONVENTIONAL_DOC_STEMS` set (~20 names: notice, changes, testing, faq, getting-started/getting_started, security, code_of_conduct, skill, todo, authors, maintainers, install, upgrading, …) is only shown as a few examples, affecting exactly which `.md` stems are exempt from orphan flagging. · `coverage.py (CONVENTIONAL_DOC_STEMS)`
- **[minor]** `dir_spec_path` path construction is under-specified: `<dir>` maps to the containing directory's basename, a literal `dir_spec_name` is used verbatim as the filename, and a repo-root file (no dirname) falls back to `repo_name`. · `coverage.py (dir_spec_path)`
- **[minor]** Default config values are not stated: `authoring.layout` defaults to "per-file" and `dir_spec_name` defaults to "<dir>" when absent from config. · `coverage.py (coverage)`
- **[minor]** The report headline renders the percent with `.0f` (integer rounding) even though stored `pct` is a 1-decimal float, and the exact section header strings/emoji (e.g. "## ⚠ Uncovered (spec-worthy, no governing pair)") are not given. · `coverage.py (format_report)`
- **[minor]** The `covered` set is seeded from pair `code` globs before co-located/per-dir routes are added, and pair-glob matches are filtered by `os.path.isfile` (non-file glob hits ignored); the ordering/isfile filtering is implicit. · `coverage.py (coverage)`

### audit — sufficiency 0.85
- **[minor]** The model reply's output-token budget defaults to 3000 tokens (REVIEW_MAX_TOKENS), the value that determines when a reply 'hit the token cap'; the spec references the cap but never states its value. · `audit.py (REVIEW_MAX_TOKENS)`
- **[minor]** file_count (nc/nd) counts only non-empty readable files, so a side whose globs match files that are all empty yields count 0 and triggers the skip path with 'no files matched', even though files existed. · `audit.py (_read_globs)`
- **[minor]** Globs are resolved and sorted per-pattern, not globally, so a file matched by two overlapping patterns is concatenated (and counted) once per pattern, and cross-pattern ordering follows pattern order rather than a global sort. · `audit.py (_read_globs)`
- **[minor]** Missing finding fields are normalized to specific defaults (summary→"", code_ref/doc_ref→None, suggestion→"") rather than being omitted or defaulted arbitrarily. · `audit.py (parse_findings)`
- **[minor]** The fallback severity regex is applied to the whole raw response only when no findings-keyed JSON object is found or the primary loop raises; a valid JSON object with an empty/all-invalid findings list returns empty without falling through to the fallback. · `audit.py (parse_findings)`

### report — sufficiency 0.86
- **[minor]** The sufficiency fingerprint renders a three-column table (`Pair | Spec completeness | Score`) showing BOTH the unicode bar AND the numeric score to 2 decimals; the spec describes it only as an 'at-a-glance table' and doesn't specify that both a bar and a separate numeric-score column appear. · `report.py (sufficiency_fingerprint)`
- **[minor]** `_bar` computes fill count via round-to-nearest (`int(round(v*width))`), so mid-range values snap to the nearest cell (with Python banker's rounding); the spec only pins the endpoints (AC-6) and never states the rounding rule for intermediate 0..1 values. · `report.py (_bar)`
- **[minor]** In the sufficiency per-module detail, skipped pairs are not filtered before sorting and (having no `sufficiency`) sort to the end alongside unscored `None` pairs; the spec's ordering rule only addresses where `None`-scored pairs land, not skipped ones. · `report.py (write_sufficiency_markdown)`
- **[minor]** Both writers overwrite `out_path` in text mode (`open(out_path,'w')`) and join multiple `truncated` notes with `'; '`; the spec mentions writing the file and truncated notes but not the overwrite semantics or the join separator. · `report.py (write_markdown)`
- **[minor]** The drift fingerprint is an h3 (`### Drift fingerprint`) with a `Pair | High+med findings` table while the sufficiency fingerprint is an h2 with descriptive headings; these exact heading levels and column labels aren't specified, so a rebuild would guess the layout. · `report.py (drift_fingerprint)`

### providers — sufficiency 0.90
- **[minor]** The concrete default model value `"anthropic:claude-opus-4-8"` is never stated — the spec only names the DEFAULT_MODEL constant and uses a different example string (`claude-opus-4`), so a rebuild would guess the wrong default. · `providers.py (module-level DEFAULT_MODEL)`
- **[minor]** The claude-code bridge subprocess enforces a 600-second timeout; this default is absent from the spec. · `providers.py (_gen_claude_code)`
- **[minor]** On a non-zero exit or error envelope the bridge raises RuntimeError with the exit code and message truncated to 400 chars (preferring stderr over stdout); the exact error-message shape/truncation isn't specified. · `providers.py (_gen_claude_code)`
- **[minor]** The bridge input-token sum combines three distinct envelope fields — input_tokens + cache_creation_input_tokens + cache_read_input_tokens — whereas the spec only says 'plain and cached' generically. · `providers.py (_gen_claude_code)`
- **[minor]** Anthropic reply assembly only concatenates blocks whose `type == "text"` (non-text blocks like tool_use/thinking are dropped), a filtering rule not stated in the spec. · `providers.py (gen)`
- **[minor]** load_env strips double quotes then single quotes in that order and reads without closing the file; the quote-stripping order/edge behavior is unspecified. · `providers.py (load_env)`

### rubric — sufficiency 0.90
- **[minor]** The exact verbatim wording of DRIFT_RUBRIC is load-bearing (test_rubric_sync.py pins specific shared phrases against SKILL.md), but the spec paraphrases the rubric rather than enumerating which phrases are pinned, so a rebuild couldn't guarantee the sync contract still passes. · `rubric.py (DRIFT_RUBRIC)`
- **[minor]** The docstring's tuning guidance — tune only 'with evidence', and this module's own spec (rubric.md) being guarded by the self-audit — is not captured, so a rebuild loses the maintenance context. · `rubric.py (module docstring)`

### sufficiency — sufficiency 0.90
- **[minor]** The skipped result's explanation string has a specific format embedding the matched counts ("no files matched (code={nc}, docs={nd})"), not just an unspecified explanation string. · `sufficiency.py (sufficiency_pair)`
- **[minor]** The repo-level run resolves caps once via audit.caps_from(config) and threads code_cap/doc_cap into each sufficiency_pair call; the spec describes pair inference but not this caps resolution at repo level. · `sufficiency.py (sufficiency_repo)`
- **[minor]** The exact user-prompt template layout ("# Sufficiency review: {label}" header, a triple-backtick-fenced "## Code" block, and a "## Spec" section) is unspecified beyond "embeds label, fenced code, spec text". · `sufficiency.py (sufficiency_pair)`
- **[minor]** An empty/falsy code_ref (not just null/"null") is also dropped because the guard requires the ref to be truthy before keeping it. · `sufficiency.py (sufficiency_pair)`

### runlog — sufficiency 0.93
- **[minor]** `git_sha` never checks git's exit code — a non-zero exit is treated as success and yields `null` only because failed git writes an empty stdout that `.strip() or None` collapses; the spec attributes null-on-failure to the exception handler alone, missing this stdout-based path for non-raising errors. · `spec_eval/runlog.py (git_sha)`
- **[minor]** The record is serialized with `json.dumps` at its defaults (ensure_ascii escaping non-ASCII, and raising on non-serializable stats values, which aborts the write) — the spec assumes stats are always JSON-encodable summary numbers and doesn't state this failure/encoding behavior. · `spec_eval/runlog.py (append_run)`
