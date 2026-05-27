# PRD — cos Home (Terminal-Primary Mission Control)

**Owner:** Wedge · **Author:** Claude (Cowork) · **Build lane:** Cowork (Claude) builds the home; Grok Build for the X/news brief specifics
**Status:** DRAFT v2 — for sign-off. **Greenfield build** — existing cos code is reference only, not a base to patch.
**Date:** 2026-05-27 (rev 2)
**Runtime:** Textual app · WezTerm (truecolor, low-power) · Monaspace or JetBrains Mono · dark theme (Grok/Doom)
**Adapts (concepts only):** `PRD-cos.md` (hard rules, local-files philosophy), `PRD-overview-brief.md` (the brief domain), `PRD-llm-wiki-dashboard.md` (D-1 fusion intent, guardrails, See/Move model).
**Supersedes:** `PRD-cos-dashboard-basecamp.md` (HTML primary). **Reverses** `PRD-llm-wiki-dashboard.md` D-2 (HTML-over-Textual). Both now carry deprecation banners.

> **Rev 2 — what changed this pass:** (1) Clean-rebuild stance — re-derive the foundation from best practices; existing cos code is reference, not a base (flips H-7). (2) Read-only export is now **Apple Notes longform daily brief**, not an HTML page; the home shows **concise blurbs**. (3) Layout locked to the **A+B hybrid** (bento + `SPC` palette); sidebar (C) deferred as an additive layer. (4) Runtime locked: WezTerm + Monaspace; **Ghostty + macos-helper retired**. (5) Vault coherence = **cos mechanical scan now** (deterministic, owned); semantic layer deferred. (6) Correction: the vault scan was **never implemented** (net-new), not "broken." (7) Dataview → native **Bases** (approved, no further check-in).

---

## 0. Relationship to prior PRDs

**Supersedes:** HTML as the primary, always-on surface (`PRD-cos-dashboard-basecamp.md`; `PRD-llm-wiki-dashboard.md` D-2). A browser is a great *scanner* and a poor *launcher* — it can't drop you into a repo, run `cos brief`, or open Obsidian without round-tripping through a fragile `cos://` URL-scheme handler. The launch friction is structural to the medium. The terminal is where the work already happens (Grok Build, Codex, Hermes) and is the one surface where **scan and launch are the same motion**.

**Keeps (carried forward unchanged):**
- **D-1 fusion** — one home surfaces both operating data (cos) and knowledge-health signals (vault), bounded: the home *reads* vault signals and *launches* into Obsidian; it is not a second knowledge store.
- **Read-only-against-the-vault** — the hardest guardrail. Automation never writes the vault; only you (in Obsidian) or the explicit, confirmed `/capture` path.
- **Privacy mode for finances** — graphs/relative by default; exact figures only on explicit drill-in.
- **Model-agnostic data contracts** — scanners write JSON, the renderer renders.

**Clean-rebuild stance (new).** This is foundational kit, so it is built greenfield. The existing cos code (`tui/app.py`, `tui/data/loader.py`, `scripts/generate_dashboard.py`, the contracts) was produced by prior AI sessions and carries workaround-shaped cruft (e.g. a literal "`'str' has no render_strips`" hack in `app.py`). It is treated as **reference** — it tells us what data exists and what already broke — not as a base to extend. A piece is reused only if it passes a best-practice bar on its own merit. "Don't reinvent the wheel" applies to the *world's* wheels (Textual, WezTerm, Bases, Python stdlib, Hermes-as-a-capability), never to our own foundation.

---

## 1. Executive summary

**cos Home** is a calm, dark, terminal-native home — a Textual app you open (or that greets you) when you sit down to work. It is the **A+B hybrid**: a bento overview you scan by default, plus a `SPC` command palette (Doom `M-x`/which-key style) that launches you into work one keystroke away. It does two jobs in one motion:

1. **See** — the live state of your operating layer (brief, finances, tasks & calendar, learning) and thinking layer (vault coherence, open questions, skills/goals), each card a concise **blurb** with a terminal-native viz (sparkline, gauge, bar).
2. **Move** — every card and palette entry launches: open the note in Obsidian (`obsidian://`), drop into a repo, fire a Grok/Hermes skill, open Cowork, or run a `cos` subcommand.

A second artifact — a **longform daily brief pushed to Apple Notes** each morning — is the read-anywhere companion: news (Grok X headlines), the open questions you're working, calendar/upcoming dates, budget, and inbox/dashboard items, assembled into a proper morning read for phone/travel. The home is concise blurbs; Apple Notes is the long version. Same generation pass, two densities.

