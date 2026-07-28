# System context — `spec-eval`
**3 external system(s) observed** across 12 scanned code file(s). Deterministic scan — no AI, no key.

| External system | Kind | Direction | Via | Evidence |
|---|---|---|---|---|
| Anthropic API | application | outbound | sdk | `spec_eval/providers.py:88` |
| Google Gemini API | application | outbound | sdk | `spec_eval/providers.py:106` +1 more |
| OpenAI API | application | outbound | sdk | `spec_eval/providers.py:98` |

> Derived from this repository's code — rows are evidence of capability in the code, not proof of runtime traffic, and a `referenced` row is a URL mention only (integration unconfirmed). Inbound callers and partner-system behavior are not observable from this repo — confirm asserted context with the owning teams. Systems reached only through config files are not scanned. Installed packages and endpoint schemas are out of scope by design.
