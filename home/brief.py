"""Daily brief generator — the longform 'morning read' for Apple Notes.

`cos brief` assembles a longform digest from the local contracts + your focus +
recent open questions + AI signals, writes it under overview-brief/outputs/, and
pushes it to Apple Notes (read-anywhere on phone/iPad). Deterministic and offline:
it reuses the LLM-written tile_summaries already in the contracts but does not
itself call a model. Nothing writes the vault.

CLI:  python -m home brief            # build + push to Apple Notes
      python -m home brief --no-push  # build + write file only
"""

from __future__ import annotations

import html as _html
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from . import data

NOTE_TITLE = "cos · daily brief"


def _recent_open_questions(root: Path, limit: int = 6) -> list[dict[str, Any]]:
    """Recent open questions, journal-sourced first. Prefers the fresh local scan
    (coherence.json, already journal-first + recent); falls back to the Cowork
    open-questions.json contract."""
    c = data._read_json(root / "knowledge-base" / "data" / "coherence.json")
    items = ((c or {}).get("open_questions") or {}).get("items")
    if items:
        return items[:limit]
    try:
        d = json.loads((root / "knowledge-base" / "data" / "open-questions.json").read_text("utf-8"))
    except Exception:
        return []
    items = [q for q in d.get("open", []) if isinstance(q, dict)]
    items.sort(key=lambda q: q.get("raised", ""), reverse=True)
    journal = [q for q in items if "/journal/" in (q.get("path") or "")]
    ordered = journal + [q for q in items if q not in journal]
    return ordered[:limit]


def _signals_full(root: Path) -> list[dict[str, Any]]:
    try:
        d = json.loads((root / "overview-brief" / "data" / "ai-news.json").read_text("utf-8"))
        return d.get("items", []) or []
    except Exception:
        return []


def build_markdown(root: Optional[Path] = None, vault: Optional[Path] = None) -> str:
    root = root or data.cos_root()
    d = data.load_all(root)
    focus, fin, tasks = d["focus"], d["finances"], d["tasks"]
    learn, kw, coh = d["learning"], d["knowledge_work"], d["coherence"]
    today = datetime.now().strftime("%A, %d %B %Y")

    L: list[str] = [f"# cos · daily brief — {today}", ""]

    L.append("## Focus")
    L.append(focus["headline"])
    L += [f"- {b}" for b in focus["bullets"]]
    L.append("")

    L.append("## Finances")
    if fin.get("runway_months") is not None:
        L.append(f"- Runway: {fin['runway_months']} months (net ${fin.get('net_monthly', 0):,.0f}/mo)")
    for g in fin.get("goals", []):
        rem = g.get("amount_remaining")
        rem_txt = f" — ${rem:,.0f} to go" if isinstance(rem, (int, float)) else ""
        L.append(f"- {g.get('name')}: {g.get('pct_complete', 0)}%{rem_txt} (by {g.get('by', '?')})")
    usr = fin.get("us_return", {})
    if usr.get("months_remaining") is not None:
        L.append(f"- US return: {usr['months_remaining']} months away (target {usr.get('target_date', '?')})")
    L.append("")

    L.append("## Today / upcoming")
    if tasks["calendar_unavailable"]:
        L.append("- No events (calendar connector off)")
    else:
        for e in tasks["events"][:6]:
            L.append(f"- {e.get('title', e) if isinstance(e, dict) else e}")
        if not tasks["events"]:
            L.append("- No events scheduled")
    L.append(f"- Tasks due this week: {len(tasks['tasks_due'])}")
    L.append("")

    L.append("## Knowledge work")
    L.append(f"- Inbox: {kw['inbox_count']} unprocessed")
    L.append(f"- Workbench: {kw['workbench_count']} in progress")
    L.append(f"- Journal open questions: {kw['journal_questions']}")
    if kw.get("tile_summary"):
        L += ["", kw["tile_summary"]]
    L.append("")

    oq = _recent_open_questions(root)
    if oq:
        L.append("## Open questions (recent)")
        for q in oq:
            src = (q.get("path") or "").split("/")[-1].replace(".md", "")
            L.append(f"- \"{q.get('question', '?')}\"" + (f" — {src}" if src else ""))
        L.append("")

    L.append("## Learning")
    L.append(f"- Backlog: {learn['backlog_count']} ({learn['unread']} unread, {learn['to_study']} to-study)")
    for it in learn["items"][:3]:
        L.append(f"- {it['title']} [{it['status']}]")
    L.append("")

    sig = _signals_full(root)
    if sig:
        L.append("## AI signals (Grok)")
        for s in sig[:5]:
            line = f"- {s.get('title', '?')}"
            if s.get("date"):
                line += f" ({s['date']})"
            L.append(line)
            if s.get("summary"):
                L.append(f"  {s['summary']}")
        L.append("")

    flags = []
    if (kw.get("inbox_count") or 0) >= 10:
        flags.append("Inbox clearing slower than intake — a synthesis pass would convert the stream into durable notes.")
    if not coh["scan_ok"]:
        flags.append("Vault coherence scan not yet built / runner can't see the vault — stale-note detection is blind.")
    if flags:
        L.append("## Flags")
        L += [f"- {f}" for f in flags]
        L.append("")

    L.append("---")
    L.append(f"generated {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M %Z')} · cos home")
    return "\n".join(L)


