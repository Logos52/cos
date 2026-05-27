"""Clean, COS_ROOT-aware loaders for the cos home (greenfield).

Reads the local JSON contracts and a human-maintained focus file, returning
plain dicts with graceful degradation. No Textual dependency.

The existing `tui/data/loader.py` is treated as *reference* for what data
exists — these loaders are re-derived clean (per PRD H-7), normalize shapes,
and never raise: a missing/broken contract yields {"ok": False, "note": ...}.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


def cos_root() -> Path:
    """Resolve the cos root from $COS_ROOT, else ~/cos."""
    env = os.environ.get("COS_ROOT")
    return Path(env) if env else Path.home() / "cos"


def _read_json(path: Path) -> Optional[dict]:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return None


def load_finances(root: Optional[Path] = None) -> dict[str, Any]:
    root = root or cos_root()
    d = _read_json(root / "finances" / "data" / "runway.json")
    if not d:
        return {"ok": False, "note": "runway.json not found"}
    return {
        "ok": d.get("error") is None,
        "runway_months": d.get("runway_months"),
        "net_monthly": d.get("net_monthly"),
        "currency": d.get("currency", "USD"),
        "goals": d.get("goals", []) or [],
        "us_return": d.get("us_return", {}) or {},
        "note": d.get("error"),
    }


def load_tasks(root: Optional[Path] = None) -> dict[str, Any]:
    root = root or cos_root()
    d = _read_json(root / "tasks-calendar" / "data" / "upcoming.json") or {}
    cal_off = bool(d.get("calendar_unavailable"))
    return {
        "ok": not cal_off,
        "events": d.get("events", []) or [],
        "tasks_due": d.get("tasks_due", []) or [],
        "calendar_unavailable": cal_off,
        "note": d.get("notes") or d.get("note"),
    }


def load_learning(root: Optional[Path] = None) -> dict[str, Any]:
    root = root or cos_root()
    d = _read_json(root / "learning-pipeline" / "data" / "intake-queue.json") or {}
    queue = d.get("queue", []) or []
    items = [{"title": q.get("title", "?"), "status": q.get("status", "")} for q in queue]
    return {
        "ok": True,
        "backlog_count": d.get("backlog_count", len(queue)),
        "unread": sum(1 for q in queue if q.get("status") == "unread"),
        "to_study": sum(1 for q in queue if q.get("status") == "to-study"),
        "items": items,
        "tile_summary": d.get("tile_summary"),
    }


def load_knowledge_work(root: Optional[Path] = None) -> dict[str, Any]:
    root = root or cos_root()
    d = _read_json(root / "overview-brief" / "data" / "status.json") or {}
    inbox = d.get("inbox", {}) or {}
    workbench = d.get("workbench", {})
    if isinstance(workbench, dict):
        wb_count = workbench.get("count", 0)
    elif isinstance(workbench, list):
        wb_count = len(workbench)
    else:
        wb_count = 0
    jq = d.get("journal_questions", 0)
    if isinstance(jq, dict):
        jq = jq.get("count", 0)
    inbox_items = inbox.get("items", []) if isinstance(inbox, dict) else []
    return {
        "ok": bool(d),
        "inbox_count": inbox.get("count", 0) if isinstance(inbox, dict) else 0,
        "workbench_count": wb_count,
        "journal_questions": jq,
        "recent_inbox": [it.get("title", "?") for it in inbox_items[:3]],
        "tile_summary": d.get("tile_summary"),
    }


def load_signals(root: Optional[Path] = None) -> dict[str, Any]:
    root = root or cos_root()
    d = _read_json(root / "overview-brief" / "data" / "ai-news.json") or {}
    items = d.get("items", []) or []
    return {
        "ok": bool(items),
        "source": d.get("source", "grok"),
        "count": d.get("count", len(items)),
        "items": [{"title": it.get("title", "?"), "date": it.get("date", "")} for it in items[:5]],
    }


def load_coherence(root: Optional[Path] = None) -> dict[str, Any]:
    """Vault coherence signals. Prefers the local scan (coherence.json, written
    by `cos scan`); falls back to the Cowork stale-notes/open-questions contracts."""
    root = root or cos_root()
    c = _read_json(root / "knowledge-base" / "data" / "coherence.json")
    if c and c.get("scan_ok"):
        return {
            "ok": True,
            "open_q": (c.get("open_questions") or {}).get("count", 0),
            "stale_count": (c.get("stale") or {}).get("count"),
            "orphans": (c.get("orphans") or {}).get("count"),
            "missing_frontmatter": (c.get("missing_frontmatter") or {}).get("count"),
            "total_notes": c.get("total_notes"),
            "scan_ok": True,
            "note": None,
        }
    oq = _read_json(root / "knowledge-base" / "data" / "open-questions.json") or {}
    stale = _read_json(root / "knowledge-base" / "data" / "stale-notes.json") or {}
    stale_error = stale.get("error")
    return {
        "ok": stale_error is None,
        "open_q": oq.get("count", 0),
        "stale_count": None if stale_error else stale.get("count", 0),
        "orphans": None,
        "scan_ok": stale_error is None,
        "note": "run `cos scan` to build coherence locally" if stale_error else None,
    }


def vault_root(root: Optional[Path] = None) -> Optional[Path]:
    """Resolve the Obsidian vault location (read-only). Tries, in order:
    $LLM_VAULT_ROOT, the knowledge-base config vault_path, a sibling of cos,
    then ~/llm-knowledge-base. Returns None if none exist."""
    env = os.environ.get("LLM_VAULT_ROOT")
    if env:
        p = Path(env).expanduser()
        if p.exists():
            return p
    root = root or cos_root()
    cfg = _read_json(root / "knowledge-base" / "inputs" / "config.json") or {}
    vp = cfg.get("vault_path")
    if vp:
        p = Path(vp).expanduser()
        if p.exists():
            return p
    sib = root.parent / "llm-knowledge-base"
    if sib.exists():
        return sib
    home = Path.home() / "llm-knowledge-base"
    return home if home.exists() else None


_WIKILINK_LABELLED = re.compile(r"\[\[[^\]|]+\|([^\]]+)\]\]")
_WIKILINK_BARE = re.compile(r"\[\[([^\]]+)\]\]")


def _strip_wikilinks(s: str) -> str:
    s = _WIKILINK_LABELLED.sub(lambda m: m.group(1), s)
    s = _WIKILINK_BARE.sub(lambda m: m.group(1).split("/")[-1], s)
    return s


def _trim_bullet(s: str, limit: int = 64) -> str:
    s = _strip_wikilinks(s).strip()
    # Prefer the clause before an em dash; cap length.
    head = s.split(" — ")[0].strip()
    if len(head) > limit:
        head = head[: limit - 1].rstrip() + "…"
    return head


def _blurb(raw: str, limit: int = 42) -> str:
    """A genuine short blurb: the first wikilink label, else the lead clause."""
    m = re.search(r"\[\[[^\]|]+\|([^\]]+)\]\]|\[\[([^\]]+)\]\]", raw)
    if m:
        return (m.group(1) or m.group(2).split("/")[-1]).strip()
    text = _strip_wikilinks(raw).strip()
    head = re.split(r"\s[—-]\s", text)[0].strip()
    return head if len(head) <= limit else head[: limit - 1].rstrip() + "…"


def _extract_section_bullets(text: str, heading: str) -> list[str]:
    """Collect '- ' bullets under a '## <heading>' section (until the next '## ')."""
    out: list[str] = []
    in_section = False
    want = heading.strip().lower()
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("## "):
            in_section = line[3:].strip().lower() == want
            continue
        if in_section and line.lstrip().startswith("- "):
            out.append(line.lstrip()[2:].strip())
    return out


def load_focus(root: Optional[Path] = None) -> dict[str, Any]:
    """Read 'what I'm working on' focus (read-only).

    Priority: a configured vault section (default journal/index.md →
    'What's On My Mind'), then the cos seed overview-brief/inputs/focus.md,
    then a default prompt. Source is configurable in
    overview-brief/inputs/config.json under `focus`.
    """
    root = root or cos_root()
    cfg = (_read_json(root / "overview-brief" / "inputs" / "config.json") or {}).get("focus", {})
    source = cfg.get("source", "journal/index.md")
    section = cfg.get("section", "What's On My Mind")

    headline: Optional[str] = None
    bullets: list[str] = []

    vroot = vault_root(root)
    if vroot:
        fpath = vroot / source
        try:
            if fpath.exists():
                raw_bullets = _extract_section_bullets(fpath.read_text(encoding="utf-8"), section)
                bullets = [_blurb(b) for b in raw_bullets if b.strip()]
                if bullets:
                    headline = section
        except Exception:
            pass

    if not bullets:  # fallback: cos seed
        seed = root / "overview-brief" / "inputs" / "focus.md"
        try:
            if seed.exists():
                got = False
                for raw in seed.read_text(encoding="utf-8").splitlines():
                    line = raw.strip()
                    if not line or line.startswith("#") or line.startswith("<!--"):
                        continue
                    if line.startswith("- "):
                        bullets.append(line[2:].strip())
                    elif not got:
                        headline = line
                        got = True
        except Exception:
            pass

    if not headline:
        headline = "Set focus in journal/index.md → What's On My Mind"
    return {"ok": True, "headline": headline, "bullets": bullets[:4], "source": source}


def _parse_frontmatter(text: str) -> dict[str, str]:
    if not text.lstrip().startswith("---"):
        return {}
    lines = text.splitlines()
    try:
        start = next(i for i, l in enumerate(lines) if l.strip() == "---")
    except StopIteration:
        return {}
    fm: dict[str, str] = {}
    for l in lines[start + 1:]:
        if l.strip() == "---":
            break
        if ":" in l:
            k, v = l.split(":", 1)
            fm[k.strip()] = v.strip().strip('"')
    return fm


def _to_int(v: Any) -> Optional[int]:
    try:
        return int(str(v).split("/")[0].strip())
    except (ValueError, AttributeError, TypeError):
        return None


def load_skills(root: Optional[Path] = None) -> dict[str, Any]:
    """mg-kolbs skills with current/final level + competency. Reads frontmatter
    if present (post-migration), else the `**Current Level:**` body lines."""
    root = root or cos_root()
    vroot = vault_root(root)
    if not vroot:
        return {"ok": False, "items": []}
    sdir = Path(vroot) / "mg-kolbs" / "Skills"
    if not sdir.exists():
        return {"ok": False, "items": []}
    items = []
    for p in sorted(sdir.glob("*.md")):
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        fm = _parse_frontmatter(text)
        cur = _to_int(fm.get("current-level"))
        fin = _to_int(fm.get("final-level"))
        comp = fm.get("competency", "")
        if cur is None:
            m = re.search(r"Current Level:\**\s*(\d+)", text)
            cur = int(m.group(1)) if m else None
        if fin is None:
            m = re.search(r"Final Level:\**\s*(\d+)", text)
            fin = int(m.group(1)) if m else None
        if not comp:
            m = re.search(r"Competency:\**\s*([^\n*]+)", text)
            comp = m.group(1).strip() if m else ""
        items.append({"name": p.stem, "current": cur, "final": fin, "competency": comp})
    return {"ok": True, "items": items}


def load_all(root: Optional[Path] = None) -> dict[str, Any]:
    root = root or cos_root()
    return {
        "focus": load_focus(root),
        "finances": load_finances(root),
        "tasks": load_tasks(root),
        "learning": load_learning(root),
        "knowledge_work": load_knowledge_work(root),
        "signals": load_signals(root),
        "coherence": load_coherence(root),
        "skills": load_skills(root),
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
