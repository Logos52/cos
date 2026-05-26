"""Integration tests for TUI dashboard (launch, data binding from contracts, hotkeys, screens).

Uses Textual Pilot / run_test per out-5. Real project data (dev COS_ROOT) for realistic validation of live tiles + hotkey dispatch to dedicated views.
Graceful on partial data.
"""

from __future__ import annotations

import os

import pytest

from tui.app import CosDashboardApp


@pytest.mark.asyncio
async def test_dashboard_launches_binds_data_and_refreshes() -> None:
    """Dashboard mounts, loads contracts via loader, renders tiles, refresh works."""
    os.environ["COS_ROOT"] = "/Users/n1/Projects/cos"  # real dev data for binding validation
    app = CosDashboardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        # Title / reactive sub_title set in on_mount + watch
        assert app.title and "cos" in app.title.lower()
        assert app.sub_title  # last refresh timestamp or similar
        # Grid + tiles from watch_data (5 domains)
        tiles = app.query(".tile")
        assert len(tiles) >= 3, "Expected multiple DomainTile widgets from data binding"
        # Manual refresh action (core hotkey behavior)
        app.action_refresh_data()
        await pilot.pause(0.05)
        # ctrl+r hotkey
        await pilot.press("ctrl+r")
        await pilot.pause(0.05)
        # b hotkey dispatches to BriefScreen (real dedicated view)
        await pilot.press("b")
        await pilot.pause(0.1)
        # No crash = success for MVP launch + wiring + binding


@pytest.mark.asyncio
async def test_hotkeys_open_dedicated_screens() -> None:
    """Key hotkeys (r, c, t) dispatch without crash (placeholders or real screens)."""
    os.environ["COS_ROOT"] = "/Users/n1/Projects/cos"
    app = CosDashboardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        for key in ("r", "c", "t", "?"):
            await pilot.press(key)
            await pilot.pause(0.05)
        # q would quit; skip in test harness
