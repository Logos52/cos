# PRD — `cos`: An Autonomous Personal OS in Cowork

**Owner:** Wedge · **Author:** drafted in Claude chat · **Build surface:** Claude Cowork (model-agnostic — any capable agent can execute)
**Foundation:** Cowork Productivity plugin · **Data layer:** local files in `~/cos/` · **Status:** Foundational Cowork build complete; TUI MVP + model-agnostic migration in progress; out-4 docs/process updates applied — 2026-05-26

---

## 1. Executive summary

`cos` is a personal operating system built inside Claude Cowork: a single local workspace that unifies recurring life-and-business work into scheduled workflows, an always-on dashboard, and on-demand skills, all sitting on a stable local file layer.

**Domains (4):** `finances`, `knowledge-base`, `learning-pipeline`, `tasks-calendar`.

**Interaction patterns (all 4):**
- **Dashboard** — `dashboard.html`, the always-on visual the plugin generates and workflows refresh.
- **Daily Digest** — a scheduled morning brief into `briefs/`, reading across all domains.
- **Skills Suite** — on-demand commands in `toolbox/` (`/today`, `/research`).
- **Autonomous Builder** — drop a brief in `builds/`, get a staged project back; **stages and waits for explicit sign-off before shipping** (never unattended-ships).

**Build shape:** multi-session, hours flexible.
- **Session 1 (foundation + core):** setup → data layer → `finances` + `knowledge-base` → Daily Digest → `dashboard.html`.
- **Session 2 (remaining domains + advanced patterns):** `learning-pipeline` → `tasks-calendar` → Skills Suite → Autonomous Builder → polish.

**Why it fits and scales:** Four domains is the metaprompt's ceiling for a single window, so it's deliberately split across two sessions rather than thinned. The architecture adds new domains as new folders without restructuring, so anything deferred (health, the Textual front-end) slots in later as a folder + workflows.

**Foundational note:** `cos` is the base layer for downstream projects, so the owner is kept in the loop throughout — no unattended destructive or shipping actions in this build.

## Current Status Snapshot (2026-05-26 + out-4)
Foundational Cowork build (blocks 0-10 per §7) complete and operational. TUI MVP advanced in parallel waves (live dashboard tiles from data contracts via tui/data/loader.py, hotkeys to 4 real dedicated screens mirroring toolbox/ skills, Grok X-brief/research skeletons writing to data/ e.g. ai-news.json, unified `cos` CLI via scripts/cos + tui/__main__.py with real `cos brief` dispatch). Model-agnostic migration underway per dedicated PRD (data layer proven portable contract; Grok layer skeleton exists). out-4 complete: PRDs updated with status/roadmap, Cowork surface documented (see root README.md), Autonomy Charter created (prds/AUTONOMY-CHARTER.md). Cowork surfaces (Productivity plugin + schedules + TASKS.md + toolbox/ + plugin memory) continue working in parallel with portable TUI/CLI/Grok over same data/.

---

## 2. Quick start — moving this into Cowork

This PRD was produced in Claude chat. The build happens in Cowork. This section is the handoff.

### Getting into Cowork (you do this)
1. Open Claude Cowork.
2. Create a new project pointed at a **local** folder: `~/cos/`.
3. Load this PRD into the project: drop `PRD-cos.md` into the project folder, **or** paste its contents into the first Cowork message.

Nothing is set up yet at this point — the project is a blank slate. The first build block (Block 0) handles all setup.

