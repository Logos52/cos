# /capture — Vault Writer (the ONLY vault writer in cos)

Stages a note for filing into ~/llm-knowledge-base. NEVER writes without explicit "proceed" from Wedge.

## Usage

`/capture [text or paste content]`

## Instructions

1. Take the provided text and determine the best note format (title, tags, body)
2. Determine the target path inside ~/llm-knowledge-base:
   - Default: ~/llm-knowledge-base/inbox/YYYY-MM-DD-<slug>.md
   - If the content clearly belongs to a specific area (e.g. agentic-eng, ICS), suggest that path instead
3. Stage the note — show Wedge:
   - **Exact target path**
   - **Full note content** (formatted as it will be written)
4. STOP. Ask: "Proceed? (yes/no — or suggest a different path)"
5. Write ONLY after receiving explicit "proceed" or "yes"
6. If Wedge says no, or suggests changes, revise and re-stage before writing

## Hard rules

- NEVER write to the vault without explicit per-write confirmation ("proceed")
- NEVER write as a side effect of any other workflow
- This is the ONLY skill in cos permitted to write to ~/llm-knowledge-base
- One confirmation per write — don't batch multiple notes under a single "proceed"
- Never overwrite an existing vault note without showing the diff and getting explicit confirmation
