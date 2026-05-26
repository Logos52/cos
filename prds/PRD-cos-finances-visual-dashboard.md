# PRD: Finances Visual Dashboard & Graphs (ASCII/Unicode)

**Owner:** Wedge  
**Date:** 2026-05-27  
**Status:** Draft — Ready for review and prioritization  
**Related:** PRD-cos-model-agnostic-migration-and-terminal-dashboard.md, PRD-cos.md, current TUI implementation in `tui/`

---

## Problem

The current Finances tile in the cos terminal mission control dashboard is functional but visually lightweight and information-poor compared to the ambition of the system. It shows basic numbers (runway months, net monthly, etc.) in a uniform box, the same as every other domain.

The user wants Finances to evolve into a **visually rich, first-class "workspace"** within the dashboard:

- Default view should be **numberless** (graphs and visual shapes only) for quick emotional/systemic understanding.
- Numbers and details should appear on demand (click / expand / dedicated view).
- The tile should feel like the entry point to a richer **Finances workspace/dashboard** rather than just another data box.
- This must fit into the larger desired masonry/responsive grid layout with proper visual hierarchy (Brief largest, Learning + Knowledge Work next tier, Finances appropriately weighted).

Additionally, as we move toward the full model-agnostic vision, Finances is a high-leverage domain for demonstrating rich, Grok-augmented visuals that Cowork alone struggles to produce elegantly.

---

## Goals

- Deliver **ASCII / Unicode art graphs** (sparklines, simple bar charts, trend lines, goal progress visuals) in the main Finances tile.
- Make the default presentation **numberless** — shapes and patterns convey the story at a glance.
- Provide a clear, low-friction path to **expand / click into a dedicated Finances workspace** that reveals full numbers, details, and richer interactions.
- Ensure the implementation feels native in the Textual TUI and works beautifully with the planned masonry/responsive grid design.
- Keep the data layer clean and model-agnostic (new visualization data can be added to existing contracts or new lightweight published artifacts).
- Lay groundwork for future Grok-powered insights (e.g., "Grok-generated commentary" or trend analysis that can be rendered alongside the graphs).

---

## Success Criteria

- The Finances tile in the main dashboard renders attractive, readable ASCII/Unicode graphs without numbers by default.
- Clicking or activating the tile (keyboard or mouse) smoothly transitions the user into a richer Finances view/workspace.
- The visual design works well inside the overall dashboard layout (masonry or prioritized grid) and maintains high contrast / Grok aesthetic.
- Data required for the graphs is available via the existing or lightly extended data contracts.
- The feature is implemented in a way that is easy to evolve (future richer charts, Grok annotations, historical views, etc.).
- Performance and responsiveness remain excellent (no heavy dependencies).

---

## Scope

**In (MVP for this PRD):**
- Design and implementation of 2–4 core graph types using pure Rich / Unicode (runway trend sparkline, goal progress bars, net monthly direction, simple historical comparison).
- Numberless default rendering in the main dashboard tile.
- Click / hotkey / focus action that opens a dedicated Finances workspace Screen (can start simple and grow).
- Minimal data contract extensions (if any) in `finances/data/runway.json` or a new lightweight visualization artifact.
- Integration notes with the planned masonry/responsive dashboard layout.
- Basic keyboard + mouse navigation into the expanded view.

**Out (future phases or separate PRDs):**
- Full interactive charting library or canvas-style visuals.
- Historical multi-year views and advanced analytics.
- Grok-generated narrative overlays on the graphs (this can be added later on top of the rendering layer).
- Export, sharing, or printing of the visuals.
- Mobile or other non-terminal renderings.

**Non-goals:**
- Replacing the existing number-based tile entirely in one step (we can keep backward compatibility during transition).
- Heavy computation or external data fetching inside the TUI tile itself (respect the data-contract philosophy).

---

## Current State (as of 2026-05-27)

- Basic Finances tile exists in `tui/app.py` (`DomainTile` for "Finances").
- It renders runway months, net monthly, and US return months from `finances/data/runway.json`.
- The data is produced by `refresh_finances()` in `tui/data/loader.py` (reads `finances/inputs/goals.json` + `income.csv`).
- Dedicated screens pattern already exists (BriefScreen, ResearchScreen, etc.) and is wired to hotkeys.
- The overall dashboard is moving toward a more sophisticated layout (masonry/responsive grid with visual hierarchy).
- No graph or visual rendering currently exists for any domain.

