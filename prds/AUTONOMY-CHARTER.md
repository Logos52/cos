# Autonomy Charter — cos

**Version:** 2026-05-26 (out-4)  
**Owner:** Wedge  
**References:** CLAUDE.md (hard rules), AGENTS.md / operating-instructions.md (reversibility, PRD-first, no inferred permission), PRD-cos.md (Builder stages never ships unattended; foundational no unattended destructive), root README.md (Cowork surface section), data layer contracts.

**Goal:** Make the autonomy/approval tension explicit and operational. Define unattended (safe, low-risk) vs. always gated (destructive, irreversible, or high-trust). Require logging + clear rollback paths. "No proceed, no action." No inference from context or urgency.

## Unattended (safe for scheduled / background / agent invocation without per-run confirmation)
- Read-only or derived writes to `data/` only:
  - Domain refreshes (finance-refresh, vault-scan (read-only against vault), intake-refresh, calendar-tasks-refresh): daily per schedules in CLAUDE.md; overwrite own `data/*.json` using inputs/config + sources; tz from config.
  - TUI data loads / `action_refresh_data` (pure reads via loader.py).
  - Dashboard HTML regen or TUI tile refresh from contracts.
  - Brief aggregation that only reads contracts (Cowork or future Grok).
- Explicitly-invoked Grok skeletons (e.g. 'g' in BriefScreen or `cos brief` then g): write only to designated slots (ai-news.json, outputs/) with structured payloads; log actor + timestamp.
- Idempotent re-runs or dry-runs of portable consumers (TUI, future Grok refreshers) over the stable contracts.

**Constraints for unattended:** Must honor one-writer-per-file, never touch `inputs/`, never write vault, never perform gated ops below. Degrade gracefully on missing data.

## Always Gated (explicit owner "proceed" or confirmation required; never unattended)
- Any interaction with Obsidian vault `~/llm-knowledge-base/`: only the capture path (stage exact target path + full content; write only after explicit "proceed"; never side-effect of refresh/automation/brief). This is the *only* vault writer.
- Any write to `inputs/` (human-maintained by definition; automation never touches).
- Destructive / irreversible / high-impact:
  - Delete, overwrite, or bulk-mutate personal or derived data outside standard refresh patterns.
  - Financial actions, US-return modeling changes with real impact, mass ops.
  - Shipping / deploy / publish / "ship" from Autonomous Builder (always stages in `builds/<name>/`, reports summary, stops for sign-off; archive on completion).
  - Comms or actions in owner's name.
  - Cross-surface simultaneous writes (violates one-writer invariant; sequential migration only).
- New scheduled Grok/Hermes jobs that could cross into gated areas until explicitly classified + logged here.
- Anything the operator (or future charter exceptions) marks gated.

**Gate mechanism:** Show plan + exact scope + what is irreversible; wait for explicit owner "proceed" (recorded in session/brief/note). Interrupting with a question is always cheaper than silent destruction (per AGENTS.md).

## Logging Requirements
- Unattended actions: append entry with timestamp (ICT or config tz), actor (e.g. "cowork-finance-refresh", "grok-x-brief-2026-05-26", "tui-loader"), summary of inputs (no PII/secrets), files written, outcome (success / partial / error).
- Gated actions: full plan text + owner confirmation recorded.
- Storage: simple append-only under `logs/` (future) or per-domain `outputs/audit-*.md` or `data/` metadata; human-reviewable plain text. TUI/Grok/Cowork must emit consistent format.
- Every new domain or Grok skill: add classification + log spec to its CLAUDE.md + update this charter.

## Rollback & Recovery
- `data/` files are always derived/overwritable: re-run the responsible refresh (or TUI refresh) from `inputs/` + external sources (Calendar, web, read-only vault scan). No loss of source truth.
- Vault writes: only additive new notes (inbox or specified); owner can manually delete/edit in Obsidian. No automation ever mutates existing notes.
- Builds: everything staged in `builds/<name>/` (or archive/); safe to delete or ignore pre-sign-off.
- Full workspace: git for source (prds/, tui/, toolbox/, scripts/); sensitive data (inputs/, briefs/, data/ with numbers, memory/people) gitignored + backed externally by owner. File-level restore via re-clone or backups + re-run refreshes.
- No databases or external state of record; pure files enable simple rsync/backup/restore.

## Governance & Evolution
- New work (PRD, domain, skill, Grok integration): explicitly classify as unattended or gated *before* implementation; document in relevant CLAUDE.md + here.
- Audit on every new PRD/domain (per AGENTS.md governance).
- If charter conflicts with hard rules or "things changed": stop, re-interview owner, update.
- Exceptions (e.g. future trusted low-risk scheduled Grok refreshes): added only after explicit owner sign-off + logging/rollback verified; never assumed.
- This charter reduces sycophancy and risk: push back on anything ambiguous.

**Test:** A senior reviewer or future agent can read this + CLAUDE.md + a random refresh/prompt and correctly say "this runs unattended" or "this requires proceed + log".

Ready for use by Cowork workflows, TUI actions, Grok scripts, Hermes. Update as the portable layer grows.