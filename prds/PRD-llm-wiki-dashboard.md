# PRD — Unified Mission Control (`llm-wiki-dashboard`)

> [!PARTIALLY SUPERSEDED] **Surface direction superseded by `PRD-cos-home-terminal.md` (2026-05-27).** The HTML-primary / hosted-in-Obsidian decision (D-2) is replaced by a Textual terminal app as the primary home. Still live from this doc: the fusion intent (D-1) and the read-only-vault + privacy guardrails, which the new PRD carries forward. Kept for history; deletion deferred.

**Owner:** Wedge · **Author:** Claude (Cowork) · **Build surface:** spec authored in Cowork; build lane TBD (Grok Build recommended, consistent with the existing cos generator)
**Status:** DRAFT — for sign-off. Nothing is built. This PRD is the proposal.
**Date:** 2026-05-27
**Adapts:** `PRD-cos.md`, `PRD-cos-dashboard-basecamp.md`
**Supersedes (proposed):** the cos Basecamp dashboard as a *cos-only* surface — see Decision D-1 and Open Question O-1.
**Related context (vault):** `journal/2026-05-23-Possible-Paths-Autonomous-OS-Dashboard-and-Builder-System.md`, `journal/2026-05-24-Fresh-Start-Personal-Workflow-OS-Checklist.md`, `journal/2026-05-26-COS-and-Knowledge-Base-Operating-System-Progress.md`, `00 Command Center/Home.md`, `mg-kolbs/`.

---

## 0. What changed since the last decision (read this first)

This PRD deliberately **reverses a prior decision** and you should confirm that before anything else.

Your 2026-05-24 "Fresh Start" checklist and 2026-05-26 progress note drew a hard line: *"cos is independent from llm-knowledge-base. Pipeline status not surfaced here,"* with skills/experiments and wiki-health pulse explicitly **deferred** out of cos, and the relationship fixed as `cos = operating surface / llm-knowledge-base = durable thinking layer`.

You have now asked to **fuse the two into one dashboard**. That is a direct override of the "independent" decision. It is a reasonable change — the two systems share a person, a day, and a set of decisions — but it is load-bearing, so it sits at the top as **Decision D-1** and **Open Question O-1**. Everything below assumes the fusion is approved.

What does *not* change: the **read-only-against-the-vault** guardrail and the **privacy display mode** for financial data. Those survive the fusion intact (see §8).

---

## 1. Executive summary

A single **mission-control launchpad** that fuses your operating layer (cos: overview brief, finances, tasks & calendar, learning) with your thinking layer (the Obsidian vault: synthesis pipeline, wiki health, open questions, skills & goals). It does two jobs at once:

1. **See** — surface the live state of both systems in one calm, scannable, Basecamp-style surface, where **each card has its own visualization** (a funnel is not a progress bar is not a sparkline).
2. **Move** — act as a *jumping-off point* from data into work: every card can launch you into the right place — open the note in Obsidian, start a Kolb's reflection, kick a Grok Build / Hermes skill, drop into Cowork.

It is **sourced from** both the cos local data contracts and a read-only scan of the vault, **hosted mostly in Obsidian** (HTML cockpit + native Bases views), and it **never writes the vault** — editing happens where you already edit, in Obsidian.

The governing principle, lifted from your own 2026-05-26 note: the dashboard separates *what I can do* from *what needs my judgment*.

---

## 2. Problem

You operate across two adjacent systems and a spread of tools, and there is no single surface that shows both at once or gets you from "what's the state" to "doing the next thing":

- **State is scattered.** Finances, an X/AI news brief, the calendar, the raw→workbench→wiki pipeline, wiki health, open questions, and the mg-kolbs skills/goals system each live in a different place. Assembling the picture is manual.
- **Your #1 pain is vault coherence** — duplicate/stale notes, decisions and open questions getting buried. There is no surface that makes staleness, orphans, and unanswered questions *visible* so they can be acted on.
- **There is no launchpad.** Even when you know the state, getting into the work is a separate navigation step. The dashboard should be the place you *start the day from and act out of*, not a passive report.
- **The mg-kolbs trackers don't render.** Goals, Skills, 1% Gains, 30 Day Plan all contain ```dataview``` "Live View" blocks — but **Dataview is not installed**, so those blocks show nothing today. The skills/goals system is effectively invisible in-app.
- **The cos dashboard and the vault are siloed.** The existing cos Basecamp dashboard shows cos's operating domains but, by prior decision, deliberately excludes the vault. You now want them together.

