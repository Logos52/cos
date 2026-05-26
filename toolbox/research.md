# /research — Research Skill

Routes by argument type: ticker → finances domain, software/framework → learning domain.

## Usage

`/research [ticker|software]`

## Routing logic

**If argument looks like a stock ticker (1-5 uppercase letters, e.g. NVDA, AAPL, BTC):**
- Research via web search: fundamentals, recent news, relevance to owner's investment goals
- Read ~/cos/finances/inputs/goals.json for context on targets and runway
- Write findings to ~/cos/finances/outputs/research-<TICKER>-YYYY-MM-DD.md
- Do NOT fabricate price data or forward projections — use only what web search returns
- If no live data available, say so clearly and prompt owner to check manually

**If argument is a software name / framework / tool:**
- Summarize what it is, why it's relevant, key docs/resources
- Add an entry to ~/cos/learning-pipeline/data/intake-queue.json with status "to-study"
  - Dedupe by URL — skip if already in queue
- Write a summary note to ~/cos/learning-pipeline/outputs/research-<name>-YYYY-MM-DD.md

## Hard rules

- Never fabricate numbers, prices, or performance figures
- Never write to any inputs/ folder
- Never write to ~/llm-knowledge-base
- Degrade gracefully if web search is unavailable — report what was found, prompt for manual input
