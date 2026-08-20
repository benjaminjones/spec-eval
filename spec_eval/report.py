"""Render the drift + sufficiency reports (markdown) — the legible product output.

The "fingerprint" is a MARKDOWN unicode-bar table (diffable, code-searchable, renders in any markdown viewer),
toggled by `include_fingerprint`.
"""
import os
from . import providers


def drift_load(r):
    """High+medium findings that stand. A finding withdrawn by the verification pass stays in the record
    but is not counted — a withdrawal is itself a reviewable claim, so it is shown rather than deleted.

    A `stale` finding is also shown and not counted. It reports an outdated declarative value, not a broken
    guarantee: a value like a default or a threshold defines a term rather than constraining behaviour, so
    there is nothing for the code to violate. Counting it as drift is a category error, and it is the one
    this counter existed to make. Absent class reads as `drift`, so pre-existing records count as before."""
    return sum(1 for f in r["findings"]
               if f["severity"] in ("high", "medium")
               and f.get("class", "drift") != "stale"
               and f.get("verification", {}).get("verdict", "upheld") != "withdrawn")


def not_graded(r):
    """True when the model never produced a verdict for this pair, so `clean` would be a false reading.

    Narrow on purpose: only a REPLY cap with an empty findings list qualifies. An INPUT cap means the
    model graded what it was shown, and a reply cap that still yielded findings produced a verdict that
    may merely be short. `0` and `not graded` are different states and only one is safe to act on."""
    return (not r.get("skipped")
            and not r["findings"]
            and "reply hit the token cap" in (r.get("truncated") or []))


def _bar(v, width=20):
    """Unicode bar for a 0..1 value (full block = filled, light shade = empty)."""
    v = max(0.0, min(1.0, float(v)))
    filled = int(round(v * width))
    return "█" * filled + "░" * (width - filled)


def sufficiency_fingerprint(results):
    """A markdown unicode-bar table of per-pair sufficiency (worst first). Pure text."""
    rs = sorted((r for r in results if r.get("sufficiency") is not None), key=lambda r: r["sufficiency"])
    if not rs:
        return ""
    lines = ["", "## Sufficiency fingerprint  *(at a glance — worst first)*", "",
             "| Pair | Spec completeness | Score |", "|---|---|---|"]
    for r in rs:
        lines.append(f"| `{r['label']}` | `{_bar(r['sufficiency'])}` | {r['sufficiency']:.2f} |")
    return "\n".join(lines) + "\n"


def drift_fingerprint(results):
    """A markdown table of per-pair drift load (✓ clean / count). Pure text."""
    rs = [r for r in results if not r.get("skipped")]
    if not rs:
        return ""
    lines = ["", "### Drift fingerprint", "", "| Pair | High+med findings |", "|---|---|"]
    for r in rs:
        n = drift_load(r)
        cell = "⚠ not graded" if not_graded(r) else ("✓ clean" if n == 0 else f"⚠ {n}")
        lines.append(f"| `{r['label']}` | {cell} |")
    return "\n".join(lines) + "\n"


def _evidence_block(evidence):
    """The quoted code/doc snippets a finding rests on, rendered as an indented fenced block.

    The rubric asks for `evidence` precisely so a reader can check a finding instead of taking it on
    trust, and the FAQ tells them to read it — so it has to reach the report. Fenced because the content
    is source, and indented four spaces so a multi-line quote stays inside its list item instead of
    ending the list. A fence inside the evidence would close ours early, so backticks are stripped."""
    body = "\n".join("    " + ln for ln in str(evidence).replace("```", "'''").split("\n"))
    return "    - *evidence:*\n\n    ```\n" + body + "\n    ```\n"


