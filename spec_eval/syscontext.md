## 1. Purpose

**In one line:** Deterministically inventory the external systems a repository's code observably talks to, with verifiable evidence per entry.

This module answers the arc42 "context & scope" question — *what does this system talk to?* — from code evidence instead of hand-maintained prose. It scans the repo's code files for four evidence classes and reduces them to a deduplicated inventory of external systems, each row carrying the `file:line` sites that prove it. The inventory feeds the overview layer's System context section and the free `context` CLI command. The governing constraint a reviewer can check: **the same tree always produces the same result — no model call, no API key, no timestamp.**

Scope by design: systems and direction only. Installed-package lists, endpoint schemas, and ownership registers are excluded — they change faster than an overview should, and they already have better homes (lockfiles, contracts, catalogs). A system reachable only through a config file or partner-repo knowledge is invisible to this scan, and the report says so instead of guessing. Rows are evidence of **capability in the code, not proof of runtime traffic** — the boundary note states this on every report.

## 2. Definitions

| Term | Meaning |
|------|---------|
| entry | One observed external system: `{system, kind, direction, via, evidence[], evidence_total}`. Deduplicated by `(system, direction)`. |
| kind | `infra` (datastores, queues, buckets, email), `application` (SaaS APIs, RPC/GraphQL peers), `configured` (an endpoint injected via environment variable — target unknown from this repo), `referenced` (a URL literal — a mention, integration unconfirmed), or `inbound-surface` (a web-framework import: the code exposes an API). |
| direction | `outbound` (this code calls out) or `inbound` (this code is called; callers are not observable from this repo). |
| via | How the evidence was matched: `sdk` (SDK/driver import), `scheme` (connection-string scheme like `postgres://`), `url` (literal HTTP(S) URL), `env` (endpoint-shaped environment variable name), `framework` (web-framework import). An entry may carry several. |
| evidence site | `{file, line, match}` — repo-relative path, 1-based line number, and the matched source line (stripped, capped at `LINE_CAP` chars). At most `EVIDENCE_CAP` sites are kept per entry **per directory** (so per-dir scoping always finds a dir's own sites); `evidence_total` always counts all of them repo-wide. |
| scanned file | A code file (per `code_ext`, default `coverage.DEFAULT_CODE_EXT`) outside `PRUNE_DIRS` whose exclusion tier is not `test`, `generated`, or `user`, and that does not sit under an illustrative directory (`examples`, `samples`, `demo`, …) — example code demonstrates integrations, it doesn't have them. Glue/tooling files ARE scanned — real integrations live in entrypoints and scripts. |
| scope_dir | Optional directory filter for a per-dir overview: only evidence sitting DIRECTLY in that directory counts. |
| result | `{schema, scanner, repo, files_scanned, unscanned, entries[]}` — `schema` is the fingerprint format version (currently 2). |
| scanner (provenance) | `{version, tables_digest}` — the package version plus a stable 16-char hash of ALL detection tables. Identifies the scanner that produced a fingerprint; the drift check compares it FIRST. |
| diff outcome | `clean` (same systems), `drift` (a system added or removed — the only gate-failing outcome), or `rebaseline` (scanner provenance or schema differs, so the two fingerprints are not comparable as code drift). |
| unscanned | `{ext: count}` of recognized source files in languages outside the scan's support (`.cpp`, `.clj`, `.scala`, …) that were NOT walked. Reported wherever the inventory is shown — a repo the scanner can't read must never read as "talks to nothing". |

## 3. Behavior

**Detection.** The tree is walked in sorted order (directories and files), and each scanned file is read once as UTF-8 (decode errors ignored, capped at `FILE_CAP` bytes) and matched line by line — both fixed, so the fingerprint cannot vary with the filesystem or locale. Prose is never evidence: comment-marker lines, Python multi-line triple-quoted blocks (docstrings), `/* … */` block-comment interiors, and trailing `//` / `#` comments are all excluded — a quote-aware stripper keeps markers inside string literals (a glob like `"src/*"`) from being mistaken for comments.

- **SDK / driver imports** — on import-shaped lines only (`import` / `from` / `use` / `pub use` / `extern crate` / C# `using` (incl. `global using`) / `require` / `export … from` / dynamic `import(…)` / the continuation line of a multi-line ESM import, plus the quoted path lines inside Go's multi-line `import ( … )` block; TypeScript `import type` is excluded — erased at runtime), a curated table maps module names to systems (`psycopg2` → PostgreSQL, `kafkajs` → Apache Kafka, `stripe` → Stripe), including JVM dotted-package prefixes (`org.apache.kafka`, `com.stripe`), .NET using-directives (`Npgsql`, `StackExchange.Redis`), Go module paths (`github.com/lib/pq`), Rust crates (`rdkafka`, `lapin`), and Swift packages (`PostgresNIO`, `RediStack`). Token boundaries prevent lookalike hits (`redis_helper`, `./redis`). Abstraction layers whose driver hides inside the library map to honestly-hedged entries — ORMs (`sqlalchemy`, `django.db`, `sequelize`, Hibernate/JPA, EF Core, Exposed, `sqlx`/`diesel`) → `SQL database (engine not resolved)`, gRPC clients → `gRPC peer (target not resolved)`, GraphQL clients → `GraphQL endpoint (not resolved)` — and a co-located literal upgrades the name where one exists (a Django `ENGINE` backend string, a SQLAlchemy DSN via the scheme matcher). Google Cloud and Azure client packages resolve to their named service; AWS resolves per ecosystem — `boto3` client ids, JS v3 (`@aws-sdk/client-*`), Go v2 (`aws-sdk-go-v2/service/*`), Rust (`aws_sdk_*`), Java v1/v2 (`com.amazonaws.services.*` / `software.amazon.awssdk.services.*`), .NET (`using Amazon.*`) — an id outside the display table still yields a title-cased entry (`bedrock-runtime` → `AWS Bedrock Runtime`), falling back to one `AWS (service not resolved)` entry when an SDK is present but no service is named.
- **Web-framework imports** map to an `inbound-surface` entry (`HTTP surface exposed (Flask)`): the code demonstrably exposes an API, and that is ALL the repo can show — its callers are asserted context, not observed.
- **Connection-string schemes** (`postgres://`, `amqps://`, `s3://`, SQLAlchemy dialect forms like `postgresql+asyncpg://`, and Oracle's `jdbc:oracle:thin:@…` subprotocol form) match anywhere in a line; a dialect scheme falls back to its base system (`postgresql+asyncpg` → PostgreSQL).
- **Literal HTTP(S) URLs** yield one `referenced` entry per host — a URL alone proves a mention, not a call, so these rows are demoted below observed integrations and labeled unconfirmed in the report. Hosts on a documentation domain (`example.com`, `w3.org`, `github.com`, `wikipedia.org`, …) are skipped — matched at a domain boundary, so `hooks.mygithub.com` still counts; `api.github.com` is kept. Hostnames without a dot (e.g. `localhost`) never match.
- **Endpoint-shaped environment variables** — on lines mentioning `env` (or Rust's `var(`), an UPPER_SNAKE name ending in `_URL`, `_HOST`, `_ENDPOINT`, `_DSN`, `_BUCKET`, `_QUEUE`, `_TOPIC`, `_BROKER`, `_URI`, `_HOSTNAME`, `_ADDR`, or `_SERVER` — singular or plural (`KAFKA_BROKERS`) — becomes a `configured` entry named after the variable, whether quoted, bare after `process.env.`, or destructured (`const { PAYMENTS_API_URL } = process.env`). **Why:** the variable name is real, observable domain information even though the target it points at is unknown from this repo.

**Reduction.** Findings are merged by `(system, direction)`: `via` values accumulate (sorted), evidence sites accumulate (sorted by file then line, capped at `EVIDENCE_CAP`, full count in `evidence_total`). Entries are ordered by kind (`infra` → `application` → `configured` → `referenced` → `inbound-surface`), then system, then direction. **Why:** stable ordering makes the JSON a diffable fingerprint — a future drift check compares scanner output to scanner output.

**Evidence block (for overview synthesis).** `evidence_block(result, scope_dir=None)` renders the entries as an `## OBSERVED SYSTEM EVIDENCE (system context)` block — one line per system with its first evidence site and remaining-site count — prefixed with the instruction that anything not listed was NOT observed. When nothing was observed (or nothing in `scope_dir`), it returns an empty string, and the overview carries no System context section at all — never an invented one.

**Report.** `format_report` renders the inventory as a markdown table plus a fixed boundary note: rows are derived from this repository's code; inbound callers and partner-system behavior are not observable from this repo; config-file-only systems are not scanned; packages and schemas are out of scope by design.

**Language support.** Detection idioms and curated ecosystems are exercised end-to-end for **Python, JavaScript/TypeScript (incl. `.mjs`/`.cjs`), Java, Kotlin (incl. `.kts`), C#, Go, Rust, Swift, and Ruby**. PHP files are walked and served by the generic matchers (schemes, URLs, env vars) without a curated SDK table yet. **C++ and Clojure are not scanned by default** — their extensions are not in the default `code_ext`, and their comment/import idioms (`#include`, ns-forms) are not yet modeled; other JVM languages (Scala, Groovy) can ride the JVM dotted-package keys only if their extensions are added via `code_ext`. Widening a language is a table/idiom/extension addition, never an architecture change.

**The gap is stated, never silent.** Files with recognized source extensions outside `code_ext` are counted into `unscanned`, and every surface that shows the inventory carries the fixed `Not scanned: …` line — the CLI summary, the report, and the repo-level evidence block (the rubric reproduces it verbatim beneath the overview's table). **Why:** the scan's worst failure shape is a confidently near-empty report on a repo it couldn't read.

**Drift check (`diff` + `spec-eval context --check`).** `diff(baseline, current)` compares two scan results by their `(system, direction)` **key set** — the identity that matters — never by JSON bytes, so an evidence line moving, a second call site, or a file rename is `clean`, not drift. It compares scanner provenance FIRST — `(schema, version, tables_digest)`: any difference yields `rebaseline` (the scanner learned to see more — re-store the baseline; never counts as drift), which is what stops table growth from firing false drift in every consuming repo once baselines are committed. `version` is the catch-all (any released scanner change bumps it); `tables_digest` additionally catches a local table edit made without a version bump. Otherwise an added or removed system is `drift`. `diff_receipt` renders the outcome as named `+`/`-` delta lines in the SPEC-HEALTH click-to-verify style — one line per changed system with an evidence site, never a full-table reprint or an evidence-churn row. The `context --check` command loads the stored `system-context.json` baseline, diffs the fresh scan, prints the receipt, and **exits 1 only on `drift`** (a re-baseline or a clean run exit 0); it never overwrites the baseline — a plain `context` run does that.

**Overview freshness stamp (the second edge).** The drift check verifies two edges. Edge 1 (above) is code → stored fingerprint. Edge 2 is stored fingerprint → the generated `OVERVIEW.md`: when `generate --overview` renders a System context section, it appends an invisible HTML-comment stamp (`fingerprint_digest` — a hash of the observed `(system, direction)` key set) recording the fingerprint the section came from. `context --check` reads that stamp back (`overview_stale`) and prints a ⚠ warning when it no longer matches the current scan — the code's external systems changed but the overview was not regenerated. **Overview staleness warns; it does not fail the gate** (regenerating a doc is a different action from investigating code drift). An overview with no stamp is never flagged.

## 4. Contracts

*Reference — consult when implementing or reviewing a change; skip on a first read for intent.*

Semantic shapes:
- **scan result**: `{schema: int, scanner: {version, tables_digest}, repo: str, files_scanned: int ≥ 0, unscanned: {ext: count}, entries: [entry]}`.
- **entry**: `{system: str, kind: infra|application|configured|referenced|inbound-surface, direction: outbound|inbound, via: [str] sorted, evidence: [{file, line ≥ 1, match ≤ LINE_CAP chars}], evidence_total ≥ len(evidence)}`.
- **diff**: `{outcome: clean|drift|rebaseline, scanner_changed: bool, added: [Δentry], removed: [Δentry]}` where a Δentry is `{system, direction, kind, via, evidence: "file:line"|null}`.

### Invariants (*rules that must always hold*)

| ID | Invariant |
|----|-----------|
| INV-1 | Scanning is deterministic: the same tree and config always produce byte-identical results — no model call, no key, no timestamp. |
| INV-2 | Every entry carries at least one evidence site; there is no way to add an entry without a `file:line`. |
| INV-3 | Files whose exclusion tier is `test`, `generated`, or `user` — and files under illustrative directories (`examples`, `samples`, `demo`, …) — are never scanned; directories in `PRUNE_DIRS` are never walked. |
| INV-4 | Entries are sorted by `(kind order, system, direction)` and evidence by `(file, line)` — the JSON is a stable, diffable fingerprint. |
| INV-5 | At most `EVIDENCE_CAP` evidence sites are stored per entry per directory, and `evidence_total` still counts every observed site — capping is visible, never silent. |
| INV-6 | `evidence_block` returns an empty string when no entry (in scope) exists — an empty scan can never produce a System context section. |
| INV-7 | Recognized source files outside `code_ext` are counted into `unscanned` and surfaced with the fixed `Not scanned:` line in the CLI output, the report, and the repo-level evidence block — a language gap is stated, never silent. |
| INV-8 | Every fingerprint carries `scanner` provenance (version + tables digest); `tables_digest` hashes ALL detection knowledge — every table and every hoisted regex/literal that can change the key set — so a change to any of them moves the digest. |
| INV-9 | `diff` decides identity by the `(system, direction)` key set only; two results differing solely in evidence sites, `via`, counts, or repo name are `clean`. |
| INV-10 | When provenance (`schema`, scanner `version`, or `tables_digest`) differs, `diff` returns `rebaseline` and never `drift`, regardless of how the entry sets differ — so ANY scanner change (a release bumps `version`; a local table edit moves `tables_digest`) is absorbed as a re-baseline, never false drift. |
| INV-11 | `fingerprint_digest` depends only on the observed `(system, direction)` key set; two scans with the same systems produce the same stamp even if evidence sites moved. |
| INV-12 | `overview_stale` returns False when the markdown carries no stamp — an unstamped overview is never flagged stale. |

### Acceptance criteria (*Given / When / Then*)

| ID | Given | When | Then |
|----|-------|------|------|
| AC-1 | a file containing `boto3.client("s3")` | `scan` runs | an `AWS S3` entry (`infra`, `outbound`, via `sdk`) with that file:line as evidence. |
| AC-2 | a file importing `flask` | `scan` runs | an `HTTP surface exposed (Flask)` entry (`inbound-surface`, `inbound`). |
| AC-3 | a URL `https://api.partner.com/v1` in code and `https://example.com/docs` in the same file | `scan` runs | one `HTTP endpoint api.partner.com` entry; no entry for `example.com`. |
| AC-4 | `os.environ["ORDERS_QUEUE_URL"]` | `scan` runs | a `Configured endpoint (ORDERS_QUEUE_URL)` entry (`configured`, via `env`). |
| AC-5 | the same evidence in a `tests/` file only | `scan` runs | no entry — test fixtures are not system context. |
| AC-6 | two files both importing `psycopg2` | `scan` runs | ONE PostgreSQL entry with both evidence sites and `evidence_total` 2. |
| AC-7 | any repo | `scan` runs twice | the two results are identical (deep equality). |
| AC-8 | a result with no entries | `evidence_block` is called | returns `""`. |
| AC-9 | `os.getenv("DATABASE_URL")` (no `environ`) | `scan` runs | a `Configured endpoint (DATABASE_URL)` entry — the `getenv` idiom counts. |
| AC-10 | a `.go` file with `github.com/gin-gonic/gin` inside an `import ( … )` block | `scan` runs | an `HTTP surface exposed (Gin)` entry. |
| AC-11 | `import sqlalchemy` (no DSN literal) | `scan` runs | a `SQL database (engine not resolved)` entry — the abstraction layer is reported hedged, never silently missed. |
| AC-12 | `using Npgsql;` (C#) and `require "redis"` (Ruby) | `scan` runs | a PostgreSQL and a Redis entry — the `using` and parenless-`require` idioms count. |
| AC-13 | a multi-line Python docstring containing `redis://…` and a URL | `scan` runs | no entry — triple-quoted prose is skipped like comments. |
| AC-14 | `examples/demo.py` importing `stripe` | `scan` runs | no entry — illustrative directories are never scanned. |
| AC-15 | a literal URL as a file's only evidence | `scan` runs | the entry's kind is `referenced` — a mention, ordered below observed integrations. |
| AC-16 | a `/* … */` block comment containing an import and a scheme, and a code line with a trailing `//` URL | `scan` runs | no entry from any of them — block interiors and trailing comments are prose. |
| AC-17 | `@aws-sdk/client-s3` (JS), `aws-sdk-go-v2/service/sqs` (Go), `aws_sdk_dynamodb` (Rust), `com.amazonaws.services.sns` (Java), `using Amazon.S3;` (C#) | `scan` runs | each resolves to its named AWS service entry. |
| AC-18 | a multi-line ESM import ending `} from "kafkajs";`, an `export … from`, and a dynamic `import("amqplib")` | `scan` runs | all three count as import evidence; `import type` lines never do. |
| AC-19 | a repo containing `main.cpp` and `core.clj` beside supported code | `scan` runs | `unscanned` counts both, and the report/CLI/evidence block carry the `Not scanned:` line naming the extensions. |
| AC-20 | a baseline, then the same code with an import moved to a different line | `diff` runs | outcome `clean` — the evidence site moved but the system set did not. |
| AC-21 | a baseline with PostgreSQL, then code that drops it and adds Redis | `diff` runs | outcome `drift`; `added` = Redis (with a `file:line`), `removed` = PostgreSQL. |
| AC-22 | a baseline whose `tables_digest` differs from the current scanner | `diff` runs | outcome `rebaseline`, `scanner_changed` true — never `drift`. |
| AC-23 | a stored baseline, then drifted code | `spec-eval context --check` runs | prints the named-delta receipt and exits 1; the baseline file is not overwritten. |
| AC-24 | an overview stamped from a scan, then code that adds a system | `overview_stale(md, fresh_scan)` | returns True — the stamped digest no longer matches the current systems. |
| AC-25 | `generate --overview` on code with observed systems | authoring runs | the written `OVERVIEW.md` ends with a `<!-- system-context-fingerprint: … -->` stamp. |
