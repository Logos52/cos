"""Dedicated Tasks/Calendar screen for the cos TUI (wave2-3).

Implements a Doom-Emacs-style full-screen dedicated view for the unified schedule.
Pulls from:
- TASKS.md (root; human-maintained board: In Progress / Up Next / Backlog / Done sections)
- tasks-calendar/data/upcoming.json (via shared loader; merged calendar events + tasks_due
  from connector + recurring.md + TASKS.md per the tasks-calendar domain)

Reuses data loader (load_schedule) exactly as dashboard tiles and BriefScreen do.
No data duplication. Read-only view (no direct writes to TASKS.md or inputs/ — follows hard rules).

Supports viewing + refresh. Simple interactions (e.g. mark task) are future/stub only
(the task-management skill owns writes to TASKS.md).

Internal TODO (wave2-3):
- Once stable, enhance launcher (__main__.py) dispatch for `cos tasks` / `cos calendar`
  to launch this screen directly (like BriefScreen for `cos brief`).
- Future richer interactions: filter by section, "mark done" that calls out to skill
  or writes via approved path (never direct edit of TASKS.md from TUI).
- Add due-date highlighting, conflict flags (tight gaps), Grok-powered "optimize schedule".
- Wire any additional hotkeys if needed beyond the dashboard 't'.
- Reference BriefScreen for CSS/toolbar/action patterns and loader reuse.

Follows conventions: surgical (no loader changes), reuses existing _load patterns
internally where needed, Grok Build dark theme, references existing patterns.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static

# Reuse the shared data loader (no duplication of contracts)
from ..data.loader import DEFAULT_COS_ROOT, load_schedule


# --- tiny internal helpers (matches BriefScreen style; surgical, no edits to loader.py) ---

def _load_text(path: Path, default: str = "") -> str:
    """Load text file with graceful fallback. Matches loader.py _load_json style."""
    try:
        if path.exists():
            return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        pass
    return default


def _parse_tasks_sections(text: str) -> dict[str, list[str]]:
    """Minimal parser for TASKS.md sections (## In Progress etc.).
    Robust to current empty file and future content.
    """
    sections: dict[str, list[str]] = {
        "In Progress": [],
        "Up Next": [],
        "Backlog": [],
        "Done": [],
    }
    current: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("## "):
            key = line[3:].strip()
            if key in sections:
                current = key
            else:
                current = None
            continue
        if line.startswith("# "):
            current = None
            continue
        if current and (line.startswith("- ") or line.startswith("* ")):
            item = line[2:].strip()
            if item:
                sections[current].append(item)
        elif current and line and not line.startswith("#"):
            # Fallback for loose items under section
            sections[current].append(line)
    return sections


def load_tasks_calendar(cos_root: Path = DEFAULT_COS_ROOT) -> dict[str, Any]:
    """Unified payload for the screen.
    - Raw + parsed TASKS.md (if present)
    - Schedule data via the canonical loader (upcoming.json)
    """
    tasks_path = cos_root / "TASKS.md"
    md_text = _load_text(tasks_path, "# Tasks\n\n## In Progress\n## Up Next\n## Backlog\n## Done\n")
    sections = _parse_tasks_sections(md_text)
    sched = load_schedule(cos_root)
    return {
        "tasks_md_raw": md_text,
        "tasks_sections": sections,
        "schedule": sched,
        "source_paths": {
            "tasks_md": str(tasks_path),
            "upcoming_json": str(cos_root / "tasks-calendar" / "data" / "upcoming.json"),
        },
    }


# --- The Screen ---

class TasksCalendarScreen(Screen):
    """Full dedicated Tasks/Calendar view (Doom-Emacs style per approved plan).

    Replaces the placeholder in app.py action_open_tasks.
    Real behavior: loads unified data on open/refresh; renders structured view.
    Matches BriefScreen wiring, CSS, toolbar, help, etc.
    """

    CSS = """
    TasksCalendarScreen {
        background: #0d0f14;   /* Grok Build dark */
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

    #tasks-content {
        padding: 1 2;
        border: round #2a2d3a;
        margin: 1;
    }

    .tasks-content {
        width: 100%;
        height: auto;
    }
    """

    BINDINGS = [
        Binding("escape", "pop_screen", "Back to dashboard"),
        Binding("r", "refresh", "Refresh (TASKS.md + upcoming.json)"),
        Binding("?", "show_help", "Help"),
        Binding("q", "quit", "Quit"),
        # Future: Binding("m", "mark_task", "Mark task (future)"),
    ]

    data: reactive[dict] = reactive({})

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="toolbar"):
            yield Button("Refresh (r)", id="btn-refresh", variant="primary")
            yield Button("Back (esc)", id="btn-back")
            yield Button("Mark (future)", id="btn-mark", variant="success")
        with VerticalScroll():
            yield Static("", id="tasks-content")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "cos — Tasks/Calendar"
        self.sub_title = "unified view (TASKS.md + tasks-calendar/data/upcoming.json)"
        self.action_refresh()

    def watch_data(self, _data: dict) -> None:
        self._update_display()

    def _update_display(self) -> None:
        try:
            content_widget = self.query_one("#tasks-content", Static)
            content_widget.update(self._build_display_text())
        except Exception:
            # Safe during early mount / errors
            pass

    def _build_display_text(self) -> str:
        """Render unified view as readable text (mirrors brief markdown style)."""
        d = self.data or {}
        sched = d.get("schedule", {})
        secs = d.get("tasks_sections", {})
        src = d.get("source_paths", {})

        lines: list[str] = ["# Tasks / Calendar — Unified Schedule", ""]

        tz = sched.get("timezone", "Asia/Ho_Chi_Minh")
        cal_avail = not sched.get("calendar_unavailable", False)
        lines.append(f"Timezone: {tz}  |  Calendar: {'available' if cal_avail else 'unavailable (TASKS.md + recurring only)'}")
        if sched.get("note"):
            lines.append(f"Note: {sched['note']}")
        lines.append("")

        # TASKS.md sections
        lines.append("## From TASKS.md (human board)")
        total_tasks = 0
        for sec_name in ["In Progress", "Up Next", "Backlog", "Done"]:
            items = secs.get(sec_name, [])
            total_tasks += len(items)
            lines.append(f"### {sec_name} ({len(items)})")
            if items:
                for item in items[:8]:
                    lines.append(f"- {item}")
                if len(items) > 8:
                    lines.append(f"  ... +{len(items)-8} more")
            else:
                lines.append("- (empty)")
            lines.append("")
        lines.append(f"(Total tracked in TASKS.md: {total_tasks})")
        lines.append("")

        # upcoming.json
        lines.append("## From tasks-calendar/data/upcoming.json (via loader)")
        events = sched.get("events", []) or []
        tasks_due = sched.get("tasks_due", []) or []
        lines.append(f"Events (lookahead): {len(events)}")
        for ev in events[:5]:
            if isinstance(ev, dict):
                title = ev.get("title") or ev.get("summary") or str(ev)
                when = ev.get("start") or ev.get("time") or ""
                lines.append(f"- {title} {f'({when})' if when else ''}")
            else:
                lines.append(f"- {ev}")
        if len(events) > 5:
            lines.append(f"  ... +{len(events)-5} more")
        lines.append("")

        lines.append(f"Tasks due: {len(tasks_due)}")
        for td in tasks_due[:8]:
            if isinstance(td, dict):
                title = td.get("title") or td.get("task") or str(td)
                due = td.get("due") or td.get("date") or ""
                lines.append(f"- {title} {f'(due {due})' if due else ''}")
            else:
                lines.append(f"- {td}")
        if len(tasks_due) > 8:
            lines.append(f"  ... +{len(tasks_due)-8} more")
        lines.append("")

        lines.append(f"Source: {src.get('tasks_md', 'TASKS.md')} + {src.get('upcoming_json', 'upcoming.json')}")
        lines.append("")
        lines.append("_Generated by TasksCalendarScreen (reuses tui/data/loader.py; read-only view of unified schedule)_")
        return "\n".join(lines)

    def action_refresh(self) -> None:
        """Re-read TASKS.md + upcoming.json (via load_schedule)."""
        try:
            self.data = load_tasks_calendar(DEFAULT_COS_ROOT)
            self.sub_title = "refreshed | unified from TASKS.md + upcoming.json (loader)"
            self.notify("Refreshed Tasks/Calendar unified view.")
            self._update_display()
        except Exception as exc:
            self.notify(f"Refresh failed: {exc}", severity="error")

    def action_show_help(self) -> None:
        help_text = (
            "[bold cyan]Tasks/Calendar Screen — unified view (Doom-Emacs style)[/]\n\n"
            "  r / Refresh button : Re-read TASKS.md (raw sections) + tasks-calendar/data/upcoming.json\n"
            "                       (via shared load_schedule; same contract as dashboard Schedule tile)\n"
            "  esc / Back         : Pop back to main dashboard tiles\n"
            "  ?                    : This help\n"
            "  q                    : Quit the entire TUI\n\n"
            "Unified schedule support:\n"
            "- TASKS.md is the canonical human task board (In Progress/Up Next/Backlog/Done)\n"
            "- upcoming.json is the live merged view written by tasks-calendar domain\n"
            "  (calendar events + due tasks + recurring; notes when calendar_unavailable)\n"
            "- This screen is the dedicated full view behind hotkey 't' (see dashboard ? help)\n\n"
            "Hard rules: read-only here. Never writes TASKS.md or inputs/. tz from config.\n"
            "Future: simple mark interactions will route through the task skill (not direct edit).\n"
            "See: tasks-calendar/CLAUDE.md, tui/data/loader.py:load_schedule, BriefScreen for patterns."
        )
        self.notify(help_text, timeout=30)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn-refresh":
            self.action_refresh()
        elif bid == "btn-back":
            self.app.pop_screen()
        elif bid == "btn-mark":
            self.notify(
                "Mark task (future): will be implemented as gated action routing through "
                "the task-management skill (owns TASKS.md writes per hard rules). "
                "Current view is read-only."
            )


# For direct execution during dev (rarely used; matches BriefScreen)
if __name__ == "__main__":
    from textual.app import App

    class _DevApp(App):
        def on_mount(self):
            self.push_screen(TasksCalendarScreen())

    _DevApp().run()
