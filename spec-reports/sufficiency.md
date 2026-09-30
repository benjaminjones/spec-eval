# Spec sufficiency — `spec-eval`
detector: `claude-code` · 12/12 pairs scored · 12 model call(s)

**Average sufficiency 0.82** — how completely does the spec capture the code's behavior? (1.0 = no gaps found; gaps = behavior in the code but not the spec. An indicator, not a guarantee.)

## Sufficiency fingerprint  *(at a glance — worst first)*

| Pair | Spec completeness | Score |
|---|---|---|
| `cli` | `████████████░░░░░░░░` | 0.62 |
| `providers` | `██████████████░░░░░░` | 0.72 |
| `compare` | `███████████████░░░░░` | 0.76 |
| `audit` | `████████████████░░░░` | 0.80 |
| `verify` | `████████████████░░░░` | 0.80 |
| `syscontext` | `████████████████░░░░` | 0.82 |
| `authoring` | `█████████████████░░░` | 0.85 |
| `sufficiency` | `█████████████████░░░` | 0.85 |
| `report` | `█████████████████░░░` | 0.87 |
| `coverage` | `██████████████████░░` | 0.88 |
| `runlog` | `██████████████████░░` | 0.90 |
| `rubric` | `██████████████████░░` | 0.92 |

## Per-module gaps  *(worst first)*

### cli — sufficiency 0.62
- **[major]** The entire `compare` subcommand is absent from the spec — it takes two `--reps` JSON files plus `--margin`/`--allow-sha-mismatch`/`--out`, makes no model calls, writes `compare.json`, and prints MDE-at-80%-power first, an underpowered warning, delta ± SE with df/Student-t 95% CI, TOST verdict or `m_star` when no margin is given, Benjamini-Hochberg results, per-vendor noise share, dropped single-vendor pairs, and an exploratory-deltas caveat; a refusal raises SystemExit(2). · `spec_eval/cli.py (main)`
- **[major]** `sufficiency --reps N` is undocumented: it re-scores every pair N times, prints a per-rep `scored/total` progress line, uses rep 1 for the single-run report/JSON, and (when N>1) writes `sufficiency-reps.json` carrying model, repo, `git_sha`, `reps_requested` and every raw rep, then prints the observed min-max spread. · `spec_eval/cli.py (main)`
- **[major]** `sufficiency --max-calls N` is undocumented: it installs a hard ceiling on model calls via `providers.set_max_calls` (aborting the run rather than exceeding it) and prints a ceiling banner; it exists only on `sufficiency`, not on `audit`/`generate`/`diagram`. · `spec_eval/cli.py (_add_max_calls / main)`
- **[minor]** Audit's summary line has two forms: when some attempted pairs are ungraded (`report.not_graded`) it prints graded/attempted/total separately so an ungraded pair stays in the denominator rather than reading as clean, and it logs `pairs_graded` alongside `pairs_audited`. · `spec_eval/cli.py (main)`
- **[minor]** The terminal cap on the uncovered list (and the orphan list, which reuses it) is 25 entries, with the overflow note only printed for the uncovered list. · `spec_eval/cli.py (UNCOVERED_LIST_CAP / main)`
- **[minor]** The generate run-log record also carries `failed` and `stray` counts, not just `authored`/`skipped`/`flagged`. · `spec_eval/cli.py (main)`
- **[minor]** `diagram` exits non-zero with 'no spec-worthy code files … nothing to diagram' when the module set is empty. · `spec_eval/cli.py (main)`
- **[minor]** `diagram --write`/`--add-section` validate the write target (doc exists, Architecture section present) BEFORE synthesis, so a doc that will be refused fails fast without paying for any model call. · `spec_eval/cli.py (main)`

