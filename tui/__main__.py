"""Entry point for `cos` (and `python -m tui`).

This powers:
    cos
    cos dashboard
    cos brief           # real dedicated TUI screen (BriefScreen with scans + Grok)
    cos research        # placeholder for future dedicated screen
    cos capture         # placeholder
    cos tasks           # placeholder (also 'calendar' alias)
    python -m tui ...
    python -m tui brief
    python -m tui --help

Packaged via pyproject.toml [project.scripts] so `pip install -e .` (or pipx)
provides the global `cos` console command (preferred over manual symlink).

The scripts/cos bash launcher ensures COS_ROOT (for data layer) and
PYTHONPATH are set correctly before exec'ing this (still useful for dev).

Subcommands provide clean dispatch in the unified `cos` CLI (per the
model-agnostic migration PRD) while keeping the full TUI as the primary
experience. 'brief' now dispatches directly to its real dedicated view.

Grok integration: wired in BriefScreen ('g' hotkey + button runs skeleton
that writes structured data to overview-brief/data/ai-news.json; UI
reflects it immediately. Future real X tool calls will replace stub).
"""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from .app import CosDashboardApp

# Dedicated screen dispatch support.
# BriefScreen (first real MVP dedicated view) is imported so `cos brief`
# (and `python -m tui brief`) launches the full functional TUI directly.
# Other screens (research, capture, tasks/calendar) will follow the exact
# same host-App + push pattern once implemented in parallel waves.
from textual.app import App
from .screens.brief_screen import BriefScreen

# out-3 Grok layer refreshers (standalone, schema-validated, for CLI + direct
# use by Grok Build / Hermes outside TUI/Cowork). All write to the same data
# contracts as the rest of the system.
from .data.loader import (
    refresh_finances,
    refresh_knowledge_base,
    refresh_learning,
    refresh_schedule,
    refresh_overview_brief_status,
    refresh_all,
    write_grok_ai_news,
)


# Internal TODO (wave2-5 launcher enhancement):
# - This task enhances dispatch for clean subcommand support + real Brief
#   TUI launch (previously brief was text-only placeholder).
# - When Capture/Research/Tasks dedicated screens are added to tui/screens/
#   (parallel waves, matching BriefScreen pattern + app.py hotkeys), replace
#   the _placeholder_cli calls with real _run_*_screen() helpers here.
#   Reference: BriefHostApp below + the _DevApp at bottom of brief_screen.py.
# - Hotkeys in app.py (b/r/c/t/ctrl+r/?/q) are the source of truth for
#   in-TUI actions; CLI subcommands provide the corresponding top-level entry.
# - Future: richer options per subcommand (e.g. `cos research "AI agents"`)
#   via subparsers or grouped args, per PRD Phase 1 unified CLI examples
#   like `cos refresh --domain finances`.
# - All changes surgical + documented. Bash launcher (scripts/cos) remains
#   a thin env wrapper (no logic duplication). Matches CODING_CONVENTIONS.md,
#   CLAUDE.md (min code, no speculation), and AGENTS.md style.
# - Respects COS_ROOT everywhere (exported by launcher; read by loader.py
#   and all screens/brief logic). Help via argparse is first-class.
# - Test with: python -m tui --help ; python -m tui brief ; etc.


def _run_brief_screen() -> None:
    """Launch the real BriefScreen as the primary TUI for `cos brief`.

    This replaces the previous text-only placeholder. It gives a first-class
    dedicated Doom-Emacs-style view directly from the CLI:
    - Full live vault scans + operational data (via shared loader)
    - Canonical markdown rendering
    - Real actions: r=refresh+rescan, w=write status+brief md, g=Grok AI News
      skeleton (writes ai-news.json), esc=back (but root here), ? =help, q=quit
    - Buttons for the actions too.
    - All hard rules honored (read-only vault, writes only to data/ under
      overview-brief/ and briefs/, tz from tasks-calendar/inputs/config.json).

    Uses a minimal host App (standard Textual pattern for launching a Screen
    as the initial/primary experience). See BriefScreen docstring for full spec.
    """
    class BriefHostApp(App):
        """Minimal host App to present BriefScreen directly as the root view.

        Used exclusively by the CLI dispatch path (`cos brief` / `python -m tui brief`).
        The main CosDashboardApp continues to push BriefScreen on 'b' hotkey
        (with its extra refresh side-effect).
        """
        def on_mount(self) -> None:
            self.push_screen(BriefScreen())

    BriefHostApp().run()


