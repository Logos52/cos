# cos — Cross-Cutting Memory

## Owner

Wedge — freelance researcher / engineer, digital nomad
Direct comms, PRD-first, approve-before-execute on anything destructive or irreversible.
Full profile: `memory/people.md`

## Domains

| Domain | Purpose |
|--------|---------|
| `finances` | Runway, goals, US-return countdown |
| `knowledge-base` | Vault scan — stale notes, open questions |
| `learning-pipeline` | Intake queue, reading backlog |
| `tasks-calendar` | Unified upcoming view (calendar + TASKS.md) |

## Key terms

| Term | Meaning |
|------|---------|
| `vault` | `~/llm-knowledge-base/` — Obsidian second brain, adjacent to this project |
| `runway` | Months of expenses covered by current liquid savings |
| `ICS` | Learning techniques system (`vault/raw/private/ICS/`) |
| `llm-wiki` | Karpathy-style GitHub Pages knowledge base |
| `ICT` | UTC+7 / Asia/Ho_Chi_Minh — Wedge's current timezone |

Full glossary: `memory/terminology.md`

## Hard rules

- **`inputs/` is never written by a refresh workflow.** Human-maintained. Refresh workflows write only to `data/` and `outputs/`.
- **Vault is read-only for all scheduled/automated work. No exceptions.** Never create, edit, move, or delete anything in `~/llm-knowledge-base/` automatically.
- **`/capture` is the only vault writer** — stages a note, shows exact path + content, writes only after explicit "proceed."
- **Timezone from config, never hardcoded.** Read from `tasks-calendar/inputs/config.json`.
- **Anything destructive or irreversible:** show plan + scope, flag what can't be undone, wait for explicit "proceed." No inferred permission.
- **One writer per `data/` file.** Reads can be shared; writes cannot. Applies to any future multi-agent migration.

## Data layer

All state lives in plain files under `~/cos/`. Connectors (Calendar, GitHub, web) and external systems (Hermes, the vault) are **sources** — read from, occasionally pushed to on confirmation — never storage.

## Interaction patterns

| Pattern | Output |
|---------|--------|
| Dashboard | `dashboard.html` — always-on visual |
| Daily Digest | `briefs/brief-YYYY-MM-DD.md` — 07:15 ICT |
| Skills | `toolbox/` — `/today`, `/research`, `/capture` |
| Builder | `builds/` — staged, sign-off gated |

## Coding conventions

See `CODING_CONVENTIONS.md`.
