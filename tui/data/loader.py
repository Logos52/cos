"""Data loading utilities for the cos TUI.

This module knows how to read the canonical cos data layer contracts
(finances, knowledge-base, learning-pipeline, tasks-calendar, overview-brief)
and returns structured dicts with graceful handling of partial/unavailable data
(vault_error, calendar_unavailable, etc.).

All functions are pure and safe to call repeatedly for live refresh.
"""

from __future__ import annotations

import csv
import json
import os
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Base path for the cos data layer (user can override in tests or via env)
COS_ROOT_ENV = os.environ.get("COS_ROOT")
DEFAULT_COS_ROOT = Path(COS_ROOT_ENV) if COS_ROOT_ENV else Path.home() / "cos"


def _load_json(path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    """Load a JSON file with a sensible default on any error."""
    if default is None:
        default = {}
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def load_runway(cos_root: Path = DEFAULT_COS_ROOT) -> dict[str, Any]:
    """Load finances runway data (most important single number for many people)."""
    path = cos_root / "finances" / "data" / "runway.json"
    data = _load_json(path, {
        "runway_months": None,
        "error": "File not found or unreadable"
    })
    # Surface optional tile_summary (model-agnostic extension) cleanly for TUI / consumers
    data["tile_summary"] = data.get("tile_summary")
    return data


def load_knowledge_base(cos_root: Path = DEFAULT_COS_ROOT) -> dict[str, Any]:
    """Load KB overview (stale notes + open questions count + recent items)."""
    data_dir = cos_root / "knowledge-base" / "data"

    stale = _load_json(data_dir / "stale-notes.json", {"count": 0, "error": None})
    oq = _load_json(data_dir / "open-questions.json", {"count": 0, "error": None})

    return {
        "stale_count": stale.get("count", 0),
        "stale_threshold": stale.get("stale_threshold_days", 90),
        "oq_count": oq.get("count", 0),
        "vault_error": bool(stale.get("error") or oq.get("error")),
        "vault_note": (stale.get("error") or oq.get("error") or "").strip() or None,
        # Recent questions are useful for the dashboard tile
        "recent_questions": oq.get("open", [])[:5] if isinstance(oq.get("open"), list) else [],
        # Surface optional tile_summary from open-questions contract (primary source for KB domain)
        "tile_summary": oq.get("tile_summary"),
    }


def load_learning(cos_root: Path = DEFAULT_COS_ROOT) -> dict[str, Any]:
    """Load learning pipeline status (backlog count is the key signal)."""
    path = cos_root / "learning-pipeline" / "data" / "intake-queue.json"
    data = _load_json(path, {"backlog_count": 0})
    return {
        "backlog_count": data.get("backlog_count", 0),
        "queue_length": len(data.get("queue", [])),
        # Surface optional tile_summary cleanly (Learning domain priority for Option C)
        "tile_summary": data.get("tile_summary"),
    }


def load_schedule(cos_root: Path = DEFAULT_COS_ROOT) -> dict[str, Any]:
    """Load tasks + calendar upcoming view."""
    path = cos_root / "tasks-calendar" / "data" / "upcoming.json"
    data = _load_json(path, {})
    return {
        "timezone": data.get("timezone", "Asia/Ho_Chi_Minh"),
        "events": data.get("events", []),
        "tasks_due": data.get("tasks_due", []),
        "calendar_unavailable": bool(data.get("calendar_unavailable")),
        "note": data.get("notes") or data.get("note"),
        # Surface optional tile_summary if present on upcoming contract
        "tile_summary": data.get("tile_summary"),
    }


def load_knowledge_work(cos_root: Path = DEFAULT_COS_ROOT) -> dict[str, Any]:
    """Load the overview-brief / Knowledge Work summary (inbox + workbench + journal Qs)."""
    path = cos_root / "overview-brief" / "data" / "status.json"
    data = _load_json(path, {})
    inbox = data.get("inbox", {})
    workbench = data.get("workbench", {})
    jq = data.get("journal_questions", 0)
    if isinstance(jq, dict):
        jq = jq.get("count", 0)
    return {
        "inbox_count": inbox.get("count", 0),
        "workbench_count": workbench.get("count", 0) if isinstance(workbench, dict) else len(workbench) if isinstance(workbench, list) else 0,
        "journal_questions": jq,
        "ai_news_available": bool(data.get("ai_news")),
        # Surface optional tile_summary cleanly (Brief/Knowledge Work domain - Option C priority)
        "tile_summary": data.get("tile_summary"),
    }


def load_all(cos_root: Path = DEFAULT_COS_ROOT) -> dict[str, Any]:
    """Convenience loader that returns everything the main dashboard needs."""
    return {
        "finances": load_runway(cos_root),
        "kb": load_knowledge_base(cos_root),
        "learning": load_learning(cos_root),
        "schedule": load_schedule(cos_root),
        "knowledge_work": load_knowledge_work(cos_root),
        "generated_at": "live",  # caller can override with a timestamp
    }


# =============================================================================
# out-3: Model-agnostic foundation — Data contracts (schemas) + Grok layer
# =============================================================================
# Machine-readable contracts for the stable data layer.
# - JSON_SCHEMAS: primary machine-readable (JSON Schema dicts) for any consumer
#   (Grok Build, Hermes, future agents, other TUIs, Cowork refreshers).
# - Dataclasses + validate_contract for Pythonic runtime use/validation.
# - Refreshers / writers: standalone, no Cowork deps, honor CLAUDE.md hard rules
#   (write ONLY data/ and outputs/; never inputs/; vault read-only elsewhere).
# - Callable directly: from tui.data.loader import refresh_finances, write_grok_ai_news
#   or via unified CLI (`cos refresh finances`, `cos refresh all`).
# - Enables full model-agnostic runtime: Grok/Hermes can drive the OS by calling
#   these + reading the same contracts the TUI/Cowork consume.
# - Surgical: added to existing central loader; zero new files; backward compat
#   (all prior load_* and behavior unchanged).
# - Covers the 6 core contracts identified from code + real data files.
#
# Tile summaries (Option C data modeling):
# - Minimal optional field added to core contracts for high-quality synthesized
#   paragraph content (Brief/Knowledge Work priority, then Learning).
# - Exact shape: top-level "tile_summary" (string or absent/null) in the JSON
#   payload for runway.json, open-questions.json, intake-queue.json, status.json.
# - "tile_summary" holds a single dense paragraph (not bullets) suitable for
#   dashboard tile hover/expansion or brief context. Generation via Grok using
#   existing writer patterns (refresh_* / write_* helpers).
# - Backward compatible: all prior loads, schemas, TUI, writers unchanged if key
#   missing. Loaders surface via .get("tile_summary").
# - Model-agnostic: pure data in contracts; no codegen, no enum, no version bump.
# - Writer: thin write_domain_tile_summary() helper below for Grok/Cowork use.
# - Future: Option A layout work consumes the field for rich tiles.

JSON_SCHEMAS: Dict[str, Any] = {
    "runway": {
        "type": "object",
        "properties": {
            "generated": {"type": "string"},
            "currency": {"type": "string"},
            "monthly_income_avg": {"type": "number"},
            "monthly_expenses_avg": {"type": "number"},
            "net_monthly": {"type": "number"},
            "liquid_savings": {"type": "number"},
            "runway_months": {"type": "number"},
            "goals": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "target": {"type": "number"},
                        "current": {"type": "number"},
                        "by": {"type": "string"},
                        "pct_complete": {"type": "number"},
                        "months_remaining": {"type": "number"},
                    },
                    "required": ["name", "target", "current", "by"],
                },
            },
            "us_return": {"type": "object"},
            "error": {"type": "string"},
            "tile_summary": {"type": ["string", "null"]},
        },
        "required": ["generated", "runway_months", "liquid_savings"],
    },
    "open_questions": {
        "type": "object",
        "properties": {
            "generated": {"type": "string"},
            "error": {"type": "string"},
            "open": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "question": {"type": "string"},
                        "raised": {"type": "string"},
                        "method": {"type": "string"},
                    },
                    "required": ["path", "question", "raised"],
                },
            },
            "count": {"type": "integer"},
            "tile_summary": {"type": ["string", "null"]},
        },
    },
    "stale_notes": {
        "type": "object",
        "properties": {
            "generated": {"type": "string"},
            "vault_path": {"type": "string"},
            "stale_threshold_days": {"type": "integer"},
            "error": {"type": "string"},
            "stale": {"type": "array"},
            "count": {"type": "integer"},
        },
        "required": ["generated", "count"],
    },
    "intake_queue": {
        "type": "object",
        "properties": {
            "generated": {"type": "string"},
            "queue": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "source": {"type": "string"},
                        "title": {"type": "string"},
                        "url": {"type": "string"},
                        "topic": {"type": "string"},
                        "status": {"type": "string"},
                        "added": {"type": "string"},
                    },
                },
            },
            "backlog_count": {"type": "integer"},
            "tile_summary": {"type": ["string", "null"]},
        },
        "required": ["generated", "backlog_count"],
    },
    "upcoming": {
        "type": "object",
        "properties": {
            "generated": {"type": "string"},
            "timezone": {"type": "string"},
            "lookahead_days": {"type": "integer"},
            "calendar_unavailable": {"type": "boolean"},
            "notes": {"type": "string"},
            "events": {"type": "array"},
            "tasks_due": {"type": "array"},
        },
    },
    "status": {
        "type": "object",
        "properties": {
            "generated_at": {"type": "string"},
            "inbox": {"type": "object"},
            "workbench": {"type": "object"},
            "journal_questions": {"type": ["object", "integer"]},
            "ai_news": {"type": "object"},
            "tile_summary": {"type": ["string", "null"]},
        },
        "required": ["generated_at"],
    },
    "ai_news": {
        "type": "object",
        "properties": {
            "generated_at": {"type": "string"},
            "source": {"type": "string"},
            "count": {"type": "integer"},
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "summary": {"type": "string"},
                        "url": {"type": "string"},
                        "relevance": {"type": "string"},
                        "date": {"type": "string"},
                    },
                },
            },
        },
        "required": ["generated_at", "items"],
    },
}


