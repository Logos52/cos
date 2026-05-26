"""Main Textual application for the cos mission control dashboard."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Grid, Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Button, Footer, Header, Static

from .data.loader import load_all, ensure_fresh_data
from .screens.brief_screen import BriefScreen
from .screens.capture_screen import CaptureScreen
from .screens.research_screen import ResearchScreen


class DomainTile(Static):
    """A single domain tile with title + key stats.

    We inherit from Static and call self.update() with Rich markup directly.
    This avoids the previous pattern of yielding an inner Static(a_string),
    which could lead to 'str' object has no attribute 'render_strips' under
    certain layout constraints (the error the user was hitting).
    """

    def __init__(self, title: str, data: dict, **kwargs) -> None:
        super().__init__(**kwargs)
        self.title = title
        self.data = data
        # Set the content immediately. Because tiles are created fresh
        # every time in watch_data, this is sufficient and reliable.
        self.update(self._build_text())

    def _build_text(self) -> str:
        d = self.data
        if self.title == "Finances":
            runway = d.get("runway_months")
            if runway is None:
                return f"[bold red]Finances[/]\nError: {d.get('error', 'unavailable')}"
            return (
                f"[bold cyan]Finances[/]\n"
                f"Runway: [bold green]{runway:.1f}[/] months\n"
                f"Net: ${d.get('net_monthly', 0):,.0f}/mo\n"
                f"US return: {d.get('us_return', {}).get('months_remaining', '?')} mo"
            )

        if self.title == "Knowledge Base":
            oq = d.get("oq_count", 0)
            stale = d.get("stale_count", 0)
            note = d.get("vault_note")
            status = "[yellow]vault error[/]" if d.get("vault_error") else "[green]ok[/]"
            return (
                f"[bold cyan]Knowledge Base[/]\n"
                f"Open Qs: [bold]{oq}[/]\n"
                f"Stale: {stale}\n"
                f"Status: {status}"
                + (f"\n[dim]{note[:60]}...[/]" if note else "")
            )

        if self.title == "Learning":
            return (
                f"[bold cyan]Learning Pipeline[/]\n"
                f"Backlog: [bold]{d.get('backlog_count', 0)}[/]\n"
                f"Queue: {d.get('queue_length', 0)}"
            )

        if self.title == "Schedule":
            note = d.get("note") or ("[yellow]calendar unavailable[/]" if d.get("calendar_unavailable") else "")
            return (
                f"[bold cyan]Schedule[/]\n"
                f"Events: {len(d.get('events', []))}\n"
                f"Tasks due: {len(d.get('tasks_due', []))}"
                + (f"\n[dim]{note}[/]" if note else "")
            )

        if self.title == "Knowledge Work":
            return (
                f"[bold cyan]Knowledge Work[/]\n"
                f"Inbox: [bold]{d.get('inbox_count', 0)}[/]\n"
                f"Workbench: {d.get('workbench_count', 0)}\n"
                f"Journal Qs: {d.get('journal_questions', 0)}"
            )

        return f"[bold]{self.title}[/]\n(no data)"


class CosDashboardApp(App):
    """Main mission control dashboard for cos."""

    CSS = """
    /* Grok Build refined theme: dark clean high-contrast terminal, minimal chrome,
       keyboard-first, cyan/green accents for titles/values (matches xAI Grok CLI aesthetic). */
    Screen {
        background: #0a0c10;   /* deeper Grok terminal dark */
        layout: vertical;      /* explicit stacking so the Grid gets space */
    }

    #tiles {
        height: 1fr;                    /* take all available vertical space */
        grid-size: 5 1;                 /* 5 columns, 1 row (tiles side-by-side) */
        grid-columns: 1fr 1fr 1fr 1fr 1fr;  /* Textual does not support repeat() */
        grid-gutter: 1 1;
        padding: 1 0;
    }

    .tile {
        border: round #1e212a;
        padding: 1 1;
        min-height: 7;                  /* guarantee the box is tall enough to see */
        height: 100%;
    }

    .tile-content {
        width: 100%;
        height: 100%;
    }

    Footer {
        background: #0f1118;
        color: #b0b5c0;  /* higher contrast */
    }

    .log-header {
        padding: 0 1;
        color: #5a5f6a;
        text-style: dim;
    }

    .log-pane {
        height: 5;
        border: round #1e212a;
        padding: 0 1;
        margin: 0 1;
        background: #0f1118;
        color: #a8adb8;
        overflow-y: auto;
    }

    Button#quick-capture {
        margin: 0 1 1 1;
        min-width: 20;
    }
    """

    BINDINGS = [
        Binding("ctrl+r", "refresh_data", "Refresh"),
        Binding("u", "update_all", "Update all"),
        Binding("b", "open_brief", "Brief"),
        Binding("r", "open_research", "Research"),
        Binding("c", "open_capture", "Capture"),
        Binding("t", "open_tasks", "Tasks/Calendar"),
        Binding("q", "quit", "Quit"),
        Binding("?", "show_help", "Help"),
    ]

    data: reactive[dict] = reactive({})

    # Live file watching (simple stdlib + Textual set_interval; no new deps).
    # Polls mtimes of the canonical data contracts; auto-calls refresh_data
    # (which updates tiles via watch_data) when external writes occur (Grok, scripts, etc.).
    _contract_files: list[str] = [
        "finances/data/runway.json",
        "knowledge-base/data/stale-notes.json",
        "knowledge-base/data/open-questions.json",
        "learning-pipeline/data/intake-queue.json",
        "tasks-calendar/data/upcoming.json",
        "overview-brief/data/status.json",
    ]
    _last_mtimes: dict[str, float] = {}

    # Activity feed for recent runs (surgical polish for dashboard)
    _activity_log: reactive[list[str]] = reactive([])

    def on_mount(self) -> None:
        self.title = "cos — mission control"
        root = os.environ.get("COS_ROOT") or (Path.home() / "cos")
        self.sub_title = f"terminal dashboard  |  root: {root}"
        # Smart startup: check Cowork/prior data, run shared refreshes only if stale (>20h).
        # This is the primary "real data first, eliminate redundancy" path per plan review.
        self._ensure_and_load()
        self.log_event(f"dashboard mounted (root={root})")
        # Force a tile population after the DOM is ready (avoids any reactive timing race
        # that can leave the grid empty even when data was loaded).
        self.call_later(self._populate_tiles)
        # Start live file watch (Textual interval + mtime polling for contract changes)
        self._last_mtimes = self._snapshot_mtimes()
        self.set_interval(5.0, self._poll_for_changes, name="live-contract-watch")

    def _populate_tiles(self) -> None:
        """Explicit safe rebuild of the domain grid (used on startup and after ensure)."""
        if not self.data:
            self.data = load_all()
        # Calling the watcher directly is reliable once we're in on_mount / call_later.
        self.watch_data(self.data)

    def compose(self) -> ComposeResult:
        yield Header()
        yield Grid(id="tiles")
        yield Button("Quick Capture (c)", id="quick-capture", variant="success")
        yield Static("Activity (recent runs)", classes="log-header")
        yield Static("", id="activity-log", classes="log-pane")
        yield Footer()

    def watch_data(self, data: dict) -> None:
        """Rebuild the tile grid whenever data changes (defensive version)."""
        try:
            grid = self.query_one("#tiles", Grid)
            grid.remove_children()

            tiles = [
                ("Finances", data.get("finances", {})),
                ("Knowledge Base", data.get("kb", {})),
                ("Learning", data.get("learning", {})),
                ("Schedule", data.get("schedule", {})),
                ("Knowledge Work", data.get("knowledge_work", {})),
            ]

            for title, payload in tiles:
                tile = DomainTile(title, payload, classes="tile")
                grid.mount(tile)
        except Exception as e:
            self.log_event(f"tile populate error: {e}")
            # Keep going; the activity log will show the problem

    def action_refresh_data(self) -> None:
        """Light reload from whatever contracts are already on disk (used by live watcher + internal)."""
        self.log_event("data refresh (light)")
        self.data = load_all()
        # Show a timestamp in the footer / sub_title for live feel
        ts = datetime.now().strftime("%H:%M:%S")
        self.sub_title = f"last refresh: {ts}"

    def _ensure_and_load(self, force: bool = False) -> None:
        """Shared ensure path (TUI startup + 'u' hotkey).

        Calls the model-agnostic loader.ensure_fresh_data which:
        - Checks mtimes of key contracts (populated by Cowork or prior shared runs)
        - Only invokes the exact same refresh_* functions if stale (>20h default) or forced
        - Returns a reason the UI can surface

        Always ends with load_all so tiles are populated with real data.
        This directly addresses the review: "check Cowork data first... run yourself only if stale",
        "automatically triggered on startup", "populate the data first" (no heavy first-run demo design).
        """
        try:
            res = ensure_fresh_data(force=force)
            reason = res.get("reason", "ensure checked")
            self.log_event(reason[:120])
            if res.get("refreshed"):
                self.notify(reason, timeout=6)
        except Exception as e:
            self.log_event(f"ensure error (non-fatal): {e}")
        # Always (re)load so the dashboard shows whatever is present
        self.data = load_all()
        ts = datetime.now().strftime("%H:%M:%S")
        root = os.environ.get("COS_ROOT") or (Path.home() / "cos")
        self.sub_title = f"last refresh: {ts}  |  root: {root}"
        self.call_later(self._populate_tiles)

    def action_update_all(self) -> None:
        """Hotkey 'u': force the full shared refresh check (bypasses 20h staleness)."""
        self.log_event("update all requested (force)")
        self._ensure_and_load(force=True)

    def _snapshot_mtimes(self) -> dict[str, float]:
        """Stdlib snapshot of mtimes for watched contracts (simple, no extra deps)."""
        root = Path(os.environ.get("COS_ROOT") or (Path.home() / "cos"))
        mtimes: dict[str, float] = {}
        for rel in self._contract_files:
            p = root / rel
            try:
                mtimes[rel] = p.stat().st_mtime if p.exists() else 0.0
            except Exception:
                mtimes[rel] = 0.0
        return mtimes

    def _poll_for_changes(self) -> None:
        """Textual periodic callback: detect external JSON contract changes and auto-refresh tiles."""
        current = self._snapshot_mtimes()
        if any(current.get(k, 0.0) > self._last_mtimes.get(k, 0.0) for k in current):
            self._last_mtimes = current
            self.action_refresh_data()
            self.notify("Live: data contracts updated on disk", timeout=1.5)
            self.log_event("data contracts changed (live)")

    def log_event(self, msg: str) -> None:
        """Append timestamped entry to activity feed (keeps last ~8)."""
        ts = datetime.now().strftime("%H:%M")
        entry = f"[{ts}] {msg}"
        current = self._activity_log[-7:] + [entry]
        self._activity_log = current

    def watch_activity_log(self, logs: list[str]) -> None:
        """Re-render the activity pane when log updates."""
        try:
            pane = self.query_one("#activity-log", Static)
            pane.update("\n".join(logs))
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle Quick Capture button from main dashboard (integrates with CaptureScreen)."""
        if event.button.id == "quick-capture":
            self.log_event("quick capture (button)")
            self.action_open_capture()

    def action_open_brief(self) -> None:
        """Open Brief view (real logic, not placeholder).

        'b' hotkey now performs a real action:
        - Triggers dashboard data refresh (reloads all contracts, updates tiles + timestamp)
        - Logs via notification
        - Pushes the dedicated BriefScreen (which does live READ-ONLY vault scans for inbox/workbench/journal,
          renders canonical brief markdown, and supports write of status.json + daily brief md).

        This wires the hotkey to useful behavior beyond a bare screen push, leveraging BriefScreen's
        existing real implementation of the /brief skill.
        """
        self.log_event("brief opened")
        self.notify("Brief hotkey triggered: refreshing dashboard data (real action) + opening BriefScreen...")
        self.action_refresh_data()
        self.push_screen(BriefScreen())

    def action_open_capture(self) -> None:
        """Open Capture dedicated view (in-app gated /capture skill).

        'c' hotkey now performs the real action (wave2-1):
        - Logs via notification
        - Pushes the dedicated CaptureScreen (full Doom-Emacs-style view with note text input,
          live reactive preview of exact target vault path in default inbox, formatted content
          preview, and explicit 'p' / Proceed confirmation gate that is the ONLY writer to
          ~/llm-knowledge-base/ per toolbox/capture.md hard rules: read-only until explicit proceed).
        """
        self.log_event("capture opened")
        self.notify("Capture hotkey triggered: opening CaptureScreen (gated /capture)...")
        self.push_screen(CaptureScreen())

    def action_open_research(self) -> None:
        """Open Research dedicated view (real, not placeholder).

        'r' hotkey now performs the real action:
        - Pushes the dedicated ResearchScreen (full Doom-Emacs-style view with prompt input
          for ticker (finances research) or software (learning research), mirroring toolbox/research.md
          routing + hard rules).
        - Includes "Run with Grok" (hotkey 'g' inside screen or button) for richer X/research
          that writes structured results to the data layer (outputs/ JSON + MD, intake-queue updates).
        - Screen supports initial_query for future prompt-passing from hotkey/CLI.
        """
        self.log_event("research opened")
        self.notify("Research hotkey triggered: opening ResearchScreen (in-app /research with prompt + Grok option)...")
        self.push_screen(ResearchScreen())

    def action_open_tasks(self) -> None:
        """Placeholder for dedicated Tasks/Calendar screen."""
        self.log_event("tasks opened (placeholder)")
        self.notify("Tasks/Calendar screen coming soon (unified from tasks-calendar domain)")

    def action_show_help(self) -> None:
        """Show comprehensive help overlay with all hotkeys, descriptions, skill support, and future notes."""
        help_text = """
[bold cyan]cos mission control — Hotkeys[/]

[bold]Visible hotkeys (always in footer bar):[/]

  b  Brief           open Brief view (REAL: auto-refreshes dashboard tiles + dedicated screen with live vault scans + writes)
  r  Research        research action (in-app /research skill — now real: dedicated screen with ticker/software input + Grok writes)
  c  Capture         quick Capture (gated /capture skill — now real: dedicated screen with input + explicit proceed gate)
  t  Tasks/Calendar  unified tasks + calendar view
  ctrl+r             Refresh data from disk contracts
  ?  Help            this overlay
  q  Quit

[bold]In-app skill support:[/]
Hotkeys launch corresponding skills from toolbox/ (brief, research, capture, tasks-calendar/).

[bold]Grok integration skeleton:[/]
"Run with Grok" options available in BriefScreen (press 'g' or button for AI News stub that writes to data layer).
See BriefScreen help for details. ResearchScreen (this wave) adds the second: ticker/software research with richer writes.
Future: richer X/research calls that populate ai-news.json etc.

[bold]Future:[/]
Dedicated views (Phase 2+) replacing remaining placeholders.
Full Grok-powered actions ("run with Grok") on screens for richer X/research that write back to data/.

This TUI is the terminal companion to Cowork (dashboard.html, briefs). All data from shared contracts — no duplication.
        """.strip()
        self.notify(help_text, timeout=20)


if __name__ == "__main__":
    CosDashboardApp().run()