---

## 3. Goals and non-goals

### Goals
- One unified, self-contained dashboard surface fusing cos's operating domains and the vault's knowledge surfaces.
- Basecamp design language, but **distinct per-card visualizations** — the layout you like, with a viz matched to each card's data.
- A genuine **launchpad**: every card offers at least one action that lands you in Obsidian or an AI tool.
- Make **skills + goals (mg-kolbs)** first-class and *actually visible* — fixing the broken Dataview situation via native **Bases**.
- Make the **coherence pain** visible: stale notes, orphans, open questions, pipeline maturity.
- **Read-only against the vault** for all automated scans; **privacy mode** for finances. Human edits in Obsidian; AI writes only on explicit confirmation.
- Model-agnostic data layer (any agent or script can populate the contracts) — inherited from cos.

### Non-goals (this build window)
- **Autonomous builder / overnight execution.** Out — that's the separate "Possible Paths" track.
- **A second dashboard.** The intent is *one* surface, not a cos dashboard plus a vault dashboard (see D-1).
- **Writing to the vault from the dashboard.** The dashboard launches you into Obsidian; it does not edit notes. (On-demand, confirmed AI capture is a future option, mirroring cos `/capture`.)
- **Health domain.** Placeholder only, as in cos — no unified health data source yet.
- **Live in-page fetch / a running server.** Snapshot model, per the cos spike (Path C). See §7.
- **Rebuilding the cos data contracts.** Finances/brief/tasks/learning contracts already exist and work; we reuse them.
- **A polished public (Quartz) version.** This is a personal operating surface first; publishing is future work.

---

## 4. Success criteria

- A generator emits a single self-contained `dashboard.html` that fuses cos + vault data, opens from disk / inside Obsidian, no server, no runtime fetch.
- Every fused domain has a card with (a) key stats, (b) a card-appropriate visualization, and (c) at least one launch action.
- Skills & goals render **live and editable** in Obsidian via Bases (no Dataview dependency).
- Stale notes, orphans, and open-question counts are visible and clickable through to the offending notes.
- Regenerates on demand (a `dashboard` command) and on a schedule; generation timestamp + per-card freshness shown.
- Degrades gracefully: a missing/stale/empty contract → a ⚠ badge and "not yet populated," never a crash or a broken chart.
- Zero writes to the vault by any scheduled/automated path (verifiable).
- Finances render with numbers hidden by default (graphs/relative only); exact figures only on explicit drill-in.

---

## 5. The mission-control model

Three layers, same as cos, extended to two data sources:

1. **Source data** — *(a)* cos local JSON contracts under `~/cos/**/data/` (operating domains) and *(b)* a **read-only scan of the vault** at `~/llm-knowledge-base/` writing new JSON contracts (knowledge domains). Plain files only. Connectors (Calendar, X/web) and the vault are *sources*, never storage.
2. **Generator** — reads every contract, normalizes timestamps, computes freshness, and bakes one `dashboard.html` with all values embedded. Pure renderer: reads contracts, never writes them, never touches the vault.
3. **Surface** — the HTML cockpit (primary) + native **Bases** views in the vault for live skills/goals editing (secondary). Launch actions bridge to Obsidian and AI tools.

**See vs. Move.** Each card answers two questions:
- *See:* what is the state? (stats + viz, as of last generation)
- *Move:* what can I do from here? (launch actions)

And it visually separates **what I can do** (safe, one-click launches) from **what needs my judgment** (review/decide items — surfaced, never auto-resolved).

---

## 6. Architecture

```
                 ┌──────────────────────────── SOURCES (read-only) ───────────────────────────┐
  cos workflows  │  ~/cos/**/data/*.json         |     ~/llm-knowledge-base/  (Obsidian vault) │
  (existing)     │  finances, overview-brief,    |     markdown + YAML frontmatter + folders   │
                 │  tasks-calendar, learning      |     + git history                           │
                 └───────────────┬───────────────┴──────────────────┬──────────────────────────┘
                                 │                                   │ (read-only scan)
                                 ▼                                   ▼
                    cos contracts (unchanged)            NEW vault-scan workflows  ──►  NEW JSON contracts
                                 │                                   │   (kb-pipeline, wiki-health, skills-goals)
                                 └───────────────┬───────────────────┘
                                                 ▼
                                   GENERATOR (extends scripts/generate_dashboard.py)
                                   reads all contracts → embeds → one dashboard.html
                                                 │
                         ┌───────────────────────┼─────────────────────────┐
                         ▼                        ▼                         ▼
                  HTML cockpit (primary)   obsidian:// launches      cos:// launches (AI/CLI)
                  Basecamp layout,         open/new notes,           Grok Build, Hermes skills,
                  per-card viz             Bases views               Cowork  (+ copy fallback)
                                                 │
                                                 ▼
                              Native Bases views in the vault (live skills/goals editing)
```

