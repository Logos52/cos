# Note for Grok — cos Dashboard (Build Brief + Live-Read Background)

**From:** Claude (Cowork)
**Date:** 2026-05-27
**Authoritative spec:** `prds/PRD-cos-dashboard-basecamp.md` — build to that; this note is orientation.

---

## DECISION & BUILD BRIEF (read this first)

Wedge resolved the direction after your feedback. **You are building a snapshot dashboard generator.**

**What to build:**
- A **generator** (your toolchain) that reads the cos data contracts and emits a single self-contained `dashboard.html` with all values **embedded at build time**. The page does **no runtime fetch** and needs **no server** — it opens straight from disk.
- Restyle the output to the **Basecamp design language** in the PRD (warm cream bg, white cards, domain accent strips, generous spacing, light/dark toggle).
- Render six domain cards: Overview Brief, Finances, Knowledge Base, Learning Pipeline, Tasks & Calendar, Health (placeholder).

**Hard requirements:**
- **Timestamp field is not uniform:** `finances`, `knowledge-base`, `learning-pipeline`, `tasks-calendar` use `generated`; `overview-brief/*.json` use `generated_at`. Normalize both. Compute per-card freshness at build (✓ fresh / ⚠ stale / — unavailable), stale threshold ~24h (reconcile with the TUI loader's ~20h — pick one shared constant).
- **Graceful degradation:** missing/unreadable file → ⚠ "data unavailable" card. Null/absent fields → "not yet populated", never a broken bar. Note `runway.json` currently has `pct_complete`/`months_remaining` = null, so finance goal bars will be empty until `cos-finance-refresh` is fixed upstream (not your job, but expect it).
- **Retire `cos-dashboard-refresh`.** Your generator becomes the **sole writer** of `dashboard.html` (one-writer-per-file rule). Don't run both.
- **Pure reader.** Generator reads `data/` only; never writes `data/`; vault stays read-only.
- **Regeneration:** daily (scheduled run of the generator, replacing `cos-dashboard-refresh`) + on demand via a `cos dashboard` command (regenerate + open).

**Interactivity (snapshot = no server, so):**
- Cards expand inline (CSS/JS), theme toggle, help overlay — all client-side.
- Action buttons **copy a `cos` command to the clipboard** (toast "paste in terminal"); they do not execute. Mapping: Overview→`cos brief`, KB→`cos vault-scan`, Finances→`cos research <ticker>`, Learning→`cos research <software>`, Tasks→`cos task add "<text>"`, header→`cos dashboard`.

**Explicitly cut / out:** agent selector (gone); full power-user keyboard set (Textual TUI is shelved — do NOT relocate keyboard power to HTML); live in-page fetch; server-side execution.

**Data contracts (read at build):**
`finances/data/runway.json`, `knowledge-base/data/{stale-notes,open-questions}.json`, `learning-pipeline/data/intake-queue.json`, `tasks-calendar/data/upcoming.json`, `overview-brief/data/{status,ai-news}.json`.

---

## Background — why snapshot, not live (what I hit in Cowork)

Wedge originally wanted the HTML to read the data **live**. I tried delivering that as a **Cowork live artifact** and proved it can't work:

1. `window.cowork` exposes only `callMcpTool`, `askClaude`, `sample`, `runScheduledTask`.
2. `callMcpTool("Read", {file_path})` routes but returns `"Read" is not in this artifact's mcp_tools allowlist`.
3. The `mcp_tools` allowlist accepts only `mcp__<server>__<tool>` names; the built-in `Read` isn't that form, so it can never be granted.
4. No MCP server tool (or registry connector) reads local files — only cloud storage (Drive, Egnyte). Direct `fetch()`/`file://` is sandbox-blocked.

Then we considered a **browser + local server** (true live `fetch`). Wedge rejected the running-server requirement (he's a nomad across machines). And a browser page can't `fetch()` local files without a server anyway (CORS on `file://`). So **snapshot (embed at build, no server)** is the chosen path — your lane, terminal-side.

## Open questions for you
1. Where should the daily regeneration run — keep it on the Cowork schedule, or move it to your scheduler/cron as part of the migration? (One writer either way.)
2. Is copy-to-clipboard acceptable for actions, or do you see a clean no-server way to do more?
3. Anything in the PRD design you'd build differently. Be blunt — Wedge wants a real second opinion, not validation.
