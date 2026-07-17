## 1. Purpose

This module lets the rest of the system ask a large-language model a question and get back text, without caring which vendor (Anthropic, OpenAI, or Google) actually answers. Callers name a model with a portable string like `"anthropic:claude-opus-4"` or a bare `"gpt-4o"`, and the module routes the request to the right vendor SDK and tracks how many tokens were consumed. Callers can also name **`claude-code`**, which routes through the **local Claude Code CLI** (the user's Claude subscription) instead of a vendor SDK — no API key at all.

The governing constraint a reviewer can check: **nothing about any specific machine, file path, or account is baked into the code — every credential comes from the environment (or, for the `claude-code` bridge, from the CLI's own login)**, so the same module runs unchanged on any machine that has the right API keys set or the CLI logged in. If a caller names a vendor the module does not know, the call fails loudly rather than guessing.

## 2. Definitions

| Term | Meaning (bounds / units) |
|------|--------------------------|
| Provider | One of `anthropic`, `openai`, `google`, or `claude-code` (the Claude Code CLI bridge). Any other value is an error. |
| Model spec | Portable string: either `provider:model` or a bare model name that maps to a default provider. Bare `claude-code` maps to the bridge with the CLI's own default model; `claude-code:<name>` passes `<name>` to the CLI's `--model`. |
| System / user | The two prompt segments sent to the model: instructions (`system`) and the question (`user`). |
| `max_tokens` | Upper bound on generated output tokens. Default 1200. Applies to Anthropic and Google; not passed to OpenAI or the `claude-code` bridge. |
| USAGE | Running totals across all calls: `in` (input tokens), `out` (output tokens), `calls` (count), `truncated` (replies cut off at the token cap). Non-negative integers. |
| LAST | Flags for the call just made: `{truncated: bool}` — meaningful when read immediately after `gen` returns (calls are sequential). |

## 3. Behavior

**Model-spec resolution.** A spec containing `:` is split into `(provider, model)`. A bare name is mapped: names beginning `gpt` → `openai`, names beginning `gemini` → `google`, everything else → `anthropic`.
> Reconstructed intent (confidence: high) — inferred from the code: the default-to-anthropic fallback treats Anthropic model names as the "unprefixed" default.

**Generation.** Given a model spec, a system prompt, and a user prompt, the module dispatches to the matching vendor SDK and returns the model's text reply as a plain string:
- Anthropic: calls the messages API with `system`, the user message, and `max_tokens`; concatenates all text blocks of the reply.
- OpenAI: calls chat completions with system+user messages; returns the first choice's content (empty string if null). **Why:** OpenAI content can be `None`; the module normalizes to `""`.
- Google: calls `generate_content` with the user text, `system_instruction`, and `max_output_tokens`; returns `r.text` (or `""`).
- Claude Code bridge: shells out to `claude -p --output-format json --system-prompt <system>` with the user prompt on **stdin**, parses the JSON envelope from **stdout only** (stderr may carry warnings), and returns its `result`. Fails loudly if the CLI is not on PATH, exits non-zero, or returns an error envelope. **Why:** the CLI runs on its own login (a Claude subscription), so this path needs no API key.

**Client caching.** Each vendor client is constructed lazily on first use and reused for subsequent calls. **Why:** avoids re-importing SDKs and re-initializing clients per call. (The Google client is cached; its SDK types are imported per call.)

**Credentials.** Clients are constructed with no arguments, so each SDK reads its own environment variable: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, and `GOOGLE_API_KEY`/`GEMINI_API_KEY` respectively. No keys or paths are passed in code. The `claude-code` bridge uses **no** environment key — it runs on the CLI's own login — and `ANTHROPIC_API_KEY` is **removed from its child environment**, so a key auto-loaded from a `.env` can never silently switch the bridge from subscription billing to the paid API.

**Environment loading.** `load_env(path)` optionally reads a `KEY=VALUE` file to populate the environment. It is non-overriding (existing env vars win), tolerant of comments (`#`) and blank lines, strips surrounding quotes from values, and does nothing if the path is missing or empty. **Why:** convenience for local runs without clobbering an already-configured environment.

**Usage tracking.** Every successful call adds its input and output token counts to `USAGE` and increments `calls`. Token counts are read from each vendor's usage metadata and treated as 0 when absent. For the `claude-code` bridge, the input count is the sum of the envelope's plain and cached input tokens — the tokens actually processed — since the CLI reports cached input separately. **Why:** token totals are exact and reported as-is; the tool deliberately does not translate them into a dollar figure — prices vary by model and change over time, so pricing belongs outside the tool.

**Truncation detection.** Every reply's stop/finish reason is checked: when the vendor reports the reply was cut off at the token cap (anthropic `max_tokens`, openai `length`, google `MAX_TOKENS`), the call is recorded as truncated — `LAST["truncated"]` for the call just made, `USAGE["truncated"]` as a running tally. The bridge's envelope exposes no stop reason, so bridge calls never set the flag. **Why:** a capped reply can pass off a partial answer as complete; callers read the flag to surface the partial view instead of staying silent.

**Error semantics.** An unrecognized provider raises `ValueError` naming the offending provider and listing the valid prefixes.

## 4. Contracts

Semantic shapes:
- `DEFAULT_MODEL` — the module constant holding the default `provider:model` string; the CLI's `--model` defaults read it (one source, not a per-subcommand literal).
- `gen(...) -> text` — the model's reply as a string, never `None` (null replies become `""`).
- `parse_model(spec) -> (provider, model)` — provider is one of the four known providers (`anthropic`, `openai`, `google`, `claude-code`) or an arbitrary string taken verbatim from before the `:`.
- `USAGE -> {in, out, calls, truncated}` — cumulative non-negative counters.
- `LAST -> {truncated: bool}` — per-call flag; read immediately after `gen` returns.

### Invariants (*rules that must always hold*)

| ID | Invariant |
|----|-----------|
| INV-1 | `gen` with an unknown provider raises `ValueError`. |
| INV-2 | `gen` never returns `None`; a null vendor reply is coerced to `""`. |
| INV-3 | Token counts added to `USAGE` are never `None` — a missing count is recorded as 0. |
| INV-4 | `load_env` never overwrites an already-set environment variable. |
| INV-5 | The `claude-code` child process never receives `ANTHROPIC_API_KEY` in its environment. |

### Acceptance criteria (*Given / When / Then*)

| ID | Given | When | Then |
|----|-------|------|------|
| AC-1 | spec `"anthropic:claude-opus-4"` | `parse_model` | returns `("anthropic", "claude-opus-4")` |
| AC-2 | bare spec `"gpt-4o"` | `parse_model` | returns `("openai", "gpt-4o")` |
| AC-3 | bare spec `"gemini-2.0-flash"` | `parse_model` | returns `("google", "gemini-2.0-flash")` |
| AC-4 | bare spec `"claude-3"` | `parse_model` | returns `("anthropic", "claude-3")` |
| AC-5 | spec `"grok:x"` | `gen(...)` | raises `ValueError` mentioning `grok` |
| AC-11 | bare spec `"claude-code"` | `parse_model` | returns `("claude-code", "")` |
| AC-12 | spec `"claude-code:haiku"` | `parse_model` | returns `("claude-code", "haiku")` |
| AC-13 | no `claude` executable on PATH | `gen("claude-code", ...)` | raises `RuntimeError` naming the missing CLI |
| AC-7 | env var `FOO` already `"a"`, file line `FOO=b` | `load_env(path)` | `FOO` stays `"a"` |
| AC-8 | file line `BAR="x"` with a missing `BAR` env var | `load_env(path)` | `BAR` becomes `x` (quotes stripped) |
| AC-9 | `load_env(None)` or a nonexistent path | called | returns without error, no env changes |
| AC-10 | any successful `gen` call | after return | `USAGE.calls` increased by exactly 1 |
| AC-14 | a reply whose stop/finish reason is the vendor's token-cap marker | after return | `LAST.truncated` is True and `USAGE.truncated` increased by 1 |