### providers — sufficiency 0.72
- **[major]** The entire process-wide call-budget feature is absent from the spec: module-level `MAX_CALLS` (None = unlimited default), `set_max_calls(n)` normalizing None/0 to unlimited, and a `CallBudgetExceeded(RuntimeError)` raised by a guard that runs BEFORE each request (so the ceiling bounds calls actually made) with a message reporting calls made, the limit, and cumulative in/out tokens. · `spec_eval/providers.py (set_max_calls / _guard / CallBudgetExceeded)`
- **[minor]** The concrete value of `DEFAULT_MODEL` (`"anthropic:claude-opus-4-8"`) is never stated, only that the constant exists. · `spec_eval/providers.py (module-level DEFAULT_MODEL)`
- **[minor]** Bridge failure messages are extracted from the CLI's JSON envelope rather than raw head bytes: try stdout then stderr, parse JSON, prefer the first non-empty `result`/`error`/`message` string, else re-serialize the envelope minus the `usage` block, cap at 600 chars, falling back to trimmed raw text or the literal "no output". · `spec_eval/providers.py (_bridge_error)`
- **[minor]** The `claude -p` subprocess is run with a 600-second timeout. · `spec_eval/providers.py (_gen_claude_code)`
- **[minor]** The spec states `max_tokens` is not passed to OpenAI at all, but the v1/responses fallback path does pass it as `max_output_tokens`. · `spec_eval/providers.py (_gen_openai_responses)`
- **[minor]** On the responses path, when the convenience field `output_text` is absent/empty the reply text is assembled by concatenating `.text` from every content part of every output item instead of failing. · `spec_eval/providers.py (_gen_openai_responses)`
- **[minor]** OpenAI chat truncation detection reads `finish_reason` from the first choice only and records False when `choices` is empty, rather than erroring. · `spec_eval/providers.py (gen)`
- **[minor]** Google truncation detection matches the substring `MAX_TOKENS` against the first candidate's finish reason enum name or its string form (tolerating both enum and raw shapes). · `spec_eval/providers.py (gen)`

### compare — sufficiency 0.76
- **[major]** The noise_share estimator is never defined computationally: within variance is the mean of per-pair sample variances over only those pairs with >= 2 reps, and the denominator is the pooled variance of all scores across all pairs (not a variance-components decomposition), with noise_share null when total variance is 0. · `spec_eval/compare.py (noise)`
- **[minor]** The noise block also emits within_vendor_variance, total_variance and pairs_with_replication (count of pairs with >= 2 reps), all absent from the spec's field list. · `spec_eval/compare.py (noise)`
- **[minor]** The MDE formula is unspecified: mde_80pct_power = (t(1-alpha/2, df) + t(0.80, df)) * se_delta. · `spec_eval/compare.py (compare)`
- **[minor]** m_star and the TOST interval formulas are unspecified: m_star = |delta| + t(1-alpha, df)*se, and ci90 is delta +/- t(1-alpha, df)*se (one-sided quantile), while ci95 uses t(1-alpha/2, df). · `spec_eval/compare.py (compare)`
- **[minor]** When a margin is supplied the output also carries underpowered_for_margin (mde > margin) plus an underpowered_note; the spec never names this verdict field or its rule. · `spec_eval/compare.py (compare)`
- **[minor]** The per-pair test is a pooled two-sample t (df = n_a + n_b - 2, pooled sp2 with zero variance substituted for single-rep arms), two-sided p rounded to 6 dp — the spec says only 'a weak two-sample test'. · `spec_eval/compare.py (compare)`
- **[minor]** alpha is a caller-settable parameter defaulting to 0.05 and simultaneously drives the CI width, the TOST/one-sided quantile, and the Benjamini-Hochberg FDR level q; the spec fixes none of this. · `spec_eval/compare.py (compare)`
- **[minor]** Vendor labels are derived from the file's 'model' key, falling back to the file path, and can be overridden by a vendor argument to load_reps — this determines the vendors list and the noise keys. · `spec_eval/compare.py (load_reps)`
- **[minor]** A file whose every record has a null sufficiency raises ValueError ('contained no scored pairs') rather than returning an empty mapping; also git_sha is only read from the object shape, so a bare list always yields sha None. · `spec_eval/compare.py (load_reps)`
- **[minor]** Sign convention is unstated: delta is first input minus second (mean_a - mean_b) per pair, then averaged. · `spec_eval/compare.py (compare)`
- **[minor]** Per-pair record shape and rounding are unspecified: keys pair, delta, mean_<vendorA>, mean_<vendorB>, reps [n_a, n_b], with deltas/CIs rounded to 4 dp, variances to 6 dp; bh_significant is a sorted list of pair labels. · `spec_eval/compare.py (compare)`
- **[minor]** Explanatory string fields shipped in every result (dropped_note, m_star_note, bh_note, quantile_basis = 'Student t at df = n-1') and the field name pairs_n for the shared-pair count are not in the spec. · `spec_eval/compare.py (compare)`

