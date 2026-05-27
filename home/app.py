"""cos home — the bento hybrid mission control (Textual).

Default view: a bento grid you scan (varying card sizes by importance).
`space` opens a command palette (Doom M-x / which-key feel) to launch.
Everything reads the local contracts + your focus; nothing writes the vault.
"""

from __future__ import annotations

import calendar as _calmod
from datetime import datetime

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Grid, Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer, Input, Label, ListItem, ListView, RichLog, Static

from . import data, launch, viz
from .theme import APP_CSS, COLORS as C


def _date() -> str:
    return datetime.now().strftime("%a %d %b")


def _hero(d: dict) -> str:
    foc, kw, coh = d["focus"], d["knowledge_work"], d["coherence"]
    lines = [
        f"[bold {C['title']}]● now[/] [{C['dim']}]· {_date()}[/]",
        f"[{C['dim']}]{foc['headline'].lower()}[/]",
    ]
    for b in foc["bullets"][:3]:
        lines.append(f"[{C['fg']}]{b}[/]")
    lines.append("")
    lines.append(
        f"inbox [{C['fg']}]{kw['inbox_count']}[/] · "
        f"workbench {kw['workbench_count']} · "
        f"journal Qs {kw['journal_questions']} · "
        f"open Qs [{C['tan']}]{coh['open_q']}[/]"
    )
    if (kw["inbox_count"] or 0) >= 10:
        lines.append(f"[{C['warn']}]! inbox clearing slower than intake — synthesis pass due[/]")
    return "\n".join(lines)


def _finances(d: dict) -> str:
    fin = d["finances"]
    lines = [f"[bold {C['title']}]○ finances[/] [{C['dim']}]· private[/]"]
    rm = fin.get("runway_months") or 0
    lines.append(f"runway [{C['sage']}]{viz.gauge(rm, 24, 9)}[/]")
    for g in (fin.get("goals") or [])[:2]:
        nm = (g.get("name") or "goal")[:12]
        lines.append(f"[{C['dim']}]{nm}[/] [{C['taupe']}]{viz.bar(g.get('pct_complete', 0), 8)}[/]")
    if not fin.get("ok"):
        lines.append(f"[{C['warn']}]{fin.get('note', 'unavailable')}[/]")
    return "\n".join(lines)


def _tasks(d: dict) -> str:
    t = d["tasks"]
    lines = [f"[bold {C['title']}]○ tasks · today[/]"]
    if t["calendar_unavailable"]:
        lines.append(f"[{C['dim']}]— no events (calendar off)[/]")
    else:
        lines.append(f"events {len(t['events'])}")
    lines.append(f"[{C['dim']}]{len(t['tasks_due'])} due this week[/]")
    return "\n".join(lines)


def _learning(d: dict) -> str:
    l = d["learning"]
    lines = [
        f"[bold {C['title']}]○ learning[/]",
        f"queue [{C['taupe']}]{viz.blocks(l['backlog_count'])}[/] {l['backlog_count']}",
    ]
    if l["items"]:
        lines.append(f"[{C['dim']}]▸ {l['items'][0]['title'][:24]}[/]")
    return "\n".join(lines)


def _coherence(d: dict) -> str:
    c = d["coherence"]
    lines = [
        f"[bold {C['title']}]○ vault coherence[/] [{C['dim']}]· #1 pain[/]",
        f"open Qs [{C['tan']}]{c['open_q']}[/]",
    ]
    if c["scan_ok"]:
        nofm = c.get("missing_frontmatter")
        extra = f" · no-fm {nofm}" if nofm is not None else ""
        lines.append(f"[{C['dim']}]stale {c['stale_count']} · orphans {c['orphans']}{extra}[/]")
    else:
        lines.append(f"[{C['dim']}]stale — · orphans — · run `cos scan`[/]")
    lines.append(f"[{C['dim']}]▸ ↵ open in obsidian[/]")
    return "\n".join(lines)


def _signals(d: dict) -> str:
    s = d["signals"]
    lines = [f"[bold {C['title']}]○ signals · grok[/] [{C['dim']}]· {s['count']}[/]"]
    for it in s["items"][:2]:
        lines.append(f"[{C['dim']}]▸ {it['title'][:22]}[/]")
    return "\n".join(lines)


def _calendar(d: dict) -> str:
    now = datetime.now()
    lines = [
        f"[bold {C['title']}]○ {now.strftime('%B %Y')}[/]",
        f"[{C['dim']}]Mo Tu We Th Fr Sa Su[/]",
    ]
    for week in _calmod.Calendar(firstweekday=0).monthdayscalendar(now.year, now.month):
        cells = []
        for day in week:
            if day == 0:
                cells.append("  ")
            elif day == now.day:
                cells.append(f"[{C['clay_hi']}]{day:2d}[/]")
            else:
                cells.append(f"[{C['dim']}]{day:2d}[/]")
        lines.append(" ".join(cells))
    return "\n".join(lines)


