"""Unit tests for tui/data/loader.py (data contracts, graceful loading, edge cases).

Part of out-5 validation. Uses temp dirs only. No writes to real ~/cos or project data.
Covers the implicit model-agnostic contracts used by TUI dashboard and Grok writes.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tui.data.loader import (
    load_runway,
    load_knowledge_base,
    load_learning,
    load_schedule,
    load_knowledge_work,
    load_all,
)


def test_load_runway_valid_contract(tmp_path: Path) -> None:
    """Valid runway.json produces expected shape."""
    d = tmp_path / "finances" / "data"
    d.mkdir(parents=True)
    payload = {"runway_months": 7.5, "net_monthly": 1500, "us_return": {"months_remaining": 4}}
    (d / "runway.json").write_text(json.dumps(payload), encoding="utf-8")
    data = load_runway(tmp_path)
    assert data["runway_months"] == 7.5
    assert data.get("net_monthly") == 1500


def test_load_runway_missing_or_unreadable_defaults(tmp_path: Path) -> None:
    """Missing file returns safe default (no crash)."""
    data = load_runway(tmp_path)
    assert data["runway_months"] is None
    assert "error" in data and data["error"]


def test_load_knowledge_base_merges_stale_and_oq(tmp_path: Path) -> None:
    """KB loader combines stale-notes + open-questions with vault_error flag."""
    d = tmp_path / "knowledge-base" / "data"
    d.mkdir(parents=True)
    (d / "stale-notes.json").write_text(json.dumps({"count": 12, "stale_threshold_days": 90}), encoding="utf-8")
    (d / "open-questions.json").write_text(json.dumps({"count": 3, "open": [{"question": "test?"}]}), encoding="utf-8")
    data = load_knowledge_base(tmp_path)
    assert data["stale_count"] == 12
    assert data["oq_count"] == 3
    assert data["vault_error"] is False
    assert len(data["recent_questions"]) == 1


def test_load_knowledge_base_vault_error_flag(tmp_path: Path) -> None:
    """Error in either file sets vault_error."""
    d = tmp_path / "knowledge-base" / "data"
    d.mkdir(parents=True)
    (d / "stale-notes.json").write_text(json.dumps({"error": "vault down"}), encoding="utf-8")
    data = load_knowledge_base(tmp_path)
    assert data["vault_error"] is True


def test_load_learning_queue_length(tmp_path: Path) -> None:
    """Learning counts backlog and queue len."""
    d = tmp_path / "learning-pipeline" / "data"
    d.mkdir(parents=True)
    (d / "intake-queue.json").write_text(json.dumps({"backlog_count": 5, "queue": [1, 2, 3]}), encoding="utf-8")
    data = load_learning(tmp_path)
    assert data["backlog_count"] == 5
    assert data["queue_length"] == 3


def test_load_schedule_defaults_and_flags(tmp_path: Path) -> None:
    """Schedule handles missing calendar + notes."""
    d = tmp_path / "tasks-calendar" / "data"
    d.mkdir(parents=True)
    (d / "upcoming.json").write_text(json.dumps({"events": [], "tasks_due": [{}], "calendar_unavailable": True, "note": "test"}), encoding="utf-8")
    data = load_schedule(tmp_path)
    assert data["calendar_unavailable"] is True
    assert len(data["tasks_due"]) == 1
    assert data["note"] == "test"


def test_load_knowledge_work_ai_news_flag(tmp_path: Path) -> None:
    """Knowledge work detects ai_news presence (Grok slot)."""
    d = tmp_path / "overview-brief" / "data"
    d.mkdir(parents=True)
    (d / "status.json").write_text(json.dumps({"inbox": {"count": 2}, "workbench": {"count": 1}, "journal_questions": 0, "ai_news": {"foo": 1}}), encoding="utf-8")
    data = load_knowledge_work(tmp_path)
    assert data["inbox_count"] == 2
    assert data["ai_news_available"] is True


def test_load_all_aggregates_expected_domains(tmp_path: Path) -> None:
    """load_all returns the 5 domains + generated_at (core TUI contract)."""
    # minimal files so loads succeed without all errors
    for rel in [
        "finances/data/runway.json",
        "knowledge-base/data/stale-notes.json",
        "knowledge-base/data/open-questions.json",
        "learning-pipeline/data/intake-queue.json",
        "tasks-calendar/data/upcoming.json",
        "overview-brief/data/status.json",
    ]:
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("{}", encoding="utf-8")

    data = load_all(tmp_path)
    for k in ("finances", "kb", "learning", "schedule", "knowledge_work"):
        assert k in data
    assert data.get("generated_at") == "live"
