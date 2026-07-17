"""Render the drift + sufficiency reports (markdown) — the legible product output.

The "fingerprint" is a MARKDOWN unicode-bar table (diffable, code-searchable, renders in any markdown viewer),
toggled by `include_fingerprint`.
"""
import os
from . import providers


def drift_load(r):
    return sum(1 for f in r["findings"] if f["severity"] in ("high", "medium"))


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
        lines.append(f"| `{r['label']}` | {'✓ clean' if n == 0 else f'⚠ {n}'} |")
    return "\n".join(lines) + "\n"


def write_markdown(results, repo, model, out_path, include_fingerprint=True):
    name = os.path.basename(os.path.abspath(repo))
    total = sum(drift_load(r) for r in results if not r.get("skipped"))
    audited = [r for r in results if not r.get("skipped")]
    lines = [f"# Drift report — `{name}`",
             f"detector: `{model}` · {len(audited)}/{len(results)} pairs audited · "
             f"{providers.USAGE['calls']} model call(s)", "",
             f"**{total} high/medium drift finding(s) across {len(audited)} audited pair(s).**", ""]
    for r in results:
        if r.get("skipped"):
            lines += [f"## {r['label']} — _skipped: {r['skipped']}_", ""]
            continue
        n = drift_load(r)
        lines.append(f"## {r['label']} — {'✓ clean' if n == 0 else f'⚠ {n} drift'}")
        if r.get("truncated"):
            lines.append(f"- ⚠ *partial view ({'; '.join(r['truncated'])}) — findings may be incomplete*")
        for f in r["findings"]:
            ref = f" (`{f.get('code_ref') or '?'}` vs `{f.get('doc_ref') or '?'}`)" if f.get("code_ref") or f.get("doc_ref") else ""
            lines.append(f"- **[{f['severity']}]** {f['summary']}{ref}")
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
