# cos — Terminal Mission Control (Textual TUI)

This is the in-progress Textual-based terminal dashboard for the `cos` personal OS.

It is the native terminal companion (and eventual primary view) for the same data layer that powers your current Cowork `dashboard.html`, briefs, and skills.

## Current Status (MVP + Real Actions + Grok Skeleton + Clean CLI Dispatch)

- Live tiles for Finances, Knowledge Base, Learning, Schedule, and Knowledge Work
- Pulls from the real canonical JSON contracts (`data/*.json` + `overview-brief/data/status.json`)
- Graceful handling of partial data (`vault_error`, `calendar_unavailable`, etc.)
- Real hotkeys wired: `ctrl+r`=light refresh (from disk), `u`=Update all (smart shared ensure: checks Cowork data first, only runs the common refresh_* if stale >~20h or forced — real data, no redundancy), `b`=Brief (auto-refreshes dashboard + opens full BriefScreen with live vault scans + write support), `c`=Capture, `t`=Tasks/Calendar, `?`=help, `q`=quit
- Startup: on launch the dashboard automatically ensures real data via the shared loader (Cowork 7am schedule + TUI open ~7:30am typically sees fresh data with zero extra work)
- Dedicated BriefScreen (Doom-Emacs style, first per-domain full view): real logic for /brief (scans inbox/workbench/journal Qs read-only, renders canonical markdown, supports write of status.json + daily brief-*.md)
- Grok integration skeleton: "run with Grok" action (hotkey `g` + button in BriefScreen) — writes structured stub to overview-brief/data/ai-news.json (the reserved Phase 2 slot); UI immediately reflects it in the AI News section. Future real X tool calls (semantic/keyword search etc.) will replace the demo payload.
- Enhanced launcher with clean subcommand dispatch (wave2-5): `cos brief` now launches the dedicated Brief TUI directly (real experience); `cos research` / `cos capture` / `cos tasks` (and `calendar`) are clean placeholders. Full support for `cos --help`, `COS_ROOT`, and `python -m tui ...` parity.
- Dark, high-contrast theme inspired by Grok Build

## Quick Start (on your machine)

The cos TUI uses a project-local Python virtual environment so it never fights
with Homebrew's externally-managed Python (the error you saw with plain `pip`).

**One-time setup (do this in your "enabler" terminal or any terminal once):**

```bash
cd ~/projects/cos

# Create isolated venv (standard, recommended pattern)
python3 -m venv .venv

# Install the only runtime dep + dev tools (inside the venv)
.venv/bin/pip install --upgrade pip
.venv/bin/pip install textual textual-dev
```

**After that, the `cos` command (and everything else) just works:**

```bash
# 1. Make the launcher executable + symlink into PATH (once)
chmod +x scripts/cos
ln -s "$(pwd)/scripts/cos" ~/bin/cos

# 2. From ANY terminal/session (no activation needed):
cos
cos dashboard
cos brief          # direct launch of dedicated Brief TUI (real scans + Grok 'g')
cos --help

# Direct (also works, launcher finds the .venv automatically):
./scripts/cos
./scripts/cos brief
```

The launcher (`scripts/cos`) + Python entry point (`tui/__main__.py`) now cleanly support:

- `cos` or `cos dashboard` → launches the main TUI dashboard (tiles + full hotkeys)
- `cos brief` → launches the dedicated Brief TUI screen directly (full real implementation with live vault scans, writes, and Grok skeleton — equivalent to 'b' inside dashboard but as a top-level/standalone command)
- `cos research`, `cos capture`, `cos tasks` (or `cos calendar`) → clean placeholders (helpful messages; dedicated screens coming in parallel waves)
- Respects `COS_ROOT` env var or defaults to `~/cos` (and auto-detects when run from inside the source tree)
- `cos --help` for usage (rich epilog listing all subcommands + Grok notes)
- Same behavior via `python -m tui ...` (for dev / agents / no symlink)

Once running (in dashboard):
- `ctrl+r` → light refresh (reload whatever is already on disk)
- `u` → Update all (force the shared Cowork/Grok ensure: checks real data staleness, refreshes only if needed via the common refresh_* paths — the "eliminate redundancy" + 7:30am-after-Cowork experience)
- `b` → BriefScreen (real: triggers dashboard refresh + full dedicated view with vault scans + writes)
- `g` (inside BriefScreen) → run Grok AI News skeleton (writes to data/ai-news.json; UI updates)
- `?` → help overlay (full hotkey + future notes)
- `q` → quit

From CLI (even without launching dashboard first):
- `cos brief` → direct dedicated Brief view (Grok 'g' available immediately)

## Subcommands & Future CLI

The unified `cos` CLI entry point (per the model-agnostic migration plan / PRD Phase 1) has been enhanced for clean subcommand dispatch:

