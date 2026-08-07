# Spec sufficiency — `spec-eval`
detector: `claude-code` · 11/11 pairs scored · 11 model call(s)

**Average sufficiency 0.86** — how completely does the spec capture the code's behavior? (1.0 = no gaps found; gaps = behavior in the code but not the spec. An indicator, not a guarantee.)

## Sufficiency fingerprint  *(at a glance — worst first)*

| Pair | Spec completeness | Score |
|---|---|---|
| `authoring` | `██████████████░░░░░░` | 0.72 |
| `verify` | `████████████████░░░░` | 0.79 |
| `report` | `█████████████████░░░` | 0.84 |
| `audit` | `█████████████████░░░` | 0.85 |
| `cli` | `█████████████████░░░` | 0.86 |
| `providers` | `█████████████████░░░` | 0.87 |
| `syscontext` | `█████████████████░░░` | 0.87 |
| `coverage` | `██████████████████░░` | 0.88 |
| `sufficiency` | `██████████████████░░` | 0.88 |
| `runlog` | `██████████████████░░` | 0.92 |
| `rubric` | `███████████████████░` | 0.93 |

## Per-module gaps  *(worst first)*

### authoring — sufficiency 0.72
- **[major]** The Architecture diagram rendering contract is summarized in one clause but its actual rules are absent: at most 5 sequence participants and 10 messages, each workflow message opening with its literal shell command, dashed replies only for user-returned artifacts, the flowchart's 12-node/18-edge budget with its ordered upstream-folding rules and one-line fold note, 2-5 stroke-only lifecycle subgraphs, the shape vocabulary (stadium/rect/[[ ]]/[( )]/[/ /]), the three exact classDefs, edge conventions (solid/dashed/exactly one ==> primary chain), node-label format, and the requirement that the data flow terminate in the same user-facing result the sequence diagram shows (the spec instead says it ends at external systems). · `spec_eval/authoring.py (ARCH_DIAGRAM_RUBRIC)`
- **[major]** The repo OVERVIEW.md is ALWAYS given a trailing architecture fingerprint receipt (`syscontext.architecture_stamp_comment(ctx, ep, files)`) — unconditional, unlike the evidence-gated system-context stamp — which is what `context --check` compares the module set against. · `spec_eval/authoring.py (generate_repo._repo_overview)`
- **[major]** The built-in per-module structure's exact skeleton is unstated: the four numbered headings ('## 1. Purpose' with a '**In one line:** <=20 words' opener, '## 2. Definitions' term table, '## 3. Behavior', '## 4. Contracts' with its italic reference cue), the '### Invariants' / '### Acceptance criteria (Given/When/Then)' tables with INV-n / AC-n IDs, and the rule that an INV may be asserted only where the code actually enforces it. · `spec_eval/authoring.py (AUTHORING_STRUCTURE)`
- **[major]** The folder-spec rubric's own section set is never given — '## 1. Purpose', '## 2. Modules' (module -> one-line responsibility table), '## 3. How it fits together', '## 4. Shared contract' (cross-module only) — plus its self-contained-reader premise. · `spec_eval/authoring.py (FOLDER_SPEC_RUBRIC)`
- **[minor]** The numeric defaults behind the named constants are omitted: REDUCE_CAP = 48000 chars, _MAX_LEVELS = 4 synthesis levels, and AUTHOR_MAX_TOKENS = 5000 output tokens for every authoring/synthesis call. · `spec_eval/authoring.py`
- **[minor]** The System-context rules also require reproducing a trailing 'Not scanned: …' language-gap line verbatim beneath the table, and explicitly override the right-sizing discipline so a single evidence-backed row is still rendered as a full table. · `spec_eval/authoring.py (_OV_SYSTEM_CONTEXT)`
- **[minor]** An unrecognised `authoring.layout` value raises ValueError naming the three valid layouts, rather than falling back to a default. · `spec_eval/authoring.py (_layout_targets)`
- **[minor]** Stray-write detection walks only .md files outside `coverage.PRUNE_DIRS` and compares an (mtime_ns, size) signature, so a write inside a pruned directory is invisible and an in-place rewrite of an existing file counts as stray. · `spec_eval/authoring.py (_md_inventory)`
- **[minor]** A synthesis over an empty item list short-circuits to empty markdown with no model call (level 1, not truncated). · `spec_eval/authoring.py (_synthesize)`
- **[minor]** `has_architecture_section` is a public fence-aware precondition the `diagram --write` path checks before synthesising, so a replace-only update on a doc lacking the section fails fast instead of burning model calls. · `spec_eval/authoring.py (has_architecture_section)`
- **[minor]** The broken-link note lists at most the first 5 unresolvable paths (deduplicated and sorted) followed by an ellipsis, and the repaired-link note reports a count of repo-root-to-document rewrites. · `spec_eval/authoring.py (_link_note)`
- **[minor]** Progress reporting also emits per-synthesis-group lines ('· synthesis pass N: group i/M (k modules)') and per-module map lines ('· module <path>'), not just one line per target. · `spec_eval/authoring.py (_synthesize)`

