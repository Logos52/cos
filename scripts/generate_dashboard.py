#!/usr/bin/env python3
"""
cos Dashboard Snapshot Generator — Basecamp-inspired calm single-file HTML.

Generates a self-contained, beautiful, no-server dashboard.html from the cos
data contracts (snapshot model). Replaces the old hand-maintained dashboard.

- Reuses/adapts tui/data/loader.py contracts and loading logic.
- Handles both "generated" and "generated_at" timestamps.
- Computes per-card freshness (shared 20h threshold with loader).
- Graceful degradation for missing/stale/partial data (tile_summary, null goals, vault errors, etc.).
- Warm cream + white cards + colored domain strips aesthetic (PRD + COS_DESIGN_DIRECTION).
- All 6 domain cards with exact anatomy from PRD: colored strip, icon+name+ts+freshness, stats, lead summary (content-first), footers with action buttons.
- Client JS: card expand (inline full-width detail), light/dark theme toggle (persisted), ? help modal, Esc, action buttons using cos:// (macOS helper) with clipboard fallback + toast.

Usage:
  python scripts/generate_dashboard.py                 # auto-detect COS_ROOT or ~/cos; writes dashboard.html
  COS_ROOT=/path/to/cos python scripts/generate_dashboard.py --output /tmp/dash.html
  python scripts/generate_dashboard.py --cos-root . --output dashboard.html

The output is pure static HTML (open from disk). Regenerate via `cos dashboard` (future CLI) or this script.
This generator is the sole writer of dashboard.html (one-writer rule; old cos-dashboard-refresh retired).

Author: Grok Build (2026-05-27 per PRD-cos-dashboard-basecamp.md)
"""

from __future__ import annotations

import argparse
import html as html_escape_module
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# --- Auto-detect + COS_ROOT handling (mirrors scripts/cos launcher + tui/app.py) ---
def detect_cos_root() -> Path:
    """Resolve COS_ROOT with precedence:
    1. COS_ROOT env var (explicit override, tests, non-~/cos workspaces).
    2. Auto-detect when this script lives inside a cos checkout (dev / direct exec).
       (scripts/generate_dashboard.py -> parent is the cos root containing tui/)
    3. Default to ~/cos (for installed usage or scheduled runs).
    """
    env = os.environ.get("COS_ROOT")
    if env:
        return Path(env).expanduser().resolve()

    script_path = Path(__file__).resolve()
    # From scripts/ dir: ../ = cos root
    candidate = script_path.parent.parent
    if (candidate / "tui" / "data" / "loader.py").exists():
        return candidate

    # cwd check (common when running from repo root)
    cwd = Path.cwd().resolve()
    if (cwd / "tui" / "data" / "loader.py").exists():
        return cwd

    # Also support running from inside tui/ or other subdirs
    for parent in script_path.parents:
        if (parent / "tui" / "data" / "loader.py").exists():
            return parent

    return (Path.home() / "cos").resolve()


def ensure_importable(cos_root: Path) -> None:
    """Make tui package importable when running from source tree (dev)."""
    if str(cos_root) not in sys.path:
        sys.path.insert(0, str(cos_root))


