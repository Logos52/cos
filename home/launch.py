"""Launch bridges for the cos home — the 'Move' half of See/Move.

Every launch is a keystroke that lands you in the right place. On macOS these
shell out to `open`; everywhere else (or in headless tests) they no-op and
return a human-readable string the UI can surface. Nothing here writes the vault.
"""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from urllib.parse import quote


def _open(arg: str) -> bool:
    opener = shutil.which("open")  # macOS
    if not opener:
        return False
    try:
        subprocess.Popen([opener, arg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def open_url(url: str) -> str:
    return f"opened {url}" if _open(url) else f"(would open) {url}"


def open_obsidian(vault: str, file: str = "") -> str:
    uri = f"obsidian://open?vault={quote(vault)}"
    if file:
        uri += f"&file={quote(file)}"
    return f"→ obsidian: {file or vault}" if _open(uri) else f"(would open) {uri}"


def copy(text: str) -> str:
    pb = shutil.which("pbcopy")
    if pb:
        try:
            subprocess.run([pb], input=text.encode("utf-8"), check=True)
            return "copied to clipboard"
        except Exception:
            pass
    return text


# --- Command bar: spawn interactive tools into WezTerm; run simple ones inline ---

# Commands that are themselves full-screen / interactive: these get a real
# terminal (a new WezTerm pane), never an inline capture.
INTERACTIVE = {
    "grok", "codex", "hermes", "claude", "aider", "cos",
    "vim", "nvim", "nano", "emacs", "htop", "top", "btop",
    "ssh", "tmux", "python", "python3", "ipython", "node", "less", "man", "fzf",
}


def is_interactive(prog: str) -> bool:
    return prog in INTERACTIVE


def in_wezterm() -> bool:
    return bool(os.environ.get("WEZTERM_PANE")) and shutil.which("wezterm") is not None


def spawn_wezterm(command: str) -> str:
    """Spawn `command` in a new WezTerm tab. Requires running inside WezTerm."""
    wez = shutil.which("wezterm")
    if not (wez and os.environ.get("WEZTERM_PANE")):
        return f"(run inside WezTerm to spawn) {command}"
    try:
        argv = shlex.split(command)
    except ValueError as e:
        return f"parse error: {e}"
    try:
        subprocess.run(
            [wez, "cli", "spawn", "--cwd", os.environ.get("COS_ROOT", os.getcwd()), "--", *argv],
            check=True, capture_output=True, text=True, timeout=10,
        )
        return f"new WezTerm tab → {command}"
    except Exception as e:  # noqa: BLE001
        return f"spawn failed: {e}"


def run_inline(command: str, timeout: int = 15) -> tuple[int, str]:
    """Run a non-interactive shell command, capturing combined output (truncated)."""
    try:
        p = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=os.environ.get("COS_ROOT") or None,
        )
        out = ((p.stdout or "") + (p.stderr or "")).strip()
        return p.returncode, out[:4000]
    except subprocess.TimeoutExpired:
        return 124, f"(timed out after {timeout}s)"
    except Exception as e:  # noqa: BLE001
        return 1, f"(error: {e})"
