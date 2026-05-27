#!/usr/bin/env python3
"""One-off: migrate mg-kolbs Skills/Goals to YAML frontmatter (additive).

Skills: derive current-level / final-level / competency from the existing body
lines (`**Current Level:** N/10` etc.) and prepend frontmatter. Body untouched.
Goals: prepend a placeholder (status: in-progress) for you to fill in Obsidian.

Idempotent: skips any note that already starts with frontmatter.
Reversible: the vault is a git repo — `git diff` / `git checkout` to revert.

Usage:  python3 migrate_mgkolbs_frontmatter.py /path/to/llm-knowledge-base
"""

import re
import sys
from pathlib import Path

vault = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "llm-knowledge-base"
skills_dir = vault / "mg-kolbs" / "Skills"
goals_dir = vault / "mg-kolbs" / "Goals"


def has_frontmatter(text: str) -> bool:
    return text.lstrip().startswith("---")


def migrate_skill(p: Path) -> str:
    text = p.read_text(encoding="utf-8")
    if has_frontmatter(text):
        return "skip (already has frontmatter)"
    cur = re.search(r"Current Level:\**\s*(\d+)", text)
    fin = re.search(r"Final Level:\**\s*(\d+)", text)
    comp = re.search(r"Competency:\**\s*([^\n*]+)", text)
    fm = ["---", "type: skill"]
    if cur:
        fm.append(f"current-level: {cur.group(1)}")
    if fin:
        fm.append(f"final-level: {fin.group(1)}")
    if comp:
        fm.append(f'competency: "{comp.group(1).strip()}"')
    fm.append('notes: ""')
    fm.append("---")
    p.write_text("\n".join(fm) + "\n" + text, encoding="utf-8")
    return "migrated"


def migrate_goal(p: Path) -> str:
    if p.stem.lower().startswith("example"):
        return "skip (example/template)"
    text = p.read_text(encoding="utf-8")
    if has_frontmatter(text):
        return "skip (already has frontmatter)"
    fm = ["---", "type: goal", "status: in-progress", 'last-evaluation: ""', 'notes: ""', "---"]
    p.write_text("\n".join(fm) + "\n" + text, encoding="utf-8")
    return "migrated"


if __name__ == "__main__":
    for p in sorted(skills_dir.glob("*.md")):
        print(f"skill  {p.name:<28} {migrate_skill(p)}")
    for p in sorted(goals_dir.glob("*.md")):
        print(f"goal   {p.name:<28} {migrate_goal(p)}")