### Project instructions — paste into the Cowork project's custom-instructions field
```
This project builds and runs `cos`, a personal OS. Conventions:

- DOMAINS: finances, knowledge-base, learning-pipeline, tasks-calendar.
- DATA LAYER IS LOCAL: all state lives in plain files under this project root
  (~/cos/). Connectors (Calendar, GitHub, web) and external systems (Hermes,
  the Obsidian vault) are SOURCES that workflows read from or push to — never
  storage. Never create folders in Google Drive or any connector.
- INPUTS ARE NEVER OVERWRITTEN: any inputs/ folder is human-maintained.
  Refresh workflows write only to data/ and outputs/, never to inputs/.
- THE OBSIDIAN VAULT (~/llm-knowledge-base/, adjacent to this project) IS
  EXTERNAL AND PROTECTED. Scheduled/automated workflows are READ-ONLY against
  it — they never write to it. The OS may write into the vault ONLY via an
  explicit, on-demand, confirmed action (the capture skill), never as a side
  effect of a refresh.
- BLOCK-BY-BLOCK EXECUTION: when I say "Start building", assume nothing is set
  up. Run Block 0 (Setup) first. Then build one block at a time, in order.
  After each block, report what was done + the done-check result, then WAIT
  for my go-ahead before the next block.
- KEEP ME IN THE LOOP: this is a foundational project. Confirm before anything
  destructive, irreversible, or that writes outside ~/cos/. No unattended ships.
- TIMEZONE: Asia/Ho_Chi_Minh (UTC+7). Owner is a digital nomad — workflows
  that assume a location must read it from config, not hardcode it.
```

### How to run the build (instructions to Cowork)
When the owner says to start, **assume nothing is set up**. FIRST run **Block 0 (Setup)** from §7: verify the Productivity plugin is installed (walk the owner through installing it if not), have the owner run `/start`, and verify the connectors this build needs are enabled (name any that must be turned on). **Only once setup is confirmed**, build the plan one block at a time, in order. After each block, report what was done and the done-check result, then wait for the owner's go-ahead.

### The first thing the owner types in Cowork
> **Start building — begin with Block 0.**

---

## 3. Goals and non-goals