### verify — sufficiency 0.79
- **[major]** The repo-level driver is not described: it resolves pairs from `config["pairs"]` or falls back to `coverage.infer_pairs(repo, config)`, matches result records to pairs by `label`, skips records with no matching pair or no findings, and rewrites `rec["findings"]` in place. · `spec_eval/verify.py (verify_repo)`
- **[minor]** The verifier prompt also carries the pair's concatenated code, and both doc and code are truncated to caps (`audit.DOC_CAP`/`audit.CODE_CAP`, overridable via `audit.caps_from(config)`), so "the whole document" is bounded. · `spec_eval/verify.py (verify_pair)`
- **[minor]** If the doc globs resolve to zero files (`nd == 0`), verification is skipped entirely and the findings are returned unverified — a second no-op path beyond the empty-findings case in AC-8. · `spec_eval/verify.py (verify_pair)`
- **[minor]** The window for the position check defaults to 3 lines (`abs(hit - cited) <= 3`) and is a parameter; the spec only says "a small window". · `spec_eval/verify.py (check_not_asserted)`
- **[minor]** Quote presence is a substring match against a single document line (`quote in line`), so a quote spanning line breaks or normalized whitespace fails and the withdrawal is rejected. · `spec_eval/verify.py (check_not_asserted)`
- **[minor]** `doc_ref` line extraction accepts both `file:L50` and `file:50` via `:L?(\d+)` and yields None otherwise, which is what makes the window check conditional. · `spec_eval/verify.py (_cited_line)`
- **[minor]** The verdict is attached to each finding under the key `verification`, and downstream filtering treats a missing key as upheld (`f.get("verification", {}).get("verdict", "upheld")`). · `spec_eval/verify.py (verify_pair / upheld)`
- **[minor]** The verifier call is capped at 2000 max tokens (verdicts only, no evidence re-quoting). · `spec_eval/verify.py (VERIFY_MAX_TOKENS)`
- **[minor]** The findings listing sent to the verifier has a fixed shape — index, severity, summary, doc_ref, code_ref, and evidence per finding — and indices are what the model must key verdicts by. · `spec_eval/verify.py (verify_pair)`
- **[minor]** Default and downgraded verdicts have specified `why` strings ("no verdict returned; upheld by default", "withdrawal rejected: …" naming absence vs. position with the found line number), and a rejected withdrawal preserves the quote while clearing the ground. · `spec_eval/verify.py (parse_verdicts / check_not_asserted)`
- **[minor]** An out-of-range or non-integer `index` in a verdict entry is skipped rather than aborting parsing, and the rubric's `not-asserted` instruction includes the "if the property appears anywhere else in the doc at the needed strength, the ground does not apply" clause. · `spec_eval/verify.py (parse_verdicts / VERIFY_RUBRIC)`

