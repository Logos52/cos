"""Muted-warm 'Cowork' palette + Textual CSS for the cos home.

Warm charcoal background, warm-bone text, a single restrained clay/terracotta
accent (PRD H-11). Everything else neutral; one accent does the work.

Colors are hex so they render identically across terminals (truecolor — use
WezTerm, not Terminal.app, which is 256-color). Use the COLORS values inside
Rich markup like:  f"[{COLORS['clay']}]text[/]".
"""

from __future__ import annotations

COLORS = {
    "bg": "#211f1d",        # warm charcoal
    "panel": "#2a2724",     # card surface
    "panel_hi": "#2c2926",  # palette / raised
    "border": "#3d3934",
    "border_hi": "#4a443d",
    "fg": "#e3ddd0",        # warm bone
    "dim": "#9b9285",       # warm gray
    "clay": "#c8775c",      # accent — terracotta
    "clay_hi": "#d4805e",   # accent — keys/highlights
    "title": "#cf9477",     # soft clay (card titles)
    "sage": "#9fa67c",      # muted positive
    "tan": "#c2a878",       # muted counts
    "taupe": "#b98f73",     # muted secondary
    "warn": "#d08a5a",      # gentle warning (no red)
}

# Textual CSS (TCSS). Hex literals keep the palette stable across terminals.
APP_CSS = """
Screen {
    background: #211f1d;
    color: #e3ddd0;
    layout: vertical;
}

#modeline {
    height: 1;
    background: #2a2724;
    color: #9b9285;
    padding: 0 1;
}

#bento {
    height: 1fr;
    padding: 1 1;
    grid-size: 4 4;
    grid-columns: 1fr 1fr 1fr 1fr;
    grid-rows: 2fr 1fr 1fr 1fr;
    grid-gutter: 1 1;
}

Card {
    background: #2a2724;
    border: round #3d3934;
    padding: 0 1;
    height: 100%;
}
Card:focus { border: round #c8775c; }

Card.hero      { column-span: 4; }
Card.finances  { column-span: 1; }
Card.tasks     { column-span: 1; }
Card.learning  { column-span: 1; }
Card.calendar  { column-span: 1; }
Card.coherence { column-span: 3; }
Card.signals   { column-span: 1; }
Card.skills    { column-span: 4; }

.card-title { color: #cf9477; text-style: bold; }
.muted { color: #9b9285; }

Footer { background: #2a2724; color: #9b9285; }

#palette {
    background: #2c2926;
    border: round #4a443d;
    width: 56;
    height: auto;
    padding: 1 1;
}
#palette-query { border: none; background: #211f1d; }
#palette-list { height: auto; max-height: 12; background: #2c2926; }

#cmd { height: 1; border: none; background: #211f1d; color: #e3ddd0; padding: 0 1; }
#cmd-out {
    height: auto;
    max-height: 8;
    background: #2a2724;
    color: #9b9285;
    border-top: round #3d3934;
    padding: 0 1;
    display: none;
}
"""