### Goals
- A working local data layer for all four domains, with seed inputs and refresh workflows.
- `finances` and `knowledge-base` fully built in Session 1 (highest-stakes data + the owner's #1 pain point).
- A `dashboard.html` and a scheduled Daily Digest reading across domains.
- `learning-pipeline`, `tasks-calendar`, the Skills Suite, and the Autonomous Builder in Session 2.
- Strict separation of truth: the Obsidian vault is read-only to automation; the OS holds only derived flags.
- A PRD any capable agent can execute (not Claude-specific).

### Non-goals (deliberately out of this build window)
- **The `cos` Textual app.** The dashboard ships as `dashboard.html`. The Textual front-end is a later, separate consumer of the same data layer (see §10). Not built here.
- **Health domain.** Deferred to a placeholder folder + §10 (owner said "eventually").
- **Resolving the autonomy/approval tension.** The Autonomous Builder stages-then-asks. True unattended autonomy is explicitly future work (§10).
- **Live market-data feed for `/research [ticker]`.** Degrades gracefully to web/news + manual inputs unless a data source is wired later.
- **Rewriting/reorganizing the vault.** The OS never edits notes; at most it files a new note on explicit request.

---

## 4. Architecture overview

### Three layers
1. **Local files (`~/cos/`)** — the only storage. Plain `.md` / `.json` files.
2. **Cowork project + Productivity plugin** — the engine: refreshes data, runs workflows, holds working memory/tasks.
3. **Dashboard (`dashboard.html`)** — the always-on visual rendered from the data layer. (A Textual `cos` app is a future second view over the same files.)

Connectors (Calendar, GitHub, web) and external systems (Hermes, the Obsidian vault) are **sources** — read from, occasionally pushed to on confirmation — never storage.

### Interaction patterns → workflows
| Pattern | Mechanism | Workflows using it |
|---|---|---|
| Dashboard | `dashboard.html` | All domains render summary tiles |
| Digest | scheduled push → `briefs/` | Daily Digest reads all 4 domains |
| Skill | on-demand → `toolbox/` | `/today`, `/research [ticker\|software]`, `/capture` |
| Builder | drop zone → `builds/` | Autonomous Builder (staged, sign-off gated) |

### Three-tier memory
- **Root `CLAUDE.md`** — cross-cutting working memory: people (just Wedge), terminology, shorthand.
- **`memory/{domain}/`** — deep knowledge per domain (derived/observed, regenerable).
- **`{domain}/CLAUDE.md`** — role and tone when working inside that domain.

### Key architectural decisions (and the tension behind each)
- **Vault = source of truth; OS holds only derived flags.** Tension: the owner's #1 pain is duplicate/stale knowledge. Putting "knowledge about the vault" in `memory/` instead of copying notes prevents recreating that pain one layer up.
- **Two-tier vault write rule.** Tension: configurability (run automations against the vault) vs. safety (no roughshod changes). Resolved: scheduled = read-only hard rule; interactive = write only on explicit confirmation.
- **Builder stages, never ships unattended.** Tension: "wake up to a finished project" vs. the owner's approve-before-execute rule. Resolved for the foundational build by staging + sign-off; full autonomy deferred.
- **`dashboard.html` over Textual.** Tension: the owner builds Textual apps, but `dashboard.html` is plugin-native and far cheaper. Resolved: ship HTML now, Textual reads the same data later.
- **Hermes read-only.** It passively remembers vault work today; treating it as a one-way source avoids a third competing write target.

---

## 5. The data layer — the foundation

Built on the Productivity plugin's root files, following the fixed root skeleton and per-domain pattern. Local plain files. Connectors are sources, never storage.

### Folder tree
```
~/cos/                          ← Cowork project root (LOCAL)
├── CLAUDE.md                   ← cross-cutting memory: Wedge, terminology, shorthand
├── TASKS.md                    ← plugin task list (also backs tasks-calendar)
├── memory/                     ← plugin deep memory
│   ├── people.md               ← just Wedge: prefs, goals, timezone
│   ├── terminology.md          ← shorthand: ICS, llm-wiki, "runway", etc.
│   ├── finances/               ← derived finance knowledge (goals, assumptions)
│   ├── knowledge-base/         ← derived vault knowledge (NOT copies of notes)
│   ├── learning-pipeline/      ← derived learning knowledge (topics, sources)
│   └── tasks-calendar/         ← derived scheduling knowledge (recurring patterns)
├── dashboard.html              ← always-on visual, rendered from data/ files
├── PRD-cos.md                  ← this PRD, at root for reference
├── toolbox/                    ← Skills Suite: /today, /research, /capture
├── briefs/                     ← Daily Digest output
│   └── archive/                ← dated past briefs
├── builds/                     ← Autonomous Builder drop zone (Session 2)
│   └── archive/                ← completed/staged build outputs
├── finances/
│   ├── CLAUDE.md               ← voice/role: financial analyst, goal-aware
│   ├── inputs/                 ← human-maintained: income, accounts, goals
│   ├── data/                   ← machine-refreshed: runway, budget rollups
│   └── outputs/                ← generated: monthly summaries, research notes
├── knowledge-base/
│   ├── CLAUDE.md               ← voice/role: librarian for the vault
│   ├── inputs/                 ← config pointing at ../llm-knowledge-base (NOT a copy)
│   ├── data/                   ← derived flags: stale notes, open questions
│   └── outputs/                ← "resurface these" lists, digest snippets
├── learning-pipeline/
│   ├── CLAUDE.md               ← voice/role: learning curator
│   ├── inputs/                 ← human-maintained: sources, reading goals
│   ├── data/                   ← machine-refreshed: intake queue, backlog
│   └── outputs/                ← processed summaries, "to study" lists
└── tasks-calendar/
    ├── CLAUDE.md               ← voice/role: scheduler, timezone-aware
    ├── inputs/                 ← human-maintained: recurring commitments
    ├── data/                   ← machine-refreshed: unified upcoming view
    └── outputs/                ← daily/weekly schedule snapshots
```
*(A `health/` placeholder folder is added in §10 for future work.)*

### Inputs vs. data
`inputs/` is human-maintained and **never** written by a refresh workflow. `data/` is machine-refreshed and freely overwritten. The one exception to "OS never writes externally" is the `/capture` skill, which can write a note **into the vault** on explicit confirmation — never automatically.

### Memory files — contents
- **`memory/people.md`** — Wedge: freelance researcher, digital nomad (currently Vietnam, UTC+7), planning US return in ~1 year; goals: budget toward investments + relocation; communication: direct, no fluff, PRD-first.
- **`memory/terminology.md`** — `ICS` (learning techniques under vault `raw/private/ICS`), `llm-wiki` (Karpathy-style GitHub Pages knowledge base), `runway` (months of expenses covered), `vault` = `~/llm-knowledge-base/`.
- **`memory/finances/`** — budget assumptions, goal targets, US-return cost model.
- **`memory/knowledge-base/`** — derived: which vault areas go stale fastest, recurring open-question themes. **Never note contents.**
- **`memory/learning-pipeline/`** — active topics, trusted sources, what "processed" means.
- **`memory/tasks-calendar/`** — recurring commitment patterns, timezone rules.

### Data file schemas

**`finances/data/runway.json`**
```json
{
  "generated": "2026-05-25T07:00:00+07:00",
  "currency": "USD",
  "monthly_income_avg": 4200,
  "monthly_expenses_avg": 1850,
  "net_monthly": 2350,
  "liquid_savings": 28500,
  "runway_months": 15.4,
  "goals": [
    {"name": "US relocation fund", "target": 25000, "current": 16200, "by": "2027-06"},
    {"name": "Investment contribution", "target": 12000, "current": 7400, "by": "2027-01"}
  ],
  "us_return": {"target_date": "2027-06-01", "months_remaining": 12}
}
```

**`finances/inputs/income.csv`** (human-maintained)
```csv
month,source,amount_usd,note
2026-05,client-a-retainer,2500,monthly retainer
2026-05,client-b-project,1700,milestone 2 of 3
2026-04,client-a-retainer,2500,
```

**`knowledge-base/data/stale-notes.json`** (derived flags — pointers, not contents)
```json
{
  "generated": "2026-05-25T07:00:00+07:00",
  "vault_path": "~/llm-knowledge-base",
  "stale_threshold_days": 90,
  "stale": [
    {"path": "raw/private/ICS/spaced-repetition.md", "last_modified": "2026-01-12", "days_stale": 133},
    {"path": "agentic-eng/tool-use-patterns.md", "last_modified": "2026-02-03", "days_stale": 111}
  ],
  "count": 2
}
```

**`knowledge-base/data/open-questions.json`**
```json
{
  "generated": "2026-05-25T07:00:00+07:00",
  "open": [
    {"path": "agentic-eng/memory-architectures.md", "question": "Best pattern for cross-session agent memory?", "raised": "2026-04-18"}
  ],
  "count": 1
}
```

**`learning-pipeline/data/intake-queue.json`**
```json
{
  "generated": "2026-05-25T07:00:00+07:00",
  "queue": [
    {"id": "2026-05-24-001", "source": "x", "title": "Thread on agentic eval harnesses", "url": "https://x.com/...", "topic": "agentic-engineering", "status": "unread", "added": "2026-05-24"},
    {"id": "2026-05-23-004", "source": "docs", "title": "Textual reactive attributes guide", "url": "https://...", "topic": "textual", "status": "to-study", "added": "2026-05-23"}
  ],
  "backlog_count": 2
}
```

**`tasks-calendar/data/upcoming.json`**
```json
{
  "generated": "2026-05-25T07:00:00+07:00",
  "timezone": "Asia/Ho_Chi_Minh",
  "events": [
    {"start": "2026-05-26T09:00:00+07:00", "title": "Client A sync", "source": "calendar"},
    {"start": "2026-05-28T00:00:00+07:00", "title": "Visa check-in window opens", "source": "manual"}
  ],
  "tasks_due": [
    {"task": "Send client B milestone 2 deliverable", "due": "2026-05-27", "source": "TASKS.md"}
  ]
}
```

### Refresh strategy
| `data/` file | Populated by | Frequency | Mode | Dedupe |
|---|---|---|---|---|
| `finances/data/runway.json` | finance-refresh, reads `inputs/income.csv` + goals | daily 07:00 | overwrite | n/a (recomputed) |
| `knowledge-base/data/stale-notes.json` | vault-scan (**read-only**) | daily 07:00 | overwrite | by path |
| `knowledge-base/data/open-questions.json` | vault-scan (**read-only**) | daily 07:00 | overwrite | by path+question |
| `learning-pipeline/data/intake-queue.json` | intake-refresh (web/X or manual add) | daily + on-demand | append, status-update | by `id` / `url` |
| `tasks-calendar/data/upcoming.json` | calendar+tasks-refresh | daily 07:00 | overwrite | by start+title |

Naming follows fixed conventions: memory `.md`, data `.json`, folders kebab-case, dated files `name-YYYY-MM-DD.md`.

---

## 6. Component specifications

**finance-refresh** — reads `finances/inputs/income.csv` + goal config; writes `finances/data/runway.json`. Schedule: daily 07:00 ICT. Computes net, runway, goal progress, US-return countdown.

**vault-scan** — **read-only** against `~/llm-knowledge-base`; writes `knowledge-base/data/stale-notes.json` + `open-questions.json`. Daily 07:00. Flags notes past staleness threshold; extracts lines marked as open questions. Writes pointers only, never note contents.

**intake-refresh** — pulls new learning items (web/X where available, else manual `/capture`); writes/appends `learning-pipeline/data/intake-queue.json`. Daily + on-demand. Dedupes by URL.

**calendar-tasks-refresh** — reads Calendar connector + plugin `TASKS.md`; writes `tasks-calendar/data/upcoming.json`. Daily 07:00, timezone-aware.

**dashboard.html** — renders tiles from all four `data/` files: runway + goals, stale-note/open-question counts, intake backlog, upcoming events. Refreshed after the morning refresh pass.

**Daily Digest** — reads all four `data/` files; writes `briefs/brief-YYYY-MM-DD.md`, archives prior. Scheduled 07:15 ICT (after refreshes).

**Skills (`toolbox/`):**
- `/today` — on-demand version of the digest (same reads).
- `/research [ticker|software]` — ticker → finances (web/news research → `finances/outputs/`); software → learning-pipeline (queues + summarizes → `learning-pipeline/outputs/`).
- `/capture [text]` — the **only** writer to the vault; stages a note, shows path + content, writes on explicit confirmation.

**Autonomous Builder** (Session 2) — watches `builds/`; on a dropped brief, plans + stages the project in `builds/<name>/`, then **stops and reports for sign-off before shipping anything**. Never writes outside `builds/` without confirmation.

All interfaces read only from the §5 data layer.

---

## 7. The build plan

Blocks are roughly hour-shaped for sequencing; hours are flexible. "Who runs it": Cowork unless a terminal/CLI/cron/git step is owner-side. Owner is a developer, so CLI steps are assigned to the owner.

| Block | What gets built | Who runs it | Output | Done when… |
|---|---|---|---|---|
| **0 — Setup** | Verify Productivity plugin installed (else guide install via Cowork → Customize → Plugins → "Productivity"); run `/start`; confirm connectors (Calendar; GitHub/web optional) | Me + Cowork | Plugin root files exist; connectors confirmed | `CLAUDE.md`, `TASKS.md`, `memory/`, `dashboard.html` exist and needed connectors are on |
| **1 — Data layer** | Full folder tree; all 4 domain folders; seed `inputs/`; 4 refresh workflows | Cowork | Tree + seed files + workflows | All folders exist, seed files populated, refreshes run without error |
| **2 — finances** | finance-refresh wired; `runway.json` live; domain `CLAUDE.md` | Cowork | Working finances domain | `runway.json` reflects seed income + goals |
| **3 — knowledge-base** | vault-scan (read-only); stale + open-question flags; domain `CLAUDE.md` | Cowork | Working KB domain | Flags generated from real vault, zero writes to vault |
| **4 — Daily Digest** | Cross-domain brief workflow + schedule | Cowork | `briefs/brief-*.md` | Brief generated reading all live domains |
| **5 — dashboard.html** | Tiles for all live domains | Cowork | Rendered dashboard | Dashboard shows finances + KB + digest data |
| *— end Session 1 —* | | | | |
| **6 — learning-pipeline** | intake-refresh; queue; domain `CLAUDE.md` | Cowork | Working learning domain | Queue populates + dedupes |
| **7 — tasks-calendar** | calendar-tasks-refresh; unified view; domain `CLAUDE.md` | Cowork | Working tasks domain | `upcoming.json` merges calendar + `TASKS.md` |
| **8 — Skills Suite** | `/today`, `/research`, `/capture` in `toolbox/` | Cowork | Installed skills | Each skill runs; `/capture` gates on confirmation |
| **9 — Autonomous Builder** | `builds/` watcher; plan+stage workflow | Cowork | Builder workflow | Dropped brief → staged project, stops for sign-off |
| **10 — Builder guard + polish** | Approval guard hardening; digest/dashboard polish; schedules verified | Cowork | Hardened system | Builder never writes outside `builds/` unconfirmed; schedules fire |

**Cut order (if behind):** Autonomous Builder → tasks-calendar → learning-pipeline. (Anything cut becomes a placeholder folder + §10 entry.)
**Never cut:** Block 0, the data layer (Block 1), the Daily Digest.

---

## 8. Setup details and copy-paste prompts

**Folder creation (Block 1):** create the full §5 tree under the project root, with seed `inputs/` files as schematized.

**finance-refresh**
```
Read finances/inputs/income.csv and the goal config in memory/finances/.
Compute monthly income avg, expenses, net, runway in months, progress toward
each goal, and months remaining to the US-return target date. Write the result
to finances/data/runway.json using the schema in the PRD.
CRITICAL: never write to finances/inputs/. Overwrite only finances/data/.
```

**vault-scan**
```
Scan the Obsidian vault at ~/llm-knowledge-base (path in
knowledge-base/inputs/ config). Find notes whose last-modified is older than
the staleness threshold, and lines flagged as open questions. Write pointers
(path, date, question) to knowledge-base/data/stale-notes.json and
open-questions.json per the PRD schema.
CRITICAL: this workflow is READ-ONLY against the vault. Never create, edit,
move, or delete any file in ~/llm-knowledge-base. Write only to
knowledge-base/data/. Store pointers, never note contents.
```

**intake-refresh**
```
Add new learning items to learning-pipeline/data/intake-queue.json. Pull from
configured sources (web/X if available) or accept manual additions. Append new
items, dedupe by url/id, update statuses. Per PRD schema.
CRITICAL: never write to learning-pipeline/inputs/. Append/update data/ only.
```

**calendar-tasks-refresh**
```
Read the Calendar connector and the plugin TASKS.md. Merge into a single
timezone-aware upcoming view (Asia/Ho_Chi_Minh) and write
tasks-calendar/data/upcoming.json per the PRD schema.
CRITICAL: never write to tasks-calendar/inputs/. Overwrite data/ only.
```

**Daily Digest**
```
Read finances/data/runway.json, knowledge-base/data/stale-notes.json +
open-questions.json, learning-pipeline/data/intake-queue.json,
tasks-calendar/data/upcoming.json. Produce a concise morning brief: runway +
goal progress, notes to resurface, learning backlog, today's schedule. Write to
briefs/brief-YYYY-MM-DD.md and move any prior brief to briefs/archive/.
CRITICAL: read-only across all domain data/. Write only to briefs/.
```

**/today** — same reads as the Daily Digest, output to chat (no file write).

**/research**
```
Argument is a ticker or a software/framework name.
- TICKER → research via web/news; summarize fundamentals + relevance to the
  owner's budgeting/investment goals; write to finances/outputs/research-<ticker>-YYYY-MM-DD.md.
- SOFTWARE → summarize; add to learning-pipeline/data/intake-queue.json as
  to-study; write notes to learning-pipeline/outputs/.
If no live data source is available, degrade gracefully: report what was found
and prompt the owner to add inputs. Never fabricate figures.
```

**/capture** (the only vault writer)
```
Stage a note from the provided text. Show the owner the exact target path
inside ~/llm-knowledge-base and the full content. WRITE ONLY after explicit
"proceed". Default target: vault inbox. This is the ONLY workflow permitted to
write to the vault, and only on explicit per-write confirmation.
```

**Autonomous Builder**
```
Watch builds/ for a dropped brief or PRD. Plan the project, then build it
staged inside builds/<name>/. Report a summary and STOP for sign-off.
CRITICAL: never write outside builds/<name>/ without explicit confirmation.
Never "ship", deploy, publish, or run destructive/irreversible actions
unattended. Always wait for the owner's explicit go-ahead.
```

---

## 9. Decision log

| # | Decision | Reasoning / trade-off |
|---|---|---|
| 1 | Four domains, split across two sessions | Four is the metaprompt's single-window ceiling; splitting keeps all four rather than thinning to two |
| 2 | finances + knowledge-base first | Highest-stakes data (US-return runway) + owner's stated #1 pain point |
| 3 | Vault = read-only source of truth | Prevents recreating the owner's duplicate/stale-notes pain one layer up |
| 4 | Two-tier vault write rule | Configurability (run automations against vault) vs. safety; scheduled=read-only, interactive=confirmed write |
| 5 | `memory/` holds derived flags, not note copies | Single source of truth for knowledge; flags are regenerable, notes are not duplicated |
| 6 | `dashboard.html` now, Textual later | Plugin-native and cheap vs. a separate Python codebase; same data layer feeds both |
| 7 | Builder stages, never ships unattended | Owner's approve-before-execute rule + `cos` being a foundational base layer |
| 8 | Hermes treated as read-only source | It only passively remembers vault work today; avoids a third write target |
| 9 | `/research` routes by argument type | One skill, two domains (ticker→finances, software→learning) — less surface, clearer intent |
| 10 | `/research` degrades gracefully | Finances data is mostly manual; no hard dependency on a market feed that may not exist |
| 11 | tasks-calendar leans on plugin `TASKS.md` | Don't reinvent what the plugin provides; the domain adds calendar merge + timezone view |
| 12 | PRD written model-agnostic | Owner will run it with other agents too; no Claude-specific assumptions in prompts |
| 13 | Timezone read from config, not hardcoded | Owner is a digital nomad; location/timezone changes |
| 14 | Health deferred to placeholder | Owner said "eventually"; keeps first build focused |

---

## 10. Out of scope / future work

**Deferred to placeholder folders (in the tree, not built this window):**
- `health/` — habits, metrics, whatever the owner later tracks. Add `inputs/data/outputs/` + a refresh workflow when ready.

**Deferred patterns/components:**
- **`cos` Textual app** — a terminal dashboard that reads the same `data/` files as `dashboard.html`. The §5 schemas are its data contract, so it slots in without changing the data layer. Built later in the owner's own toolchain (Grok Build / Codex). (MVP advanced via parallel waves: live tiles/hotkeys/4 screens/Grok skeletons/CLI in tui/; see migration PRD Current Status + tui/README.md)
- **Full Autonomous Builder autonomy** — removing the sign-off gate for trusted classes of build. Requires resolving the autonomy/approval tension; deliberately not done in the foundational layer. (Autonomy Charter created out-4 in prds/AUTONOMY-CHARTER.md; defines unattended vs always-gated + logging/rollback reqs per CLAUDE.md/AGENTS.md hard rules; see root README Cowork surface section)
- **Live market-data source** for `/research [ticker]`.

**How it scales without restructuring:** a new domain = a new `{domain}/` folder (the fixed `CLAUDE.md/inputs/data/outputs/` shape) + a refresh workflow + a memory subfolder + a dashboard tile + a line in the digest. No existing folder or workflow changes.

**What would force a re-architecture:** moving storage off local files (e.g. into a database or a connector as system-of-record); making the OS the write-authority for the vault (instead of confirmed-only writes); or true multi-user.