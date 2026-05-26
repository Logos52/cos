# PRD / Roadmap — Model-Agnostic cos + Grok Integration + Terminal Dashboard

**Owner:** Wedge  
**Date:** 2026-05-26  
**Status:** In progress — TUI MVP + Grok skeleton advanced (see Current Status); out-4 (PRD updates, Cowork surface doc in README, Autonomy Charter) complete — 2026-05-26  
**Related:** PRD-cos.md (original), PRD-overview-brief.md (Phase 2 Grok slot already reserved), AGENTS.md / operating-instructions.md

---

## Problem

`cos` is currently tightly coupled to Claude Cowork's Productivity plugin for:
- Scheduled refresh workflows and the daily / overview brief
- Skill execution surface (`/today`, `/research`, `/capture`, `/brief`, builder)
- TASKS.md backing + plugin memory
- `dashboard.html` rendering (currently a self-contained snapshot)

This creates several problems:
1. **Not model-agnostic** — The original PRD-cos.md header claims "model-agnostic — any capable agent can execute", but the runtime is Cowork-only. Grok Build, Hermes, or standalone scripts cannot easily drive the system.
2. **X briefs and deep Grok data are blocked** — Cowork has limited (or no) first-class X research depth. The owner wants rich, scheduled X thread synthesis and Grok-powered research that feeds the brief. PRD-overview-brief.md already reserves `data/ai-news.json` for "Phase 2 — Grok Build", but no implementation path exists.
3. **No terminal-native dashboard** — The current `dashboard.html` is excellent for always-on visual in the browser but the owner builds Textual apps and has explicitly listed "Textual TUI — planned later dashboard view for `cos`" in memory/people.md and learning goals. A real personal OS needs a first-class terminal experience.
4. **Prior improvement areas remain unaddressed** — Instruction duplication (AGENTS.md vs operating-instructions.md), lack of machine-readable data contracts, human maintenance burden on `inputs/`, and incomplete migration hooks for the data layer as the stable contract.

The goal is to keep everything that works in Cowork while making the system fully portable, Grok-first where it adds unique value (X research, deep synthesis), and future-proof for a Textual (or other) terminal UI over the same data.

---

## Success Criteria

- A single, versioned data contract (schemas + examples) that any consumer (Cowork refreshes, Grok scripts, Textual app, Hermes) can rely on.
- Grok-powered X briefs and enriched research that write structured output consumable by the main brief pipeline (honoring the existing `ai-news.json` / overview-brief slot).
- Working Grok-native equivalents (or supersets) of the key skills (`cos brief`, `cos research`, `cos capture`, etc.) that can run standalone or be called from Cowork.
- Clear decision + initial plan for the terminal dashboard (Textual recommended).
- Instruction duplication resolved; single canonical source with governance.
- Small, approvable first steps that deliver visible value without big rewrites.

---

## Scope

**In (Phase 1 foundation + quick wins):**
- Deduplicate operating instructions (AGENTS.md vs operating-instructions.md) → single canonical source + references only.
- Extract machine-readable data contracts (at minimum for the 5 core `data/*.json` files + overview-brief/status.json).
- Design + skeleton for Grok layer (`grok/` or `tools/grok/`) that mirrors the existing brief/skill logic but can use native X tools, deeper research, etc.
- X-brief pipeline that writes to the reserved slot in overview-brief.
- Unified "cos" CLI entrypoint pattern (so `cos brief` and Cowork `/brief` stay in sync).
- Decision record + high-level plan for terminal dashboard (Textual vs tmux).
- Document Cowork-specific surface (schedules, plugin dependencies) so it is explicit and not accidental lock-in.

**Out (later phases or separate PRDs):**
- Full port of all Cowork refreshes to Grok/Hermes (start with one domain as prototype).
- Complete Textual dashboard implementation (this doc produces the decision + architecture + first vertical slice plan).
- Autonomous Builder migration.
- Health domain expansion.

**Non-goals:**
- Changing the existing Cowork experience (it continues to work).
- Writing to the Obsidian vault except via the existing `/capture` gated path.

---

## Architecture — Model-Agnostic Foundation

