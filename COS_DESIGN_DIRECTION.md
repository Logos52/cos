# COS Design Direction — Basecamp-Inspired Calm Personal Workspace

**Owner:** Wedge  
**Date:** 2026-05-27  
**Status:** Draft — For review and iteration  
**Related:** current TUI work in `tui/`, data contracts in `data/`

---

## 1. Vision

**cos** is a calm, clean, humane personal operating system / workspace that helps you see the state of your life and move forward with focus and low cognitive overhead.

It draws primary inspiration from Basecamp’s design philosophy:

- Generous whitespace and breathing room
- Clear visual hierarchy with calm typography
- Card- and section-based layouts that feel intentional rather than dense
- A general feeling of “this is a thoughtful place to work”
- Strong emphasis on content (writing, summaries, insights) over pure data dashboards

The system has two coordinated interfaces that share the same design language and the same rich data layer:

- **Primary:** HTML dashboard (the “always-on” calm workspace view)
- **Secondary / Companion:** Textual TUI (fast, keyboard-first access and power-user workflows)

Both surfaces present the same underlying truth: rich, published, synthesized content about your domains (Finances, Knowledge Base, Learning, Tasks, Knowledge Work, etc.), augmented by Grok X research where it adds unique value.

---

## 2. Core Design Principles

| Principle                  | What it means for cos                                                                 | How it shows up                                                                 |
|---------------------------|---------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| Calm & Humane             | The interface should lower stress, not add to it.                                     | Generous padding, soft colors, clear hierarchy, no aggressive alerts or dense grids |
| Content over Clutter      | Paragraph summaries, insights, and narrative are first-class citizens.                | Tiles and cards prioritize well-written summaries over raw numbers or long lists |
| Breathing Room            | Nothing feels cramped. Elements have space to be themselves.                          | Consistent generous spacing (inspired by Basecamp’s use of whitespace)          |
| Clear Hierarchy           | What matters most is immediately obvious.                                             | Brief/Knowledge Work and Finances get visual weight; supporting domains are smaller but still respected |
| Intentional Cards         | Information is grouped into calm, self-contained cards/sections.                      | Consistent card treatment across HTML and (where possible) TUI                  |
| Typography as UI          | Good type does a lot of the heavy lifting.                                            | Clear type scale, good line-lengths, thoughtful use of weight and color         |
| Low Friction Publishing   | It should feel natural to write or share small, useful artifacts (summaries, notes).  | Easy paths to create or surface paragraph summaries and Grok X insights         |
| Coherent Dual Interfaces  | The TUI and HTML versions feel like siblings, not cousins.                            | Shared visual language, consistent naming, same underlying data and summaries   |

---

## 3. Visual Language & Aesthetic

### Color
- Soft, desaturated palette (inspired by Basecamp’s calm blues, grays, and warm neutrals).
- High contrast for text, but never harsh.
- Accent color used sparingly for important actions or highlights (e.g., Grok X content, urgent items).
- Dark mode for the TUI should feel like a natural extension, not an afterthought.

### Typography
- Clean, highly legible sans-serif (system UI fonts or similar to Basecamp’s approach).
- Generous line-height and comfortable measure.
- Clear type scale that creates visual rhythm without needing heavy decoration.

### Cards & Sections
- Subtle borders or very light background tints.
- Consistent inner padding (think “comfortable” rather than “tight”).
- Gentle visual separation between cards — not aggressive boxes.
- Cards can contain a title, optional meta, a rich paragraph summary, and a small set of key stats or actions.

### Motion & Feedback
- Subtle, purposeful transitions (nothing flashy).
- Clear but calm feedback when data refreshes or Grok content arrives.
- Focus states that feel intentional and accessible.

---

## 4. Layout & Structure

### Overall Philosophy
Move away from rigid equal-weight grids (“5 vertical boxes”) toward a calmer, more organic card-based layout with clear priority.

Inspired by Basecamp’s home/dashboard views:
- A few high-signal areas get more visual weight.
- Supporting information lives in well-behaved secondary cards.
- Plenty of whitespace so nothing feels like it’s competing for attention.

### Recommended Layout Direction (MVP)

**HTML Primary Dashboard**
- Calm top navigation or header with cos identity + global actions (refresh, search, quick capture).
- Main content area using a responsive card grid (not strict masonry, but flexible card layout that adapts gracefully).
- **High-priority zone** (top or left): Brief / Knowledge Work + Finances (the two areas the user has called out as most important).
- **Secondary cards**: Learning Pipeline, Tasks/Schedule, Knowledge Base themes.
- Each card surfaces:
  - A short, high-quality paragraph summary (the “published content” we’re investing in).
  - 1–3 key stats or visual indicators.
  - Clear, low-friction way to go deeper (clicking the card opens a focused view or dedicated workspace).

