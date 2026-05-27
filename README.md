# cos — Personal OS

A personal operating system built in [Claude Cowork](https://claude.com/product/cowork), running on the [Productivity plugin](https://claude.com/plugins). Unifies four domains of life and knowledge work into scheduled refresh workflows, a daily digest, an always-on dashboard, and on-demand skills — all backed by plain local files.

---

## Philosophy

- **Local files are the only storage.** All state lives in plain `.json` / `.csv` / `.md` files under `~/cos/`. No databases, no external services.
- **Connectors are sources, not storage.** Calendar, GitHub, web — read from them, never store to them.
- **The Obsidian vault is read-only for automation.** The `/capture` skill is the only thing that can write to it, and only on explicit per-write confirmation.
- **One writer per file.** Reads are shared; writes are not. Safe for future multi-agent migration.

---

## Structure

```
cos/
├── CLAUDE.md                   # Cross-cutting memory: owner, terms, hard rules
├── TASKS.md                    # Plugin task list (also backs tasks-calendar)
├── dashboard.html              # Always-on visual — regenerated daily by generator (scripts/generate_dashboard.py; sole writer; `cos dashboard` on-demand)
├── prds/                       # Design documents and PRDs
│   ├── PRD-cos.md              # The original design document
│   └── PRD-overview-brief.md  # Overview Brief domain
├── toolbox/                    # On-demand skill prompts
│   ├── today.md
│   ├── research.md
│   ├── capture.md
│   └── builder.md
├── briefs/                     # Daily Digest output + archive
├── builds/                     # Autonomous Builder drop zone
├── memory/                     # Deep memory per domain (see below)
├── finances/
│   ├── CLAUDE.md               # Domain role and voice
│   ├── inputs/                 # Human-maintained: income.csv, goals.json
│   ├── data/                   # Machine-refreshed: runway.json
│   └── outputs/                # Research notes, monthly summaries
├── knowledge-base/
│   ├── CLAUDE.md
│   ├── inputs/                 # config.json — vault path + staleness threshold
│   ├── data/                   # stale-notes.json, open-questions.json
│   └── outputs/
├── learning-pipeline/
│   ├── CLAUDE.md
│   ├── inputs/                 # sources.json, reading-goals.md
│   ├── data/                   # intake-queue.json
│   └── outputs/
├── tasks-calendar/
│   ├── CLAUDE.md
│   ├── inputs/                 # config.json (timezone), recurring.md
│   ├── data/                   # upcoming.json
│   └── outputs/
└── health/                     # Placeholder — future domain
```

### `inputs/` vs `data/`

`inputs/` is **human-maintained and never touched by automation.** `data/` is machine-refreshed and freely overwritten. This separation is a hard invariant — never break it.

---

## Domains

| Domain | What it does |
|--------|-------------|
| **finances** | Runway, net monthly, goal progress, savings goals |
| **knowledge-base** | Vault scan — stale notes, open questions (read-only against vault) |
| **learning-pipeline** | Intake queue — deduped by URL, status-tracked |
| **tasks-calendar** | Unified upcoming view — Calendar + TASKS.md, timezone-aware |

---

## Morning schedule

All times in your local timezone, read from `tasks-calendar/inputs/config.json` — never hardcoded.

| Time | Task |
|------|------|
| 07:00 | `finance-refresh` — reads income.csv + goals.json, writes runway.json |
| 07:01 | `vault-scan` — read-only vault scan, writes stale + open-question flags |
| 07:02 | `intake-refresh` — updates learning queue, dedupes |
| 07:03 | `calendar-tasks-refresh` — merges Calendar + TASKS.md |
| 07:15 | `daily-digest` — cross-domain brief → `briefs/brief-YYYY-MM-DD.md` |
| 07:20 | `cos dashboard` — runs generator + opens Basecamp snapshot HTML; daily via cron or user scheduler (replaces retired `dashboard-refresh` / `cos-dashboard-refresh` per one-writer rule in PRD-cos-dashboard-basecamp.md) |

---

## Snapshot dashboard (new flow per PRD-cos-dashboard-basecamp.md Phase 5)
`cos` / `cos dashboard` : runs generator + opens Basecamp snapshot HTML (primary; sole writer of dashboard.html, 20h freshness, cos:// actions). Daily via cron/scheduler. TUI companion: `cos tui`. macOS one-time: `cos setup-macos-handler` (Swift cos:// handler for Ghostty; zero bg processes). See macos-helper/ + PRD.

## On-demand skills

| Skill | What it does |
|-------|-------------|
| `/today` | Digest snapshot to chat — no file written |
| `/research [ticker\|software]` | Ticker → finances outputs; software → learning queue + outputs |
| `/capture [text]` | Stages a note for vault filing — writes only on explicit "proceed" |
| `/builder` | Reads a brief from `builds/`, stages a project, stops for sign-off |

---

## Open question convention (vault)

Two extraction methods used by `vault-scan`:

1. **Obsidian callout:** anywhere in a note
   ```markdown
   > [!question]
   > What is the best pattern for cross-session agent memory?
   ```

2. **Section heading:** in notes or journal entries
   ```markdown
   ## Open Questions
   - What is the best pattern for cross-session agent memory?
   - Should this live in the vault or in cos memory?
   ```

---

## Hard rules

- **`inputs/` is never written by a refresh workflow.** Human-maintained only.
- **The vault is read-only for all scheduled/automated work.** No exceptions.
- **`/capture` is the only vault writer** — stages, shows full content + path, writes only after explicit "proceed."
- **Timezone from config, never hardcoded.** `tasks-calendar/inputs/config.json` is the source of truth.
- **Anything destructive or irreversible:** show plan, flag what can't be undone, wait for explicit "proceed."
- **One writer per `data/` file.** Critical for future multi-agent handoffs.

---

## Adding a new domain

New domain = new folder with the fixed shape + one refresh workflow + one memory subfolder + one dashboard tile + one digest line. No existing folder or workflow needs to change.

```
cos/
└── {domain}/
    ├── CLAUDE.md       # Role, voice, hard rules for this domain
    ├── inputs/         # Human-maintained seed files
    ├── data/           # Machine-refreshed outputs
    └── outputs/        # On-demand generated content
```

---

## What's private (not in this repo)

- `finances/inputs/` — income, goals, personal financial data
- `finances/data/` — computed runway (contains real numbers)
- `memory/people.md`, `memory/terminology.md` — personal profile
- `memory/finances/`, `memory/knowledge-base/`, etc. — derived personal knowledge
- `briefs/` — daily digests (contain personal data from all domains)
- `dashboard.html` — regenerated with personal data embedded (by `scripts/generate_dashboard.py` generator; `cos dashboard` on-demand)

The `.gitignore` handles all of the above. The system structure and prompts are public; the data is not.

---

## Cowork Surface vs. Portable Core (Model-Agnostic Layer)
This section (added out-4) makes explicit what depends on the Claude Cowork Productivity plugin vs. what is portable via the stable data layer contract. See also prds/AUTONOMY-CHARTER.md and migration PRD.

**Cowork-specific (plugin / Claude Cowork runtime only; not portable without equivalent scheduler + chat surface):**
- Scheduled refreshes + morning brief (Productivity plugin tasks at 07:00 ICT etc., per CLAUDE.md schedules).
- On-demand skills execution surface: `/today`, `/research [ticker|software]`, `/capture`, `/brief`, `/builder` (via `toolbox/*.md` prompts in Cowork chat; plugin provides runtime + memory + TASKS.md backing for tasks-calendar).
- `dashboard.html` (generated by `scripts/generate_dashboard.py` snapshot per PRD-cos-dashboard-basecamp.md; open from disk; daily + `cos dashboard` on-demand; old `cos-dashboard-refresh` retired).
- Plugin TASKS.md as live source for tasks domain; plugin deep `memory/`.
- Connectors (Calendar etc.) + overall Cowork project orchestration.

**Portable / model-agnostic core (any runtime: TUI, Grok Build, Hermes, scripts; data layer is the contract):**
- All state: `~/cos/` plain files under per-domain `inputs/` (human-maintained, never written by automation), `data/` (machine-refreshed, one-writer invariant), `outputs/`, `memory/`, `briefs/`, `builds/`, `overview-brief/data/`.
- Canonical contracts: `finances/data/runway.json`, `knowledge-base/data/{stale-notes.json,open-questions.json}`, `learning-pipeline/data/intake-queue.json`, `tasks-calendar/data/upcoming.json`, `overview-brief/data/status.json` (and ai-news.json for Grok X).
- Consumers: Textual TUI (`tui/app.py`, `tui/data/loader.py`, dedicated screens, `scripts/cos` launcher with `cos brief` etc. real dispatch), future standalone Grok refreshers / X tools (write same contracts), CLI, Hermes skills.
- Hard invariants (enforced across surfaces): vault `~/llm-knowledge-base/` read-only for all automation (only `/capture` or equiv. stages + explicit proceed writes); `inputs/` human-only; one writer per `data/` file; timezone from `tasks-calendar/inputs/config.json` (never hardcoded); anything destructive/irreversible shows plan + waits for explicit "proceed" (no inference).
- Unified entry: `cos` CLI + Grok skeletons now deliver parity for key skills in terminal / outside Cowork.

This distinction enables safe migration: extend portable (TUI/Grok) while Cowork surfaces continue unchanged. New work classifies as Cowork-only or portable at PRD time.

---

## macOS Native `cos://` URL Scheme Handler

On macOS the snapshot dashboard (and any other surface) can use the custom `cos://` URL scheme for a far better experience than raw copy-to-clipboard.

- Clicking a dashboard action (e.g. "Run brief", "Research NVDA") opens a `cos://brief` or `cos://research?ticker=NVDA` URL.
- A small native Swift helper (`macos-helper/`) receives it, maps it to the exact `cos` subcommand, and drives **Ghostty** (recommended) — reusing an existing window by opening a new tab when possible, then typing the command automatically.
- The helper is tiny, has **zero background processes**, and only runs for the duration of a single URL invocation before terminating.
- Graceful fallback to Terminal.app + clear notifications if Ghostty is absent.

**One-time setup (strongly recommended):**

```bash
cos setup-macos-handler
```

This builds the helper from source (if the `macos-helper/` tree is present), installs `CosURLHandler.app` to `~/Applications`, registers the scheme, and prints Ghostty profile recommendations plus test commands.

See:

- `macos-helper/README.md` — full docs, Ghostty config snippet, troubleshooting, architecture.
- `prds/PRD-cos-dashboard-basecamp.md` — the authoritative spec for the handler and the dashboard action mapping table.
- Direct CLI testing of the built binary is also supported.

The snapshot generator (`scripts/generate_dashboard.py`, sole writer of `dashboard.html` per one-writer rule) emits buttons/links that prefer `cos://` URLs (with JS fallback to copy-to-clipboard + toast for non-macOS or missing handler). This is the integration point between the generator (Basecamp-style snapshot, cos:// + client JS) and the native helper. Old `cos-dashboard-refresh` task retired; generator + `cos dashboard` handle daily/on-demand regeneration. See prds/PRD-cos-dashboard-basecamp.md (Decision Log + Sign-Off).

---

## Built with

- [Claude Cowork](https://claude.com/product/cowork) — agent runtime
- [Productivity plugin](https://claude.com/plugins) — task list, memory, dashboard scaffolding
- [Obsidian](https://obsidian.md) — vault / second brain (external, read-only source)

---

## License

MIT — use the structure and prompts freely. Don't commit your `inputs/` or `data/`.