### Core Principle (restated from PRD-cos.md)
The **data layer** (`data/*.json`, `memory/`, selected `inputs/`, `outputs/`, and now `grok/` artifacts) is the stable contract.  
Everything else (Cowork workflows, Grok scripts, Textual app, future Hermes skills) is a consumer/producer of that contract.

### Layers

1. **Data Contracts** (new, high priority)
   - Machine-readable schemas (JSON Schema or Pydantic models) for every `data/` file.
   - Living examples + validation.
   - Versioned (v1 today, with clear evolution rules).

2. **Cowork Surface** (keep as-is for now)
   - Scheduled tasks (cos-*-refresh, cos-overview-brief-refresh, dashboard-refresh).
   - Productivity plugin TASKS.md, memory, skill runtime.
   - `dashboard.html` (snapshot or dynamic injection).

3. **Grok Layer** (new primary workstream)
   - Standalone Python CLI / scripts (`cos` command or `python -m cos`).
   - Richer implementations where Grok adds value (native X search, deeper synthesis, multi-step research).
   - Scheduled execution via cron, Grok scheduler, or Hermes.
   - Writes to the same data contracts (or new `grok/` subdirs that the brief aggregator knows how to consume).

4. **Unified Brief & Skill Surface**
   - `toolbox/brief.md` (Cowork) and `grok/brief.py` (or equivalent) both produce `briefs/brief-YYYY-MM-DD.md` + `overview-brief/data/status.json`.
   - The brief explicitly pulls from `data/ai-news.json` / X-brief artifacts (the reserved Phase 2 slot).

5. **Terminal Dashboard**
   - Textual app (recommended) that reads the exact same `data/*.json` files + optional Grok-enriched views.
   - Can run alongside or replace `dashboard.html` over time.
   - Same "new domain = new tile + data source" scaling model.