Everything is sourced from local JSON contracts (cos) plus a read-only scan of the vault. Nothing writes the vault. The terminal is primary; Apple Notes is a generated mirror.

---

## 2. Problem

You need one low-friction home that (a) lets you scan your whole-life + interests overview at a glance, and (b) launches you directly into work — and you don't have it.

- **The current HTML dashboard can scan but can't launch.** Its buttons depend on `href="#"` or a `cos://` scheme bridged by `macos-helper` — an OS round-trip with focus switches. That is the "clunky" you described; it's structural to running a launcher in a browser sandbox.
- **State is scattered across surfaces.** Finances, the X/AI-news brief, the calendar, the raw→workbench→wiki pipeline, vault health, open questions, mg-kolbs skills/goals — each lives somewhere different. Assembling the picture is manual. (Solution: unify at the *view* layer only — see §5.)
- **Surface sprawl.** `dashboard.html`, the TUI, Obsidian's `00 Command Center/Home.md`, and the Quartz `index.md` overlap. The fix is one job per surface, not a fifth surface.
- **Your #1 pain — vault coherence — isn't visible anywhere.** Stale/duplicate notes, orphans, buried open questions have no gauge. A home that omits this omits its most important signal.
- **There is no vault scan yet.** It was never implemented (net-new build), so coherence cards start empty and arrive in a later phase.
- **The TUI exists but is ugly enough that you abandoned it.** It works (live tiles, contracts, hotkeys) but uses a rigid 3×2 grid, a hard theme, flat tiles, and truncates summaries to ~70 chars. Aesthetics, not function, are the gap — and this rebuild fixes that as a first-class goal.

---

## 3. Goals and non-goals

### Goals
- **One terminal-native home (A+B hybrid)** — bento scan + `SPC` launcher — opened by a single command (or shell/tmux startup).
- **Aesthetically pleasing** — calm, dark, Grok/Doom design language, Monaspace/JetBrains Mono, generous spacing, typographic hierarchy, ASCII-native viz. This is an explicit goal, not a nicety.
- **Concise blurbs on the home; longform daily brief in Apple Notes.**
- **Per-card, terminal-native viz** — sparkline, gauge, progress bar, stacked bar — sized by importance (varying card sizes).
- **A genuine launchpad** — every card + palette entry lands you in Obsidian (`obsidian://`), a repo, an AI tool, or a `cos` subcommand, as a keystroke.
- **Make vault coherence visible** — stale, orphans, open questions, mg-kolbs progress — as read-only gauges that launch into Obsidian.
- **Read-only vault + privacy mode** preserved verbatim.
- **Greenfield foundation** built to best practices; existing code is reference only.

### Non-goals (this build window)
- **No second control surface.** Apple Notes is read-only reading, not a launcher.
- **No writing to the vault** from the home or the brief. Launch into Obsidian; edit there. (`/capture`, confirmed, stays the only write path; not in this window.)
- **No HTML reading page.** Replaced by the Apple Notes brief + the home's own readable hero card.
- **No sidebar (Option C) in v1.** It's an additive layer for later, once per-domain screens are rich enough to drill into.
- **No semantic vault analysis in v1** (near-duplicates, contradictions). Deferred; Hermes is the likely future home for it.
- **No Dataview.** mg-kolbs renders via native Bases (approved).
- **No autonomous builder / live server / Health domain** (placeholders / separate tracks).
- **No light theme.** Dark only; warm-vs-cool is the one open palette question.

---

## 4. Success criteria

- One command (`cos`) opens the hybrid home; `SPC` opens the launcher palette; launching is a single keystroke with no browser round-trip.
- The home reads as **blurbs** — X-headline density — with a terminal-native viz per card and varying card sizes by importance.
- Each morning a **longform daily brief lands in Apple Notes** containing news, open questions in progress, calendar/upcoming, budget, and inbox items.
- `obsidian://` launches open the correct note from the home.
- Vault coherence (stale / orphans / open Qs / mg-kolbs) shows as gauges once the scan is built; until then those cards show a clear "not yet built," never a crash.
- Finances render numberless by default; figures only on explicit drill-in.
- Zero writes to the vault by any automated path (verifiable).
- The home is visibly calmer and prettier than the abandoned TUI — the bar is "you'd actually want to open it."
- Built greenfield: no prior-AI cruft carried into the foundation; any reused piece is justified on merit.

