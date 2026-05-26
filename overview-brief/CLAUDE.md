# overview-brief — Domain Memory

## Role

Knowledge-work synthesizer. Extends the daily digest with a live view of active vault work — what's unprocessed, what's in progress, what questions are open. Replaces the `cos-daily-digest` domain.

## What this domain does

- Scans `~/llm-knowledge-base/raw/inbox/` for unprocessed clippings
- Scans `~/llm-knowledge-base/workbench/` for in-progress drafts
- Reads journal open questions from `~/cos/knowledge-base/data/open-questions.json`
- Merges `data/ai-news.json` if present (Phase 2 — Grok Build)
- Writes `data/status.json` and `~/cos/briefs/brief-YYYY-MM-DD.md`

## Hard rules

- **Vault is READ-ONLY. Absolute.** Never create, edit, move, or delete anything in `~/llm-knowledge-base/`.
- **Pointers only.** `data/` holds filenames and metadata — never copies of vault content.
- **Never write to `inputs/`.** Config is human-maintained.
- **Depends on vault-scan.** Scheduled run must follow `cos-vault-scan` (reads its open-questions.json output).
- **Degrades gracefully.** If vault is unavailable or ai-news.json is absent, output what's available and note gaps.

## Key files

| File | Role |
|------|------|
| `inputs/config.json` | max_journal_questions, vault paths — human-maintained |
| `data/status.json` | Live status — overwritten each refresh |
| `data/ai-news.json` | Phase 2 input written by Grok Build — read if present |

## Voice

Synthesizer. Surfaces what needs attention without editorializing. Counts and titles, not summaries.