def _placeholder_cli(command: str) -> None:
    """Print informative placeholder for subcommands whose dedicated screens
    are not yet implemented (being built in parallel waves).

    This keeps the CLI clean and future-proof: no argparse 'invalid choice'
    errors for the documented hotkey-aligned commands (`cos research` etc.).

    Messages point to:
    - Current in-TUI hotkey behavior (from app.py)
    - The corresponding toolbox/*.md skill prompt (source of truth for logic)
    - The PRD and tui/README for the plan
    - Grok integration notes where relevant (research/brief)

    Internal TODO (wave2-5+): Once the matching Screen exists (e.g.
    screens/research_screen.py), add a _run_research_screen() here that
    does the same BriefHostApp pattern, import it, and call it instead.
    Keep messages in sync with app.py action_open_* docstrings.
    """
    if command == "calendar":
        command = "tasks"  # support the natural alias from hotkey 't'

    base = (
        f"cos {command}: placeholder (future hook / dedicated TUI screen).\n"
        "\n"
        "  This subcommand is recognized for clean dispatch and future expansion.\n"
    )

    if command == "research":
        msg = base + (
            "  Current status:\n"
            "  - In the dashboard TUI: press 'r' (see ? for help overlay)\n"
            "  - Full skill: toolbox/research.md (Cowork /research)\n"
            "  - Grok skeleton already exists in BriefScreen ('g' writes ai-news.json)\n\n"
            "  Future:\n"
            "  - `cos research` will launch a dedicated ResearchScreen\n"
            "    (rich Grok X tool calls, synthesis, writes to data layer).\n"
            "  - Will feed Brief AI News section etc.\n\n"
            "See prds/PRD-cos-model-agnostic-migration-and-terminal-dashboard.md\n"
            "(Phase 1 unified CLI + Grok layer) and tui/README.md."
        )
    elif command == "capture":
        msg = base + (
            "  Current status:\n"
            "  - In the dashboard TUI: press 'c'\n"
            "  - The only vault writer: toolbox/capture.md (gated; explicit proceed)\n"
            "  - Hard rules: see CLAUDE.md + memory/terminology.md\n\n"
            "  Future:\n"
            "  - `cos capture` will launch dedicated CaptureScreen (modal or full).\n\n"
            "See toolbox/capture.md and prds/ for the capture flow."
        )
    elif command == "tasks":
        msg = base + (
            "  Current status:\n"
            "  - In the dashboard TUI: press 't'\n"
            "  - Data contracts: tasks-calendar/data/upcoming.json (from TASKS.md + calendar)\n"
            "  - Inputs: tasks-calendar/inputs/{config.json,recurring.md}\n\n"
            "  Future:\n"
            "  - `cos tasks` (or `cos calendar`) will launch unified Tasks/Calendar\n"
            "    dedicated screen (richer than current tiles).\n\n"
            "See tasks-calendar/ (CLAUDE.md + data/ + inputs/) and tui/app.py."
        )
    else:
        msg = base + (
            "  See the dashboard hotkeys (b/r/c/t), tui/app.py, and tui/README.md\n"
            "  for current status and how to use the real functionality today."
        )

    print(msg)


def main(argv: Sequence[str] | None = None) -> None:
    """Dispatch subcommands to the appropriate TUI screen or CLI logic.

    Only 'dashboard' (default) and 'brief' perform real work today.
    'brief' now launches the full dedicated BriefScreen TUI (enhancement).
    Other commands are clean, documented placeholders (no crashes, helpful text)
    until their dedicated screens land in parallel implementation waves.

    COS_ROOT is respected automatically (set by scripts/cos or $COS_ROOT;
    consumed by tui/data/loader.py and BriefScreen vault/config logic).
    --help / -h is handled natively by argparse with rich epilog.
    """
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        prog="cos",
        description="cos — terminal mission control for the personal OS (Textual TUI)",
        epilog=(
            "Default action is the dashboard TUI (live tiles + hotkeys).\n"
            "Supported subcommands (clean dispatch):\n"
            "  cos [dashboard]  Launch main tiles dashboard (b=Brief, r=Research, c=Capture, t=Tasks, ?=help)\n"
            "  cos brief        Launch dedicated Brief view (real: live scans, writes, Grok 'g' AI News skeleton)\n"
            "  cos research     Placeholder for dedicated Research screen (Grok X-powered)\n"
            "  cos capture      Placeholder for dedicated Capture screen (gated vault writer)\n"
            "  cos tasks        Placeholder for unified Tasks/Calendar screen ('calendar' alias also works)\n"
            "  cos refresh [finances|kb|learning|schedule|brief|all]  NEW (out-3): Grok layer refresher(s) — standalone, schema-validated writes to data/ contracts\n\n"
            "All paths respect COS_ROOT. Grok integration lives in BriefScreen + tui/data/loader.py (refresh_* fns + write_grok_ai_news).\n"
            "See tui/README.md for MVP status, hotkeys, Grok notes, and run instructions.\n"
            "See prds/PRD-cos-model-agnostic-migration-and-terminal-dashboard.md for the full plan."
        ),
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="dashboard",
        choices=["dashboard", "brief", "research", "capture", "tasks", "calendar", "refresh"],
        help="Subcommand (default: dashboard). 'brief' launches real TUI; 'refresh' runs Grok layer; others are future placeholders.",
    )

    args = parser.parse_args(argv)

    if args.command == "dashboard":
        CosDashboardApp().run()
    elif args.command == "brief":
        _run_brief_screen()
    elif args.command == "refresh":
        # out-3: dispatch to Grok layer refreshers in tui/data/loader.py
        # Supports `cos refresh` (all) and `cos refresh <domain>`
        # Domain peeked from original argv (surgical, keeps parser simple).
        domain = "all"
        if argv:
            if argv[0] == "refresh" and len(argv) > 1:
                domain = argv[1].lower()
            elif len(argv) > 1 and argv[1] == "refresh" and len(argv) > 2:
                domain = argv[2].lower()
        refresh_map = {
            "finances": refresh_finances,
            "kb": refresh_knowledge_base,
            "knowledge": refresh_knowledge_base,
            "learning": refresh_learning,
            "schedule": refresh_schedule,
            "brief": refresh_overview_brief_status,
            "status": refresh_overview_brief_status,
            "all": refresh_all,
        }
        fn = refresh_map.get(domain, refresh_all)
        print(f"cos refresh {domain}: running Grok layer refresher (validates + writes data/ contracts)...")
        try:
            res = fn(dry_run=False)
            if isinstance(res, dict):
                if "runway_months" in res:
                    print(f"  finances: runway_months={res.get('runway_months')}")
                else:
                    # all or others: light summary
                    keys = list(res.keys())[:3] if res else []
                    print(f"  done: {keys}...")
            else:
                print("  done.")
        except Exception as e:
            print(f"  error: {e}")
            sys.exit(1)
    elif args.command in ("research", "capture", "tasks", "calendar"):
        _placeholder_cli(args.command)
    else:
        # Unreachable with current choices
        parser.print_help(sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
