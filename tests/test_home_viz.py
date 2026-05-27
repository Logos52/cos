"""Unit tests for the cos home viz functions + data loaders.

Runs under pytest, or standalone:  python3 tests/test_home_viz.py
The viz tests are pure. The data tests use a temp COS_ROOT so they don't
depend on real files.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from home import viz, data, launch, brief, scan  # noqa: E402

_SPARK_SET = set("▁▂▃▄▅▆▇█")


def test_sparkline_length_and_charset():
    s = viz.sparkline([1, 2, 3, 4, 5, 6, 7, 8])
    assert len(s) == 8
    assert set(s) <= _SPARK_SET
    assert s[0] == "▁" and s[-1] == "█"


def test_sparkline_empty_and_flat():
    assert viz.sparkline([]) == ""
    assert viz.sparkline([None]) == ""
    flat = viz.sparkline([5, 5, 5])
    assert flat == "▁▁▁"  # no span → all lowest


def test_gauge_clamps_and_width():
    assert len(viz.gauge(15.4, 24, width=9)) == 9
    assert viz.gauge(50, 10, width=5) == "█████"   # over max clamps full
    assert viz.gauge(-3, 10, width=4) == "░░░░"     # negative clamps empty
    assert viz.gauge(1, 0, width=3) == "░░░"         # zero max → empty


def test_bar_percentage():
    assert viz.bar(0, width=10) == "▱" * 10
    assert viz.bar(100, width=10) == "▰" * 10
    assert len(viz.bar(64.8, width=10)) == 10


def test_blocks_caps():
    assert viz.blocks(3) == "▮▮▮"
    assert viz.blocks(99, max_blocks=5) == "▮▮▮▮▮"
    assert viz.blocks(0) == ""
    assert viz.blocks(None) == ""


def _seed(root: Path):
    (root / "finances" / "data").mkdir(parents=True, exist_ok=True)
    (root / "overview-brief" / "inputs").mkdir(parents=True, exist_ok=True)
    (root / "knowledge-base" / "data").mkdir(parents=True, exist_ok=True)
    (root / "finances" / "data" / "runway.json").write_text(json.dumps({
        "runway_months": 15.4, "net_monthly": 2150.0, "error": None,
        "goals": [{"name": "US fund", "pct_complete": 64.8}],
    }))
    (root / "overview-brief" / "inputs" / "focus.md").write_text(
        "# Focus\nBuilding cos.\n- one\n- two\n")
    (root / "knowledge-base" / "data" / "stale-notes.json").write_text(json.dumps({
        "error": "vault inaccessible", "count": 0}))


def test_data_loaders_graceful_and_focus():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        # Point the vault at an empty dir so focus falls back to the cos seed.
        os.environ["LLM_VAULT_ROOT"] = str(root)
        try:
            assert data.load_finances(root)["ok"] is False  # nothing seeded → graceful
            _seed(root)
            fin = data.load_finances(root)
            assert fin["ok"] is True and fin["runway_months"] == 15.4
            foc = data.load_focus(root)
            assert foc["headline"] == "Building cos." and foc["bullets"] == ["one", "two"]
            coh = data.load_coherence(root)
            assert coh["scan_ok"] is False and coh["stale_count"] is None
        finally:
            os.environ.pop("LLM_VAULT_ROOT", None)


def test_focus_from_vault_section():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        vault = root / "vault"
        (vault / "journal").mkdir(parents=True)
        (vault / "journal" / "index.md").write_text(
            "# Journal\n\n## What's On My Mind\n\n"
            "- [[wiki/Focus|Focus Management]] — return to work after drift\n"
            "- Plain bullet without a link\n\n"
            "## Recent Log\n- not this one\n"
        )
        os.environ["LLM_VAULT_ROOT"] = str(vault)
        try:
            foc = data.load_focus(root)
            assert foc["headline"] == "What's On My Mind"
            # wikilink stripped to label, em-dash clause trimmed, other section ignored
            assert foc["bullets"][0] == "Focus Management"
            assert "Plain bullet without a link" in foc["bullets"]
            assert all("not this one" not in b for b in foc["bullets"])
        finally:
            os.environ.pop("LLM_VAULT_ROOT", None)


def test_command_classification():
    assert launch.is_interactive("grok") is True
    assert launch.is_interactive("codex") is True
    assert launch.is_interactive("ls") is False
    assert launch.is_interactive("git") is False


def test_run_inline_echo():
    rc, out = launch.run_inline("echo hello")
    assert rc == 0 and out == "hello"


def test_spawn_graceful_without_wezterm():
    old = os.environ.pop("WEZTERM_PANE", None)
    try:
        msg = launch.spawn_wezterm("grok")
        assert "run inside WezTerm" in msg
    finally:
        if old is not None:
            os.environ["WEZTERM_PANE"] = old


def _seed_full(root: Path):
    for sub in ["finances/data", "overview-brief/inputs", "overview-brief/data",
                "knowledge-base/data", "learning-pipeline/data", "tasks-calendar/data"]:
        (root / sub).mkdir(parents=True, exist_ok=True)
    (root / "finances/data/runway.json").write_text(json.dumps({
        "runway_months": 15.4, "net_monthly": 2150.0, "error": None,
        "goals": [{"name": "US relocation fund", "pct_complete": 64.8, "amount_remaining": 8800, "by": "2027-06"}],
        "us_return": {"months_remaining": 12.2, "target_date": "2027-06-01"}}))
    (root / "overview-brief/inputs/focus.md").write_text("# Focus\nBuilding cos.\n- one\n- two\n")
    (root / "overview-brief/data/status.json").write_text(json.dumps({
        "generated_at": "2026-05-27T07:18:00+07:00", "inbox": {"count": 13, "items": []},
        "workbench": {"count": 1}, "journal_questions": 13, "tile_summary": "High-intake phase."}))
    (root / "knowledge-base/data/open-questions.json").write_text(json.dumps({"count": 2, "open": [
        {"path": "journal/x.md", "question": "What signal shows organized usability?", "raised": "2026-05-25"},
        {"path": "wiki/y.md", "question": "Other q", "raised": "2026-05-20"}]}))
    (root / "knowledge-base/data/stale-notes.json").write_text(json.dumps({"error": "vault inaccessible", "count": 0}))
    (root / "learning-pipeline/data/intake-queue.json").write_text(json.dumps({
        "backlog_count": 3, "queue": [{"title": "Textual reactive guide", "status": "unread"}]}))
    (root / "overview-brief/data/ai-news.json").write_text(json.dumps({
        "generated_at": "x", "items": [{"title": "Grok Build CLI", "summary": "agentic", "date": "2026-05-24"}]}))
    (root / "tasks-calendar/data/upcoming.json").write_text(json.dumps({
        "calendar_unavailable": True, "events": [], "tasks_due": []}))


def test_build_markdown_sections():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        os.environ["LLM_VAULT_ROOT"] = str(root)  # no journal → focus uses cos seed
        try:
            _seed_full(root)
            md = brief.build_markdown(root)
            for sec in ["## Focus", "## Finances", "## Today / upcoming", "## Knowledge work",
                        "## Open questions (recent)", "## Learning", "## AI signals (Grok)", "## Flags"]:
                assert sec in md, f"missing {sec}"
            assert "Runway: 15.4 months" in md
            assert "US relocation fund: 64.8%" in md
            # journal-sourced question ordered before the wiki one
            assert md.index("organized usability") < md.index("Other q")
        finally:
            os.environ.pop("LLM_VAULT_ROOT", None)


def test_markdown_to_notes_html():
    h = brief.markdown_to_notes_html("# T\n## S\n- a\n- b\n\ntext\n---")
    assert "<h1>T</h1>" in h and "<h2>S</h2>" in h
    assert "<ul>" in h and "<li>a</li>" in h and "<hr>" in h
    assert h.startswith("<html><body>")


def test_push_graceful_without_osascript():
    msg = brief.push_to_apple_notes("<html></html>")
    assert "osascript" in msg or "Apple Notes" in msg


def test_vault_coherence_scan():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "cos"
        vault = Path(td) / "vault"
        (root / "knowledge-base" / "inputs").mkdir(parents=True)
        (root / "knowledge-base" / "inputs" / "config.json").write_text(json.dumps({"stale_threshold_days": 90}))
        (vault / "wiki").mkdir(parents=True)
        (vault / "node_modules").mkdir(parents=True)
        (vault / "wiki" / "A.md").write_text("---\ntitle: A\n---\nlinks to [[B]]\n")
        (vault / "wiki" / "B.md").write_text("---\ntitle: B\n---\n> [!question] what is x?\n")
        orphan = vault / "orphan-note.md"
        orphan.write_text("no frontmatter here and links to nothing\n")
        old = time.time() - 200 * 86400
        os.utime(orphan, (old, old))
        (vault / "node_modules" / "pkg.md").write_text("# excluded, should not be scanned\n")

        p = scan.run(root, vault)
        assert p["scan_ok"] and p["total_notes"] == 3              # node_modules excluded
        assert p["missing_frontmatter"]["count"] == 1              # orphan-note
        assert "orphan-note.md" in p["orphans"]["sample"]          # no in/out links
        assert all("A.md" not in s and "B.md" not in s for s in p["orphans"]["sample"])
        assert p["stale"]["count"] == 1                            # orphan-note mtime is old
        assert p["open_questions"]["count"] >= 1                   # B's callout
        qtexts = [it["question"] for it in p["open_questions"]["items"]]
        assert any("what is x" in q for q in qtexts)               # callout text captured
        # the home's loader now reads coherence.json
        cc = data.load_coherence(root)
        assert cc["scan_ok"] and cc["orphans"] == 1


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed")