### report — sufficiency 0.84
- **[minor]** The sufficiency fingerprint's concrete shape is unspecified: an `## Sufficiency fingerprint  *(at a glance — worst first)*` heading over a three-column table (`Pair | Spec completeness | Score`) where the unicode bar is rendered inside backticks and the score to two decimals — the spec never says the bar lives in this table at all. · `report.py (sufficiency_fingerprint)`
- **[minor]** The drift fingerprint's concrete shape is unspecified: an `### Drift fingerprint` heading (h3, unlike the sufficiency fingerprint's h2) over a two-column table `Pair | High+med findings`. · `report.py (drift_fingerprint)`
- **[minor]** A withdrawn finding also suppresses its evidence block (spec only says it proposes no fix), and its withdrawal renders as `- *withdrawn on verification — {ground}:* {why}` plus an optional `- *the doc says:* “{doc_quote}”` line in curly quotes. · `report.py (write_markdown)`
- **[minor]** `_bar` accepts a configurable `width` (default 20) and computes filled cells as `int(round(v * width))`, so the rounding rule and non-20 widths are unstated. · `report.py (_bar)`
- **[minor]** Fence neutralization is a substitution of ``` with ''' (the quoted text is preserved, not stripped or escaped), and the evidence value is coerced with `str()` so non-string evidence still renders. · `report.py (_evidence_block)`
- **[minor]** The sufficiency report's per-module section is introduced by a `## Per-module gaps  *(worst first)*` heading, and skipped pairs sort at the end alongside unscored pairs (they sort by `(sufficiency is None, sufficiency or 0)`), which the spec leaves unstated. · `report.py (write_sufficiency_markdown)`
- **[minor]** Drift load treats a finding carrying a `verification` object with no `verdict` key as upheld (verdict defaults to "upheld"), so only an explicit "withdrawn" verdict excludes it. · `report.py (drift_load)`
- **[minor]** The sufficiency report's truncated note omits the drift report's "findings may be incomplete" clause, rendering only `- ⚠ *partial view ({notes})*`, with multiple notes joined by `; `. · `report.py (write_sufficiency_markdown)`

### audit — sufficiency 0.85
- **[minor]** The model call is made with a fixed output-token budget of 3000 (REVIEW_MAX_TOKENS), a module-level constant deliberately shared with the sufficiency check so both reviews use the same budget; the spec never states that any output cap is set or its value. · `spec_eval/audit.py (audit_pair)`
- **[minor]** Whether the reply was cut off is not returned by the call but read from the provider module's mutable global `providers.LAST["truncated"]` immediately after the last generation. · `spec_eval/audit.py (truncation_notes)`
- **[minor]** The exact truncation-note strings and their order are unspecified: "code input capped at ~{n:,} chars", then "docs input capped at ~{n:,} chars", then "reply hit the token cap", with comma-grouped numbers reflecting the effective (possibly config-overridden) caps. · `spec_eval/audit.py (truncation_notes)`
- **[minor]** The user-message template is unspecified: a `# Drift review: {label}` heading, the code side wrapped in a triple-backtick fence under `## Code`, and the doc side unfenced under `## Docs / spec`. · `spec_eval/audit.py (audit_pair)`
- **[minor]** `first_json_object(resp, *keys)` is a general, reusable exported helper that scans every `{` position with `JSONDecoder(strict=False).raw_decode` and accepts any caller-supplied key set (reused by the sufficiency check), not a findings-only internal step. · `spec_eval/audit.py (first_json_object)`
- **[minor]** After a findings-bearing JSON object parses successfully, parse_findings returns immediately — the regex fallback is never applied even when zero entries had a valid severity (so a well-formed object with only invalid severities yields [], not fallback findings). · `spec_eval/audit.py (parse_findings)`
- **[minor]** Cap overrides are coerced with `int()` (numeric strings accepted, non-numeric raises) and a falsy/absent `caps` key falls back to the defaults; caps are resolved once per repo audit and threaded into every pair. · `spec_eval/audit.py (caps_from)`
- **[minor]** File reads use `errors="ignore"` (undecodable bytes silently dropped rather than the file skipped) and only OSError is swallowed; whitespace-only files are treated as empty and excluded. · `spec_eval/audit.py (_read_globs)`
- **[minor]** The severity ranking map (high=3, medium=2, low=1) is an exported module constant used as the membership test for validity, not merely a documented ordering. · `spec_eval/audit.py (SEV)`