### Key decisions behind the architecture
- **Scanners write JSON; the generator only renders.** This is the proven cos pattern. The vault scan is just another contract-writer — it reads the vault read-only and writes JSON into `~/cos/knowledge-base/data/` (and a new skills/goals contract). The generator never knows or cares where a contract came from.
- **One generator, two sources, one dashboard.** Fusion = extend the existing generator to read the new vault contracts and render the new/expanded cards. We do *not* stand up a second dashboard (D-1).
- **Hybrid is real and grounded:** HTML cockpit = at-a-glance + launchpad; **Bases** = the live, editable database the dashboard links *into* for skills/goals. They are complementary, not redundant.
- **Read-only vault is non-negotiable** and inherited verbatim from cos. The only writer to the vault is you (in Obsidian) or a future explicit, confirmed capture action.

---

## 7. Design language, layout, and host model

### Design language — Basecamp-inspired, viz-per-card
Inherits the cos Basecamp palette (warm off-white `#FFFDF7`, white cards, `#1B9E55` green accent, `#F5F1EB` sidebar, 10–12px radius, subtle shadow, generous spacing, hover lift) and the light/dark toggle. **The new requirement vs. cos:** each card carries a *distinct* visualization rather than uniform stat rows. Domain color coding per card header strip + sidebar indicator.

### Layout
Sidebar + responsive card grid, header shows snapshot time + regenerate affordance, click a card to expand inline (full-width) for richer detail — same skeleton as the current `dashboard.html`.

```
┌───────────────────────────────────────────────────────────────┐
│  Header: Mission Control · Snapshot 07:15 ICT 2026-05-27  ☀/🌙 │
├──────────────┬────────────────────────────────────────────────┤
│  ● Focus      │   ┌── Overview Brief ──┐ ┌── Finances ───────┐ │
│  ● Brief      │   │ headlines + review │ │ runway bar (priv) │ │
│  ● Finances   │   └────────────────────┘ └───────────────────┘ │
│  ● Knowledge  │   ┌── Knowledge Base ──┐ ┌── Wiki Health ────┐ │
│  ● Wiki Health│   │ L4→L1 funnel       │ │ orphans/stale +   │ │
│  ● Questions  │   │ + status maturity  │ │ Dimensions radar  │ │
│  ● Skills     │   └────────────────────┘ └───────────────────┘ │
│  ● Goals      │   ┌── Open Questions ──┐ ┌── Tasks & Cal ────┐ │
│  ● Tasks      │   │ themed bars        │ │ agenda list       │ │
│  ● Learning   │   └────────────────────┘ └───────────────────┘ │
│  ● AI         │   ┌── Skills (MG) ─────┐ ┌── Goals (Kolb) ───┐ │
│  ──────────   │   │ level progress     │ │ progress + cycle  │ │
│  Active focus │   └────────────────────┘ └───────────────────┘ │
│  [?] help     │   ┌── Learning queue ──┐ ┌── AI Launchpad ───┐ │
└──────────────┴────────────────────────────────────────────────┘
```

### Host model — "mostly run on Obsidian" (needs your pick — O-2)
Three viable ways to host the HTML inside/alongside Obsidian:
- **A. Standalone, launched from Obsidian** — `dashboard.html` opens in the browser; a bookmark/URI in Obsidian launches it. Simplest, fully faithful, zero plugin risk. (Recommended for v1.)
- **B. Embedded in a note via iframe** — an `<iframe src="...dashboard.html">` inside a Markdown note, or the **Webviewer** core plugin (currently disabled). Keeps it "in Obsidian" visually; some rendering constraints.
- **C. Hybrid (recommended overall)** — A or B for the cockpit **plus** native **Bases** views for skills/goals (live, editable, in-app). This is the "hybrid" you referenced.

---

## 8. Card specifications

Each card: **Source** (which contract) · **Viz** (the per-card visualization) · **Launch** (the action[s]). Cards marked ★ are v1 core.