---

## Design Approach

### Visual Language (ASCII / Unicode)
We will use pure Rich-compatible Unicode characters for graphs:

- Sparklines for runway trend over time.
- Block characters (█ ▄ ▀ etc.) or simple bar charts for goal progress.
- Directional arrows / mini trend indicators for net monthly.
- Subtle background shading or border styles to make Finances feel distinct but harmonious.

Example (illustrative, not final):

```
Finances
Runway Trend: ▁▂▃▅▆▇█  (improving)
Goals Progress:
  US Relocation    ████████░░  68%
  Investments      ████░░░░░░  42%
Net Direction: ▲ +$420/mo
```

Numbers hidden by default. On expand/click they appear alongside or in a detail pane.

### Interaction Model
- Main dashboard tile: Visuals only + very high-level summary.
- Activation (Enter, click, or dedicated hotkey): Pushes a richer `FinancesWorkspaceScreen`.
- The workspace can start as an enhanced version of the current data + graphs and grow into a full domain dashboard over time.

### Data Considerations
- Extend `runway.json` with optional visualization-friendly fields (e.g., `runway_history`, `goal_visuals`, or keep it separate).
- Or introduce a lightweight `finances/data/visuals.json` published artifact (preferred for keeping contracts clean).
- The existing `refresh_finances()` can be enhanced to compute simple graph data.

### Integration with Dashboard Design
This work directly supports the desired masonry/responsive layout:
- Finances can be given appropriate visual weight (smaller or differently styled tile).
- The "own dashboard on click" behavior gives it the importance it deserves without dominating the main view.

---

## Phased Implementation

**Phase 0 – Foundations (small)**
- Decide on exact graph vocabulary (which 3–4 visuals to start with).
- Define minimal data shape for the graphs.
- Spike simple Unicode graph rendering in a test widget.

**Phase 1 – Main Tile Visuals**
- Implement numberless graphs in the existing Finances `DomainTile`.
- Wire basic expand/click behavior (can initially push a placeholder or enhanced detail view).
- Ensure it works cleanly inside the current (and future masonry) layout.

**Phase 2 – Dedicated Finances Workspace**
- Create `FinancesWorkspaceScreen` (or equivalent) with richer graphs, tables, and controls.
- Make the transition from main tile feel natural and delightful.
- Add keyboard navigation and help text.

**Phase 3 – Polish + Grok Extension**
- Optional Grok-powered annotations or alternative views on the graphs.
- Performance tuning, accessibility, and visual refinement.
- Documentation and examples in the PRD / README.

---

## Risks & Mitigations

- **Over-engineering the graphs too early** — Mitigated by strict "ASCII/Unicode only" constraint for Phase 1–2.
- **Layout conflicts with masonry design** — Close coordination with the dashboard layout work; treat Finances visuals as one consumer of the new grid system.
- **Data contract bloat** — Keep visualization data in optional or separate published files rather than polluting the core `runway.json` contract.

---

## Open Questions

- Which 3–4 specific graphs/visuals should be in the first implementation?
- Should the expanded Finances workspace replace or augment the existing dedicated screens pattern?
- How much historical data should we keep/render by default (last 6 months? 12? user-configurable)?
- Do we want any interaction inside the main tile itself (e.g., left/right to cycle views) or is "click to expand" the only path?
- Naming: "Finances Workspace", "Finances Dashboard", or something else?

---

## Relationship to Other Work

- Directly supports the "masonry / responsive grid" and visual hierarchy direction discussed in the terminal dashboard evolution.
- Advances the full model-agnostic + rich per-domain experience ambition without blocking other domains.
- Creates a good template for future visual work in other areas (e.g., Learning progress visuals, Knowledge Work activity graphs).

---

**Next Action:** Review and approve this PRD (or specific sections), then we can begin the Phase 0 spike (graph vocabulary + simple rendering prototype) while the overall dashboard layout work continues in parallel.

This keeps the full ambition alive while giving us a concrete, valuable, and visually distinctive piece of work to ship relatively quickly.