def write_markdown(results, repo, model, out_path, include_fingerprint=True):
    name = os.path.basename(os.path.abspath(repo))
    total = sum(drift_load(r) for r in results if not r.get("skipped"))
    audited = [r for r in results if not r.get("skipped")]
    graded = [r for r in audited if not not_graded(r)]
    # An ungraded pair is excluded from the denominator rather than counted as a clean one. The
    # "(N attempted)" clause appears only when the two differ, so an ordinary run reads as before.
    denom = (f"{len(graded)} graded pair(s) ({len(audited)} attempted)"
             if len(graded) != len(audited) else f"{len(audited)} audited pair(s)")
    lines = [f"# Drift report — `{name}`",
             f"detector: `{model}` · {len(audited)}/{len(results)} pairs audited · "
             f"{providers.USAGE['calls']} model call(s)", "",
             f"**{total} high/medium drift finding(s) across {denom}.**", ""]
    for r in results:
        if r.get("skipped"):
            lines += [f"## {r['label']} — _skipped: {r['skipped']}_", ""]
            continue
        n = drift_load(r)
        verdict = "⚠ not graded" if not_graded(r) else ("✓ clean" if n == 0 else f"⚠ {n} drift")
        lines.append(f"## {r['label']} — {verdict}")
        if r.get("truncated"):
            lines.append(f"- ⚠ *partial view ({'; '.join(r['truncated'])}) — findings may be incomplete*")
        for f in r["findings"]:
            v = f.get("verification") or {}
            gone = v.get("verdict") == "withdrawn"
            ref = f" (`{f.get('code_ref') or '?'}` vs `{f.get('doc_ref') or '?'}`)" if f.get("code_ref") or f.get("doc_ref") else ""
            # A stale finding carries its class in the label, so a reader triaging the report can see at a
            # glance that it is an outdated value rather than a violated guarantee — different fix, different
            # urgency. Severity is kept beside it: it still says how misleading the stale value is.
            tag = f"stale · {f['severity']}" if f.get("class") == "stale" else f["severity"]
            mark = f"~~**[{tag}]** {f['summary']}~~" if gone else f"**[{tag}]** {f['summary']}"
            lines.append(f"- {mark}{ref}")
            if gone:
                lines.append(f"    - *withdrawn on verification — {v.get('ground')}:* {v.get('why', '')}")
                if v.get("doc_quote"):
                    lines.append(f"    - *the doc says:* “{v['doc_quote']}”")
                continue          # a withdrawn finding keeps its claim and its ground, not its fix
            if f.get("evidence"):
                lines.append(_evidence_block(f["evidence"]))
            if f.get("suggestion"):
                lines.append(f"    - *fix:* {f['suggestion']}")
        lines.append("")
    body = "\n".join(lines)
    if include_fingerprint:
        body += drift_fingerprint(results)
    open(out_path, "w").write(body)
    return total


def write_sufficiency_markdown(results, repo, model, out_path, include_fingerprint=True):
    name = os.path.basename(os.path.abspath(repo))
    scored = [r for r in results if r.get("sufficiency") is not None]
    avg = sum(r["sufficiency"] for r in scored) / len(scored) if scored else 0
    head = [f"# Spec sufficiency — `{name}`",
            f"detector: `{model}` · {len(scored)}/{len(results)} pairs scored · "
            f"{providers.USAGE['calls']} model call(s)", "",
            f"**Average sufficiency {avg:.2f}** — how completely does the spec capture the code's behavior? "
            f"(1.0 = no gaps found; gaps = behavior in the code but not the spec. An indicator, not a guarantee.)", ""]
    # Fingerprint FIRST — the at-a-glance summary, so a reader sees the shape before the per-module detail.
    summary = sufficiency_fingerprint(results) if include_fingerprint else ""
    detail = ["## Per-module gaps  *(worst first)*", ""]
    for r in sorted(results, key=lambda x: (x.get("sufficiency") is None, x.get("sufficiency") or 0)):
        if r.get("skipped"):
            detail += [f"### {r['label']} — _skipped: {r['skipped']}_", ""]
            continue
        if r.get("sufficiency") is None:
            detail.append(f"### {r['label']} — not scored (unparseable model reply)")
        else:
            detail.append(f"### {r['label']} — sufficiency {r['sufficiency']:.2f}")
        if r.get("truncated"):
            detail.append(f"- ⚠ *partial view ({'; '.join(r['truncated'])})*")
        for g in r["gaps"]:
            ref = f" · `{g['code_ref']}`" if g.get("code_ref") else ""   # '·' — em dashes occur in gap prose; the dot splits unambiguously
            detail.append(f"- **[{g['severity']}]** {g['missing']}{ref}")
        detail.append("")
    body = "\n".join(head) + summary + "\n" + "\n".join(detail)
    open(out_path, "w").write(body)
    return avg
