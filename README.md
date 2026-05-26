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
├── dashboard.html              # Always-on visual — regenerated daily
├── PRD-cos.md                  # The original design document
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
| 07:20 | `dashboard-refresh` — regenerates `dashboard.html` with current data |

---

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
- `dashboard.html` — regenerated with personal data embedded

The `.gitignore` handles all of the above. The system structure and prompts are public; the data is not.

---

## Built with

- [Claude Cowork](https://claude.com/product/cowork) — agent runtime
- [Productivity plugin](https://claude.com/plugins) — task list, memory, dashboard scaffolding
- [Obsidian](https://obsidian.md) — vault / second brain (external, read-only source)

---

## License

MIT — use the structure and prompts freely. Don't commit your `inputs/` or `data/`.