- Primary today: `cos` / `cos dashboard` (the full mission control TUI with reactive tiles and hotkeys)
- `cos brief` : **dispatches directly to the real dedicated BriefScreen TUI** (no longer a text placeholder). You get the full in-app /brief experience (live READ-ONLY vault scans for inbox/workbench/journal, canonical markdown, 'w' write to status.json + brief-YYYY-MM-DD.md, 'g' Grok AI News skeleton writing to the reserved ai-news.json slot, all hard rules honored). Perfect top-level entry for scripts, agents, or quick access.
- Placeholders (recognized cleanly with no "invalid choice" errors, helpful guidance): `cos research`, `cos capture`, `cos tasks`, `cos calendar`. These print status + point to:
  - Current in-TUI hotkeys ('r'/'c'/'t')
  - The source toolbox/*.md skill prompts
  - Grok integration notes (especially for research/brief)
  - The PRD and this README
  - Will be upgraded to real dedicated screen launches (same BriefHostApp pattern) as the parallel waves complete the screens.
- Full parity: `python -m tui brief`, `python -m tui research`, etc. all work.
- All paths go through the existing `tui/data/loader.py` contracts (COS_ROOT-aware) and honor the one-writer / vault-read-only rules.
- The dispatch logic lives in `tui/__main__.py` (with detailed internal TODOs for the next waves) + thin delegation in `scripts/cos`.

`cos brief` now provides immediate, first-class CLI access to the full Brief + Grok skeleton experience. Other dedicated views (Research, Capture, Tasks/Calendar) are in active parallel implementation and will follow the exact same dispatch + Screen pattern.

See `tui/__main__.py` (the enhanced entrypoint) and the PRD for the direction toward richer options (e.g. `cos research "query"`).

## Next Milestones (in priority order)

1. ~~Proper visible hotkey bar + help overlay with the proposed defaults (`b`=brief, `r`=research, `c`=capture, etc.).~~ **DONE** (help overlays updated; real behavior documented)
2. ~~First real dedicated view (e.g. full Brief screen or quick Capture modal).~~ **DONE** (BriefScreen MVP with full real logic)
3. ~~Wire one action that actually triggers work (run the brief logic in-process or via the future `cos` CLI and refresh the UI).~~ **DONE** ('b' hotkey now does real refresh_data + opens BriefScreen; BriefScreen itself has live actions + writes; `cos brief` now launches it directly)
4. ~~Grok Build color/font polish + first Grok-powered action (e.g. "run with Grok" for research).~~ **DONE** (Grok skeleton wired in BriefScreen: 'g' + button; writes real ai-news.json stub to data layer; UI renders it; full comments + help)
5. ~~Packaging / `cos` entry point so you can just type `cos` from anywhere.~~ **DONE** (2026-05-26 prior: improved `scripts/cos` bash launcher + `tui/__main__.py` argparse dispatch + COS_ROOT support + doc updates).
6. ~~Enhance launcher for clean subcommand dispatch + README (wave2-5).~~ **DONE** (this update: `tui/__main__.py` now does real TUI dispatch for `cos brief` (BriefHostApp + BriefScreen) + clean placeholders for research/capture/tasks/calendar; rich help/epilog; internal TODOs for next waves; `scripts/cos` comments refreshed with supported commands + TODO. Updated this README with full current status, run examples, subcommand docs, Grok notes, and milestone. Tests: `cos --help`, `cos brief`, `python -m tui dashboard` etc. all work cleanly.)

## Architecture Notes

This TUI is deliberately thin on business logic. It is a **consumer** of the same data contracts that everything else (Cowork skills, future Grok tools, briefs) uses. This is the heart of the model-agnostic design.

No data is duplicated. All "work" (refreshes, research, capture, etc.) either happens in-process (for speed) or by calling out to the shared `cos` CLI / Grok-powered scripts.

The new `ensure_fresh_data` (loader) + `_ensure_and_load` (TUI on startup + 'u' hotkey) is the concrete shared mechanism: it inspects mtimes of the canonical contracts (populated by Cowork or prior runs), only invokes the exact same `refresh_*` functions if stale (>~20h) or forced, and surfaces a clear reason. This is the direct implementation of the plan review feedback ("check Cowork data first... run yourself only if stale", "automatically triggered on startup", "populate the data first", "eliminate redundancy", "same processes" for Grok and Cowork).

The Grok skeleton demonstrates the approved integration path: a method stub ready for real Grok X tool calls that write directly to the data layer (overview-brief/data/ai-news.json etc.). `cos brief` + the 'g' action inside it is the first visible end-to-end example.

## Development

For live-reload work inside the project:

```bash
# Activate the venv for this shell (only needed for direct `textual` CLI usage)
source .venv/bin/activate

# Nice dev experience (hot reload)
textual run --dev tui.app:CosDashboardApp
```

You can also run the TUI directly with the venv python:
```bash
.venv/bin/python -m tui
.venv/bin/python -m tui brief   # dedicated view directly
```

( Note: the dev command uses the direct class path; the `cos` launcher / `python -m tui` path is the user-facing one. The launcher auto-detects `.venv` so you rarely need to activate. )

See the parent `prds/` directory for the full model-agnostic + terminal dashboard plan (especially PRD-cos-model-agnostic-migration-and-terminal-dashboard.md for the unified `cos` CLI direction and Grok layer).

**out-3 (model-agnostic foundation) complete:** Machine-readable JSON Schemas (in tui/data/loader.py:JSON_SCHEMAS + get_json_schema) + dataclasses/validate_contract for the 6 core contracts (runway, open_questions, stale_notes, intake_queue, upcoming, status, ai_news). Grok layer: standalone refresh_finances (real csv+compute), refresh_* for other domains, write_grok_ai_news (for X-briefs), refresh_all. All importable (`from tui.data.loader import ...`), honor hard rules, no new files. Unified CLI: `cos refresh [finances|kb|...|all]` dispatches (in tui/__main__.py). Enables full Grok Build / Hermes runtime over the data layer. See loader.py source + tests/.

---

This is the visible, delightful entry point into making `cos` a first-class terminal-native personal OS while staying 100% compatible with your existing Cowork setup.
