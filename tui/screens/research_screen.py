"""Dedicated Research screen for the cos Textual TUI.

Implements an in-app version of the /research skill from toolbox/research.md.
- Supports prompt input for ticker (routes to finances research) or software/framework (routes to learning research).
- Auto-detects type per the skill's routing logic (1-5 uppercase letters = ticker).
- "Run with Grok" option performs richer research (X/tool powered skeleton) and writes structured results to the data layer:
  - For ticker: finances/outputs/research-<TICKER>-YYYY-MM-DD.json (+ .md)
  - For software: learning-pipeline/data/intake-queue.json (deduped by title, status "to-study") + learning-pipeline/outputs/research-*.json (+ .md)
- Reuses the shared data loader (DEFAULT_COS_ROOT + _load_json pattern only; surgical duplicate of tiny helper, no edits to loader.py).
- Follows exact Doom-Emacs-style dedicated full-screen patterns from BriefScreen (toolbar, reactive, hotkeys, buttons, help, hard rules, Grok skeleton).
- All writes strictly follow hard rules (data/ + outputs/ only; never inputs/, never vault ~/llm-knowledge-base).

Grok integration (wave2-2):
- "run with Grok" (hotkey 'g' + yellow button) is the hook for future real Grok X tool calls (e.g. x_semantic_search / x_keyword_search for ticker news or software discussions).
- Writes structured payloads (findings, context, source="grok-x-skeleton") directly to data layer.
- UI immediately reflects results + write confirmation.
- Mirrors the ai-news.json skeleton pattern in BriefScreen (overview-brief/data/ai-news.json).

Hard rules honored:
- Never fabricates numbers/prices/performance.
- Never writes inputs/ or the vault.
- Timezone from tasks-calendar/inputs/config.json (ICT).
- Degrades gracefully; one writer per data file respected in spirit (demo writes).
- References goals.json for ticker context (read-only).

This is the second Doom-Emacs-style dedicated full-screen view (after BriefScreen).
Other views (Capture, Tasks) will follow the same pattern.

Internal TODO (wave2-2+):
- Replace Grok skeleton with real X tool calls + synthesis (see BriefScreen action_run_grok_ai_news for pattern + __main__.py Internal TODO notes).
- Wire `cos research [query]` in tui/__main__.py (add _run_research_screen host App + import, matching BriefHostApp; see its wave2-5 Internal TODO).
- Support passing prompt from hotkey (e.g. action_open_research(query=...) or CLI arg).
- Add richer UI (e.g. results as structured table, history of past researches).
- Live preview or web fetch integration if/when available (without violating rules).
- Tests for routing, dedupe, write paths.

Reference: toolbox/research.md, BriefScreen (full patterns + Grok), app.py (hotkey), loader.py, CODING_CONVENTIONS.md (surgical + minimal), CLAUDE.md + memory/ (hard rules), tui/README.md.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from zoneinfo import ZoneInfo

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Static

# Reuse the shared data loader (no duplication of contracts; surgical tiny helper only)
from ..data.loader import DEFAULT_COS_ROOT


# --- tiny internal helpers (duplicated _load_json only; surgical, no loader.py edit) ---
# Matches BriefScreen + loader.py style exactly. Reference existing patterns.

def _load_json(path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    """Load JSON with graceful fallback. Matches loader.py / BriefScreen style."""
    if default is None:
        default = {}
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def _get_tz() -> ZoneInfo:
    """Never hardcode timezone. Always read from the canonical config (per CLAUDE.md + all screens)."""
    cfg_path = DEFAULT_COS_ROOT / "tasks-calendar" / "inputs" / "config.json"
    cfg = _load_json(cfg_path, {"timezone": "Asia/Ho_Chi_Minh"})
    tz_name = cfg.get("timezone", "Asia/Ho_Chi_Minh")
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return ZoneInfo("Asia/Ho_Chi_Minh")


def _is_ticker(q: str) -> bool:
    """Route exactly as toolbox/research.md: 1-5 uppercase letters = finances ticker."""
    q = (q or "").strip().upper()
    return q.isalpha() and 1 <= len(q) <= 5


# --- The Screen ---

class ResearchScreen(Screen):
    """Dedicated full-screen Research view (Doom-Emacs style, second after BriefScreen).

    - Prompt input (ticker or software) with auto-routing per research.md
    - Basic "Run" (no write) + "Run with Grok" (richer, writes structured to data layer)
    - Grok skeleton ready for real X/research tool calls (writes json + md to outputs/ + queue update)
    - Full hotkeys, toolbar buttons, reactive display, detailed help, hard rules.
    - Reuses loader constants + internal _load_json (surgical).
    """

    CSS = """
    ResearchScreen {
        background: #0d0f14;   /* Grok Build dark theme, matches app + BriefScreen */
    }

    #toolbar {
        dock: top;
        height: 3;
        padding: 0 1;
        background: #16181f;
    }

    Button {
        margin: 0 1;
    }

    Label {
        margin: 1 2 0 2;
        color: #8a8f9a;
    }

    Input {
        margin: 0 2 1 2;
        border: round #2a2d3a;
    }

    #research-content {
        padding: 1 2;
        border: round #2a2d3a;
        margin: 1;
    }

    .research-content {
        width: 100%;
        height: auto;
    }
    """

    BINDINGS = [
        Binding("escape", "pop_screen", "Back to dashboard"),
        Binding("r", "refresh", "Clear input + results"),
        Binding("g", "run_grok", "Run with Grok (richer + write)"),
        Binding("?", "show_help", "Help"),
        Binding("q", "quit", "Quit"),
    ]

    query_text: reactive[str] = reactive("")
    last_result: reactive[dict] = reactive({})

    def __init__(self, initial_query: str = "", **kwargs) -> None:
        """Support initial query (for future 'r' hotkey with prompt or `cos research "foo"`)."""
        super().__init__(**kwargs)
        self._initial_query = initial_query

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="toolbar"):
            yield Button("Run Research", id="btn-run", variant="primary")
            yield Button("Run with Grok (g)", id="btn-grok", variant="warning")
            yield Button("Back (esc)", id="btn-back")
        yield Label("Ticker (e.g. NVDA, AAPL, BTC) or Software (e.g. Textual, React, Hermes):")
        yield Input(
            placeholder="Enter query (auto-routes: ticker → finances, else → learning)",
            id="research-query",
            value=self._initial_query,
        )
        with VerticalScroll():
            yield Static("", id="research-content")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "cos — Research (in-app /research)"
        self.sub_title = "ticker → finances research | software → learning pipeline | Grok for richer X-powered writes"
        try:
            inp = self.query_one("#research-query", Input)
            if self._initial_query:
                self.query_text = self._initial_query
                inp.value = self._initial_query
            inp.focus()
            inp.cursor_position = len(inp.value)
        except Exception:
            pass
        self._update_display()

    def watch_query_text(self, _v: str) -> None:
        self._update_display()

    def watch_last_result(self, _v: dict) -> None:
        self._update_display()

    def _update_display(self) -> None:
        try:
            content_widget = self.query_one("#research-content", Static)
            md_text = self._build_research_markdown()
            content_widget.update(md_text)
        except Exception:
            # Safe during early mount or teardown
            pass

    def _build_research_markdown(self) -> str:
        """Render current state + results (canonical style like BriefScreen build_brief_markdown)."""
        tz = _get_tz()
        now = datetime.now(tz)
        lines: list[str] = [f"# Research — {now.strftime('%Y-%m-%d %H:%M')} (ICT)", ""]

        q = self.query_text or "(no query — enter above)"
        lines.append(f"**Query:** `{q}`")
        lines.append("")

        if self.last_result:
            typ = self.last_result.get("type", self.last_result.get("ticker") or self.last_result.get("software", "unknown"))
            lines.append(f"**Type:** {typ}")
            if self.last_result.get("source"):
                lines.append(f"**Source:** {self.last_result['source']}")
            lines.append("")

            # Structured findings / summary
            if self.last_result.get("findings"):
                lines.append("### Findings / Items")
                for item in self.last_result.get("findings", [])[:5]:
                    if isinstance(item, dict):
                        title = item.get("title", str(item))
                        summary = (item.get("summary", "") or item.get("relevance", ""))[:80]
                        lines.append(f"- **{title}** — {summary}")
                    else:
                        lines.append(f"- {item}")
                lines.append("")

            if self.last_result.get("summary"):
                lines.append(f"**Summary:** {self.last_result['summary']}")
                lines.append("")

            if self.last_result.get("note"):
                lines.append(f"_Note: {self.last_result['note']}_")
                lines.append("")

            if self.last_result.get("queue_note"):
                lines.append(f"**Queue:** {self.last_result['queue_note']}")
                lines.append("")

            if self.last_result.get("written_paths"):
                lines.append("**Written (data layer):**")
                for p in self.last_result.get("written_paths", []):
                    lines.append(f"- `{p}`")
                lines.append("")
        else:
            lines.append("Enter a ticker (e.g. NVDA) or software name above.")
            lines.append("Press **Run Research** for basic routing/summary (no writes).")
            lines.append("Press **Run with Grok (g)** for richer structured research + data layer writes.")
            lines.append("")
            lines.append("Routing mirrors toolbox/research.md exactly:")
            lines.append("- Ticker (1-5 uppercase letters) → finances research (goals context)")
            lines.append("- Software/framework/tool → learning pipeline (intake-queue + outputs)")
            lines.append("")

        lines.append("Hard rules: no fabrication, no writes to inputs/ or vault. Grok skeleton ready for real X tools.")
        lines.append(f"_Generated via ResearchScreen (in-app /research) at {now.strftime('%H:%M:%S %Z')}_")
        return "\n".join(lines)

    def _get_current_query(self) -> str:
        """Read live from Input widget (source of truth for prompt)."""
        try:
            return self.query_one("#research-query", Input).value.strip()
        except Exception:
            return self.query_text or ""

    def action_refresh(self) -> None:
        """Clear state (r hotkey)."""
        self.query_text = ""
        self.last_result = {}
        try:
            inp = self.query_one("#research-query", Input)
            inp.value = ""
            inp.focus()
        except Exception:
            pass
        self._update_display()
        self.notify("Research cleared. Enter new query.")

    def action_run_research(self) -> None:
        """Basic run (no data writes, just routing + summary per research.md)."""
        q = self._get_current_query()
        if not q:
            self.notify("Enter a ticker or software name first.", severity="warning")
            return

        self.query_text = q
        is_ticker = _is_ticker(q)
        typ = "finances (ticker)" if is_ticker else "learning (software)"
        summary = (
            f"Basic research summary for {q} ({typ}). "
            "See goals.json / intake-queue for context. Use Run with Grok for full structured write + richer results."
        )

        self.last_result = {
            "type": typ,
            "query": q,
            "summary": summary,
            "items": [],
            "note": "Basic mode — no data layer writes. Grok option performs the real skill writes (structured JSON + MD).",
        }
        self._update_display()
        self.notify(f"Basic research routed for {q} ({typ}).")

    def action_run_grok(self) -> None:
        """Grok-powered richer research + structured writes to data layer (the key wave2-2 feature).

        - Detects ticker vs software exactly as toolbox/research.md
        - For ticker: reads goals.json (context), writes structured JSON (+MD) to finances/outputs/
        - For software: dedupes + appends "to-study" to learning-pipeline/data/intake-queue.json, writes structured to outputs/
        - Payloads include source="grok-x-skeleton (TUI ResearchScreen)", findings, note for future real Grok X.
        - UI updates immediately; notification shows exact paths.
        - Ready for replacement by real Grok X tool calls (x_semantic_search etc.) in future.
        """
        q = self._get_current_query()
        if not q:
            self.notify("Enter a ticker or software name first.", severity="warning")
            return

        self.query_text = q
        is_ticker = _is_ticker(q)
        tz = _get_tz()
        now = datetime.now(tz)
        date_str = now.strftime("%Y-%m-%d")

        try:
            written: list[str] = []

            if is_ticker:
                ticker = q.strip().upper()
                goals_path = DEFAULT_COS_ROOT / "finances" / "inputs" / "goals.json"
                goals = _load_json(goals_path, {"goals": []})

                structured: dict[str, Any] = {
                    "ticker": ticker,
                    "generated_at": now.isoformat(),
                    "source": "grok-x-skeleton (TUI ResearchScreen action_run_grok)",
                    "note": "PLACEHOLDER written by Grok skeleton. Future: invoke real Grok X tools (e.g. x_keyword_search for recent fundamentals/news on ticker) + web context from goals. Never fabricate prices or projections.",
                    "goals_context": goals.get("goals", []),
                    "findings": [
                        {
                            "title": f"{ticker} — recent X / news skeleton",
                            "summary": "Discussion of fundamentals, runway relevance, investment thesis alignment (placeholder for real search synthesis).",
                            "relevance": "Directly maps to owner's goals in finances/inputs/goals.json",
                            "date": date_str,
                        },
                        {
                            "title": f"Grok Build + cos TUI integration note for {ticker}",
                            "summary": "How agentic research flows (this screen) will power richer personal OS decisions.",
                            "relevance": "Example of in-app skill + data layer write",
                            "date": date_str,
                        },
                    ],
                    "count": 2,
                }

                out_dir = DEFAULT_COS_ROOT / "finances" / "outputs"
                out_dir.mkdir(parents=True, exist_ok=True)

                json_path = out_dir / f"research-{ticker}-{date_str}.json"
                json_path.write_text(json.dumps(structured, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                written.append(str(json_path))

                md_path = out_dir / f"research-{ticker}-{date_str}.md"
                md_text = (
                    f"# Research {ticker} — {date_str}\n\n"
                    f"{structured['note']}\n\n"
                    f"## Goals Context\n"
                    f"{json.dumps(goals.get('goals', []), indent=2)}\n\n"
                    "## Findings (Grok skeleton)\n"
                )
                for f in structured["findings"]:
                    md_text += f"- **{f['title']}**: {f['summary']} ({f.get('relevance','')})\n"
                md_path.write_text(md_text, encoding="utf-8")
                written.append(str(md_path))

                self.last_result = {**structured, "type": f"finances (ticker {ticker})", "written_paths": written}

                self.notify(
                    f"Grok research for ticker {ticker} complete!\n"
                    f"Wrote structured results to data layer (per research.md):\n"
                    + "\n".join(f"  - {p}" for p in written)
                    + "\n\nFuture real Grok X calls will replace this stub with live research.\n"
                    "Dashboard / briefs can surface these on refresh.",
                    timeout=18,
                )

            else:
                # Software / framework / tool
                name = q.strip()
                name_slug = name.lower().replace(" ", "_").replace("/", "_")

                # Update intake-queue (data layer) with dedupe by title (as skill says "Dedupe by URL" — we use title for skeleton)
                queue_path = DEFAULT_COS_ROOT / "learning-pipeline" / "data" / "intake-queue.json"
                queue_data = _load_json(queue_path, {"queue": [], "backlog_count": 0, "generated": ""})
                queue: list[dict] = queue_data.get("queue", []) or []
                if not isinstance(queue, list):
                    queue = []

                dup = any(
                    isinstance(item, dict) and (item.get("title", "").lower() == name.lower() or name.lower() in str(item.get("url", "")).lower())
                    for item in queue
                )

                queue_note = ""
                if not dup:
                    new_entry = {
                        "id": f"research-{now.strftime('%Y%m%d-%H%M%S')}",
                        "source": "tui-research-grok",
                        "title": name,
                        "url": f"tui://research/software/{name_slug}",
                        "topic": "research",
                        "status": "to-study",
                        "added": date_str,
                    }
                    queue.append(new_entry)
                    queue_data["queue"] = queue
                    queue_data["backlog_count"] = len(queue)
                    queue_data["generated"] = now.isoformat()
                    queue_path.parent.mkdir(parents=True, exist_ok=True)
                    queue_path.write_text(json.dumps(queue_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                    queue_note = " (new entry added to intake-queue.json with status 'to-study')"
                else:
                    queue_note = " (already present — deduped per research.md, no duplicate write)"

                structured = {
                    "software": name,
                    "generated_at": now.isoformat(),
                    "source": "grok-x-skeleton (TUI ResearchScreen action_run_grok)",
                    "note": "PLACEHOLDER for richer software research + synthesis. Entry added to learning-pipeline per toolbox/research.md (deduped by title/URL). Future: real Grok X + docs summarization will populate better fields.",
                    "summary": f"In-app research for {name}: key concepts, why relevant, primary resources/docs (Grok skeleton).",
                    "findings": [
                        {
                            "title": f"Intro to {name}",
                            "summary": "Core ideas, official docs, community patterns (placeholder — real call will pull recent X discussion + tutorials).",
                            "url": "",
                        }
                    ],
                    "count": 1,
                }

                out_dir = DEFAULT_COS_ROOT / "learning-pipeline" / "outputs"
                out_dir.mkdir(parents=True, exist_ok=True)

                json_path = out_dir / f"research-{name_slug}-{date_str}.json"
                json_path.write_text(json.dumps(structured, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                written.append(str(json_path))

                md_path = out_dir / f"research-{name_slug}-{date_str}.md"
                md_text = (
                    f"# Research {name} — {date_str}\n\n"
                    f"{structured['note']}\n\n"
                    f"## Summary\n{structured['summary']}\n\n"
                    "## Findings (Grok skeleton)\n"
                )
                for f in structured["findings"]:
                    md_text += f"- **{f['title']}**: {f['summary']}\n"
                md_path.write_text(md_text, encoding="utf-8")
                written.append(str(md_path))

                self.last_result = {
                    **structured,
                    "type": f"learning (software {name})",
                    "queue_note": queue_note,
                    "written_paths": written,
                }

                self.notify(
                    f"Grok research for software '{name}' complete!\n"
                    f"Wrote structured results + queue update{queue_note}:\n"
                    + "\n".join(f"  - {p}" for p in written)
                    + "\n\nFuture real Grok X calls will replace stub with live research.\n"
                    "learning-pipeline will pick up the new 'to-study' item on next load.",
                    timeout=18,
                )

            self._update_display()

        except Exception as exc:
            self.notify(f"Grok research action failed (check paths/permissions): {exc}", severity="error")

    def action_show_help(self) -> None:
        help_text = (
            "[bold cyan]Research Screen — in-app /research (Doom-Emacs style dedicated view #2)[/]\n\n"
            "  Input field        : Ticker (finances research) or software name (learning research)\n"
            "                       Auto-routes exactly per toolbox/research.md (1-5 uppercase = ticker)\n"
            "  Run Research       : Basic mode — detects type, shows summary (no writes)\n"
            "  Run with Grok (g)  : NEW — Grok-powered richer research (\"run with Grok\")\n"
            "                       Writes structured JSON + MD to outputs/ (data layer)\n"
            "                       - Ticker: finances/outputs/research-*.json (+ goals context)\n"
            "                       - Software: updates learning-pipeline/data/intake-queue.json (deduped, to-study)\n"
            "                         + learning-pipeline/outputs/research-*.json\n"
            "                       UI reflects immediately. Ready for real Grok X tool calls.\n"
            "  r / Refresh button : Clear input + results\n"
            "  esc / Back         : Pop back to main dashboard tiles\n"
            "  ?                    : This help\n"
            "  q                    : Quit the entire TUI\n\n"
            "Exactly mirrors toolbox/research.md + hard rules (CLAUDE.md / memory/):\n"
            "- Routing + no fabrication + never touch inputs/ or vault\n"
            "- Tz from config.json\n"
            "- Writes only to outputs/ + data/ (one writer spirit)\n\n"
            "Grok skeleton: second wired \"run with Grok\" (after Brief AI News). Writes structured like ai-news.json.\n"
            "See BriefScreen for the first example + patterns reused here.\n\n"
            "Internal TODO (wave2-2+): real X integration, CLI dispatch in __main__.py (per its Internal TODO),\n"
            "prompt-passing from hotkey, richer UI. See docstring."
        )
        self.notify(help_text, timeout=35)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn-run":
            self.action_run_research()
        elif bid == "btn-grok":
            self.action_run_grok()
        elif bid == "btn-back":
            self.app.pop_screen()

    # Optional: pressing Enter in the input runs the rich Grok action (Doom-Emacs muscle memory)
    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "research-query":
            self.action_run_grok()


# For direct execution during dev (matches BriefScreen pattern exactly)
if __name__ == "__main__":
    from textual.app import App

    class _DevApp(App):
        def on_mount(self):
            self.push_screen(ResearchScreen())

    _DevApp().run()