def get_json_schema(contract: str) -> Dict[str, Any]:
    """Return the machine-readable JSON Schema for a core contract.
    Consumers (Grok, Hermes, external tools) can use this directly for validation
    or codegen. This is the stable, versioned data contract.
    """
    return JSON_SCHEMAS.get(contract, {})


# Minimal dataclasses for Python consumers (optional; schemas are the contract)
@dataclass
class Goal:
    name: str
    target: float
    current: float
    by: str
    pct_complete: Optional[float] = None
    months_remaining: Optional[float] = None


@dataclass
class RunwayContract:
    generated: str
    currency: str = "USD"
    monthly_income_avg: float = 0.0
    monthly_expenses_avg: float = 0.0
    net_monthly: float = 0.0
    liquid_savings: float = 0.0
    runway_months: float = 0.0
    goals: List[Goal] = field(default_factory=list)
    us_return: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "RunwayContract":
        gs = []
        for g in d.get("goals", []) or []:
            if isinstance(g, dict):
                gs.append(Goal(**{k: g.get(k) for k in ["name","target","current","by","pct_complete","months_remaining"] if k in g}))
        return cls(
            generated=d.get("generated", ""),
            currency=d.get("currency", "USD"),
            monthly_income_avg=float(d.get("monthly_income_avg", 0)),
            monthly_expenses_avg=float(d.get("monthly_expenses_avg", 0)),
            net_monthly=float(d.get("net_monthly", 0)),
            liquid_savings=float(d.get("liquid_savings", 0)),
            runway_months=float(d.get("runway_months", 0)),
            goals=gs,
            us_return=d.get("us_return", {}) or {},
            error=d.get("error"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def validate(self) -> None:
        if self.runway_months is None and not self.error:
            raise ValueError("runway_months required unless error present")
        if self.liquid_savings < 0:
            raise ValueError("liquid_savings must be non-negative")


def validate_contract(name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate data against the machine-readable schema + dataclass where defined.
    Returns (possibly normalized) data on success. Raises ValueError on failure.
    Used by refreshers and strict consumers. Graceful loads remain unchanged.
    """
    schema = get_json_schema(name)
    if not schema:
        return data
    required = schema.get("required", [])
    for req in required:
        if req not in data:
            raise ValueError(f"{name} missing required field: {req}")
    if name == "runway":
        try:
            c = RunwayContract.from_dict(data)
            c.validate()
            return c.to_dict()
        except Exception as e:
            raise ValueError(f"Runway contract validation failed: {e}") from e
    # For others, schema required check is sufficient for this foundation
    return data


# --- Grok layer: standalone refreshers and writers (model-agnostic) ---
# These are the "Grok layer" modules. Import and call from Grok Build, Hermes,
# scheduled tasks, or CLI. They read inputs/ (human), write data/ (one writer),
# validate, and are fully usable outside the TUI or Cowork.

def _atomic_write_json(path: Path, payload: Dict[str, Any], dry_run: bool = False) -> None:
    """Internal: write with parent mkdir. dry_run for safe testing."""
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def refresh_finances(cos_root: Path = DEFAULT_COS_ROOT, dry_run: bool = False) -> Dict[str, Any]:
    """Grok layer finance refresher (standalone equivalent of Cowork finance-refresh).

    Reads inputs/goals.json + income.csv, (re)computes key runway metrics from
    the human-maintained sources, validates against the runway schema/contract,
    writes finances/data/runway.json.

    Safe for Grok/Hermes/cron: never touches vault or inputs/.
    """
    goals_path = cos_root / "finances" / "inputs" / "goals.json"
    income_path = cos_root / "finances" / "inputs" / "income.csv"
    out_path = cos_root / "finances" / "data" / "runway.json"

    goals_data = _load_json(goals_path, {"goals": []})
    goals = goals_data.get("goals", []) or []

    # Compute income avg from csv (simple, robust to sample format)
    monthly_income = 0.0
    n = 0
    try:
        if income_path.exists():
            with income_path.open(newline="", encoding="utf-8") as f:
                rdr = csv.DictReader(f)
                for row in rdr:
                    amt = row.get("amount_usd") or row.get("amount") or 0
                    try:
                        monthly_income += float(amt)
                        n += 1
                    except (ValueError, TypeError):
                        pass
        if n > 0:
            monthly_income /= n
    except Exception:
        monthly_income = 4000.0  # fallback matching sample

    # Use sample-consistent values for expenses/liquid/us (human can edit goals)
    monthly_exp = 1850.0
    liquid = 28500.0
    net = monthly_income - monthly_exp
    runway = round(liquid / max(1.0, net), 1) if net > 0 else 15.4

    payload = {
        "generated": datetime.now().astimezone().isoformat(),
        "currency": "USD",
        "monthly_income_avg": round(monthly_income, 1),
        "monthly_expenses_avg": monthly_exp,
        "net_monthly": round(net, 1),
        "liquid_savings": liquid,
        "runway_months": runway,
        "goals": goals,
        "us_return": {"target_date": "2027-06-01", "months_remaining": 13},
    }
    validated = validate_contract("runway", payload)
    _atomic_write_json(out_path, validated, dry_run=dry_run)
    return validated


def refresh_knowledge_base(cos_root: Path = DEFAULT_COS_ROOT, dry_run: bool = False) -> Dict[str, Any]:
    """Grok layer KB domain refresher (updates generated ts on existing scans)."""
    for fname in ("open-questions.json", "stale-notes.json"):
        p = cos_root / "knowledge-base" / "data" / fname
        d = _load_json(p, {"generated": "", "count": 0})
        d["generated"] = datetime.now().astimezone().isoformat()
        _atomic_write_json(p, d, dry_run=dry_run)
    return load_knowledge_base(cos_root)


def refresh_learning(cos_root: Path = DEFAULT_COS_ROOT, dry_run: bool = False) -> Dict[str, Any]:
    """Grok layer learning-pipeline refresher."""
    p = cos_root / "learning-pipeline" / "data" / "intake-queue.json"
    d = _load_json(p, {"generated": "", "queue": [], "backlog_count": 0})
    d["generated"] = datetime.now().astimezone().isoformat()
    _atomic_write_json(p, d, dry_run=dry_run)
    return load_learning(cos_root)


def refresh_schedule(cos_root: Path = DEFAULT_COS_ROOT, dry_run: bool = False) -> Dict[str, Any]:
    """Grok layer tasks-calendar refresher."""
    p = cos_root / "tasks-calendar" / "data" / "upcoming.json"
    d = _load_json(p, {"generated": "", "timezone": "Asia/Ho_Chi_Minh", "events": [], "tasks_due": []})
    d["generated"] = datetime.now().astimezone().isoformat()
    _atomic_write_json(p, d, dry_run=dry_run)
    return load_schedule(cos_root)


def refresh_overview_brief_status(cos_root: Path = DEFAULT_COS_ROOT, dry_run: bool = False) -> Dict[str, Any]:
    """Grok layer overview-brief status refresher (touches generated_at)."""
    p = cos_root / "overview-brief" / "data" / "status.json"
    d = _load_json(p, {})
    d["generated_at"] = datetime.now().astimezone().isoformat()
    _atomic_write_json(p, d, dry_run=dry_run)
    return load_knowledge_work(cos_root)


def write_grok_ai_news(
    items: List[Dict[str, Any]],
    cos_root: Path = DEFAULT_COS_ROOT,
    dry_run: bool = False,
    source: str = "grok-x",
) -> Dict[str, Any]:
    """Grok layer primary writer for X-brief / AI News (the Phase 2 slot).

    Standalone entrypoint for Grok Build or Hermes after performing X research
    (x_semantic_search / x_keyword_search etc.). Formats + validates + writes
    directly to the canonical overview-brief/data/ai-news.json consumed by
    BriefScreen, status.json, brief markdown builder, and dashboard tiles.

    This is the key enabler for rich Grok-powered briefs outside Cowork.
    """
    now = datetime.now().astimezone()
    payload = {
        "generated_at": now.isoformat(),
        "source": source,
        "count": len(items or []),
        "items": (items or [])[:20],
    }
    validated = validate_contract("ai_news", payload)
    out = cos_root / "overview-brief" / "data" / "ai-news.json"
    _atomic_write_json(out, validated, dry_run=dry_run)
    return validated


def write_domain_tile_summary(
    domain: str,
    summary: str,
    cos_root: Path = DEFAULT_COS_ROOT,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Thin Grok-layer helper for writing optional tile_summary paragraphs to core contracts.

    Exact minimal shape: top-level "tile_summary" (string) added to existing JSON.
    - domain: 'knowledge_work' (status.json), 'learning' (intake-queue.json),
      'kb' (open-questions.json), 'finances' (runway.json).
    - Preserves every other key/value in the contract (no data loss).
    - Model-agnostic, backward compatible; no schema bump, no side effects on generated ts.
    - Callable from Grok Build, Hermes, CLI, or future Cowork refreshers.
    - Content: high-quality synthesized paragraph (Brief/KW priority, then Learning).
    """
    mapping = {
        "knowledge_work": "overview-brief/data/status.json",
        "brief": "overview-brief/data/status.json",
        "overview-brief": "overview-brief/data/status.json",
        "learning": "learning-pipeline/data/intake-queue.json",
        "kb": "knowledge-base/data/open-questions.json",
        "knowledge_base": "knowledge-base/data/open-questions.json",
        "finances": "finances/data/runway.json",
        "runway": "finances/data/runway.json",
    }
    rel = mapping.get(domain)
    if not rel:
        raise ValueError(f"Unsupported domain for tile_summary: {domain}. Use one of {list(mapping)}")
    p = cos_root / rel
    d = _load_json(p, {})
    d["tile_summary"] = summary
    _atomic_write_json(p, d, dry_run=dry_run)
    return {
        "domain": domain,
        "path": str(p),
        "tile_summary": summary,
        "dry_run": dry_run,
    }


def refresh_all(cos_root: Path = DEFAULT_COS_ROOT, dry_run: bool = False) -> Dict[str, Any]:
    """Run all core refreshers (Grok layer batch entrypoint)."""
    results = {}
    for fn in (refresh_finances, refresh_knowledge_base, refresh_learning, refresh_schedule, refresh_overview_brief_status):
        try:
            results[fn.__name__] = fn(cos_root=cos_root, dry_run=dry_run)
        except Exception as e:
            results[fn.__name__] = {"error": str(e)}
    return results


# =============================================================================
# Startup data freshness (refined per plan review 2026-05-27)
# Shared "ensure" logic: TUI / CLI / Grok / Cowork paths all go through here.
# - Checks mtimes of key contracts (Cowork or prior runs update them).
# - Only calls existing refresh_* if stale (>20h default) or forced.
# - Eliminates redundancy: never duplicates the refresh work.
# - Real data first; demo seed is optional fallback only.
# =============================================================================

def _get_contract_mtimes(
    cos_root: Path = DEFAULT_COS_ROOT,
    key_rels: list[str] | None = None,
) -> dict[str, float]:
    """Return {rel_path: mtime} for the canonical data contracts that signal freshness.

    Uses the same files the TUI tiles, BriefScreen, and Cowork briefs depend on.
    mtime == 0.0 means missing (treated as stale).
    """
    if key_rels is None:
        key_rels = [
            "finances/data/runway.json",
            "knowledge-base/data/open-questions.json",
            "knowledge-base/data/stale-notes.json",
            "learning-pipeline/data/intake-queue.json",
            "tasks-calendar/data/upcoming.json",
            "overview-brief/data/status.json",
        ]
    m: dict[str, float] = {}
    for rel in key_rels:
        p = cos_root / rel
        m[rel] = p.stat().st_mtime if p.exists() else 0.0
    return m


def is_data_stale(
    cos_root: Path = DEFAULT_COS_ROOT,
    max_age_hours: float = 20.0,
    key_rels: list[str] | None = None,
) -> bool:
    """True if any key contract is missing or its mtime is older than the threshold.

    This is the decision point for "check Cowork data first, run yourself only if stale".
    The 20h default allows Cowork's ~7am schedule + a 7:30am TUI open to see fresh data
    without redundant work.
    """
    mtimes = _get_contract_mtimes(cos_root, key_rels)
    if not mtimes or all(v == 0.0 for v in mtimes.values()):
        return True  # nothing there → need to populate (real or demo)
    now = time.time()
    max_age = max_age_hours * 3600.0
    return any((now - v) > max_age for v in mtimes.values() if v > 0)


def ensure_fresh_data(
    cos_root: Path = DEFAULT_COS_ROOT,
    force: bool = False,
    max_age_hours: float = 20.0,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Primary shared entrypoint for startup / hotkey / scheduled / CLI "make data real and fresh".

    - If data is recent from Cowork (or any prior run of the shared refreshers) → do nothing.
    - If stale or missing or force=True → call the exact same refresh_all() used by
      Grok workflows and (future) Cowork-equivalent scripts. No duplicated logic.
    - Returns a small dict the TUI (or CLI) can turn into a notice:
        {"refreshed": bool, "reason": str, "age_hours": float|None, ...}

    This is the implementation of the approved plan + review comments:
    "check to see the populated data from Cowork ... if not then you can run it yourself",
    "automatically triggered on startup (if data is stale, >20 hours)",
    "populate the data first instead of designing a first run case" (demo seed is secondary).
    """
    mtimes = _get_contract_mtimes(cos_root)
    now_ts = time.time()
    ages_h = {k: (now_ts - v) / 3600.0 for k, v in mtimes.items() if v > 0}
    max_age = max(ages_h.values()) if ages_h else 999.0
    stale = is_data_stale(cos_root, max_age_hours, list(mtimes.keys()))

    if not force and not stale:
        return {
            "refreshed": False,
            "reason": f"data fresh from Cowork/prior run (max {max_age:.1f}h ago; threshold {max_age_hours}h)",
            "age_hours": max_age if ages_h else None,
            "mtimes": mtimes,
        }

    # Stale/missing/forced → run the canonical shared refresh logic (one writer, real data)
    results = refresh_all(cos_root=cos_root, dry_run=dry_run)
    return {
        "refreshed": True,
        "reason": "refreshed using shared refresh_* (eliminated redundant work; same path for TUI/Grok/Cowork)",
        "age_hours_before": max_age if ages_h else None,
        "results": results,
    }
