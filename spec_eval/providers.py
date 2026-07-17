"""Portable model providers — anthropic / openai / google (env-keyed) plus the `claude-code` bridge (the local
Claude Code CLI: your Claude subscription, NO API key). Usage-tracked. No hardcoded paths.

Truncation transparency: every API reply carries a stop/finish reason; when it says the reply hit `max_tokens`,
that fact is recorded (`LAST["truncated"]` for the call just made, `USAGE["truncated"]` as a tally) so callers
can flag a partial view instead of passing it off as complete. The bridge exposes no stop reason, so bridge
calls never set the flag."""
import os

DEFAULT_MODEL = "anthropic:claude-opus-4-8"   # THE single default model; the CLI's --model defaults read this
_clients = {}
USAGE = {"in": 0, "out": 0, "calls": 0, "truncated": 0}   # exact token + call tallies; the tool reports usage, never a dollar figure
LAST = {"truncated": False}   # the call JUST made (calls are sequential); read it right after gen() returns


def load_env(path):
    """Minimal .env loader (KEY=VALUE), non-overriding. Safe if the file is absent."""
    if not path or not os.path.exists(path):
        return
    for line in open(path):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def parse_model(spec):
    """'anthropic:claude-opus-4-8' → (anthropic, claude-opus-4-8); bare names get a sensible default provider.
    'claude-code' → the Claude Code CLI bridge ('claude-code:<name>' passes <name> to the CLI's --model)."""
    if spec == "claude-code":
        return "claude-code", ""                               # bridge, using the CLI's own default model
    if ":" in spec:
        p, m = spec.split(":", 1)
        return p, m
    if spec.startswith("gpt"):
        return "openai", spec
    if spec.startswith("gemini"):
        return "google", spec
    return "anthropic", spec


def _track(u_in, u_out, truncated=False):
    """Record one call's token usage and whether its reply was cut off at the token cap (None-safe)."""
    USAGE["in"] += u_in or 0
    USAGE["out"] += u_out or 0
    USAGE["calls"] += 1
    USAGE["truncated"] += 1 if truncated else 0
    LAST["truncated"] = bool(truncated)


def _gen_claude_code(model, system, user):
    """Bridge to the Claude Code CLI (`claude -p`): runs on the CLI's own login — a Claude subscription — so NO
    API key is needed. ANTHROPIC_API_KEY is stripped from the child environment so a stray key (e.g. auto-loaded
    from a .env) can never silently switch billing from the subscription to the paid API. Reads the CLI's
    `--output-format json` envelope from stdout only (stderr may carry warnings); token counts are exact, from
    the envelope's `usage`. `max_tokens` is not passed (the CLI has no such flag), and the envelope exposes no
    stop reason — so bridge calls can never flag reply truncation."""
    import json
    import shutil
    import subprocess
    exe = shutil.which("claude")
    if not exe:
        raise RuntimeError("model 'claude-code' needs the Claude Code CLI on PATH — install it and log in once, "
                           "or use an API-key provider (anthropic: / openai: / google:)")
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    cmd = [exe, "-p", "--output-format", "json", "--system-prompt", system]
    if model:
        cmd += ["--model", model]
    r = subprocess.run(cmd, input=user, capture_output=True, text=True, env=env, timeout=600)
    if r.returncode != 0:
        raise RuntimeError(f"`claude -p` failed (exit {r.returncode}): {(r.stderr or r.stdout).strip()[:400]}")
    d = json.loads(r.stdout)                                   # {"result": text, "usage": {...}, "is_error": bool, ...}
    if d.get("is_error") or "result" not in d:
        raise RuntimeError(f"`claude -p` returned an error envelope: {r.stdout[:400]}")
    u = d.get("usage") or {}
    u_in = ((u.get("input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0)
            + (u.get("cache_read_input_tokens") or 0))         # the CLI reports cached input separately; sum = tokens actually processed
    _track(u_in, u.get("output_tokens"))
    return d.get("result") or ""


def gen(model_spec, system, user, max_tokens=1200):
    prov, model = parse_model(model_spec)
    if prov == "claude-code":
        return _gen_claude_code(model, system, user)
    if prov == "anthropic":
        if "anthropic" not in _clients:
            import anthropic
            _clients["anthropic"] = anthropic.Anthropic()      # reads ANTHROPIC_API_KEY
        r = _clients["anthropic"].messages.create(
            model=model, max_tokens=max_tokens, system=system,
            messages=[{"role": "user", "content": user}])
        _track(r.usage.input_tokens, r.usage.output_tokens,
               truncated=(getattr(r, "stop_reason", None) == "max_tokens"))
        return "".join(b.text for b in r.content if getattr(b, "type", None) == "text")
    if prov == "openai":
        if "openai" not in _clients:
            from openai import OpenAI
            _clients["openai"] = OpenAI()                       # reads OPENAI_API_KEY
        r = _clients["openai"].chat.completions.create(
            model=model, messages=[{"role": "system", "content": system}, {"role": "user", "content": user}])
        _track(r.usage.prompt_tokens, r.usage.completion_tokens,
               truncated=(getattr(r.choices[0], "finish_reason", None) == "length" if r.choices else False))
        return r.choices[0].message.content or ""
    if prov == "google":
        from google import genai
        from google.genai import types
        if "google" not in _clients:
            _clients["google"] = genai.Client()                # reads GOOGLE_API_KEY / GEMINI_API_KEY
        r = _clients["google"].models.generate_content(
            model=model, contents=user,
            config=types.GenerateContentConfig(system_instruction=system, max_output_tokens=max_tokens))
        um = getattr(r, "usage_metadata", None)
        cands = getattr(r, "candidates", None) or []
        fr = getattr(cands[0], "finish_reason", None) if cands else None
        _track(getattr(um, "prompt_token_count", 0), getattr(um, "candidates_token_count", 0),
               truncated="MAX_TOKENS" in (getattr(fr, "name", None) or str(fr or "")))
        return r.text or ""
    raise ValueError(f"unknown provider '{prov}' (use anthropic: / openai: / google: / claude-code)")