### audit — sufficiency 0.80
- **[major]** The spec calls the rubric a fixed prompt and omits the config-overridable `rubric: {drift, sufficiency}` setting, which takes a FILE path (relative paths resolved against the repo/project dir) and hard-errors with SystemExit on a missing or empty file rather than silently falling back to the default. · `spec_eval/audit.py (rubric_from)`
- **[minor]** The model call's output budget (REVIEW_MAX_TOKENS = 3000, deliberately shared with the sufficiency check so a truncated findings list stays parseable) is never given a value in the spec, which only mentions that a reply may hit "the token cap". · `spec_eval/audit.py (REVIEW_MAX_TOKENS)`
- **[minor]** The parsers keep a CLOSED schema — any key a custom rubric asks the model for beyond the seven finding keys is dropped silently, so a custom pointer (quote, line range, section id) must ride inside `code_ref` to survive. · `spec_eval/audit.py (parse_findings)`
- **[minor]** The meaning of the `class` axis is undefined: it is orthogonal to severity, `stale` denotes an outdated declarative value rather than a broken guarantee, and a `stale` finding is reported but not counted as drift. · `spec_eval/audit.py (CLASSES)`
- **[minor]** If an exception is raised partway through iterating parsed findings, the already-collected findings are retained AND the regex fallback then appends a finding per `"severity"` match, so the same drift item can appear twice. · `spec_eval/audit.py (parse_findings)`
- **[minor]** `truncation_notes` is a shared helper producing the identical pair-level partial-view note list for both audit and sufficiency, with the reply-truncation flag read from the provider's LAST-call state rather than from the response itself. · `spec_eval/audit.py (truncation_notes)`

### verify — sufficiency 0.80
- **[major]** The repo-level entry point is undescribed: how pairs are resolved (config `pairs`, else inferred via coverage.infer_pairs), that result records are matched to pairs by `label`, that records with no matching pair or no findings are skipped, and that results are mutated in place and returned. · `spec_eval/verify.py (verify_repo)`
- **[minor]** The verification prompt also carries the pair's code text (not just the document and findings), and each finding is listed with index, severity, summary, doc_ref, code_ref and evidence. · `spec_eval/verify.py (verify_pair)`
- **[minor]** Document and code are read through size caps (defaults from audit.CODE_CAP/DOC_CAP, overridable via `caps_from(config)`), so the 'whole document' is actually truncated at a cap. · `spec_eval/verify.py (verify_pair)`
- **[minor]** When no document content can be read for the pair (zero doc files matched), findings are returned unverified with no model call. · `spec_eval/verify.py (verify_pair)`
- **[minor]** The position-check window is ±3 lines, and the match is substring containment within a single document line (any occurrence within the window passes; the rejection message reports the first occurrence). · `spec_eval/verify.py (check_not_asserted)`
- **[minor]** A cited line is extracted from `doc_ref` by matching `:L<digits>` or `:<digits>`; a doc_ref in any other shape is treated as citing no line, so only presence is checked. · `spec_eval/verify.py (_cited_line)`
- **[minor]** The verifier call is capped at 2000 max output tokens, on the rationale that it returns verdicts only. · `spec_eval/verify.py (VERIFY_MAX_TOKENS)`
- **[minor]** Default/downgraded verdicts carry specific placeholder text: missing verdicts get why 'no verdict returned; upheld by default' with empty quote, while a withdrawal downgraded for a bad ground keeps the model's doc_quote and why. · `spec_eval/verify.py (parse_verdicts)`