# --- Safe JSON loader (duplicated from loader.py _load_json; keeps generator standalone & robust) ---
def _load_json(path: Path, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Load JSON with graceful fallback. Never crashes generator."""
    if default is None:
        default = {}
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


# --- Timestamp + freshness (shared constant with tui/data/loader.py is_data_stale ~20h) ---
FRESHNESS_THRESHOLD_HOURS = 20.0


def parse_timestamp(ts: Optional[str]) -> Optional[datetime]:
    if not ts or not isinstance(ts, str):
        return None
    s = ts.strip()
    if not s:
        return None
    # Normalize common variants
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            # Assume local tz for naive stamps (common in some writers)
            dt = dt.astimezone()
        return dt
    except Exception:
        try:
            # Fallback: very loose parse
            return datetime.fromisoformat(s.replace(" ", "T"))
        except Exception:
            return None


def format_timestamp(dt: Optional[datetime], short: bool = True) -> str:
    if not dt:
        return "—"
    # Prefer compact "07:15 ICT" style; include date only in expanded views
    try:
        # Use tzname if available
        tzname = dt.tzname() or "local"
        if short:
            return dt.strftime("%H:%M") + f" {tzname}"
        return dt.strftime("%Y-%m-%d %H:%M %Z")
    except Exception:
        return dt.isoformat()[:16]


def compute_freshness(ts_str: Optional[str], threshold_h: float = FRESHNESS_THRESHOLD_HOURS) -> Dict[str, Any]:
    """Return dict with status, badge, label, age_h. Aligns with loader 20h stale logic."""
    if not ts_str:
        return {"status": "unavailable", "badge": "—", "label": "no data", "age_h": None, "color": "#9ca3af"}

    dt = parse_timestamp(ts_str)
    if not dt:
        return {"status": "unavailable", "badge": "—", "label": "bad ts", "age_h": None, "color": "#9ca3af"}

    now = datetime.now(dt.tzinfo or timezone.utc)
    age_h = max(0.0, (now - dt).total_seconds() / 3600.0)

    if age_h < threshold_h:
        return {
            "status": "fresh",
            "badge": "✓",
            "label": f"fresh · {age_h:.1f}h",
            "age_h": round(age_h, 1),
            "color": "#16a34a",
        }
    else:
        return {
            "status": "stale",
            "badge": "⚠",
            "label": f"stale · {age_h:.1f}h",
            "age_h": round(age_h, 1),
            "color": "#ca8a04",
        }


# --- Domain action mappings (per PRD table + cos:// custom scheme) ---
ACTION_MAP: Dict[str, Dict[str, str]] = {
    "overview": {"primary": "cos brief", "url": "cos://brief", "label": "Open brief"},
    "finances": {"primary": "cos research NVDA", "url": "cos://research?ticker=NVDA", "label": "Research ticker"},
    "kb": {"primary": "cos vault-scan", "url": "cos://vault-scan", "label": "Run vault scan"},
    "learning": {"primary": "cos research Textual", "url": "cos://research?software=Textual", "label": "Research in pipeline"},
    "tasks": {"primary": "cos task add \"...\"", "url": "cos://task-add", "label": "Add task"},
    "health": {"primary": "echo 'Health domain planning'", "url": "cos://health", "label": "Plan domain"},
    "dashboard": {"primary": "cos dashboard", "url": "cos://dashboard", "label": "Regenerate"},
}


def url_to_command(url: str) -> str:
    """Best-effort reverse map for fallback copy text."""
    for dom, spec in ACTION_MAP.items():
        if spec.get("url") == url:
            return spec["primary"]
    if "dashboard" in url:
        return "cos dashboard"
    if "brief" in url:
        return "cos brief"
    if "vault" in url:
        return "cos vault-scan"
    if "research" in url:
        return "cos research <query>"
    if "task" in url:
        return 'cos task add "..."'
    return "cos dashboard"


# --- Data builder (reuses loader + direct loads for timestamps + ai-news + graceful handling) ---
def build_snapshot_data(cos_root: Path) -> Dict[str, Any]:
    """Load all contracts, normalize timestamps, compute freshness, assemble rich snapshot."""
    ensure_importable(cos_root)

    # Prefer importing the canonical loader (reuse contracts, _load_json behavior, tile_summary surfacing)
    try:
        from tui.data.loader import (
            load_runway,
            load_knowledge_base,
            load_learning,
            load_schedule,
            load_knowledge_work,
        )
        loader_available = True
    except Exception:
        loader_available = False
        # Will fall back to direct loads below

    now = datetime.now().astimezone()
    snapshot: Dict[str, Any] = {
        "generated": now.isoformat(),
        "generated_human": now.strftime("%Y-%m-%d %H:%M %Z"),
        "cos_root": str(cos_root),
        "threshold_hours": FRESHNESS_THRESHOLD_HOURS,
        "domains": {},
    }

    # --- Overview Brief (status.json + ai-news.json) ---
    try:
        status_path = cos_root / "overview-brief" / "data" / "status.json"
        ai_path = cos_root / "overview-brief" / "data" / "ai-news.json"
        status = _load_json(status_path, {})
        ai = _load_json(ai_path, {})
        gen_ts = status.get("generated_at") or ai.get("generated_at")
        fresh = compute_freshness(gen_ts)

        inbox = status.get("inbox", {}) or {}
        workbench = status.get("workbench", {}) or {}
        jq = status.get("journal_questions", 0)
        if isinstance(jq, dict):
            jq = jq.get("count", 0)

        ai_count = ai.get("count", 0)
        ai_items = (ai.get("items") or [])[:3]

        overview = {
            "name": "Overview Brief",
            "icon": "📋",
            "color": "#4F46E5",
            "generated": gen_ts,
            "freshness": fresh,
            "inbox_count": inbox.get("count", 0),
            "workbench_count": (workbench.get("count", 0) if isinstance(workbench, dict) else (len(workbench) if isinstance(workbench, list) else 0)),
            "journal_questions": jq,
            "ai_news_count": ai_count,
            "ai_news_items": ai_items,
            "ai_news_source": ai.get("source", "Grok"),
            "tile_summary": status.get("tile_summary"),
            "actions": [
                {"label": ACTION_MAP["overview"]["label"], "command": ACTION_MAP["overview"]["primary"], "url": ACTION_MAP["overview"]["url"]},
                {"label": "Regenerate", "command": ACTION_MAP["dashboard"]["primary"], "url": ACTION_MAP["dashboard"]["url"]},
            ],
        }
        snapshot["domains"]["overview"] = overview
    except Exception as e:
        snapshot["domains"]["overview"] = {
            "name": "Overview Brief", "icon": "📋", "color": "#4F46E5",
            "error": str(e), "freshness": {"status": "unavailable", "badge": "—", "label": "load failed"},
            "actions": [{"label": "Open brief", "command": "cos brief", "url": "cos://brief"}],
        }

    # --- Finances ---
    try:
        if loader_available:
            fin = load_runway(cos_root)
        else:
            fin = _load_json(cos_root / "finances" / "data" / "runway.json", {})
        raw = _load_json(cos_root / "finances" / "data" / "runway.json", {})
        gen_ts = raw.get("generated") or raw.get("generated_at")
        fresh = compute_freshness(gen_ts)

        runway = fin.get("runway_months")
        net = fin.get("net_monthly")
        goals = fin.get("goals") or []
        us = (fin.get("us_return") or {})
        us_months = us.get("months_remaining", 13)

        # Numberless graph helpers (progress / sparklines baked)
        runway_visual = min(100, int((runway or 0) / 24 * 100)) if runway else 0  # 24mo = "full"
        for g in goals:
            if g.get("pct_complete") is None and g.get("target") and g.get("current"):
                try:
                    g["pct_complete"] = round(100 * g["current"] / g["target"], 1)
                except Exception:
                    g["pct_complete"] = None

        fin_dom = {
            "name": "Finances",
            "icon": "💰",
            "color": "#1B9E55",
            "generated": gen_ts,
            "freshness": fresh,
            "runway_months": runway,
            "net_monthly": net,
            "liquid_savings": fin.get("liquid_savings"),
            "us_return_months": us_months,
            "goals": goals,
            "runway_visual_pct": runway_visual,
            "tile_summary": fin.get("tile_summary"),
            "actions": [
                {"label": ACTION_MAP["finances"]["label"], "command": ACTION_MAP["finances"]["primary"], "url": ACTION_MAP["finances"]["url"]},
            ],
        }
        snapshot["domains"]["finances"] = fin_dom
    except Exception as e:
        snapshot["domains"]["finances"] = {
            "name": "Finances", "icon": "💰", "color": "#1B9E55",
            "error": str(e), "freshness": {"status": "unavailable", "badge": "—", "label": "load failed"},
            "actions": [{"label": "Research ticker", "command": "cos research NVDA", "url": "cos://research?ticker=NVDA"}],
        }

    # --- Knowledge Base ---
    try:
        if loader_available:
            kb = load_knowledge_base(cos_root)
        else:
            oq = _load_json(cos_root / "knowledge-base" / "data" / "open-questions.json", {})
            st = _load_json(cos_root / "knowledge-base" / "data" / "stale-notes.json", {})
            kb = {
                "stale_count": st.get("count", 0),
                "stale_threshold": st.get("stale_threshold_days", 90),
                "oq_count": oq.get("count", 0),
                "vault_error": bool(st.get("error") or oq.get("error")),
                "vault_note": (st.get("error") or oq.get("error") or "").strip() or None,
                "recent_questions": (oq.get("open") or [])[:3],
            }
        raw_oq = _load_json(cos_root / "knowledge-base" / "data" / "open-questions.json", {})
        gen_ts = raw_oq.get("generated") or raw_oq.get("generated_at")
        fresh = compute_freshness(gen_ts)

        kb_dom = {
            "name": "Knowledge Base",
            "icon": "🗄️",
            "color": "#D97706",
            "generated": gen_ts,
            "freshness": fresh,
            "stale_count": kb.get("stale_count", 0),
            "stale_threshold": kb.get("stale_threshold", 90),
            "oq_count": kb.get("oq_count", 0),
            "recent_questions": kb.get("recent_questions", [])[:3],
            "vault_error": kb.get("vault_error"),
            "vault_note": kb.get("vault_note"),
            "tile_summary": raw_oq.get("tile_summary"),
            "actions": [
                {"label": ACTION_MAP["kb"]["label"], "command": ACTION_MAP["kb"]["primary"], "url": ACTION_MAP["kb"]["url"]},
                {"label": "Browse questions", "command": "cos vault-scan", "url": "cos://vault-scan"},
            ],
        }
        snapshot["domains"]["kb"] = kb_dom
    except Exception as e:
        snapshot["domains"]["kb"] = {
            "name": "Knowledge Base", "icon": "🗄️", "color": "#D97706",
            "error": str(e), "freshness": {"status": "unavailable", "badge": "—", "label": "load failed"},
            "actions": [{"label": "Run vault scan", "command": "cos vault-scan", "url": "cos://vault-scan"}],
        }

    # --- Learning Pipeline ---
    try:
        if loader_available:
            lr = load_learning(cos_root)
        else:
            lr = _load_json(cos_root / "learning-pipeline" / "data" / "intake-queue.json", {})
        raw = _load_json(cos_root / "learning-pipeline" / "data" / "intake-queue.json", {})
        gen_ts = raw.get("generated") or raw.get("generated_at")
        fresh = compute_freshness(gen_ts)

        queue = raw.get("queue") or []
        top_item = queue[0] if queue else None

        learn_dom = {
            "name": "Learning Pipeline",
            "icon": "📚",
            "color": "#2563EB",
            "generated": gen_ts,
            "freshness": fresh,
            "backlog_count": lr.get("backlog_count", raw.get("backlog_count", 0)),
            "queue_length": len(queue),
            "top_item": top_item,
            "recent_items": queue[:3],
            "tile_summary": lr.get("tile_summary") or raw.get("tile_summary"),
            "actions": [
                {"label": ACTION_MAP["learning"]["label"], "command": ACTION_MAP["learning"]["primary"], "url": ACTION_MAP["learning"]["url"]},
            ],
        }
        snapshot["domains"]["learning"] = learn_dom
    except Exception as e:
        snapshot["domains"]["learning"] = {
            "name": "Learning Pipeline", "icon": "📚", "color": "#2563EB",
            "error": str(e), "freshness": {"status": "unavailable", "badge": "—", "label": "load failed"},
            "actions": [{"label": "Research in pipeline", "command": "cos research Textual", "url": "cos://research?software=Textual"}],
        }

    # --- Tasks & Calendar ---
    try:
        if loader_available:
            sch = load_schedule(cos_root)
        else:
            sch = _load_json(cos_root / "tasks-calendar" / "data" / "upcoming.json", {})
        raw = _load_json(cos_root / "tasks-calendar" / "data" / "upcoming.json", {})
        gen_ts = raw.get("generated") or raw.get("generated_at")
        fresh = compute_freshness(gen_ts)

        tasks_dom = {
            "name": "Tasks & Calendar",
            "icon": "📅",
            "color": "#E11D48",
            "generated": gen_ts,
            "freshness": fresh,
            "calendar_unavailable": bool(sch.get("calendar_unavailable") or raw.get("calendar_unavailable")),
            "note": sch.get("note") or raw.get("notes") or raw.get("note"),
            "events_count": len(sch.get("events", []) or raw.get("events", [])),
            "tasks_count": len(sch.get("tasks_due", []) or raw.get("tasks_due", [])),
            "timezone": sch.get("timezone") or raw.get("timezone", "Asia/Ho_Chi_Minh"),
            "tile_summary": sch.get("tile_summary") or raw.get("tile_summary"),
            "actions": [
                {"label": ACTION_MAP["tasks"]["label"], "command": ACTION_MAP["tasks"]["primary"], "url": ACTION_MAP["tasks"]["url"]},
                {"label": "Connect calendar →", "command": "cos tasks", "url": "cos://tasks"},
            ],
        }
        snapshot["domains"]["tasks"] = tasks_dom
    except Exception as e:
        snapshot["domains"]["tasks"] = {
            "name": "Tasks & Calendar", "icon": "📅", "color": "#E11D48",
            "error": str(e), "freshness": {"status": "unavailable", "badge": "—", "label": "load failed"},
            "actions": [{"label": "Add task", "command": 'cos task add "..."', "url": "cos://task-add"}],
        }

    # --- Health (placeholder per PRD; no contract yet) ---
    snapshot["domains"]["health"] = {
        "name": "Health",
        "icon": "🏃",
        "color": "#0D9488",
        "generated": None,
        "freshness": {"status": "unavailable", "badge": "—", "label": "coming soon"},
        "placeholder": "Health domain data contracts and refreshers are planned. Track sleep, movement, energy, and recovery here.",
        "actions": [
            {"label": ACTION_MAP["health"]["label"], "command": ACTION_MAP["health"]["primary"], "url": ACTION_MAP["health"]["url"]},
        ],
    }

    return snapshot


# --- HTML rendering helpers (pure, no deps) ---
def _esc(text: Any) -> str:
    if text is None:
        return ""
    return html_escape_module.escape(str(text))


def render_progress_bar(pct: Optional[float], width: int = 100) -> str:
    if pct is None:
        return '<span class="muted small">not yet populated</span>'
    p = max(0, min(100, float(pct)))
    return (
        f'<div class="progress" title="{p:.0f}%">'
        f'<div class="progress-track"><div class="progress-fill" style="width:{p}%"></div></div>'
        f'<span class="progress-label">{p:.0f}%</span>'
        f'</div>'
    )


def render_card_overview(d: Dict[str, Any]) -> str:
    fresh = d.get("freshness", {})
    ts = format_timestamp(parse_timestamp(d.get("generated")))
    lead = f'<p class="lead">{_esc(d.get("tile_summary"))}</p>' if d.get("tile_summary") else ""
    color = d.get("color", "#4F46E5")

    stats = f"""
      <div class="stat"><span class="k">Inbox</span><span class="v">{d.get('inbox_count', 0)} unprocessed</span></div>
      <div class="stat"><span class="k">Workbench</span><span class="v">{d.get('workbench_count', 0)} in progress</span></div>
      <div class="stat"><span class="k">Journal Qs</span><span class="v">{d.get('journal_questions', 0)} captured</span></div>
      <div class="stat"><span class="k">AI News</span><span class="v">{d.get('ai_news_count', 0)} threads ({_esc(d.get('ai_news_source', 'Grok'))})</span></div>
    """

    actions = ""
    for a in d.get("actions", []):
        actions += f'<button class="btn" data-cmd="{_esc(a["command"])}" data-url="{_esc(a["url"])}" onclick="event.stopImmediatePropagation(); triggerAction(this.dataset.url || this.dataset.cmd)">{_esc(a["label"])}</button>'

    return f"""
<div class="card" id="card-overview" data-domain="overview" onclick="expandCard('overview')" style="--domain-color:{color}">
  <div class="card-strip"></div>
  <div class="card-header">
    <span class="icon">{d.get('icon', '📋')}</span>
    <span class="name">{_esc(d.get('name'))}</span>
    <span class="ts">{_esc(ts)}</span>
    <span class="freshness {fresh.get('status','unavailable')}" style="color:{fresh.get('color','#9ca3af')}">{fresh.get('badge','—')} { _esc(fresh.get('label','')) }</span>
  </div>
  <div class="card-body">
    {lead}
    <div class="stats">{stats}</div>
  </div>
  <div class="card-footer">{actions}</div>
</div>
"""


def render_card_finances(d: Dict[str, Any]) -> str:
    fresh = d.get("freshness", {})
    ts = format_timestamp(parse_timestamp(d.get("generated")))
    color = d.get("color", "#1B9E55")
    lead = f'<p class="lead">{_esc(d.get("tile_summary"))}</p>' if d.get("tile_summary") else ""

    runway = d.get("runway_months")
    net = d.get("net_monthly")
    us = d.get("us_return_months", 13)
    runway_bar = render_progress_bar(d.get("runway_visual_pct"))

    goals_html = ""
    for g in (d.get("goals") or [])[:2]:
        pct = g.get("pct_complete")
        goals_html += (
            f'<div class="goal">'
            f'<div class="goal-head"><span>{_esc(g.get("name"))}</span><span class="small muted">by {_esc(g.get("by","—"))}</span></div>'
            f'{render_progress_bar(pct)}'
            f'</div>'
        )
    if not goals_html:
        goals_html = '<div class="muted small">No active goals populated yet.</div>'

    stats = f"""
      <div class="stat"><span class="k">Runway</span><span class="v big">{runway if runway is not None else '—'} mo</span></div>
      <div class="stat"><span class="k">Net / mo</span><span class="v">{"$" + str(net) if net is not None else "—"}</span></div>
      <div class="stat"><span class="k">US return</span><span class="v">{us} mo</span></div>
      <div class="stat"><span class="k">Visual</span><span class="v">{runway_bar}</span></div>
    """

    actions = ""
    for a in d.get("actions", []):
        actions += f'<button class="btn" data-cmd="{_esc(a["command"])}" data-url="{_esc(a["url"])}" onclick="event.stopImmediatePropagation(); triggerAction(this.dataset.url || this.dataset.cmd)">{_esc(a["label"])}</button>'

    return f"""
<div class="card" id="card-finances" data-domain="finances" onclick="expandCard('finances')" style="--domain-color:{color}">
  <div class="card-strip"></div>
  <div class="card-header">
    <span class="icon">{d.get('icon', '💰')}</span>
    <span class="name">{_esc(d.get('name'))}</span>
    <span class="ts">{_esc(ts)}</span>
    <span class="freshness {fresh.get('status','unavailable')}" style="color:{fresh.get('color','#9ca3af')}">{fresh.get('badge','—')} { _esc(fresh.get('label','')) }</span>
  </div>
  <div class="card-body">
    {lead}
    <div class="stats">{stats}</div>
    <div class="goals"><div class="small muted" style="margin:8px 0 4px">Goals</div>{goals_html}</div>
  </div>
  <div class="card-footer">{actions}</div>
</div>
"""


def render_card_kb(d: Dict[str, Any]) -> str:
    fresh = d.get("freshness", {})
    ts = format_timestamp(parse_timestamp(d.get("generated")))
    color = d.get("color", "#D97706")
    lead = f'<p class="lead">{_esc(d.get("tile_summary"))}</p>' if d.get("tile_summary") else ""

    note = ""
    if d.get("vault_error"):
        note = f'<div class="note">⚠ {_esc(d.get("vault_note") or "Vault data from last-good scan")}</div>'

    recent = ""
    for q in (d.get("recent_questions") or [])[:1]:
        recent += f'<div class="q"><div>{_esc(q.get("question"))}</div><div class="qpath small muted">{_esc(q.get("path"))}</div></div>'

    stats = f"""
      <div class="stat"><span class="k">Stale notes</span><span class="v">{d.get('stale_count',0)} <span class="tag">&gt;{d.get('stale_threshold',90)}d</span></span></div>
      <div class="stat"><span class="k">Open questions</span><span class="v">{d.get('oq_count',0):,}</span></div>
    """

    actions = ""
    for a in d.get("actions", []):
        actions += f'<button class="btn" data-cmd="{_esc(a["command"])}" data-url="{_esc(a["url"])}" onclick="event.stopImmediatePropagation(); triggerAction(this.dataset.url || this.dataset.cmd)">{_esc(a["label"])}</button>'

    return f"""
<div class="card" id="card-kb" data-domain="kb" onclick="expandCard('kb')" style="--domain-color:{color}">
  <div class="card-strip"></div>
  <div class="card-header">
    <span class="icon">{d.get('icon', '🗄️')}</span>
    <span class="name">{_esc(d.get('name'))}</span>
    <span class="ts">{_esc(ts)}</span>
    <span class="freshness {fresh.get('status','unavailable')}" style="color:{fresh.get('color','#9ca3af')}">{fresh.get('badge','—')} { _esc(fresh.get('label','')) }</span>
  </div>
  <div class="card-body">
    {note}
    {lead}
    <div class="stats">{stats}</div>
    {f'<div class="recent-qs"><div class="small muted" style="margin-top:8px">Recent open question</div>{recent}</div>' if recent else ''}
  </div>
  <div class="card-footer">{actions}</div>
</div>
"""


def render_card_learning(d: Dict[str, Any]) -> str:
    fresh = d.get("freshness", {})
    ts = format_timestamp(parse_timestamp(d.get("generated")))
    color = d.get("color", "#2563EB")
    lead = f'<p class="lead">{_esc(d.get("tile_summary"))}</p>' if d.get("tile_summary") else ""

    top = d.get("top_item") or {}
    top_html = f'<div class="q"><div>{_esc(top.get("title"))}</div><div class="qpath small muted">{_esc(top.get("topic"))} · { _esc(top.get("status","")) } · added {_esc(top.get("added",""))}</div></div>' if top else '<div class="muted small">Queue empty</div>'

    stats = f"""
      <div class="stat"><span class="k">Backlog</span><span class="v">{d.get('backlog_count',0)} items</span></div>
      <div class="stat"><span class="k">Queue</span><span class="v">{d.get('queue_length',0)}</span></div>
    """

    actions = ""
    for a in d.get("actions", []):
        actions += f'<button class="btn" data-cmd="{_esc(a["command"])}" data-url="{_esc(a["url"])}" onclick="event.stopImmediatePropagation(); triggerAction(this.dataset.url || this.dataset.cmd)">{_esc(a["label"])}</button>'

    return f"""
<div class="card" id="card-learning" data-domain="learning" onclick="expandCard('learning')" style="--domain-color:{color}">
  <div class="card-strip"></div>
  <div class="card-header">
    <span class="icon">{d.get('icon', '📚')}</span>
    <span class="name">{_esc(d.get('name'))}</span>
    <span class="ts">{_esc(ts)}</span>
    <span class="freshness {fresh.get('status','unavailable')}" style="color:{fresh.get('color','#9ca3af')}">{fresh.get('badge','—')} { _esc(fresh.get('label','')) }</span>
  </div>
  <div class="card-body">
    {lead}
    <div class="stats">{stats}</div>
    <div class="recent-qs"><div class="small muted" style="margin:8px 0 4px">Top item</div>{top_html}</div>
  </div>
  <div class="card-footer">{actions}</div>
</div>
"""


def render_card_tasks(d: Dict[str, Any]) -> str:
    fresh = d.get("freshness", {})
    ts = format_timestamp(parse_timestamp(d.get("generated")))
    color = d.get("color", "#E11D48")
    lead = f'<p class="lead">{_esc(d.get("tile_summary"))}</p>' if d.get("tile_summary") else ""

    cal_note = ""
    if d.get("calendar_unavailable"):
        cal_note = '<div class="note">⚠ Calendar unavailable — using TASKS.md only</div>'

    stats = f"""
      <div class="stat"><span class="k">Calendar</span><span class="v">{"⚠ not connected" if d.get("calendar_unavailable") else "connected"}</span></div>
      <div class="stat"><span class="k">Tasks</span><span class="v">{d.get('tasks_count',0)} logged</span></div>
      <div class="stat"><span class="k">Upcoming</span><span class="v">{d.get('events_count',0)} events</span></div>
    """

    actions = ""
    for a in d.get("actions", []):
        actions += f'<button class="btn" data-cmd="{_esc(a["command"])}" data-url="{_esc(a["url"])}" onclick="event.stopImmediatePropagation(); triggerAction(this.dataset.url || this.dataset.cmd)">{_esc(a["label"])}</button>'

    return f"""
<div class="card" id="card-tasks" data-domain="tasks" onclick="expandCard('tasks')" style="--domain-color:{color}">
  <div class="card-strip"></div>
  <div class="card-header">
    <span class="icon">{d.get('icon', '📅')}</span>
    <span class="name">{_esc(d.get('name'))}</span>
    <span class="ts">{_esc(ts)}</span>
    <span class="freshness {fresh.get('status','unavailable')}" style="color:{fresh.get('color','#9ca3af')}">{fresh.get('badge','—')} { _esc(fresh.get('label','')) }</span>
  </div>
  <div class="card-body">
    {cal_note}
    {lead}
    <div class="stats">{stats}</div>
    {f'<div class="small muted" style="margin-top:6px">{_esc(d.get("note",""))}</div>' if d.get("note") else ''}
  </div>
  <div class="card-footer">{actions}</div>
</div>
"""


def render_card_health(d: Dict[str, Any]) -> str:
    fresh = d.get("freshness", {})
    color = d.get("color", "#0D9488")
    ts = "—"

    actions = ""
    for a in d.get("actions", []):
        actions += f'<button class="btn" data-cmd="{_esc(a["command"])}" data-url="{_esc(a["url"])}" onclick="event.stopImmediatePropagation(); triggerAction(this.dataset.url || this.dataset.cmd)">{_esc(a["label"])}</button>'

    return f"""
<div class="card" id="card-health" data-domain="health" onclick="expandCard('health')" style="--domain-color:{color}">
  <div class="card-strip"></div>
  <div class="card-header">
    <span class="icon">{d.get('icon', '🏃')}</span>
    <span class="name">{_esc(d.get('name'))}</span>
    <span class="ts">{ts}</span>
    <span class="freshness {fresh.get('status','unavailable')}" style="color:{fresh.get('color','#9ca3af')}">{fresh.get('badge','—')} { _esc(fresh.get('label','')) }</span>
  </div>
  <div class="card-body">
    <div class="placeholder">{_esc(d.get('placeholder', 'Coming soon.'))}</div>
  </div>
  <div class="card-footer">{actions}</div>
</div>
"""


def render_full_html(data: Dict[str, Any]) -> str:
    """Assemble the complete self-contained Basecamp-inspired HTML."""
    overview = data["domains"].get("overview", {})
    finances = data["domains"].get("finances", {})
    kb = data["domains"].get("kb", {})
    learning = data["domains"].get("learning", {})
    tasks = data["domains"].get("tasks", {})
    health = data["domains"].get("health", {})

    cards = (
        render_card_overview(overview)
        + render_card_finances(finances)
        + render_card_kb(kb)
        + render_card_learning(learning)
        + render_card_tasks(tasks)
        + render_card_health(health)
    )

    # Full embedded data for JS expand + future use
    data_json = json.dumps(data, indent=2, default=str, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>cos — Snapshot Dashboard</title>
<style>
:root {{
  --bg: #FFFDF7;
  --card: #FFFFFF;
  --border: #E8E5DF;
  --text: #1f2937;
  --muted: #6b7280;
  --accent: #1B9E55;
  --shadow: 0 1px 4px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.03);
  --radius: 12px;
  --gap: 24px;
  font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}}
.dark {{
  --bg: #0f1117;
  --card: #1a1d27;
  --border: #2a2d3a;
  --text: #e2e8f0;
  --muted: #64748b;
  --accent: #6366f1;
  --shadow: 0 1px 4px rgba(0,0,0,0.3);
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0; padding: 0; background: var(--bg); color: var(--text);
  font-size: 14.5px; line-height: 1.6;
}}
.container {{ max-width: 1180px; margin: 0 auto; padding: 32px 24px; }}
header {{
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid var(--border);
}}
header .brand {{ font-size: 22px; font-weight: 700; letter-spacing: -.02em; color: var(--accent); }}
header .meta {{ font-size: 12px; color: var(--muted); }}
.layout {{ display: flex; gap: 28px; }}
.sidebar {{
  width: 210px; flex-shrink: 0; padding-top: 8px;
}}
.sidebar h3 {{ font-size: 11px; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); margin: 0 0 8px 4px; }}
.sidebar ul {{ list-style: none; padding: 0; margin: 0; }}
.sidebar li {{ margin: 2px 0; }}
.sidebar a {{ display: block; padding: 8px 12px; border-radius: 8px; color: var(--text); text-decoration: none; font-size: 13.5px; }}
.sidebar a:hover {{ background: rgba(0,0,0,0.04); }}
.dark .sidebar a:hover {{ background: rgba(255,255,255,0.06); }}
.main {{ flex: 1; min-width: 0; }}
.cards-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
  gap: var(--gap);
}}
@media (max-width: 860px) {{
  .layout {{ flex-direction: column; }}
  .sidebar {{ width: 100%; }}
  .cards-grid {{ grid-template-columns: 1fr; }}
}}
.card {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  overflow: hidden;
  transition: transform .15s ease, box-shadow .15s ease;
  cursor: pointer;
  display: flex; flex-direction: column;
}}
.card:hover {{ transform: translateY(-1px); box-shadow: 0 6px 16px rgba(0,0,0,0.08); }}
.card-strip {{ height: 4px; background: var(--domain-color, #4F46E5); }}
.card-header {{
  padding: 14px 18px 10px; display: flex; align-items: center; gap: 8px;
  border-bottom: 1px solid var(--border); font-size: 13px;
}}
.card-header .icon {{ font-size: 17px; line-height: 1; }}
.card-header .name {{ font-weight: 600; }}
.card-header .ts {{ margin-left: auto; color: var(--muted); font-size: 11px; white-space: nowrap; }}
.card-header .freshness {{ font-size: 11px; padding: 1px 7px; border-radius: 999px; background: rgba(0,0,0,0.04); white-space: nowrap; }}
.dark .card-header .freshness {{ background: rgba(255,255,255,0.06); }}
.card-body {{ padding: 16px 18px; font-size: 13.5px; flex: 1; }}
.card-body .lead {{ margin: 0 0 12px; color: #374151; line-height: 1.55; }}
.dark .card-body .lead {{ color: #cbd5e1; }}
.stats {{ display: flex; flex-direction: column; gap: 2px; }}
.stat {{ display: flex; justify-content: space-between; align-items: baseline; padding: 5px 0; border-bottom: 1px dotted var(--border); font-size: 13.5px; }}
.stat:last-child {{ border-bottom: none; }}
.stat .k {{ color: var(--muted); }}
.stat .v {{ font-weight: 600; }}
.stat .big {{ font-size: 18px; line-height: 1; color: #166534; }}
.dark .stat .big {{ color: #4ade80; }}
.progress {{ display: flex; align-items: center; gap: 8px; margin: 4px 0; }}
.progress-track {{ flex: 1; height: 5px; background: var(--border); border-radius: 999px; overflow: hidden; }}
.progress-fill {{ height: 100%; background: var(--domain-color, #1B9E55); transition: width .3s; }}
.progress-label {{ font-size: 11px; color: var(--muted); min-width: 32px; text-align: right; }}
.goals {{ margin-top: 8px; }}
.goal {{ margin: 6px 0; }}
.goal-head {{ display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 3px; }}
.note {{ font-size: 11.5px; color: #854d0e; background: #fefce8; padding: 6px 8px; border-radius: 6px; margin-bottom: 8px; }}
.dark .note {{ background: #422006; color: #fde047; }}
.recent-qs .q {{ font-size: 12.5px; padding: 4px 0; border-top: 1px dotted var(--border); }}
.recent-qs .qpath {{ font-size: 10.5px; margin-top: 1px; }}
.card-footer {{
  padding: 10px 12px; background: #faf8f2; border-top: 1px solid var(--border);
  display: flex; gap: 6px; flex-wrap: wrap;
}}
.dark .card-footer {{ background: #11151f; }}
.btn {{
  font-size: 12px; padding: 6px 13px; border-radius: 999px; border: 1px solid var(--border);
  background: #fff; color: var(--text); cursor: pointer; transition: all .1s;
  white-space: nowrap;
}}
.dark .btn {{ background: #1f2533; border-color: #374151; color: #e2e8f0; }}
.btn:hover {{ background: #f5f1eb; transform: translateY(-0.5px); }}
.dark .btn:hover {{ background: #2a3242; }}
.placeholder {{ color: var(--muted); font-style: italic; padding: 12px 0; }}
.muted, .small {{ color: var(--muted); }}
.small {{ font-size: 11.5px; }}
.tag {{ font-size: 10px; padding: 0 5px; border-radius: 3px; background: var(--border); color: var(--muted); margin-left: 4px; }}

/* Expanded panel */
#expanded {{ display: none; }}
#expanded.visible {{ display: block; margin-top: 12px; }}
.expanded-content {{
  background: var(--card); border: 1px solid var(--border); border-radius: var(--radius);
  box-shadow: var(--shadow); padding: 20px 24px;
}}
.expanded-content h2 {{ margin: 0 0 12px; font-size: 18px; }}
.expanded-content .close {{ float: right; cursor: pointer; font-size: 13px; padding: 4px 10px; border: 1px solid var(--border); border-radius: 999px; }}
#grid.hidden {{ display: none; }}

/* Sidebar + header buttons */
.header-actions {{ display: flex; gap: 8px; align-items: center; }}
.header-actions button {{ font-size: 12px; padding: 6px 12px; border-radius: 999px; border: 1px solid var(--border); background: transparent; cursor: pointer; }}
.header-actions button:hover {{ background: rgba(0,0,0,0.03); }}
.dark .header-actions button:hover {{ background: rgba(255,255,255,0.06); }}

/* Toast */
#toast {{
  position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
  background: #111827; color: #fff; padding: 10px 16px; border-radius: 8px;
  font-size: 13px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); display: none; z-index: 9999; max-width: 420px; text-align: center;
}}
.dark #toast {{ background: #1f2937; }}

/* Help modal */
#help-modal {{ display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.4); z-index: 9998; align-items: center; justify-content: center; }}
#help-modal.visible {{ display: flex; }}
.help-content {{
  background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 24px; width: 92%; max-width: 520px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.2);
}}
.help-content table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
.help-content td {{ padding: 6px 0; border-bottom: 1px dotted var(--border); }}
.help-content td:first-child {{ font-family: ui-monospace, monospace; width: 70px; color: var(--accent); }}
</style>
</head>
<body>
<div class="container">
  <header>
    <div>
      <span class="brand">cos</span>
      <span style="margin-left:8px; color:var(--muted); font-size:13px;">Snapshot Dashboard</span>
    </div>
    <div class="meta">
      Snapshot • {_esc(data.get('generated_human'))} &nbsp;·&nbsp; threshold {data.get('threshold_hours')}h
    </div>
    <div class="header-actions">
      <button onclick="showHelp()" title="Keyboard shortcuts (?)" >?</button>
      <button onclick="toggleTheme()" id="theme-btn" title="Toggle light/dark">☀︎</button>
      <button onclick="triggerAction('cos://dashboard')" title="Regenerate this dashboard">⟳ Regenerate</button>
    </div>
  </header>

  <div class="layout">
    <nav class="sidebar">
      <h3>Domains</h3>
      <ul>
        <li><a href="#" onclick="document.getElementById('card-overview').scrollIntoView({{behavior:'smooth'}}); return false;">📋 Overview Brief</a></li>
        <li><a href="#" onclick="document.getElementById('card-finances').scrollIntoView({{behavior:'smooth'}}); return false;">💰 Finances</a></li>
        <li><a href="#" onclick="document.getElementById('card-kb').scrollIntoView({{behavior:'smooth'}}); return false;">🗄️ Knowledge Base</a></li>
        <li><a href="#" onclick="document.getElementById('card-learning').scrollIntoView({{behavior:'smooth'}}); return false;">📚 Learning Pipeline</a></li>
        <li><a href="#" onclick="document.getElementById('card-tasks').scrollIntoView({{behavior:'smooth'}}); return false;">📅 Tasks &amp; Calendar</a></li>
        <li><a href="#" onclick="document.getElementById('card-health').scrollIntoView({{behavior:'smooth'}}); return false;">🏃 Health</a></li>
      </ul>
      <div style="margin-top:28px; font-size:11px; color:var(--muted); padding-left:4px; line-height:1.4;">
        Calm Basecamp-inspired snapshot.<br>
        Click any card to expand.<br>
        Actions use <code>cos://</code> (macOS helper) + clipboard fallback.
      </div>
    </nav>

    <div class="main">
      <div id="grid" class="cards-grid">
        {cards}
      </div>

      <div id="expanded" class="expanded-panel">
        <div id="expanded-content" class="expanded-content"></div>
      </div>
    </div>
  </div>

  <div style="margin-top:40px; font-size:11px; color:var(--muted); text-align:center;">
    Self-contained snapshot • Open from disk • Regenerate with <code>cos dashboard</code> or this generator<br>
    Data root: {_esc(data.get('cos_root'))} • Generated { _esc(data.get('generated_human')) }
  </div>
</div>

<!-- Toast -->
<div id="toast"></div>

<!-- Help Modal -->
<div id="help-modal" onclick="if (event.target.id==='help-modal') hideHelp()">
  <div class="help-content" onclick="event.stopImmediatePropagation()">
    <h3 style="margin-top:0">Keyboard Shortcuts &amp; Tips</h3>
    <table>
      <tr><td><strong>?</strong></td><td>Toggle this help</td></tr>
      <tr><td><strong>Esc</strong></td><td>Close expanded card or help</td></tr>
      <tr><td><strong>Click card</strong></td><td>Expand inline with richer detail</td></tr>
      <tr><td><strong>Action buttons</strong></td><td>Trigger cos:// (macOS) or copy command</td></tr>
      <tr><td><strong>Theme</strong></td><td>Header sun/moon — persists in localStorage</td></tr>
    </table>
    <p style="margin:16px 0 0; font-size:12px; color:var(--muted);">
      This is a calm reading surface (snapshot, no live fetch, no server). 
      Full power-user workflows live in the Textual TUI (<code>cos</code>).
    </p>
    <button onclick="hideHelp()" style="margin-top:16px; float:right;">Close</button>
  </div>
</div>

<script>
const DASH_DATA = {data_json};

let currentExpanded = null;

function showToast(html, timeoutMs = 5200) {{
  const t = document.getElementById('toast');
  t.innerHTML = html;
  t.style.display = 'block';
  clearTimeout(t._hideTimer);
  t._hideTimer = setTimeout(() => {{ t.style.display = 'none'; }}, timeoutMs);
}}

function fallbackCopy(text) {{
  const ta = document.createElement('textarea');
  ta.value = text;
  document.body.appendChild(ta);
  ta.select();
  try {{ document.execCommand('copy'); showToast('Copied: ' + text); }} catch(e) {{ showToast('Copy failed — ' + text); }}
  ta.remove();
}}

function triggerAction(input) {{
  if (!input) return;
  const isUrl = input.startsWith('cos://');
  let command = input;
  if (isUrl) {{
    command = DASH_DATA._commandMap && DASH_DATA._commandMap[input] ? DASH_DATA._commandMap[input] : (function(u){{
      if (u.includes('brief')) return 'cos brief';
      if (u.includes('vault')) return 'cos vault-scan';
      if (u.includes('research')) return 'cos research <query>';
      if (u.includes('task')) return 'cos task add "..."';
      if (u.includes('dashboard')) return 'cos dashboard';
      return 'cos dashboard';
    }})(input);
  }}
  // Attempt cos:// custom scheme (macOS helper will catch and run in Ghostty)
  if (isUrl) {{
    try {{
      const a = document.createElement('a');
      a.href = input;
      a.style.display = 'none';
      document.body.appendChild(a);
      a.click();
      setTimeout(() => a.remove(), 80);
    }} catch(e) {{ /* ignore */ }}
  }}
  // Always offer clean clipboard fallback (works everywhere)
  if (navigator.clipboard && navigator.clipboard.writeText) {{
    navigator.clipboard.writeText(command).then(() => {{
      showToast('Copied: <strong>' + command + '</strong><br><small>Paste in terminal. On macOS the cos:// helper can auto-execute.</small>');
    }}).catch(() => fallbackCopy(command));
  }} else {{
    fallbackCopy(command);
  }}
}}

// Build rich expanded content from data (content-first, calm)
function buildExpandedHTML(domain, d) {{
  let html = `<h2>${{d.icon || ''}} ${{d.name || domain}}</h2>
    <button class="close" onclick="collapseExpanded()">Back to grid ✕</button>`;
  const fresh = d.freshness || {{}};
  html += `<div style="margin-bottom:12px; font-size:12px; color:var(--muted)">Snapshot: ${{d.generated ? new Date(d.generated).toLocaleString() : '—'}} <span style="color:${{fresh.color || '#9ca3af'}}">(${{(fresh.badge || '—')}} ${{fresh.label || ''}})</span></div>`;

  if (d.tile_summary) {{
    html += `<p style="font-size:14px; line-height:1.6; margin:12px 0 16px; padding:12px; background:rgba(0,0,0,0.02); border-radius:8px;">${{_esc(d.tile_summary)}}</p>`;
  }}

  if (domain === 'overview') {{
    html += `<div><strong>Inbox:</strong> ${{d.inbox_count || 0}} unprocessed<br>
             <strong>Workbench:</strong> ${{d.workbench_count || 0}}<br>
             <strong>Journal questions:</strong> ${{d.journal_questions || 0}}<br>
             <strong>AI News:</strong> ${{d.ai_news_count || 0}} threads</div>`;
    if (d.ai_news_items && d.ai_news_items.length) {{
      html += `<h4 style="margin-top:16px">Recent AI News</h4><ul style="font-size:13px">`;
      d.ai_news_items.forEach(it => {{
        html += `<li><a href="${{it.url || '#'}}" target="_blank">${{it.title}}</a> — <span class="muted">${{it.relevance || ''}}</span></li>`;
      }});
      html += `</ul>`;
    }}
  }} else if (domain === 'finances') {{
    html += `<div><strong>Runway:</strong> ${{d.runway_months || '—'}} months &nbsp; | &nbsp; <strong>Net:</strong> ${{d.net_monthly || '—'}}</div>`;
    if (d.goals && d.goals.length) {{
      html += `<h4 style="margin:14px 0 6px">Goals</h4>`;
      d.goals.forEach(g => {{
        const p = (g.pct_complete != null) ? g.pct_complete : (g.target && g.current ? (100*g.current/g.target) : null);
        html += `<div style="margin:6px 0">${{g.name}} — target ${{g.target}} current ${{g.current}} ${{p!=null ? '('+p.toFixed(0)+'%' : '')}} by ${{g.by || '—'}}</div>`;
      }});
    }}
  }} else if (domain === 'kb') {{
    html += `<div><strong>Open questions:</strong> ${{d.oq_count || 0}} &nbsp; <strong>Stale:</strong> ${{d.stale_count || 0}} (&gt;${{d.stale_threshold||90}}d)</div>`;
    if (d.recent_questions && d.recent_questions.length) {{
      html += `<h4 style="margin-top:12px">Recent open questions</h4><ul style="font-size:12.5px">`;
      d.recent_questions.forEach(q => {{ html += `<li>${{q.question}} <span class="muted">(${{_esc(q.path)}})</span></li>`; }});
      html += `</ul>`;
    }}
    if (d.vault_note) html += `<div class="note" style="margin-top:12px">${{d.vault_note}}</div>`;
  }} else if (domain === 'learning') {{
    html += `<div><strong>Backlog:</strong> ${{d.backlog_count || 0}} items (${{d.queue_length || 0}} in queue)</div>`;
    if (d.recent_items && d.recent_items.length) {{
      html += `<h4 style="margin-top:12px">Queue</h4><ul>`;
      d.recent_items.forEach(it => {{ html += `<li>${{it.title}} <span class="tag">${{it.topic}}</span> <span class="muted">(${{it.status}})</span></li>`; }});
      html += `</ul>`;
    }}
  }} else if (domain === 'tasks') {{
    html += `<div>Calendar: ${{d.calendar_unavailable ? 'unavailable' : 'available'}}<br>Events: ${{d.events_count||0}} &nbsp; Tasks due: ${{d.tasks_count||0}}</div>`;
    if (d.note) html += `<div class="note">${{d.note}}</div>`;
  }} else if (domain === 'health') {{
    html += `<p>${{d.placeholder || 'Coming soon.'}}</p>`;
  }}

  html += `<div style="margin-top:20px; padding-top:12px; border-top:1px solid var(--border); font-size:12px; color:var(--muted)">Actions in this view use the same cos:// + clipboard behavior as the compact cards.</div>`;
  return html;
}}

function expandCard(domain) {{
  const grid = document.getElementById('grid');
  const panel = document.getElementById('expanded');
  const content = document.getElementById('expanded-content');

  if (currentExpanded === domain) {{
    collapseExpanded();
    return;
  }}

  const d = DASH_DATA.domains[domain];
  if (!d) return;

  content.innerHTML = buildExpandedHTML(domain, d);
  grid.classList.add('hidden');
  panel.classList.add('visible');
  currentExpanded = domain;
  window.scrollTo({{top: panel.offsetTop - 40, behavior: 'smooth'}});
}}

function collapseExpanded() {{
  const grid = document.getElementById('grid');
  const panel = document.getElementById('expanded');
  grid.classList.remove('hidden');
  panel.classList.remove('visible');
  currentExpanded = null;
}}

function toggleTheme() {{
  const root = document.documentElement;
  const isDark = root.classList.toggle('dark');
  localStorage.setItem('cos-theme', isDark ? 'dark' : 'light');
  document.getElementById('theme-btn').textContent = isDark ? '☾' : '☀︎';
}}

function showHelp() {{
  document.getElementById('help-modal').classList.add('visible');
}}
function hideHelp() {{
  document.getElementById('help-modal').classList.remove('visible');
}}

// Keyboard
document.addEventListener('keydown', function(e) {{
  if (e.key === '?' && !document.getElementById('help-modal').classList.contains('visible')) {{
    e.preventDefault();
    showHelp();
  }}
  if (e.key === 'Escape') {{
    const modal = document.getElementById('help-modal');
    if (modal.classList.contains('visible')) {{
      hideHelp();
    }} else if (currentExpanded) {{
      collapseExpanded();
    }}
  }}
}});

// Init
(function init() {{
  // Theme restore
  const saved = localStorage.getItem('cos-theme');
  const btn = document.getElementById('theme-btn');
  if (saved === 'dark') {{
    document.documentElement.classList.add('dark');
    if (btn) btn.textContent = '☾';
  }} else {{
    if (btn) btn.textContent = '☀︎';
  }}

  // Attach a global command map for triggerAction fallback
  DASH_DATA._commandMap = {{}};
  Object.keys(DASH_DATA.domains || {{}}).forEach(dom => {{
    (DASH_DATA.domains[dom].actions || []).forEach(a => {{
      if (a.url) DASH_DATA._commandMap[a.url] = a.command;
    }});
  }});

  // Gentle welcome toast on first load (non-intrusive)
  // setTimeout(() => {{ showToast('Welcome. Click any card to expand. Use ? for help.', 2800); }}, 1200);
  console.log('%c[cos-dashboard] Basecamp snapshot ready — data baked at generation time.', 'color:#6b7280');
}})();

// Expose a tiny API for debugging / future CLI integration
window.cosDashboard = {{ expand: expandCard, collapse: collapseExpanded, toggleTheme, triggerAction, data: DASH_DATA }};
</script>
</body>
</html>
"""
    return html


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="Generate the cos Basecamp-style snapshot dashboard (self-contained HTML)."
    )
    p.add_argument(
        "--cos-root",
        type=Path,
        default=None,
        help="Path to cos data root (defaults to auto-detect or ~/cos).",
    )
    p.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output HTML path (default: <cos-root>/dashboard.html).",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Overwrite even if output exists (default: yes for generator).",
    )
    p.add_argument(
        "--print-data",
        action="store_true",
        help="Print the computed snapshot JSON to stdout (for inspection) and exit.",
    )
    args = p.parse_args(argv)

    cos_root = (args.cos_root or detect_cos_root()).resolve()
    if not cos_root.exists():
        print(f"Warning: COS_ROOT {cos_root} does not exist; proceeding (will show unavailable cards).", file=sys.stderr)

    print(f"[cos-dashboard] COS_ROOT = {cos_root}", file=sys.stderr)

    data = build_snapshot_data(cos_root)

    if args.print_data:
        print(json.dumps(data, indent=2, default=str, ensure_ascii=False))
        return 0

    out_path = (args.output or (cos_root / "dashboard.html")).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    html = render_full_html(data)
    out_path.write_text(html, encoding="utf-8")

    print(f"[cos-dashboard] Wrote {out_path} ({len(html):,} bytes)", file=sys.stderr)
    print(f"[cos-dashboard] Open it directly in a browser. Regenerate with `cos dashboard` (future) or this script.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
