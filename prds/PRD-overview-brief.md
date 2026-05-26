# PRD — Overview Brief Domain

**Status:** Draft — awaiting sign-off  
**Date:** 2026-05-26  
**Author:** Claude (Cowork)

---

## Problem

The daily digest covers four operational domains (finances, knowledge-base, learning-pipeline, tasks-calendar) but tells you nothing about the state of your active knowledge work — what raw material is sitting unprocessed in your vault, what workbench drafts are in progress, and what open questions from your journal are going unanswered. This is the most tactically relevant information for a focused work session, and it's currently invisible.

A second gap exists for external AI news synthesis. That section is deferred to Phase 2 (Grok Build). Phase 1 covers the internal knowledge-work view only.

The overview-brief domain replaces and extends the existing daily digest. Rather than a separate parallel output, the digest becomes the overview-brief: same cross-domain operational view plus the new knowledge-work synthesis layer.

---

## Success Criteria

- The existing `cos-daily-digest` scheduled task is replaced by `cos-overview-brief-refresh`
- Running the refresh produces `overview-brief/data/status.json` and `briefs/brief-YYYY-MM-DD.md`
- The brief contains all existing digest sections plus a new `Knowledge Work` section covering: inbox queue, workbench in-progress, and journal open questions
- The dashboard tile for this domain reflects current status from `status.json`
- The workflow is fully read-only against the vault
- Phase 2 AI news slot is reserved in the schema; absent data degrades gracefully

---

## Scope

**In (Phase 1):**
- `raw/inbox/` scan — list all `.md` files with `title`, `source`, `created` from frontmatter
- `workbench/` scan — list all `.md` files with filename and days since last modified (no stale threshold; workbench is kept clean so all files are considered active)
- Journal open questions — filter `knowledge-base/data/open-questions.json` to entries whose source path contains `/journal/`; surface the 3 most recently created
- Write `overview-brief/data/status.json`
- Replace `cos-daily-digest` scheduled task with `cos-overview-brief-refresh`
- Update `briefs/brief-YYYY-MM-DD.md` output format to include `Knowledge Work` section
- Add or update dashboard tile (layout TBD post-build)

**Out (Phase 1):**
- AI news / X feed synthesis → **Phase 2, Grok Build** (see handoff below)
- Any write-back to the vault
- Workbench promotion workflow
- Sourcing from outside `llm-knowledge-base/raw/inbox/`, `llm-knowledge-base/workbench/`, and the existing `open-questions.json`

**On-demand skill — `/brief`:**
- Runs the full refresh on demand at any time, outside the schedule
- Reads inbox + workbench + open-questions.json, writes `status.json` and `briefs/brief-YYYY-MM-DD.md`
- Outputs the brief to chat
- Prompt lives in `toolbox/brief.md` — same pattern as `/today`

---

## Constraints

- **Vault is read-only.** No writes to `llm-knowledge-base/`. Hard rule, no exceptions.
- **`inputs/` never written by automation.** Config is human-maintained.
- **Depends on vault-scan.** The refresh reads `knowledge-base/data/open-questions.json` written by `cos-vault-scan` at 07:01 ICT. Schedule must run after vault-scan.
- **Workbench has no consistent frontmatter.** Age is inferred from file modification date. No stale threshold applied — all workbench files listed as active.
- **Frontmatter on inbox files is consistent.** Fields: `title`, `source`, `author`, `published`, `created`, `tags: clippings`. Parser can rely on these.
- **Time-agnostic design.** Refresh can be triggered at any time of day — schedule is a default, not a constraint on when the skill can run.

---

## Data Schema

`overview-brief/data/status.json`:

```json
{
  "generated_at": "2026-05-26T07:05:00+07:00",
  "inbox": {
    "count": 13,
    "items": [
      {
        "title": "Hermes Agent Masterclass",
        "source": "https://x.com/...",
        "created": "2026-05-17",
        "filename": "Hermes Agent Masterclass.md"
      }
    ]
  },
  "workbench": {
    "count": 1,
    "items": [
      {
        "filename": "2026-05-25 Wiki Status + Health Check Report.md",
        "days_old": 1
      }
    ]
  },
  "journal_questions": {
    "count": 0,
    "sample": []
  },
  "ai_news": {
    "available": false,
    "note": "Phase 2 — Grok Build"
  }
}
```

---

## Phase 2 Handoff (Grok Build)

When Grok delivers the AI news component, it writes to `overview-brief/data/ai-news.json` (separate file, same domain folder). The overview-brief refresh checks for this file at runtime and merges it into `status.json` if present. Phase 1 and Phase 2 are fully decoupled — Phase 1 degrades gracefully when `ai-news.json` is absent.

`ai-news.json` expected shape (Grok to implement):
```json
{
  "generated_at": "...",
  "items": [
    {
      "headline": "...",
      "source": "...",
      "url": "...",
      "summary": "..."
    }
  ]
}
```

---

## Folder Structure

```
cos/
└── overview-brief/
    ├── CLAUDE.md        # Domain role and hard rules
    ├── inputs/
    │   └── config.json  # max_journal_questions (default: 3), vault paths
    └── data/
        ├── status.json      # machine-refreshed on demand / scheduled
        └── ai-news.json     # Phase 2, written by Grok Build
```

---

## Plan

**Step 1** — Create `overview-brief/` folder structure, `CLAUDE.md`, `inputs/config.json`  
**Step 2** — Replace `cos-daily-digest` scheduled task with `cos-overview-brief-refresh`: reads inbox + workbench + open-questions.json, writes `status.json` + `briefs/brief-YYYY-MM-DD.md`  
**Step 3** — Create `cos-skill-brief` ad-hoc task + `toolbox/brief.md` prompt  
**Step 4** — Verify refresh output: run manually, inspect JSON and brief file  
**Step 5** — Update dashboard tile (layout decision deferred to post-build review)  

---

## Open Questions

- **Dashboard layout:** Currently 4 tiles. Replace Health placeholder or add 5th? Deferred — decide after seeing the built output.
- **Journal questions volume:** Current `open-questions.json` contains 0 journal-specific entries. This will populate over time as vault-scan catches them. No action needed now.
- **Journal questions volume:** Current `open-questions.json` contains 0 journal-specific entries. This will populate over time as vault-scan catches them. No action needed now.

---

## Sign-Off Checklist

- [x] Domain name: `overview-brief`
- [x] Replaces/extends existing daily digest (not a new parallel domain)
- [x] No stale threshold for workbench — all files listed as active
- [x] Dashboard layout: deferred post-build
- [x] Phase 2 Grok handoff via `ai-news.json`
- [x] `/brief` on-demand skill included in Phase 1
- [ ] **Explicit proceed from Wedge**