def markdown_to_notes_html(md: str) -> str:
    """Light markdown→HTML for Apple Notes (headings, bullets, paragraphs)."""
    out: list[str] = []
    in_list = False

    def close_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    for raw in md.splitlines():
        line = raw.rstrip()
        if not line:
            close_list()
            continue
        if line.startswith("# "):
            close_list()
            out.append(f"<h1>{_html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            close_list()
            out.append(f"<h2>{_html.escape(line[3:])}</h2>")
        elif line.startswith("- "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{_html.escape(line[2:])}</li>")
        elif line == "---":
            close_list()
            out.append("<hr>")
        else:
            close_list()
            out.append(f"<div>{_html.escape(line)}</div>")
    close_list()
    return "<html><body>" + "\n".join(out) + "</body></html>"


def write_output(md: str, root: Optional[Path] = None) -> Path:
    """Write to overview-brief/outputs/ (a generated slot — never the vault)."""
    root = root or data.cos_root()
    out_dir = root / "overview-brief" / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"daily-brief-{datetime.now().strftime('%Y-%m-%d')}.md"
    path.write_text(md + "\n", encoding="utf-8")
    return path


def push_to_apple_notes(html_body: str, title: str = NOTE_TITLE) -> str:
    """Upsert a single Apple Notes note named `title` (macOS only; graceful elsewhere)."""
    tmp = Path(tempfile.gettempdir()) / "cos-daily-brief.html"
    tmp.write_text(html_body, encoding="utf-8")
    osa = shutil.which("osascript")
    if not osa:
        return f"(no osascript — wrote {tmp}; run on macOS to push to Notes)"
    script = (
        f'set p to POSIX file "{tmp}"\n'
        'set theBody to (read p as «class utf8»)\n'
        f'set theName to "{title}"\n'
        'tell application "Notes"\n'
        '  set found to (notes whose name is theName)\n'
        '  if (count of found) > 0 then\n'
        '    set body of item 1 of found to theBody\n'
        '  else\n'
        '    make new note with properties {name:theName, body:theBody}\n'
        '  end if\n'
        'end tell'
    )
    try:
        subprocess.run([osa, "-e", script], check=True, capture_output=True, text=True, timeout=30)
        return f"pushed to Apple Notes: {title}"
    except Exception as e:  # noqa: BLE001
        return f"Notes push failed: {e}"


def main_cli(argv: Optional[list[str]] = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    push = "--no-push" not in argv
    do_scan = "--no-scan" not in argv
    root = data.cos_root()
    if do_scan:  # refresh coherence locally first so the brief + home reflect the vault
        try:
            from . import scan
            s = scan.run(root, data.vault_root(root))
            if s.get("scan_ok"):
                print(f"coherence: {s['total_notes']} notes · stale {s['stale']['count']} · "
                      f"orphans {s['orphans']['count']}")
        except Exception as e:  # noqa: BLE001
            print(f"(scan skipped: {e})")
    md = build_markdown(root, data.vault_root(root))
    out = write_output(md, root)
    print(f"brief written: {out}")
    if push:
        print(push_to_apple_notes(markdown_to_notes_html(md)))
    else:
        print("(--no-push: skipped Apple Notes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main_cli())