### cli — sufficiency 0.86
- **[minor]** The terminal list cap is a fixed 25 entries (UNCOVERED_LIST_CAP), and the orphan list is truncated at the same cap with no '… and N more' overflow line (only the uncovered list gets one). · `spec_eval/cli.py (main — coverage branch / UNCOVERED_LIST_CAP)`
- **[minor]** `diagram` exits non-zero with 'no spec-worthy code files … nothing to diagram' when the module set is empty, even without --write. · `spec_eval/cli.py (main — diagram branch)`
- **[minor]** `context --check` resolves the overview doc as OVERVIEW.md then README.md (same lookup as diagram --write) and names the missing-doc default 'OVERVIEW.md' in messages; the spec says it reads <repo>/OVERVIEW.md only. · `spec_eval/cli.py (_diagram_target / main — context branch)`
- **[minor]** The `--check` delta receipt is stamped with the repo's git SHA (runlog.git_sha) passed into syscontext.diff_receipt. · `spec_eval/cli.py (main — context branch)`
- **[minor]** `generate`'s run-log record also carries `failed` and `stray` counts (spec lists only authored/skipped/flagged), and the generate result contract admits the `failed` and `stray` statuses. · `spec_eval/cli.py (main — generate branch)`
- **[minor]** Single-file scope for `generate` forces authoring layout to 'per-pair', and _file_scope resolves the per-dir folder-spec name via the config's `dir_spec_name` (default '<dir>') only when the co-located <stem>.md does not exist. · `spec_eval/cli.py (_file_scope)`
- **[minor]** `diagram --write/--add-section` validates the target doc and its Architecture section BEFORE synthesis, so a refused write costs no model calls. · `spec_eval/cli.py (main — diagram branch)`
- **[minor]** The coverage result shape also includes `unmodeled` entries of {dir, files} (and orphans/unmodeled are optional keys accessed via .get), which the documented `cov` contract omits. · `spec_eval/cli.py (main — coverage branch)`

### providers — sufficiency 0.87
- **[minor]** The actual value of `DEFAULT_MODEL` (`"anthropic:claude-opus-4-8"`) is never stated — the spec only says the constant exists, so a rebuild would have to guess the default model. · `spec_eval/providers.py (module-level constants)`
- **[minor]** The `claude -p` subprocess is run with a hard 600-second timeout, which will raise on long CLI calls; no timeout is mentioned in the spec. · `spec_eval/providers.py (_gen_claude_code)`
- **[minor]** The bridge treats a JSON envelope that merely lacks a `result` key (not just `is_error`) as an error envelope and raises. · `spec_eval/providers.py (_gen_claude_code)`
- **[minor]** Bridge failure messages embed the child output truncated to 400 characters, preferring stderr over stdout on non-zero exit; the spec specifies neither the content nor the cap. · `spec_eval/providers.py (_gen_claude_code)`
- **[minor]** `_track` unconditionally overwrites `LAST["truncated"]` on every call, so a bridge (or non-truncated) call actively resets a previously-True flag rather than leaving it unset. · `spec_eval/providers.py (_track)`
- **[minor]** OpenAI's truncation check guards against an empty `choices` list (falling back to False), but the return path indexes `choices[0]` unguarded — an empty-choices reply raises IndexError rather than returning "". · `spec_eval/providers.py (gen)`

