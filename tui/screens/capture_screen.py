"""Dedicated Capture screen for the cos Textual TUI.

Implements an in-app version of the /capture skill from toolbox/capture.md.
- Provides multi-line input for note text (paste or type).
- Computes and live-previews the exact target path inside the vault (default: ~/llm-knowledge-base/inbox/YYYY-MM-DD-<slug>.md per the skill).
- Shows formatted content preview (as it will be written).
- Explicit "proceed" confirmation gate (hotkey 'p' + toolbar button) is the ONLY code path that ever writes to the vault.
- All other interactions (typing, preview updates, clear, navigation) are strictly read-only.

Doom-Emacs-style dedicated full-screen view (matches BriefScreen pattern exactly).
Hard rules (enforced by construction):
- NEVER writes to ~/llm-knowledge-base without explicit per-write "proceed".
- This remains the only permitted vault writer in cos.
- One confirmation per note (no batching).
- User sees exact path + full content before any write is possible.

Follows surgical reuse of BriefScreen structure, CSS, bindings, actions, help, state, and tiny helpers style.
No over-engineering. Minimal code that delivers the gated capture experience.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static, TextArea


# --- tiny internal helpers (surgical, self-contained, mirrors BriefScreen style exactly) ---

def _expand_path(p: str | Path) -> Path:
    """Expand ~ and return Path. Matches brief_screen.py helper."""
    return Path(p).expanduser()


def _make_slug(text: str, max_len: int = 40) -> str:
    """Generate a safe filename slug from the first line/words of the note.
    Strips leading # (md headings), keeps alnum + hyphens. Surgical min impl.
    """
    if not text or not text.strip():
        return "untitled-note"
    # First line or first ~80 chars
    first = text.strip().splitlines()[0][:80]
    # Remove leading markdown heading markers
    first = re.sub(r"^#+\s*", "", first)
    # Keep only alnum, space, hyphen; collapse
    first = re.sub(r"[^a-zA-Z0-9\s-]", "", first)
    words = [w.lower() for w in first.split() if w.strip()]
    slug = "-".join(words[:6]) or "note"
    if len(slug) > max_len:
        slug = slug[:max_len].rstrip("-")
    return slug or "untitled-note"


def _get_default_inbox() -> Path:
    """Default target directory exactly as specified in toolbox/capture.md."""
    return _expand_path("~/llm-knowledge-base/inbox")


def _compute_target_path(note_text: str) -> Path:
    """Return the exact target path for the staged note (default inbox rule)."""
    today = datetime.now().strftime("%Y-%m-%d")
    slug = _make_slug(note_text)
    return _get_default_inbox() / f"{today}-{slug}.md"


def _format_note_for_write(note_text: str) -> str:
    """Return the content exactly as it will be written to disk.
    If the user supplied what looks like a full note (starts with # or ---), pass through.
    Otherwise derive a minimal clean frontmatter + body (title from first line).
    Mirrors the skill's "full note content (formatted as it will be written)".
    """
    text = (note_text or "").strip()
    if not text:
        return ""
    # Pass-through if user already provided structure
    if text.startswith("#") or text.startswith("---"):
        return text + "\n"
    # Derive simple title + optional body
    lines = text.splitlines()
    title = lines[0].strip()[:80] or "Untitled Note"
    body = "\n".join(lines[1:]).strip()
    created = datetime.now().strftime("%Y-%m-%d %H:%M")
    frontmatter = f'''---
title: "{title}"
created: "{created}"
source: "cos TUI /capture (in-app)"
---

'''
    return frontmatter + (body + "\n" if body else "")


# --- The Screen (exact parallel construction to BriefScreen) ---

class CaptureScreen(Screen):
    """Full dedicated Capture view (Doom-Emacs style per-domain screen).

    Replaces the placeholder behavior for the 'c' hotkey.

    Real gated /capture logic:
    - Live TextArea input
    - Reactive live preview of exact vault target path (inbox default) + formatted content
    - 'p' / Proceed button: the single, explicit confirmation gate. This is the ONLY writer.
    - All other UI is read-only (no accidental or side-effect writes ever).

    Matches BriefScreen exactly in layout, state, help, theming, and dev runner.
    """

    CSS = """
    CaptureScreen {
        background: #0d0f14;
    }

    #toolbar {
        dock: top;
        height: 3;
        padding: 0 1;
        background: #16181f;
    }

    Button {
        margin: 0 1;
    }

    #note-input {
        height: 14;
        border: round #2a2d3a;
        margin: 1;
    }

    #path-preview, #content-preview {
        padding: 1 2;
        border: round #2a2d3a;
        margin: 0 1 1 1;
        background: #11131a;
        min-height: 3;
    }

    .preview-label {
        color: #8a8f9a;
        padding: 0 2;
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("escape", "pop_screen", "Back to dashboard"),
        Binding("p", "proceed_write", "Proceed & write (THE ONLY vault writer)"),
        Binding("c", "clear_note", "Clear input"),
        Binding("?", "show_help", "Help"),
        Binding("q", "quit", "Quit"),
    ]

    note_text: reactive[str] = reactive("")
    target_path: reactive[Path | None] = reactive(None)
    preview_content: reactive[str] = reactive("")

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="toolbar"):
            yield Button("Clear (c)", id="btn-clear")
            yield Button("Proceed & Write (p)", id="btn-proceed", variant="success")
            yield Button("Back (esc)", id="btn-back")
        with Vertical():
            yield Static("Note text (type or paste content to capture):", classes="preview-label")
            yield TextArea(
                "",
                id="note-input",
                language="markdown",
                theme="dracula",
                show_line_numbers=True,
            )
            yield Static(
                "Target vault path (live preview — default ~/llm-knowledge-base/inbox/ per /capture):",
                classes="preview-label",
            )
            yield Static("", id="path-preview")
            yield Static(
                "Formatted content preview (exactly as will be written on Proceed):",
                classes="preview-label",
            )
            yield Static("", id="content-preview")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "cos — Capture (in-app /capture — gated vault writer)"
        self.sub_title = "dedicated Doom-Emacs view | explicit proceed gate before ANY vault write"
        self._update_previews()
        # Focus the editor immediately (Doom-Emacs capture flow)
        try:
            ta = self.query_one("#note-input", TextArea)
            ta.focus()
        except Exception:
            pass

    def watch_note_text(self, _new_text: str) -> None:
        self._update_previews()

    def _update_previews(self) -> None:
        """Recompute path + formatted preview from current note_text (live, read-only)."""
        try:
            path_widget = self.query_one("#path-preview", Static)
            content_widget = self.query_one("#content-preview", Static)

            note = self.note_text or ""
            target = _compute_target_path(note)
            self.target_path = target

            path_widget.update(
                f"[bold cyan]{target}[/]\n"
                "[dim](computed from first line for slug; always inbox/ default — change via future path suggestion)[/]"
            )

            formatted = _format_note_for_write(note)
            self.preview_content = formatted
            display = formatted if len(formatted) <= 1800 else formatted[:1800] + "\n... (preview truncated)"
            content_widget.update(display or "[dim](enter text above for live preview)[/]")
        except Exception:
            # Safe no-op (early mount or widget query race)
            pass

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """Live binding: any edit updates reactives + previews (still read-only until 'p')."""
        if event.text_area.id == "note-input":
            self.note_text = event.text_area.text

    def action_clear_note(self) -> None:
        """Clear the editor and previews (read-only operation)."""
        try:
            ta = self.query_one("#note-input", TextArea)
            ta.text = ""
            self.note_text = ""
            self.notify("Input cleared.")
        except Exception:
            pass

    def action_proceed_write(self) -> None:
        """EXPLICIT CONFIRMATION GATE — the single, only writer in the entire TUI.

        Per toolbox/capture.md hard rules (and AGENTS.md reversibility):
        - User must have seen the exact path + full formatted content in the previews.
        - Only this action (p key or green button) ever calls mkdir + write_text.
        - One note per proceed. No side effects, no auto-writes, no batch.
        - After success: clears for the next capture (user can stay or esc).

        This is the in-app realization of the /capture skill's "STOP. Ask: Proceed?"
        """
        note = self.note_text or ""
        if not note.strip():
            self.notify("Nothing to capture (empty input).", severity="warning")
            return

        target: Path = self.target_path or _compute_target_path(note)
        formatted = self.preview_content or _format_note_for_write(note)

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(formatted, encoding="utf-8")

            self.notify(
                f"WROTE (explicit proceed gate honored): {target}\n"
                "This was the ONLY write path. Vault note is now staged in inbox.\n"
                "Process later via BriefScreen, dashboard, or /brief. Input cleared for next note.",
                timeout=18,
            )
            # Clear after successful gated write (ready for next capture in same session)
            self.action_clear_note()
        except Exception as exc:
            self.notify(f"Write failed (check permissions or path): {exc}", severity="error")

    def action_show_help(self) -> None:
        help_text = (
            "[bold cyan]Capture Screen — in-app /capture (Doom-Emacs dedicated view)[/]\n\n"
            "  p / Proceed & Write button : THE EXPLICIT GATE — the one and only action that writes to ~/llm-knowledge-base/.\n"
            "                              Exactly as required by toolbox/capture.md:\n"
            "                              • Stage (show exact target path + full formatted content)\n"
            "                              • STOP until user confirms\n"
            "                              • Write ONLY on explicit 'proceed' (p or button)\n"
            "                              • One note per confirmation; never batch or side-effect\n"
            "  Type or paste in TextArea  : Live reactive updates to path slug (derived from content) + content preview.\n"
            "                               All of this is READ-ONLY. No writes occur.\n"
            "  c / Clear button           : Clear the note (read-only)\n"
            "  esc / Back                 : Return to main dashboard tiles (no write performed)\n"
            "  ?                          : This help overlay\n"
            "  q                          : Quit the TUI\n\n"
            "Precisely mirrors toolbox/capture.md + the established BriefScreen pattern:\n"
            "- Input for note text\n"
            "- Determine + show exact target (inbox/YYYY-MM-DD-slug.md default)\n"
            "- Stage the note (path + content preview)\n"
            "- Gated write only after explicit proceed\n\n"
            "Hard rules (enforced here and nowhere else in cos):\n"
            "• Vault writes ONLY via this screen's proceed action.\n"
            "• Never as side effect of any other workflow or hotkey.\n"
            "• This TUI screen is the sole permitted vault writer.\n"
            "• Matches AGENTS.md reversibility: user sees everything and explicitly authorizes before write.\n\n"
            "This is the second dedicated per-domain Doom-Emacs view (after BriefScreen)."
        )
        self.notify(help_text, timeout=30)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn-clear":
            self.action_clear_note()
        elif bid == "btn-proceed":
            self.action_proceed_write()
        elif bid == "btn-back":
            self.app.pop_screen()


# For direct execution during dev (rarely used, mirrors BriefScreen)
if __name__ == "__main__":
    from textual.app import App

    class _DevApp(App):
        def on_mount(self):
            self.push_screen(CaptureScreen())

    _DevApp().run()
