"""Read-only vault coherence scan (Phase 2).

Walks the Obsidian vault and writes `knowledge-base/data/coherence.json` with
mechanical, deterministic signals: stale notes, orphans, open questions, and
missing frontmatter. Runs LOCALLY (where the vault is reachable) via `cos scan`
or as the first step of `cos brief` — sidestepping the `cos-vault-scan` Cowork
runner that only mounts ~/cos and can't see ~/llm-knowledge-base. Never writes
the vault. Semantic coherence (near-duplicates, contradictions) is deferred.
"""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from . import data

# Always-pruned structural dirs (the vault is also a Quartz project w/ node_modules).
STRUCTURAL_EXCLUDE = {".git", ".obsidian", ".trash", "node_modules", "public", "quartz", ".github"}
# Non-durable dirs excluded from coherence by default — tooling/source/meta, not
# durable wiki notes. Tunable via knowledge-base/inputs/config.json -> coherence.exclude_dirs.
DEFAULT_CONTENT_EXCLUDE = {"templates", "hermes", "raw", "_meta"}
# Dirs whose notes are never flagged as orphans (date-addressed, not link-addressed)
# but ARE still scanned for open questions etc. Tunable via coherence.orphan_exclude_dirs.
DEFAULT_ORPHAN_EXCLUDE = {"journal"}
# Hub/system notes that are naturally link-sparse — don't flag as orphans.
HUB_STEMS = {"index", "readme", "about", "license", "license-content", "home",
             "claude", "agents", "changelog", "globals"}

_WIKILINK = re.compile(r"\[\[([^\]]+)\]\]")
_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def _iter_md(vault: Path, excludes: set[str]):
    for dirpath, dirnames, filenames in os.walk(vault):
        dirnames[:] = [d for d in dirnames if d not in excludes and not d.startswith(".")]
        for fn in filenames:
            if fn.endswith(".md") and not fn.startswith("."):
                yield Path(dirpath) / fn


def _link_targets(text: str) -> set[str]:
    targets: set[str] = set()
    for m in _WIKILINK.finditer(text):
        t = m.group(1).split("|")[0].split("#")[0].strip()
        if t:
            targets.add(Path(t).stem.lower())
    return targets


def _extract_open_questions(text: str) -> list[str]:
    """Open questions via the documented conventions: `> [!question]` callouts
    (title on the marker line, or the next quoted line) and bullets under a
    `## Open Questions` heading. Returns the question text strings."""
    qs: list[str] = []
    lines = text.splitlines()
    in_oq = False
    for i, raw in enumerate(lines):
        s = raw.strip()
        if s.startswith("## "):
            in_oq = s[3:].strip().lower() == "open questions"
            continue
        if in_oq and s.startswith("- "):
            qs.append(s[2:].strip())
        if s.lower().startswith("> [!question"):
            idx = s.find("]")
            rest = s[idx + 1:].lstrip("+- ").strip() if idx != -1 else ""
            if rest:
                qs.append(rest)
            elif i + 1 < len(lines) and lines[i + 1].lstrip().startswith(">"):
                qs.append(lines[i + 1].lstrip().lstrip("> ").strip())
    return [q for q in qs if q]


def run(root: Optional[Path] = None, vault: Optional[Path] = None,
        threshold_days: Optional[int] = None) -> dict[str, Any]:
    root = root or data.cos_root()
    vault = vault or data.vault_root(root)
    out_path = root / "knowledge-base" / "data" / "coherence.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not vault or not Path(vault).exists():
        payload = {"generated": datetime.now().astimezone().isoformat(),
                   "scan_ok": False, "error": "vault not found", "total_notes": 0}
        out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return payload

    vault = Path(vault)
    cfg = data._read_json(root / "knowledge-base" / "inputs" / "config.json") or {}
    if threshold_days is None:
        threshold_days = cfg.get("stale_threshold_days", 90)
    coh_cfg = cfg.get("coherence") or {}
    excludes = STRUCTURAL_EXCLUDE | set(coh_cfg.get("exclude_dirs", DEFAULT_CONTENT_EXCLUDE))
    orphan_excludes = set(coh_cfg.get("orphan_exclude_dirs", DEFAULT_ORPHAN_EXCLUDE))
    cutoff = time.time() - threshold_days * 86400

    notes: list[str] = []
    outbound: dict[str, set[str]] = {}
    inbound: set[str] = set()
    open_items: list[dict[str, str]] = []
    missing_fm: list[str] = []
    stale: list[str] = []

    for p in _iter_md(vault, excludes):
        rel = str(p.relative_to(vault))
        notes.append(rel)
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            text = ""
        if not text.lstrip().startswith("---"):
            missing_fm.append(rel)
        try:
            if p.stat().st_mtime < cutoff:
                stale.append(rel)
        except Exception:
            pass
        m = _DATE_RE.search(Path(rel).name)
        raised = m.group(0) if m else ""
        for q in _extract_open_questions(text):
            open_items.append({"question": q[:300], "path": rel, "raised": raised})
        tgts = _link_targets(text)
        outbound[rel] = tgts
        inbound |= tgts

    orphans = [
        rel for rel in notes
        if Path(rel).stem.lower() not in HUB_STEMS
        and rel.split("/")[0] not in orphan_excludes
        and not outbound.get(rel)
        and Path(rel).stem.lower() not in inbound
    ]

    open_items.sort(key=lambda q: q["raised"], reverse=True)     # recent first
    open_items.sort(key=lambda q: "/journal/" not in q["path"])  # stable: journal first

    payload = {
        "generated": datetime.now().astimezone().isoformat(),
        "vault_path": str(vault),
        "scan_ok": True,
        "total_notes": len(notes),
        "stale_threshold_days": threshold_days,
        "excluded_dirs": sorted(excludes),
        "stale": {"count": len(stale), "sample": sorted(stale)[:10]},
        "orphans": {"count": len(orphans), "sample": sorted(orphans)[:10]},
        "open_questions": {"count": len(open_items), "items": open_items[:60]},
        "missing_frontmatter": {"count": len(missing_fm), "sample": sorted(missing_fm)[:10]},
    }
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload


def main_cli(argv: Optional[list[str]] = None) -> int:
    p = run()
    if not p.get("scan_ok"):
        print(f"coherence scan: {p.get('error', 'failed')}")
        return 1
    print(
        f"coherence scan: {p['total_notes']} notes · "
        f"stale {p['stale']['count']} · orphans {p['orphans']['count']} · "
        f"open Qs {p['open_questions']['count']} · "
        f"missing frontmatter {p['missing_frontmatter']['count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main_cli())