### ★ Active Focus / North Star  *(launchpad spine)*
- **Source:** a small `focus.json` contract (current focus + last-session focus) — manually set or captured.
- **Viz:** a single prominent banner line — current north-star initiative — with a faint "last session" continuity line beneath.
- **Launch:** open the focus note in Obsidian; set/replace focus (confirmed capture).

### ★ Overview Brief
- **Source:** `overview-brief/data/status.json` + `overview-brief/data/ai-news.json` (X / AI synthesized news) **plus** one "resurface this" vault note pick from the wiki-health scan.
- **Viz:** headline + compact synthesized-news list; one "note to review" chip from the vault.
- **Launch:** `cos://brief` (run/refresh brief); open the picked note in Obsidian.

### ★ Finances  *(privacy mode)*
- **Source:** `finances/data/runway.json`.
- **Viz:** runway bar + goal-progress bars — **numbers hidden by default** (relative bars / percentages only); exact figures revealed only on explicit drill-in. (Your Fresh-Start privacy model.)
- **Launch:** `cos://research?ticker=…`; drill-in to reveal figures.

### ★ Knowledge Base — Synthesis Pipeline
- **Source:** new `knowledge-base/data/kb-pipeline.json` from the vault scan: counts for raw/inbox + Clippings, workbench (L3/L2), wiki (L1); status distribution (draft / developing / seed / stable); promotion candidates.
- **Viz:** L4→L3→L2→L1 **funnel** + a **status-maturity stacked bar**.
- **Launch:** open `workbench/`; open `notes/index`; launch a triage/synthesis skill (`cos://` → Grok/Hermes).

### Wiki Health
- **Source:** new `knowledge-base/data/wiki-health.json` from the scan (can reuse/extend `tools/maintenence/drift.py` + `maintenence.py`): orphan notes, broken wikilinks, stale notes (by `updated`/mtime), Five Dimensions coverage.
- **Viz:** small bars for orphans/broken/stale + a **Five Dimensions radar/heatmap**.
- **Launch:** run health check (`cos://` → Hermes/Grok); open a flagged note in Obsidian.

### Open Questions & Decisions
- **Source:** parse `00 Command Center/Open Questions.md` (counts by theme, most recent) + any frontmatter-flagged decisions.
- **Viz:** **themed horizontal bars** (System Design, Metacognition, Agentic Engineering, Language, …) with recent-question chips.
- **Launch:** open Open Questions.md; capture a new question (confirmed); launch research on one.