def _skills(d: dict) -> str:
    sk = d["skills"]
    lines = [f"[bold {C['title']}]○ skills · mg-kolbs[/]"]
    if not sk.get("ok") or not sk["items"]:
        lines.append(f"[{C['dim']}]no skills found[/]")
        return "\n".join(lines)
    for s in sk["items"][:6]:
        cur = s["current"] or 0
        fin = s["final"] or 10
        g = viz.gauge(cur, 10, 8)
        lines.append(f"[{C['dim']}]{s['name'][:16]:<16}[/] [{C['sage']}]{g}[/] [{C['dim']}]{cur}→{fin}[/]")
    return "\n".join(lines)


BUILDERS = {
    "hero": _hero,
    "finances": _finances,
    "tasks": _tasks,
    "learning": _learning,
    "calendar": _calendar,
    "coherence": _coherence,
    "signals": _signals,
    "skills": _skills,
}


class Card(Static):
    can_focus = True


class CmdInput(Input):
    """Minibuffer input — escape returns focus to the body so hotkeys work again."""

    BINDINGS = [Binding("escape", "leave", "leave", show=False)]

    def action_leave(self) -> None:
        self.app.action_leave_cmd()


class Palette(ModalScreen[str]):
    """Doom-style launcher. Returns the chosen action id (or None on escape)."""

    BINDINGS = [Binding("escape", "dismiss", "close")]

    ITEMS = [
        ("b", "brief & flags", "brief"),
        ("k", "vault coherence", "coherence"),
        ("f", "finances", "finances"),
        ("l", "learning queue", "learning"),
        ("c", "capture to obsidian", "capture"),
        ("r", "research with grok", "research"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="palette"):
            yield Input(placeholder="go to / run…", id="palette-query")
            items = [
                ListItem(Label(f"[{C['clay_hi']}]{k}[/]  {label}"), id=f"act-{action}")
                for k, label, action in self.ITEMS
            ]
            yield ListView(*items, id="palette-list")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self.dismiss((event.item.id or "act-").removeprefix("act-"))


class CosHome(App):
    CSS = APP_CSS
    TITLE = "cos — mission control"

    BINDINGS = [
        Binding("space", "palette", "palette"),
        Binding("grave_accent", "focus_cmd", "command"),
        Binding("b", "launch('brief')", "brief"),
        Binding("f", "launch('finances')", "finances"),
        Binding("t", "launch('tasks')", "tasks"),
        Binding("l", "launch('learning')", "learning"),
        Binding("k", "launch('coherence')", "coherence"),
        Binding("g", "launch('signals')", "signals"),
        Binding("r", "refresh_data", "refresh"),
        Binding("q", "quit", "quit"),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.data = data.load_all()

    def compose(self) -> ComposeResult:
        yield Static(self._modeline(), id="modeline")
        with Grid(id="bento"):
            for cid, builder in BUILDERS.items():
                yield Card(builder(self.data), id=cid, classes=cid)
        yield CmdInput(placeholder="run a command, or a tool like grok    (` to open, esc to leave)", id="cmd")
        yield RichLog(id="cmd-out", highlight=False, markup=False, wrap=True)
        yield Footer()

    def _modeline(self) -> str:
        when = datetime.now().strftime("%H:%M")
        return f"[{C['clay']}]cos[/] [{C['dim']}]· mission control · {when} · clay-dark[/]"

    def on_mount(self) -> None:
        # Start with a card focused so single-key hotkeys are live immediately;
        # the command bar is opt-in via backtick (or click).
        try:
            self.query_one("#hero", Card).focus()
        except Exception:
            pass

    def action_refresh_data(self) -> None:
        self.data = data.load_all()
        for cid, builder in BUILDERS.items():
            try:
                self.query_one(f"#{cid}", Card).update(builder(self.data))
            except Exception:
                pass
        self.query_one("#modeline", Static).update(self._modeline())
        self.notify("refreshed from disk")

    def action_palette(self) -> None:
        self.push_screen(Palette(), self._on_palette_choice)

    def _on_palette_choice(self, action: str | None) -> None:
        if action:
            self.action_launch(action)

    def action_launch(self, target: str) -> None:
        vr = data.vault_root()
        vault = vr.name if vr else "llm-knowledge-base"
        msg = {
            "brief": "→ brief (regenerate: `cos brief`)",
            "coherence": launch.open_obsidian(vault, "00 Command Center/Open Questions.md"),
            "finances": "→ finances (drill-in)",
            "learning": "→ learning queue",
            "capture": "→ capture (gated /capture)",
            "research": "→ research with grok",
            "tasks": "→ tasks / calendar",
            "signals": "→ ai signals (grok)",
        }.get(target, f"→ {target}")
        self.notify(msg)

    # --- command bar (minibuffer) ---
    def action_focus_cmd(self) -> None:
        self.query_one("#cmd", Input).focus()

    def action_leave_cmd(self) -> None:
        try:
            self.query_one("#hero", Card).focus()
        except Exception:
            pass

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "cmd":
            return
        raw = (event.value or "").strip()
        event.input.value = ""
        if not raw:
            return
        out = self.query_one("#cmd-out", RichLog)
        out.display = True
        prog = raw.split()[0]
        if launch.is_interactive(prog):
            out.write(f"⟫ {launch.spawn_wezterm(raw)}")
        else:
            rc, text = launch.run_inline(raw)
            out.write(f"$ {raw}")
            if text:
                out.write(text)
            out.write(f"[exit {rc}]")


if __name__ == "__main__":
    CosHome().run()