### syscontext — sufficiency 0.82
- **[major]** The curated detection tables' actual contents are only exemplified, so a rebuild must guess which systems are recognized and with what kind — e.g. Celery broker, Memcached, LDAP, Elasticsearch/OpenSearch, Cassandra, Oracle, SMTP, MariaDB (infra) and Twilio, SendGrid, Slack, OpenAI, Anthropic, Google APIs, ccxt, yfinance, Alpaca, Interactive Brokers (application), plus the exact key spellings per ecosystem. · `spec_eval/syscontext.py (SDK_IMPORTS)`
- **[minor]** The numeric values of the named constants are never given: EVIDENCE_CAP=8, LINE_CAP=160, FILE_CAP=2,000,000 bytes, EP_MODULE_MAIN_CAP=6, and the scheme matcher's 2–32 char scheme length bound. · `spec_eval/syscontext.py (module constants)`
- **[minor]** AWS service-name derivation rules for ids outside the display table are unstated: ids of ≤4 chars are upper-cased and longer ones hyphen-split/title-cased, and SDK plumbing namespaces (runtime, extensions, util, core, config, auth) are skipped rather than reported as services. · `spec_eval/syscontext.py (_scan_file)`
- **[minor]** boto3 bookkeeping is per file and conditional: a known `.client(id)` resolves on any line without an import, an unknown id only yields a title-cased entry when boto3 was imported in that same file, and `AWS (service not resolved)` is emitted only when boto3 was imported and no client id resolved in that file. · `spec_eval/syscontext.py (_scan_file)`
- **[minor]** `overview_evidence(ctx_result, ep_result=None)` — the single composer that joins the entry-point block then the system block with a blank line and returns None when neither observed anything, so `generate --overview` and `diagram` always get identical evidence in identical order — is absent from the spec. · `spec_eval/syscontext.py (overview_evidence)`
- **[minor]** Entry-point name/target label conventions are unspecified: dotted module name with target 'command-line interface' (cli-main) or 'run as a script' (module-main), the app-object variable name with '<Framework> app object (constructed)', and `python -m <pkg>` (package dir dotted, or repo basename at root). · `spec_eval/syscontext.py (_scan_entrypoints_file)`
- **[minor]** The entry-point kind ordering used for sorting (script → package-main → web-app → cli-main → module-main) is never stated, unlike the system KIND_ORDER. · `spec_eval/syscontext.py (EP_KIND_ORDER)`
- **[minor]** Per-file entry-point precedence rules: only the FIRST `__main__` guard in a file is used, a `__main__.py` file suppresses its own guard entry entirely, and a framework app object is emitted in addition to (not instead of) a guard entry. · `spec_eval/syscontext.py (_scan_entrypoints_file)`
- **[minor]** Framework app-object detection requires an assignment-shaped construction (`name = Flask(`) and covers a fixed factory list — Flask, FastAPI, Sanic, Quart, Bottle, Tornado (Quart appears here but not in the inbound-framework table). · `spec_eval/syscontext.py (FRAMEWORK_APP_FACTORIES)`
- **[minor]** `diff_receipt`'s concrete output shapes are unspecified: the clean line '0 system-context changes', the optional ' @ <sha>' annotation, the fixed re-baseline explanation text, and that a rebaseline receipt also prints the ±delta lines. · `spec_eval/syscontext.py (diff_receipt)`
- **[minor]** The recognized-but-unsupported extension list backing `unscanned` (~30 extensions: .c/.cpp/.h/.m/.scala/.groovy/.clj/.ex/.erl/.hs/.ml/.fs/.vb/.pl/.r/.jl/.dart/.lua/.zig/.nim …) and the fixed note's remediation clause ('Add the extension(s) to `code_ext` …') are not given. · `spec_eval/syscontext.py (OTHER_SOURCE_EXT)`
- **[minor]** Unsupported-extension files are counted into `unscanned` before any exclusion filtering, so a .cpp file under tests/ or examples/ still increments the language-gap counts. · `spec_eval/syscontext.py (scan)`
- **[minor]** The full documentation-domain skip list (schema.org, json-schema.org, pypi.org, npmjs.com, opensource.org, creativecommons.org, shields.io, readthedocs.io, stackoverflow.com, example.org/.net) and the extra connection schemes recognized (gs, smtp, ftp/sftp, nats, mqtt, jdbc:sqlserver, mongodb+srv, rediss) are only partially exemplified. · `spec_eval/syscontext.py (SKIP_HOST_SUFFIXES, SCHEME_SYSTEMS)`
- **[minor]** `from google import genai` is detected as a distinct 'Google Gemini API' application entry, and Google Cloud entries are named 'Google Cloud <title-cased service id>' with underscores/hyphens converted. · `spec_eval/syscontext.py (_GOOGLE_GENAI_RE)`
- **[minor]** The compiled stamp patterns are deliberately public module surface (STAMP_RE, ARCH_STAMP_RE) for other modules to match against, and the comment format is `<!-- <name>: <hex> -->` with whitespace tolerance. · `spec_eval/syscontext.py (_Stamp)`