---

## 5. The model — See vs Move, terminal-primary

Three layers, two consumers:

1. **Source data** — (a) cos local JSON contracts under `~/cos/**/data/`; (b) a **read-only scan of the vault** (net-new) writing JSON contracts (wiki-health, open-questions, skills-goals). Plain files only. Connectors and the vault are *sources*, never storage.
2. **Consumers** — (a) the **Textual hybrid home** reads contracts + watches mtimes for live updates (primary); (b) a **generator** assembles the longform daily brief and pushes it to **Apple Notes** (secondary, read-only). Neither writes the vault.
3. **Launch bridges** — `obsidian://`, `cos` CLI subcommands, AI tools (Grok/Hermes/Cowork), with copy-to-clipboard fallback.

**Scattered state is solved at the view layer, not by relocation.** Each source stays where it belongs (finances as CSV, notes in Obsidian, calendar in a connector, news from Grok). A scanner reads each into a uniform contract; the home is the single renderer. The home is organized by *how you think*, in four zones: **Now** (hero brief), **Operating** (finances, tasks, learning), **Thinking** (coherence, open questions, skills/goals), **Signals** (AI news). One home, four zones, many sources, zero relocation.

**See vs Move, per card:** *See* = state (blurb + viz); *Move* = ≥1 keystroke/palette launch. Visually separate **what I can do** (safe launches) from **what needs my judgment** (review items — surfaced, never auto-resolved).

---

## 6. Architecture

```
        ┌──────────────────────── SOURCES (read-only) ───────────────────────────┐
 cos    │  ~/cos/**/data/*.json        |   ~/llm-knowledge-base/ (Obsidian vault) │
 work-  │  finances, overview-brief,   |   markdown + YAML + folders + git        │
 flows  │  tasks-calendar, learning    |                                          │
        └───────────────┬─────────────┴───────────────────┬──────────────────────┘
                        │                                  │ (read-only scan — NET-NEW)
                        ▼                                  ▼
      cos contracts (re-derived clean)       vault-scan (new): wiki-health,
                        │                     open-questions, skills-goals → JSON
                        └───────────────┬──────────────────┘
                                        ▼
             ┌──────────────────────────┴───────────────────────────┐
             ▼                                                        ▼
   TEXTUAL HYBRID HOME  (PRIMARY)                          GENERATOR → Apple Notes (SECONDARY)
   bento scan + SPC palette,                               longform daily brief (news, open Qs,
   blurbs + per-card viz, mtime watch,                     calendar, budget, inbox), pushed
   keystroke launches                                      each morning via Shortcut/osascript
             │                                                        │ (read-only · mobile/travel)
   ┌─────────┼──────────────┐
   ▼         ▼              ▼
 obsidian:// cos CLI    Grok / Hermes / Cowork
 open note  brief/...   fire skill / research

   RETIRED: dashboard.html (as launcher) · Ghostty · macos-helper (cos:// bridge)
```

Greenfield: the home and the contracts are re-derived to best practices. The existing generator/loader inform *what data exists*, not *how to build it*.

---

## 7. Design language & layout

The abandoned TUI was functional but flat (rigid 3×2 grid, hard background, tiles clipped to 70 chars). Target: calm, dark, techy — Doom Emacs design language, terminal-native.