### ★ Skills (mg-kolbs)
- **Source:** new `skills-goals.json` from the scan of `mg-kolbs/Skills/*` **and** the native **Bases** view over the same folder.
- **Viz:** **current→final level progress bars** per skill (e.g. SIR 5→7), competency tag.
- **Launch:** open the skill note / Bases view in Obsidian; start a **Kolb's reflection** from template (`obsidian://new`).
- **Dependency:** skill notes must expose `current-level`, `final-level`, `competency` as **YAML frontmatter** (today they're in body text) — see §10 Block 0.

### ★ Goals (mg-kolbs)
- **Source:** `skills-goals.json` from `mg-kolbs/Goals/*` + Bases.
- **Viz:** **goal progress bars** (current vs final) + **next-action chips** parsed from each goal's unchecked checklist items (e.g. Agentic Engineering: "Set SMARTER goals," "Schedule weekly evaluation").
- **Launch:** open the goal; run a weekly evaluation; open the Kolb's cycle.

### 1% Gains / Kolb's Cycle
- **Source:** `mg-kolbs/1% Gains Log`, `Goal Tracking`, Kolb's entries.
- **Viz:** **sparkline/timeline** of recent gains + a **Kolb's cycle ring** (Experience → Reflect → Abstract → Experiment) showing each skill's current stage.
- **Launch:** log a 1% gain; new Kolb's reflection.

### Tasks & Calendar
- **Source:** `tasks-calendar/data/upcoming.json` (Calendar connector + `TASKS.md`). Currently shows ⚠ until the calendar connector is wired.
- **Viz:** agenda list (next 7 days) + due-tasks list.
- **Launch:** `cos://task-add`; connect calendar.

### Learning Pipeline (intake)
- **Source:** `learning-pipeline/data/intake-queue.json` — content intake/backlog (distinct from mg-kolbs skill *development*).
- **Viz:** backlog count + top items list.
- **Launch:** `cos://research?software=…`; open queue.

### ★ AI Launchpad  *(launchpad spine)*
- **Source:** static config of available entry points + (optionally) available Grok/Hermes skills.
- **Viz:** launch tiles for **Grok Build**, **Cowork**, **Hermes** (+ recent/available skills).
- **Launch:** `cos://` to open the tool / run a skill; copy-prompt fallback for Cowork.

### Health  *(placeholder)*
- Coming-soon card, as in cos. No data source yet.

---

## 9. Data contract (AI-agnostic)

The generator reads these at build time and embeds the values. Any agent or script that writes to these schemas feeds the dashboard. The rendered page contains no file paths and makes no requests.

| Contract | Domain | Status |
|---|---|---|
| `overview-brief/data/status.json`, `ai-news.json` | Overview Brief | exists (cos) |
| `finances/data/runway.json` | Finances | exists (cos) |
| `tasks-calendar/data/upcoming.json` | Tasks & Calendar | exists (cos) |
| `learning-pipeline/data/intake-queue.json` | Learning intake | exists (cos) |
| `knowledge-base/data/kb-pipeline.json` | KB pipeline | **NEW (vault scan)** |
| `knowledge-base/data/wiki-health.json` | Wiki Health | **NEW (vault scan)** |
| `knowledge-base/data/skills-goals.json` | Skills & Goals | **NEW (vault scan)** |
| `knowledge-base/data/open-questions.json` | Open Questions | extend cos's existing |
| `focus.json` | Active Focus | **NEW (manual/capture)** |

**Timestamp normalization** (inherited gotcha): cos files split between `generated` and `generated_at`; the generator normalizes both and computes per-card freshness (✓ fresh / ⚠ stale / — unavailable). Shared staleness constant = **20h** (matches the cos generator + TUI loader).

**Degradation:** missing/unreadable contract → ⚠ + "data unavailable." Null/absent fields → "not yet populated," never a broken chart.

> **Known upstream data gaps (not this build's job to fix, but it's blocked on them for full value):**
> - `cos-finance-refresh` writes some goal fields null + a runway figure that looks like a single-month average — goal bars stay empty until fixed upstream.
> - `cos-vault-scan` couldn't reach the vault from the scheduled runner (`~/llm-knowledge-base` not mounted) — the new vault contracts depend on resolving that mount.
> - **mg-kolbs frontmatter** — skill/goal level/competency/status live in body text, not YAML. The Skills/Goals cards and the Bases views both need them in frontmatter (Block 0).

---

## 10. Build plan

Blocks are sequencing units; sign off block-by-block (your operating rule). Nothing ships unattended.

| Block | What gets built | Output | Done when |
|---|---|---|---|
| **0 — Data prep & decisions** | Confirm D-1 (fusion) + O-1..O-4. Migrate mg-kolbs skill/goal level/competency/status into **YAML frontmatter**. Resolve the vault mount for scanning. | Clean frontmatter; mount resolved; decisions logged | Bases can read skills/goals; scan can reach the vault |
| **1 — Vault scan → contracts** | Read-only scanners writing `kb-pipeline.json`, `wiki-health.json`, `skills-goals.json`, extended `open-questions.json` | New JSON contracts | Contracts populate from the real vault; **zero writes to the vault** |
| **2 — Generator fusion** | Extend the generator to read cos + vault contracts and render the fused card set with per-card viz | Updated `dashboard.html` | One dashboard shows both systems; graceful on missing data |
| **3 — Skills/Goals via Bases** | Native Bases views over `mg-kolbs/Skills` + `Goals`; replace the dead Dataview blocks | Live editable views | Skills/goals render + edit in Obsidian, no Dataview |
| **4 — Launch actions** | `obsidian://` open/new wired per card; `cos://` AI/CLI launches; copy fallback | Working launchpad | Every v1 card has a working action |
| **5 — Host + polish** | Pick host model (O-2); privacy mode for finances; light/dark; freshness; help overlay; schedule + on-demand regen | Shipped v1 | Opens in/from Obsidian; finances numbers hidden by default |

**v1 core cards (★):** Active Focus, Overview Brief, Finances, Knowledge Base pipeline, Skills, Goals, AI Launchpad.
**v1.5/v2:** Wiki Health detail, Open Questions, 1% Gains/Kolb's ring, Learning intake, Health, confirmed AI capture (vault write), Quartz/public version.

**Build owner:** Grok Build recommended (it built the cos generator and owns the terminal/build lane); Cowork owns this spec + the contracts. (O-3.)

---

## 11. Constraints & guardrails (inherited from cos)

- **Read-only against the vault** for all automated/scheduled scans. Never create, edit, move, delete, promote, or publish vault content. Writes happen in Obsidian (you) or via a future explicit, confirmed capture.
- **Privacy display mode** for finances (and any private/sensitive surface): graphs/relative by default, exact numbers only on drill-in. `private/` vault content excluded from scan output or gated.
- **No server, no runtime fetch** — snapshot baked at generation (cos Path C; live-fetch needs a server, which you rejected; the Cowork-artifact route can't read local files — spike-proven).
- **One writer per contract**; the generator is the sole writer of `dashboard.html`.
- **Model-agnostic** — contracts are plain JSON any runtime can write (Claude, Grok, Hermes, scripts).
- **Reversibility** — block-by-block sign-off; nothing destructive or irreversible without explicit "proceed"; the frontmatter migration in Block 0 is shown and confirmed before any mass edit.
- **Timezone** read from config (Asia/Ho_Chi_Minh today; you're a nomad — never hardcode).

---

## 12. Decision log

| # | Decision | Reasoning / trade-off |
|---|---|---|
| **D-1** | **Fuse cos + llm-knowledge-base into one dashboard** | Overrides the 2026-05-24/05-26 "cos is independent, pipeline not surfaced" decision, per your explicit 2026-05-27 instruction. One surface for one day's work. **Confirm in O-1.** |
| D-2 | HTML snapshot, Basecamp design, viz-per-card | You like the Basecamp layout and want different visualizations per card; HTML supports that and clickable launches; your latest cos decision already shelved Textual for HTML. Dataview tables and Textual both fight per-card viz. |
| D-3 | Read-only vault preserved | Your hardest guardrail survives the fusion. Dashboard reads + launches; Obsidian (human) writes. |
| D-4 | Skills/goals via native **Bases**, not Dataview | Bases is already enabled; Dataview is not. Fixes the dead "Live View" blocks without a plugin install. |
| D-5 | Reuse cos contracts + generator; add a vault scan | Don't rebuild working finance/brief/tasks plumbing; "fresh" applies to the card model + design, not the proven pattern. |
| D-6 | Scanners write JSON; generator renders | Keeps the vault read-only and the generator a pure renderer; model-agnostic. |
| D-7 | Privacy mode for finances | Your Fresh-Start privacy model: graphs default, numbers on drill-in. |

---

## 13. Open questions (need your call before/at Block 0)

- **O-1 — Confirm the fusion (D-1).** Is this one unified dashboard absorbing the cos Basecamp dashboard, rather than a second dashboard? (PRD assumes yes.)
- **O-2 — Host model.** A (standalone, launched from Obsidian), B (iframe/Webviewer embed in a note), or C (hybrid: cockpit + Bases)? (PRD recommends C, with A as the cockpit mechanism for v1.)
- **O-3 — Build lane.** Grok Build (consistent with the existing generator), or another runtime?
- **O-4 — Filename/name.** Keep `PRD-llm-wiki-dashboard.md` (your phrasing) even though the thing is now broader than the wiki? Suggested system name: **Mission Control**. The PRD file currently lives at `cos/prds/PRD-llm-wiki-dashboard.md`.
- **O-5 — Active Focus source.** Manual note, a `focus.json` you set, or derived from recent activity?
- **O-6 — mg-kolbs frontmatter migration.** OK to move skill/goal level/competency/status into YAML frontmatter across `mg-kolbs/Skills/*` and `Goals/*` (shown + confirmed before any mass edit)?

---

## 14. Out of scope / future work

- **Autonomous builder + overnight execution** (the "Possible Paths" track) — the dashboard could later surface its queue, but the builder is not in this window.
- **Confirmed AI capture** (the one sanctioned vault-write path, mirroring cos `/capture`) — quick-capture a task, question, or 1% gain into the vault on explicit confirmation.
- **Public / Quartz version** of the dashboard with the privacy model enforced.
- **Calendar connector** integration (Tasks & Calendar shows ⚠ until wired).
- **Health domain** — needs a unified data source first.
- **Richer drill-downs** — per-domain workspace screens (cos Phase 2).

**How it scales without re-architecture:** a new card = a new contract (or a new field in an existing one) + a sidebar entry + a render block. The vault scan and the generator don't restructure. What *would* force a re-architecture: moving storage off local files; making the dashboard a write-authority for the vault; or adding a live server.
