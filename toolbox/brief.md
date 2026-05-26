# /brief — On-Demand Overview Brief

Runs the full overview-brief refresh on demand and outputs the result to chat. Also writes status.json and briefs/brief-YYYY-MM-DD.md.

## Instructions

### Step 1 — Read operational domain data
Read:
- ~/cos/finances/data/runway.json
- ~/cos/knowledge-base/data/stale-notes.json
- ~/cos/knowledge-base/data/open-questions.json
- ~/cos/learning-pipeline/data/intake-queue.json
- ~/cos/tasks-calendar/data/upcoming.json

### Step 2 — Scan the vault (READ-ONLY)

**Inbox:** List all .md files in ~/llm-knowledge-base/raw/inbox/. For each, extract frontmatter: title, source, created.

**Workbench:** List all .md files in ~/llm-knowledge-base/workbench/. For each, record filename and days since last modified.

**Journal open questions:** Read ~/cos/knowledge-base/data/open-questions.json, filter to entries whose `source` contains "/journal/". Take the 3 most recent.

### Step 3 — Check for AI news
Check if ~/cos/overview-brief/data/ai-news.json exists and read it if so.

### Step 4 — Write status.json
Write ~/cos/overview-brief/data/status.json with the full status payload (inbox, workbench, journal_questions, ai_news).

### Step 5 — Write and output the brief
Write ~/cos/briefs/brief-YYYY-MM-DD.md (ICT date) and output the full brief to chat.

Use the brief format from the cos-daily-digest scheduled task (Finances, Knowledge Base, Learning Pipeline, Schedule, Knowledge Work, Flags sections).

## Hard rules
- Never write to ~/llm-knowledge-base/
- Never write to any inputs/ folder
- Timezone: ICT (Asia/Ho_Chi_Minh, UTC+7)
- If vault data is unavailable, note in Flags and continue with what's readable