### One-Writer + Read-Only Rules (strengthened)
- Still enforced.
- New rule: Grok components document their writer (even if it's the same logical "cos" entity).

---

## Decision: Terminal Dashboard — Textual vs tmux

**Recommendation: Textual (strong).**

### Evidence from the project itself
- PRD-cos.md Decision 6 + §10: Explicitly chose `dashboard.html` for speed/cheapness in Cowork; "Textual `cos` app is a later, separate consumer of the same data layer."
- memory/people.md: "Textual TUI — planned later dashboard view for `cos`".
- learning-pipeline/inputs/reading-goals.md + intake-queue: Owner is actively studying "Textual reactive attributes guide".
- AGENTS.md + operating-instructions.md: List Textual as a core tool in the ecosystem.
- Zero mentions of tmux anywhere in the repository (grep across all .md + code).

### Technical & UX comparison
- **Textual**: Rich, component-based, reactive, mouse + keyboard, beautiful layouts, live updating, Python-native (matches owner's tool preferences and the "cos as personal OS" vision). Can consume the JSON contracts directly (or via a small shared library). Supports the exact same "new domain = new tile" pattern.
- **tmux**: Excellent multiplexer for combining existing CLIs (`watch -n 60 cat finances/data/runway.json`, `tail -f briefs/brief-*.md`, etc.). Zero new dependencies. However, it is not a "dashboard framework" — limited interactivity, no real widgets, hard to make polished or maintainable as complexity grows. Feels like a hack rather than the intended long-term UI layer.

**Conclusion**: tmux is acceptable for a 1-evening quick-and-dirty status bar. For the actual "terminal mode" of the personal OS the owner is building, **Textual is the only choice that aligns with the project's DNA, the owner's explicit plans, and the quality bar of the rest of cos**.

Phase 1 for the dashboard: Decision record (this doc) + a minimal vertical slice (e.g., Finances + KB tiles in a Textual app that reads the same JSONs as the current `D` object in dashboard.html).

---

## X Briefs + Grok Data in the Brief (already half-designed)

The architecture anticipated this:

- `overview-brief/inputs/config.json` has `ai_news_path`.
- `toolbox/brief.md`, `overview-brief/CLAUDE.md`, and PRD-overview-brief.md all reference Phase 2 Grok Build writing `data/ai-news.json`.
- Current briefs already surface X content that lands in the vault inbox.

**Plan**:
- Grok writes structured X-brief artifacts (e.g., `overview-brief/data/x-briefs/2026-05-26.json` or directly into the ai-news schema).
- The brief aggregator (whether Cowork prompt or Grok script) merges them.
- Use the native X tools available to Grok (keyword/semantic search, threads, etc.) for scheduled deep dives that Cowork cannot match.

This is one of the highest-ROI places Grok can add unique value immediately.

---

## Current Status (as of 2026-05-26, post TUI MVP waves + out-4 docs)
**Completed (verified in code/docs exploration):**
- TUI dashboard + live data binding: `tui/app.py` + `tui/data/loader.py` (tiles from real contracts: runway.json, stale-notes/open-questions.json, intake-queue.json, upcoming.json, overview-brief/data/status.json); graceful vault_error/calendar_unavailable handling.
- Hotkeys + 4 dedicated views: `b` (Brief real: vault scans read-only + writes + 'g' Grok X-brief to ai-news.json), `r` (Research real + Grok), `c` (Capture gated), `t` (Tasks/Calendar); all in `tui/screens/`, mirroring `toolbox/*.md` logic.
- Grok skeleton: X-briefs/research write structured to data layer (reserved ai-news.json slot + UI); ready for real X tools (x_semantic_search etc.).
- Unified CLI/launcher: `scripts/cos` (thin bash: COS_ROOT, venv, PYTHONPATH) + `tui/__main__.py` (argparse dispatch: `cos brief` launches real TUI; placeholders point to PRD/toolbox); `cos --help`, `python -m tui` parity.
- Theming + packaging partial: Grok dark high-contrast; global `cos` via symlink + documented venv (no full pip entrypoint yet).
- Data layer stable contract in use: per-domain `data/*.json` + overview-brief + loader (portable across Cowork/Grok/TUI).

**Remaining (roadmap items not yet complete):**
- Machine-readable schemas + validation for contracts.
- Standalone Grok refreshers (full Cowork workflow port).
- Live file watching.
- Full packaging (global entrypoint), parity, testing/validation.
- (Cowork surface doc + Autonomy Charter added by this out-4 task.)

**Model-agnostic progress:** TUI/CLI/Grok now working portable consumers of the data contracts; Cowork (toolbox/ + Productivity plugin schedules/TASKS.md/memory) is one optional surface, not the only runtime.

**TUI startup data freshness (refined 2026-05-27 per plan review comments):**
The focused auto-populate plan (see session snapshot) was approved with these explicit points:
- Check Cowork-populated data first (or prior shared runs). Only run refreshes yourself if not updated/stale. Primary goal: eliminate redundancy between Cowork chat commands, Grok workflows, and TUI.
- The check + conditional refresh is automatically triggered on TUI startup (if data is stale, e.g. more than ~20 hours old on key contracts such as runway.json, overview-brief/data/status.json, open-questions.json, etc.).
- Prioritize populating real data first via the shared `refresh_*` functions (same processes for Grok and Cowork). Designing a heavy "first run case" with demo seeding as the main UX is overkill; demo/sample data remains only as an optional, low-priority fallback for completely empty dev environments (e.g. running from the git tree with no real ~/cos data yet). Real ~/cos data + Cowork 7am schedule + hotkey manual "update all" is the experience.

Implementation lives in `tui/data/loader.py` (staleness helpers + `ensure_fresh_data` that reuses every existing refresh_*) + `tui/app.py` (on_mount + hotkey) + launcher/docs. Ties directly to the model-agnostic vision and the 7:30am-after-Cowork preference.

---

## Phased Roadmap

### Phase 0 — Immediate Hygiene (1–2 sessions)
- Deduplicate AGENTS.md / operating-instructions.md → choose canonical (AGENTS.md recommended) + update all references.
- Add governance rule in the canonical source: "All other instruction files must reference or include via link. Audit on every new PRD/domain."
- Quick win: Make the duplication risk visible in the next daily brief or a dedicated note.

### Phase 1 — Model-Agnostic Foundation (2–4 sessions)
- Extract data contracts (schemas + validation) for the core files.
- Create `grok/` (or `tools/grok/`) skeleton with a small shared library for reading/writing the contracts.
- Implement first Grok-powered component: X-brief pipeline + injection into overview-brief (honoring the existing slot).
- Unified CLI pattern (`cos brief`, `cos refresh --domain finances`, etc.).
- Document Cowork surface explicitly (schedules, what the plugin owns vs what the data layer owns). (Completed out-4 via root README.md section + this status update)
- Decision record + first vertical slice plan for Textual dashboard. (MVP complete: live tiles/hotkeys/4 real screens + Grok 'g' + unified `cos` CLI/launcher per tui/README.md + app.py + __main__.py)

### Phase 2 — Grok Skills & Deeper Integration (ongoing)
- Grok-native versions (or strict supersets) of the key skills.
- Scheduled Grok jobs (X research, deeper daily synthesis, research on demand).
- Optional: Grok-driven enrichment that writes "Grok notes" into `outputs/` or a new `grok/` folder that the brief can surface.

### Phase 3 — Terminal Dashboard (parallel or after Phase 1 foundation)
- Textual app that reproduces (and improves on) the current `dashboard.html` experience using the same data contracts.
- Live refresh, domain tiles, graceful handling of vault_error / partial data (exactly as the HTML does today).
- Can be run in terminal while Cowork dashboard continues in the browser.
- **Finances Visuals & Graphs** (see new `PRD-cos-finances-visual-dashboard.md`): Numberless ASCII/Unicode art graphs in the main tile, click-to-expand into a richer Finances workspace. First step toward visually rich, domain-specific experiences inside the overall masonry/responsive dashboard design.

### Phase 4 — Migration & Autonomy (future)
- Move individual refreshes/skills to Grok Build + Hermes runtime.
- Full Autonomy Charter (what can run unattended vs always gated). (Created out-4 as prds/AUTONOMY-CHARTER.md; references hard rules from CLAUDE.md + AGENTS.md; see also README Cowork surface section)
- Retire or deprecate Cowork-only surfaces only after equivalent capability exists outside it.

---

## Concrete Next Actions (Small, Approvable Wins)

1. **This week**: Resolve the instruction duplication (highest immediate risk per multiple agents). I can produce the exact consolidated version + diff for sign-off.
2. **Next 1–2 sessions**: Pick one data file (e.g., `finances/data/runway.json` + `overview-brief/data/status.json`) and produce the first machine-readable schema + validator. Tiny win that demonstrates the contract approach.

3. **out-5 (validation & testing, this session)**: Full end-to-end test suite created + run (13 tests passing after fixes). Unit: data loader + all contracts (incl. ai-news for Grok). Integration: TUI Pilot launch/binding/hotkeys + real Grok X-brief (ai-news.json write) + research writes. E2E: launcher `cos` / `python -m tui` dispatch + subcommands exercised. 2 critical bugs found & surgically fixed (loader stray future import at tui/data/loader.py:134; TUI grid.clear() -> remove_children() in app.py:181). Schemas from out-3 now loadable (model-agnostic foundation). See tests/unit/test_data_loader.py, tests/integration/test_*.py (abs paths in /Users/n1/Projects/cos/tests/). MVP validated + ready for packaging/Grok foundation. (No new docs; updated here surgically.)
3. **Decision gate**: Approve "Textual for terminal dashboard" (with the evidence above) so we can start a minimal vertical slice without bikeshedding.
4. **Quick Grok value demo**: Implement a one-off Grok X-brief generator (using the available X tools) that writes to the reserved slot and appears in the next overview brief. Visible proof that the Phase 2 handoff works.

---

## Open Questions (for sign-off)

- Preferred name/structure for the Grok layer (`grok/`, `tools/`, `cos-cli/`?)?
- Do we want a single `cos` Python package that both Cowork prompts and standalone Grok scripts can import, or keep them loosely coupled via the JSON contracts only?
- Target for first Textual vertical slice (Finances + KB tiles? Full 4-domain + Knowledge Work)?
- Any hard constraints on where scheduled Grok jobs run (local cron, a small VPS, Hermes, GitHub Actions, etc.)?

---

This document turns the prior sub-agent findings + the new explicit requirements (model-agnostic + Grok/X + terminal dashboard) into one coherent, phased, approvable plan that respects the existing Cowork experience while systematically removing the accidental lock-in.

Ready for review and explicit "proceed" on Phase 0 + the Textual decision.