**Layout — A+B hybrid.**
- Default view: a **bento grid** with varying card sizes by importance. **Now/brief = hero (largest); vault coherence = wide & prominent** (it's your #1 pain — it earns weight); **finances = small** (numberless gauges don't need room); tasks/learning/signals = medium/small. Textual `column-span`/`row-span` drive the bento.
- `SPC` opens a **command palette** (Textual's built-in command palette, Doom `M-x`/which-key feel) for fuzzy go-to / run-action — the launcher.
- A thin **command bar / minibuffer** above the footer (`:` to focus, `esc` to leave): type a tool name (`grok`, `codex`, `hermes`) to spawn it full-size in a new WezTerm pane/tab; type a simple command to run it and see output inline. No embedded PTY — interactive tools get a real terminal, not a cramped box.
- Per-card hotkeys remain (`b/f/t/l/k/g`), shown in a which-key footer (doom-modeline-style status bar: root, clock, theme, mode).
- **Sidebar (Option C) deferred** — additive later when per-domain screens are rich enough to drill into; no rework to add it.

**Theme (locked).** Dark, **muted warm — Anthropic/Cowork register**: warm charcoal background (~`#211f1d`), warm-bone text (~`#e3ddd0`), and a single restrained **clay/terracotta accent** (~`#c8775c`) carrying keys/highlights. Everything else neutral (warm grays, a muted sage for positive, a muted tan for counts) — calm, not gruvbox-bright. One accent does the work; high text contrast; never harsh. Swappable later.

**Typography & widgets (Textual built-ins, minimal deps).**
- `Markdown` widget for the hero brief (renders blurbs cleanly; no truncation).
- `Sparkline` (built-in) for trends (open-Q rate, intake).
- `ProgressBar` / Rich `Bar` for goal completion + runway gauge.
- `Collapsible` for finances privacy drill-in and "go deeper."
- `textual-plotext` only if a card genuinely needs a plotted chart.

**Runtime.** WezTerm (truecolor — required for the palette; low power — cap FPS / disable animations to protect the M3 battery). Monaspace (duospace) or JetBrains Mono. Terminal.app is explicitly ruled out (256-color, would muddy the palette).

---

## 8. Card specifications

Each card: **title · blurb · viz · launch**. Blurbs are X-headline density.

| Card | See (blurb + viz) | Move (launch) |
|---|---|---|
| **Now / hero** (large) | 1–3 blurbs: top flags, key counts; `Markdown` | `b` → brief; open Apple Notes brief |
| **Finances** (small) | runway **gauge**, goal **bars**, numberless | `Collapsible` reveals figures; `f` |
| **Tasks & Calendar** (medium) | today's events/tasks; "cal off" if connector down | `t`; open calendar |
| **Learning** (small) | intake **stacked bar**, backlog count | open top item; `r` research |
| **Vault coherence** (wide) | stale + **sparkline**, orphans, open-Q count | `k`; `obsidian://` open offending note |
| **mg-kolbs skills/goals** (later) | per-skill **bars** from `skills-goals.json` (Bases-backed) | `obsidian://` open Bases view / skill |
| **Signals (Grok)** (small) | 3–5 X headlines | open source; `g` refresh |

Missing/not-yet-built data → a clear "not yet built / not populated," never a crash.

---

## 9. The daily brief & exports

Two densities from one generation pass:
- **Home (blurbs).** Per-domain one-liners / 2–3 bullets at X-headline density, rendered in the bento + hero card. This is the scan surface.
- **Apple Notes (longform daily brief).** A proper morning read assembled each day: Grok X news headlines, the open questions you're actively working, calendar + upcoming dates, budget snapshot, and inbox/dashboard items. Pushed to Apple Notes via a Mac-side Shortcut / `osascript` so it syncs to phone/iPad for travel reading.
  - Caveats (accepted): Apple Notes is rich-text, not Markdown — tables/code degrade; `obsidian://` links aren't reliably clickable there. On mobile you're reading, not launching, so this is fine.
  - **Not chosen:** an HTML reading page (no job left once the home is readable and Apple Notes covers mobile); writing the brief into the vault (breaches read-only-vault).

---

## 10. Data layer (re-derived clean)

- **Re-derive the contracts to best practices.** Use the existing contracts (runway, open_questions, stale_notes, intake_queue, upcoming, status, ai_news) as a *spec of what data exists*, then define clean, validated schemas. Keep a field/shape only if it's right, not because it's there.
- **Vault scan is net-new.** Build a read-only scanner that walks `~/llm-knowledge-base/` and writes JSON: stale (mtime > threshold), orphans (link graph), open-Q counts (tag/pattern), missing frontmatter. Deterministic, owned, no external coupling.
- **`skills-goals.json`** — read-only scan of `mg-kolbs/Skills/*` + `Goals/*` YAML frontmatter (after the Dataview→Bases frontmatter migration). The home renders bars; Obsidian renders the editable Bases view from the same frontmatter.
- All scanners write JSON; the home/generator only render. Vault stays read-only.

---

## 11. Build plan (phased)

**Phase 0 — Greenfield home skeleton + design language.** New Textual app built clean: dark Grok/Doom theme (warm or cool per sign-off), bento layout with varying card sizes, `SPC` command palette, which-key modeline, Monaspace, WezTerm target. Renders the *operating* contracts that already have data (finances, brief, tasks, learning) as blurbs + viz. This is the "make it pretty" deliverable, on data that works.

**Phase 1 — Daily brief → Apple Notes.** Generator assembles the longform daily brief (news, open Qs, calendar, budget, inbox) and pushes to Apple Notes via Shortcut/`osascript`; scheduled each morning.

**Phase 1.5 — Command bar (minibuffer).** Thin `:`-focused input above the footer: interactive tools (`grok`/`codex`/`hermes`) spawn into WezTerm panes via `wezterm cli spawn`; simple commands run via subprocess with inline captured output (timeout-guarded). No embedded PTY.

**Phase 2 — Vault coherence (mechanical scan).** ✅ Built: `home/scan.py` (`cos scan`) walks the vault read-only and writes `knowledge-base/data/coherence.json` (stale / orphans / open-Q / missing-frontmatter), content-scoped and tunable via `coherence.exclude_dirs`. Runs **locally** (where the vault is reachable) and is folded into `cos brief`, sidestepping the `cos-vault-scan` Cowork runner's mount limitation — that scheduled task is now redundant. The home's coherence card reads `coherence.json`. The scan also extracts the open-question **list** (text + path + date), which `cos brief` now uses instead of the stale Cowork contract — so `cos-vault-scan` has been **disabled** (retired). ✅ **mg-kolbs:** a read-only skills card (reads frontmatter or body) is in the home; the skill/goal notes were migrated to YAML frontmatter (9 skills derived from body, 3 goals with placeholder `status` — additive, git-reversible), and the dead `dataview` blocks in `Skills.md` / `Goals.md` were swapped for Bases views. **Still pending (yours):** set real goal statuses in Obsidian, verify the Bases views render, and decide on the other ~8 mg-kolbs `dataview` blocks (Tasks, 1% Gains, Experiments, …) — separate databases, not migrated.

**Phase 3 — Polish & retire.** Retire `dashboard.html`, Ghostty, macos-helper. Optional `cos` as shell/tmux startup. (Future: sidebar/Option C; semantic coherence via Hermes; on-demand `/capture`.)

Sequencing: Phase 0+1 ship a pretty, launch-capable home + mobile brief on working data. Phase 2 waits on the net-new scan so coherence cards aren't built on empty data.

---

## 12. Constraints & guardrails

- **Greenfield foundation** — existing cos code is reference, not a base; reuse only on merit.
- **Read-only vault** — no automated path writes `~/llm-knowledge-base`. `/capture` (confirmed) is the sole write path; out of scope here.
- **Privacy mode** — finances numberless by default; figures only on explicit drill-in.
- **Local files only; one writer per file; inputs/ vs data/ invariant** preserved.
- **Model-agnostic** — any agent/script can populate contracts; consumers are dumb renderers.
- **Runtime** — WezTerm (truecolor, FPS-capped for battery), Monaspace/JetBrains Mono. No Terminal.app.
- **Command bar** — spawning interactive tools requires running inside WezTerm (its mux); degrades gracefully (notify) elsewhere. Inline runs are non-interactive and timeout-guarded.
- **Graceful degradation** — missing/not-built data → clear placeholder, never a crash.

---

## 13. Decision log

| # | Decision | Reasoning |
|---|---|---|
| **H-1** | Terminal (Textual) is the primary home. | Reverses basecamp + wiki D-2. Terminal = where work happens; only surface where scan + launch are one motion. |
| **H-2** | Read-only export = **Apple Notes longform daily brief** (was HTML page). | You want to read on phone/travel; Apple Notes syncs natively. HTML page has no job once the home is readable. |
| **H-3** | Fusion kept (D-1), bounded — read vault signals + launch into Obsidian, not a second store. | Addresses your #1 pain (coherence) without duplication. |
| **H-4** | Terminal-native viz is sufficient. | Sparkline/ProgressBar/Rich bars/plotext cover gauges/bars/sparklines. ASCII viz is the intent. |
| **H-5** | Home = concise blurbs; Apple Notes = longform. | Two densities, one generation pass. |
| **H-6** | Vault coherence = cos mechanical scan now (net-new); semantic deferred. | Own the deterministic foundation; don't couple to Hermes prematurely. (Correction: scan was never implemented, not broken.) |
| **H-7** | **Greenfield rebuild; existing cos code is reference, not a base.** | *Flipped from rev 1.* Foundational kit must be best-practice, not prior-AI cruft patched forward. "Don't reinvent" applies to the world's wheels, not our foundation. |
| **H-8** | Layout = A+B hybrid (bento + `SPC` palette); sidebar (C) deferred. | Serves scan-everything + one-key launch on today's data; sidebar earns its keep only once per-domain screens are rich. Additive later, no rework. |
| **H-9** | Runtime = WezTerm + Monaspace; Ghostty + macos-helper retired. | WezTerm: truecolor + low power (M3 battery). Ghostty/helper only existed to bridge HTML launches we're killing. |
| **H-10** | Dataview → native Bases. | No plugin dependency; prettier; one frontmatter source feeds both Obsidian and the home. (Approved, no further check-in.) |
| **H-11** | Theme = muted warm, Anthropic/Cowork register (warm charcoal · bone · clay accent). | Dialed back from gruvbox-amber to a calmer, restrained warm; one clay accent does the work. Resolves O-A. |
| **H-12** | Cowork (Claude) executes the build; Grok Build owns the X/news brief. | Wedge: Claude has tracked intent better here; Grok is stronger on X data. |
| **H-13** | Hero focus = human-maintained `overview-brief/inputs/focus.md` (read-only to the home). | Lives in the `inputs/` slot Wedge owns; seeded from the 2026-05-26 journal; avoids fragile journal parsing. |
| **H-14** | Command bar = spawn interactive tools into WezTerm panes + run simple commands inline; no embedded PTY. | A nested full-screen TUI (`grok`) inside a box fights escape keys, cramps the viewport, and duplicates WezTerm. Spawning out gives a real terminal and fits the launch-out model; inline runs cover quick non-interactive commands. Degrades gracefully outside WezTerm. |
| **H-15** | Coherence scan runs **locally** (`cos scan` / inside `cos brief`), content-scoped + config-tunable, writing `coherence.json`. | Running where the vault is reachable resolves the `cos-vault-scan` runner's mount limitation without touching Cowork infra; scoping to durable dirs avoids orphan noise from tooling/source files. The Cowork `cos-vault-scan` task is now redundant. |
| **H-16** | mg-kolbs: card reads frontmatter-or-body; migration adds frontmatter (additive, git-reversible) and swaps `dataview`→Bases for Skills/Goals only. | The card works without a migration (reads body), so it's risk-free; the migration is additive (no deletions) and git-tracked. Scoped to skills/goals; other mg-kolbs dataview blocks left untouched. Bases YAML may need a UI tweak. |

---

## 14. Open questions

- ~~**O-A — Theme.**~~ Resolved (H-11): muted warm, Anthropic/Cowork register.
- ~~**O-B — Hero "Now" source.**~~ Resolved: a human-maintained `overview-brief/inputs/focus.md` (seeded from the 2026-05-26 journal), read-only to the home. Can later point at a vault `Focus.md`.
- ~~**O-C — Brief schedule.**~~ Resolved: pushed at the Daily Digest slot (~07:17, `cos-daily-digest`); `cos brief` regenerates on demand.

---

## 15. Out of scope / future work

- **Sidebar / Option C** — additive nav layer for drilling, once per-domain screens are rich.
- **Semantic vault coherence** — near-duplicates, contradictions — likely a nightly Hermes skill writing a contract the home renders.
- **Confirmed AI capture** into the vault (the one sanctioned write path).
- **Autonomous builder / overnight execution** (separate track).
- **Calendar connector** wiring (Tasks/Calendar shows "off" until done).
- **Health domain** (needs a data source).
- **Deletion sweep** — retire `dashboard.html` + archive the superseded PRDs once the home ships.

**How it scales without re-architecture:** a new card = a new contract (or field) + a render block + a binding. What *would* force a re-architecture: moving storage off local files; making the home a write-authority for the vault; or adding a live server.

---

## Sign-Off Checklist

- [ ] H-1/H-2 confirmed — terminal hybrid home primary; Apple Notes = the read-only daily brief.
- [ ] H-7 confirmed — greenfield rebuild; existing code is reference only.
- [ ] H-8 confirmed — A+B hybrid layout; sidebar deferred.
- [ ] H-9 confirmed — WezTerm + Monaspace; Ghostty + macos-helper retired.
- [x] O-A — palette chosen: muted warm (Anthropic/Cowork).
- [x] O-B — hero source: human-maintained `inputs/focus.md` (seeded from journal).
- [x] O-C — brief at the ~07:17 digest slot; `cos brief` on demand.
- [ ] Confirmed: no path writes the vault; finances numberless by default.
- [ ] Phase 0 approved to start (greenfield home skeleton on working data).