**Finances Card (special treatment)**
- Numberless by default: simple ASCII/Unicode sparklines, progress bars, directional indicators.
- Clicking the card (or an explicit “Expand” affordance) reveals numbers + richer graphs + the beginning of a dedicated Finances workspace.

**Textual TUI Companion**
- Retains the current spanned priority grid approach as a starting point, but applies the same calm card philosophy where possible.
- Strong emphasis on keyboard navigation and fast “go deeper” actions (the existing hotkeys `b`, `r`, `c`, `t`, `u` remain core).
- Tiles show the same paragraph summaries (adapted for terminal density — bullets or short paragraphs as appropriate).

### Hierarchy & Priority
- **Brief / Knowledge Work** — usually the most prominent.
- **Finances** — visually important but can be calmer (graphs instead of big numbers).
- **Learning + Knowledge Base** — strong second-tier presence.
- **Tasks/Schedule** — supportive rather than dominant.

---

## 5. Content Treatment

This direction doubles down on the existing “content-first” work:

- **Paragraph summaries** are the heart of the experience. They should feel like something you’d actually want to read and publish.
- Numbers and raw counts are supporting actors, not the headline.
- Grok X research (ai-news, threads, signals) appears as calm, clearly attributed cards or sections — never overwhelming the human-authored content.
- Every domain should eventually have a “published voice” (the summaries we’re building).

**Example card content rhythm (HTML):**
- Card title (domain name)
- 2–4 sentence paragraph summary (the valuable published content)
- 1–3 small visual indicators or key stats
- Subtle “Go deeper” or expand affordance

---

## 6. Interaction & Navigation

- Clicking a card should feel like “entering that area of the workspace” (similar to opening a project or section in Basecamp).
- Dedicated domain views (the existing BriefScreen, Research, Capture, Tasks, etc., and future Finances workspace) should feel like focused, calm spaces rather than dense admin screens.
- Global actions (refresh all, quick capture, Grok X refresh) should be discoverable but not intrusive.
- The TUI should feel like a faster, keyboard-native sibling — same content, same calm intent, different interaction model.

---

## 7. Relationship Between Interfaces

- The HTML dashboard is the “main stage” — where you spend relaxed time reviewing state and publishing insights.
- The TUI is the “fast lane” and power tool — great for quick checks, running workflows, and when you’re already in the terminal.
- Both should feel like part of the same calm system. When you see a summary in the HTML dashboard, you should recognize the same voice and data when you open the TUI.

---

## 8. Near-Term Priorities (Design & Implementation)

1. **Refine the overall HTML layout direction** — move from the current TUI “5 boxes” mental model to a calmer card-based structure.
2. **Establish the Basecamp-inspired visual language** in the HTML (colors, typography, card treatment, spacing).
3. **Adapt paragraph summaries** for the new card format (length, tone, when to use bullets vs prose).
4. **Define the Finances visual language** (numberless graphs + expand behavior) and how it fits the calm card system.
5. **Create a lightweight TUI companion treatment** that respects the same principles without trying to perfectly replicate the HTML layout.
6. **Map the domains** more explicitly to Basecamp-style sections (Messages, To-dos, Docs, etc.) so the metaphor feels coherent.

---

## 9. Inspirations & References

- Basecamp (primary)
- Calm, high-quality modern tools that prioritize focus (Notion in calm modes, Linear, Arc, etc.)
- The existing cos values: model-agnostic data contracts, rich published content, Grok X as a thoughtful collaborator rather than a noisy feed.

---

## 10. Open Questions

- How literally do we want to use Basecamp’s section names (Messages, To-dos, Docs, etc.) vs. cos-native names?
- What is the right balance between “calm” and “information dense” in the terminal version?
- How much of the Basecamp philosophy (e.g., the emphasis on writing and communication) should influence how we encourage publishing summaries and notes inside cos?

---

**Next step:** Once this direction is reviewed and refined, we can move into concrete design explorations (wireframes or high-fidelity mocks for the HTML dashboard + updated TUI treatment) and begin implementation against the existing data contracts.

This document is meant to be living — we’ll update it as we learn what actually feels like “Basecamp for a personal OS.”