### syscontext — sufficiency 0.87
- **[minor]** The numeric values of the caps are never given — EVIDENCE_CAP=8, LINE_CAP=160, FILE_CAP=2_000_000 bytes, EP_MODULE_MAIN_CAP=6 — so a rebuild would have to guess every threshold the spec names symbolically. · `syscontext.py`
- **[minor]** The exact display names and full contents of the detection tables are not enumerated (e.g. `RabbitMQ (AMQP)`, `SMTP (email)`, `Celery broker`, `Crypto exchange APIs (ccxt)`, the full SCHEME_SYSTEMS/AWS_SERVICES/SKIP_HOST_SUFFIXES/OTHER_SOURCE_EXT lists), yet those strings are the entry identity the fingerprint and diff key on. · `syscontext.py (SDK_IMPORTS)`
- **[minor]** AWS resolution details are unstated: service ids in the plumbing set (runtime, extensions, util, core, config, auth) are dropped, an id of ≤4 chars is upper-cased while longer ids are title-cased, and an unrecognized `.client("x")` id only yields an entry when `import boto3` was seen earlier in the SAME file. · `syscontext.py (_scan_file)`
- **[minor]** `overview_evidence(ctx_result, ep_result=None)` — the single composer that concatenates the entry-point block THEN the system block (blank-line joined) and returns None when neither observed anything — is absent from the spec. · `syscontext.py (overview_evidence)`
- **[minor]** Under `scope_dir`, scoped entries have `evidence_total` REWRITTEN to the in-scope site count (not the repo-wide total), contradicting the general rule that `evidence_total` always counts all sites. · `syscontext.py (_scoped)`
- **[minor]** The fixed `Not scanned: …` sentence is never quoted, though the spec says the rubric reproduces it verbatim; its exact wording (per-extension counts, the 'language(s) outside the scan's support' clause, and the 'Add the extension(s) to code_ext' remedy) would be reinvented differently. · `syscontext.py (unscanned_note)`
- **[minor]** `diff_receipt` takes an optional `sha` rendered as a ` @ <sha>` suffix, emits `0 system-context changes` for clean, and prints delta lines beneath the re-baseline head as well as the drift head. · `syscontext.py (diff_receipt)`
- **[minor]** Entry-point naming/precedence rules are unspecified: a `__main__.py` short-circuits any `__main__` guard in the same file (never a cli-main), package-main is stamped at line 1 with match `__main__.py`, cli-main/module-main names are the dotted module path with targets `command-line interface` / `run as a script`. · `syscontext.py (_scan_entrypoints_file)`
- **[minor]** Web-app detection is only an assignment form `<var> = <Framework>(` over the list Flask/FastAPI/Sanic/Quart/Bottle/Tornado, with the entry `name` being the assigned variable and `target` the string `<Framework> app object (constructed)`. · `syscontext.py (FRAMEWORK_APP_FACTORIES)`
- **[minor]** CLI-main detection markers are unstated: only `ArgumentParser(`, `add_subparsers(`, `@click.group`, or `@click.command` upgrade a bare guard to `cli-main`. · `syscontext.py (_scan_entrypoints_file)`
- **[minor]** Recognized-but-unsupported source files are counted into `unscanned` BEFORE the test/generated/user-exclusion and illustrative-directory filters, so a `.cpp` under `tests/` still inflates the language-gap note. · `syscontext.py (scan)`
- **[minor]** Google detection specifics: `google.cloud.<svc>` / `from google.cloud import <svc>` / `@google-cloud/<svc>` render as `Google Cloud <Title Cased svc>` (infra), and `from google import genai` maps to `Google Gemini API` (application). · `syscontext.py (_GOOGLE_CLOUD_RE)`

### coverage — sufficiency 0.88
- **[minor]** The full conventional-doc stem list (24 entries including `notice`, `contributing`, `changes`, `testing`, `faq`, `getting-started`/`getting_started`, `security`, `code_of_conduct`, `skill`, `todo`, `authors`, `maintainers`, `install`, `upgrading`, `agent`, `cursorrules`, `copilot-instructions`, `llms`) and the case-insensitive stem comparison are not enumerated — the spec gives only examples plus an ellipsis. · `spec_eval/coverage.py (CONVENTIONAL_DOC_STEMS)`
- **[minor]** `dir_spec_path` resolution rules are unspecified: the `<dir>` sentinel means the containing directory's own basename, any other value is used verbatim as the filename stem, and a repo-root file falls back to the repo directory name. · `spec_eval/coverage.py (dir_spec_path)`
- **[minor]** Unmodeled markdown at the repo root is grouped under the literal key `"."` rather than a directory name. · `spec_eval/coverage.py (unmodeled_markdown)`
- **[minor]** Report rendering details are unstated: the headline percent is printed with zero decimals (`{pct:.0f}%`) even though `pct` carries one, the "Excluded … by class" section is emitted unconditionally (even when empty), and unmodeled groups append `…` when the file count exceeds the 3-file sample. · `spec_eval/coverage.py (format_report)`
- **[minor]** Exact PRUNE_DIRS membership is elided in the spec (`venv`, `env`, `.mypy_cache`, `.pytest_cache`, `.ruff_cache`, `.tox`, `htmlcov`, `.eggs`, `.idea`, `.vscode`, `jspm_packages`, `thirdparty`), and the prune list differs from the `generated` exclusion tier (e.g. `formal` prunes nothing but marks generated). · `spec_eval/coverage.py (PRUNE_DIRS)`
- **[minor]** `infer_pairs` labels a pair with the code file's basename stem only (so same-stem files in different directories yield duplicate labels), and it ignores both configured `pairs` and the per-dir layout — only same-stem siblings are inferred. · `spec_eval/coverage.py (infer_pairs)`
- **[minor]** `uncovered` is computed as `spec_worthy - covered` using the unintersected covered set, and pair-glob matches can add files outside the candidate/extension universe to `covered` before intersection. · `spec_eval/coverage.py (coverage)`

### sufficiency — sufficiency 0.88
- **[minor]** The skip result's explanation string has a specific format — `no files matched (code=<nc>, docs=<nd>)` embedding both matched-file counts — which the spec describes only as 'an explanation string'. · `spec_eval/sufficiency.py (sufficiency_pair)`
- **[minor]** The exact user-message layout sent to the model is unspecified: a `# Sufficiency review: {label}` heading, a `## Code` section wrapping the concatenated code in a bare triple-backtick fence, then an unfenced `## Spec` section with the doc text. · `spec_eval/sufficiency.py (sufficiency_pair)`
- **[minor]** `sufficiency_pair` accepts optional per-call `code_cap`/`doc_cap` override arguments that fall back to `audit.CODE_CAP`/`audit.DOC_CAP` when None, while the repo-level entry point derives them via `audit.caps_from(config)`. · `spec_eval/sufficiency.py (sufficiency_pair, sufficiency_repo)`
- **[minor]** A pair missing the `code` or `docs` key entirely is tolerated (defaults to an empty glob list, yielding 0 matches and the skip path) rather than raising. · `spec_eval/sufficiency.py (sufficiency_pair)`
- **[minor]** No validation or clamping is performed on model output — the score is passed through `float()` unbounded (so values outside [0,1] survive) and `severity` is only lowercased, not checked against the major/minor vocabulary. · `spec_eval/sufficiency.py (sufficiency_pair)`
- **[minor]** `config.get("pairs") or infer_pairs(...)` means an empty or otherwise falsy `pairs` value also triggers inference, not just an absent key. · `spec_eval/sufficiency.py (sufficiency_repo)`
- **[minor]** A `code_ref` that is empty/falsy is dropped by the same guard as `"null"`, and the spec does not state that the `"null"` string check is case-insensitive. · `spec_eval/sufficiency.py (sufficiency_pair)`
- **[minor]** Pairs are evaluated strictly sequentially in a list comprehension (no concurrency, and one pair's model call cannot be skipped or short-circuited by another). · `spec_eval/sufficiency.py (sufficiency_repo)`

### runlog — sufficiency 0.92
- **[minor]** The SHA lookup is a separately callable public helper `git_sha(repo)` returning the short hash string or None; the spec describes only the inline resolution behavior, not this standalone function/signature. · `spec_eval/runlog.py (git_sha)`
- **[minor]** The subprocess return code is never checked — the result is derived purely from stripped stdout (empty stdout coerces to None) and stderr is captured then silently discarded, so a failing-but-chatty git still yields whatever it printed on stdout. · `spec_eval/runlog.py (git_sha)`
- **[minor]** Serialization uses `json.dumps` with defaults, so non-JSON-serializable values in `stats` raise (the write is unguarded, unlike the git failure path) and non-ASCII characters are escaped. · `spec_eval/runlog.py (append_run)`

### rubric — sufficiency 0.93
- **[minor]** The module docstring's self-audit linkage — that `rubric.md` sitting beside the module IS this module's own spec and is guarded by spec-eval's self-audit — is not stated in the spec, which only documents the SKILL.md mirror and the sync test. · `spec_eval/rubric.py (module docstring)`
- **[minor]** The rubric is a second-person LLM prompt string (persona framing "You are a careful technical reviewer...", imperative instructions, trailing literal JSON schema example) rather than structured data; a rebuild could plausibly emit the same rules as a dict/enum and break the phrase-level sync test. · `spec_eval/rubric.py (DRIFT_RUBRIC)`