### authoring — sufficiency 0.85
- ⚠ *partial view (docs input capped at ~28,000 chars)*
- **[major]** The built-in per-module rubric's actual section skeleton is never stated: '## 1. Purpose' (bold '**In one line:** <=20 words' opener, WHAT+WHY, constraint as a checkable consequence), '## 2. Definitions' table, '## 3. Behavior' (no per-method walkthrough), '## 4. Contracts' with semantic shapes, a '### Invariants' table of INV-n ids asserted ONLY where the code enforces them (assert/clamp/validation/raised error), and a '### Acceptance criteria (*Given / When / Then*)' table of AC-n ids with concrete numbers. · `spec_eval/authoring.py (AUTHORING_STRUCTURE)`
- **[minor]** FOLDER_SPEC_RUBRIC's section set is unspecified — a directory spec must be SELF-CONTAINED (the per-module specs may not exist) with '## 1. Purpose', '## 2. Modules' (module -> one-line responsibility table), '## 3. How it fits together', '## 4. Shared contract' (cross-module only). · `spec_eval/authoring.py (FOLDER_SPEC_RUBRIC)`
- **[minor]** The concrete default constants are missing: REDUCE_CAP = 48000 chars, _MAX_LEVELS = 4 recursion passes, AUTHOR_MAX_TOKENS = 5000 output tokens used at every authoring/synthesis call site. · `spec_eval/authoring.py (module-level constants)`
- **[minor]** Several AUTHORING_DISCIPLINE rules are absent: organize headings by CAPABILITY and never make a function signature or language type a heading, drop code trivia, every table row filled (never an empty INV-/AC- row), and label inferred rationale as '> Reconstructed intent (confidence: low/med/high) — inferred from the code.' · `spec_eval/authoring.py (AUTHORING_DISCIPLINE)`
- **[minor]** `has_architecture_section` — the fence-aware public precondition the `diagram --write` path checks BEFORE synthesising so a replace-only update on a doc with no Architecture section fails fast instead of burning model calls — is not specified. · `spec_eval/authoring.py (has_architecture_section)`
- **[minor]** `diagram_block`'s return contract is not given: it returns the 5-tuple (section_body_markdown, ctx, ep, modules, note|None) so callers can stamp fingerprints from the same scans and module set. · `spec_eval/authoring.py (diagram_block)`
- **[minor]** Two System-context rules are missing: a trailing 'Not scanned:' language-gap line in the evidence block must be reproduced verbatim beneath the table, and the System-context rules take PRECEDENCE over the right-sizing discipline (a single evidence-backed row still renders a full table; 'unknown from this repo' counts as filled). · `spec_eval/authoring.py (_OV_SYSTEM_CONTEXT)`
- **[minor]** The diagram rubric's concrete rendering budgets and visual legend are omitted (<=5 participants, <=10 messages, <=12 nodes / 18 edges, 2-5 stroke-only lifecycle subgraphs, the stadium/rect/[[ ]]/[( )]/[/ /] shape legend, and the exact process/artifact/external classDef fill+stroke+color palette with no theme/init/linkStyle). · `spec_eval/authoring.py (ARCH_DIAGRAM_RUBRIC)`
- **[minor]** `_layout_targets` error and skip semantics are unstated: an unknown layout raises ValueError naming the three valid values, and a config pair with no `docs` entry or no matching code files is silently dropped from the target set. · `spec_eval/authoring.py (_layout_targets)`
- **[minor]** Stray-write detection scope is unspecified: the inventory walks only `.md` files, prunes coverage's PRUNE_DIRS, and keys each file by (mtime_ns, size), so an unchanged non-target file is not reported and ignored directories are invisible. · `spec_eval/authoring.py (_md_inventory)`
- **[minor]** Force-fit slicing arithmetic and note truncation thresholds are absent: each item gets max(200, cap // len(items) - 40) chars plus a '...[truncated]' marker, and the broken-link note lists at most 5 paths before an ellipsis. · `spec_eval/authoring.py (_synthesize)`

### sufficiency — sufficiency 0.85
- **[major]** The rubric is overridable per-repo via config (`audit.rubric_from(config, "sufficiency", SUFFICIENCY_RUBRIC, repo)`), and `sufficiency_pair` accepts an injected `rubric` (falling back to the built-in when None) — the spec presents SUFFICIENCY_RUBRIC as the only, fixed rubric. · `spec_eval/sufficiency.py (sufficiency_repo)`
- **[minor]** `sufficiency_pair` takes optional `code_cap`/`doc_cap` arguments that override the config/audit defaults when not None, so callers can cap per-pair rather than only via `caps.code`/`caps.docs`. · `spec_eval/sufficiency.py (sufficiency_pair)`
- **[minor]** A parsed gap missing its `severity` or `missing` key is not dropped or defaulted to a sentinel — both coerce to the empty string, so a malformed gap still appears in the result list. · `spec_eval/sufficiency.py (sufficiency_pair)`
- **[minor]** The parsed `sufficiency` float is never clamped or validated against [0.0, 1.0], so an out-of-range model score passes through verbatim despite the documented bounds. · `spec_eval/sufficiency.py (sufficiency_pair)`
- **[minor]** The skipped result never carries `truncated` notes (truncation is computed only after the skip return), and its `skipped` string has a specific shape embedding both match counts (`no files matched (code=N, docs=M)`). · `spec_eval/sufficiency.py (sufficiency_pair)`

### report — sufficiency 0.87
- **[minor]** The sufficiency fingerprint's concrete table shape is unspecified: heading `## Sufficiency fingerprint  *(at a glance — worst first)*`, three columns `Pair | Spec completeness | Score`, label and bar wrapped in inline code, score formatted to two decimals. · `report.py (sufficiency_fingerprint)`
- **[minor]** The drift fingerprint's concrete table shape is unspecified: `### Drift fingerprint` (an h3, unlike the sufficiency fingerprint's h2), single data column headed `High+med findings`, cell values `⚠ not graded` / `✓ clean` / `⚠ N`. · `report.py (drift_fingerprint)`
- **[minor]** The bar's value→cell mapping (`int(round(v*width))`, i.e. half-up rounding of v×20) is not stated, so mid-range scores (e.g. 0.42 → 8 filled) can't be reproduced; only the v=1.0 endpoint is pinned by AC-6. · `report.py (_bar)`
- **[minor]** A withdrawn finding suppresses its evidence block as well as its fix line (the loop `continue`s after the ground/doc-quote lines); the spec only says it proposes no fix. · `report.py (write_markdown)`
- **[minor]** The withdrawn-finding lines' conditionality and format are unspecified: `*withdrawn on verification — {ground}:* {why}` always emitted (with `why` defaulting to empty), and the `*the doc says:* “…”` line only when `doc_quote` is present. · `report.py (write_markdown)`
- **[minor]** The drift report's per-pair detail sections are emitted in input order (including skipped pairs in place), which the spec never states — it only fixes ordering for the fingerprints and the sufficiency detail. · `report.py (write_markdown)`
- **[minor]** In the sufficiency report, skipped pairs sort into the same last bucket as unscored pairs (their `sufficiency` is None), rather than appearing in input position. · `report.py (write_sufficiency_markdown)`
- **[minor]** Fence neutralization in the evidence block is done by replacing ``` with `'''` and the value is coerced with `str()`, so non-string evidence renders via its repr rather than erroring. · `report.py (_evidence_block)`

### coverage — sufficiency 0.88
- **[minor]** The full conventional-doc stem list is not enumerated (spec gives only examples), so a rebuild would not know that stems like `testing`, `security`, `faq`, `todo`, `install`, `upgrading`, `authors`, `maintainers`, `notice`, `contributing`, `changes`, `skill`, `code_of_conduct`, `getting-started`, `cursorrules`, `copilot-instructions`, `llms` are also exempt from orphan and unmodeled reporting. · `coverage.py (CONVENTIONAL_DOC_STEMS)`
- **[minor]** `dir_spec_path` semantics are under-specified: a code file at the repo root uses the repo directory's basename as the folder-spec stem, and a non-`<dir>` `dir_spec_name` is used as a literal filename in the code file's own directory. · `coverage.py (dir_spec_path)`
- **[minor]** Unmodeled markdown at the repo root (no path separator) is grouped under the directory key `"."` rather than being skipped. · `coverage.py (unmodeled_markdown)`
- **[minor]** The exact prune-directory membership is only partially listed; entries like `venv`, `env`, `htmlcov`, `.tox`, `.eggs`, `.mypy_cache`, `.pytest_cache`, `.ruff_cache`, `site-packages`, `jspm_packages`, `thirdparty` would have to be guessed, and pruning also suppresses `.md` collection (so specs inside those trees are invisible to orphan/unmodeled detection). · `coverage.py (PRUNE_DIRS)`
- **[minor]** Report rendering details are unspecified: the headline prints the percent with zero decimals (despite `pct` carrying one), the `# Spec coverage — <repo name>` heading, the `…` continuation marker on unmodeled samples, and the Excluded section being emitted unconditionally even when empty. · `coverage.py (format_report)`

### runlog — sufficiency 0.90
- **[minor]** `git_sha(repo)` is a standalone public helper with its own contract (returns the short SHA string or None) that callers can use independently; the spec folds it entirely into `append_run` and never defines it as part of the module's API surface. · `spec_eval/runlog.py (git_sha)`
- **[minor]** Git's exit status is ignored — the SHA is taken from stripped stdout whenever it is non-empty, so a non-zero returncode with output would still be recorded, and empty/whitespace-only stdout yields null; the spec implies failure is detected by the command erroring. · `spec_eval/runlog.py (git_sha)`
- **[minor]** `stats` values must be JSON-serializable; a non-serializable value raises out of `json.dumps` and propagates to the caller after the output directory and (possibly) an empty `runs.jsonl` have already been created — the spec only specifies error tolerance for git resolution. · `spec_eval/runlog.py (append_run)`

### rubric — sufficiency 0.92
- **[minor]** The spec omits that `DRIFT_RUBRIC` is a verbatim prompt string containing no format placeholders/templating slots for the pair's code or doc content (the pair is supplied out-of-band by the caller), so a rebuild could plausibly add `{code}`/`{doc}` substitution points. · `spec_eval/rubric.py (DRIFT_RUBRIC)`
- **[minor]** The spec's sync contract omits the docstring's second maintenance pointer — that `rubric.md` beside the module is the module's own spec and is guarded by spec-eval's self-audit — so a rebuild would restore only the SKILL.md mirror half of the KEEP IN SYNC block. · `spec_eval/rubric.py (module docstring)`
