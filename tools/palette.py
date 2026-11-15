#!/usr/bin/env python3
"""The colours of the profile: the P(doom) palette.

    python3 tools/palette.py      # writes .github/profile-3d-contrib.json

Every value in the first block is copied from the palette of the P(doom)
music video (jnvhr/im-upping-my-pdoom, src/mv/core.py): gold on obsidian
black. The name banner and the terminal import this file. The contribution
graph is drawn by an action that reads its colours from a settings file,
so running this writes that file. The link badges in README.md carry two
of these colours in their addresses (GRID and GOLD, without the #).
"""
import json
from pathlib import Path

# ---- the P(doom) palette
BG = "#0a0a0a"  # obsidian black
INK = "#f4f4f0"
GOLD = "#f5b420"
GOLD_DARK = "#785810"
GOLD_LIGHT = "#ffe28c"
GRID = "#262626"
GRID2 = "#3a3a38"
DIM = "#6e6e68"
PAPER = "#f5f3ef"
PAPER_GRID = "#d6d2c8"


def mix(a, b, t):
    """A colour t of the way from a to b."""
    pa, pb = (tuple(int(c[i : i + 2], 16) for i in (1, 3, 5)) for c in (a, b))
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(pa, pb))


def darker(colour, k):
    """The shading the contribution graph uses for the sides of a block."""
    f = 0.7**k
    return "#%02x%02x%02x" % tuple(round(int(colour[i : i + 2], 16) * f) for i in (1, 3, 5))


GOLD_MID = mix(GOLD_DARK, GOLD, 0.5)

# ---- what each colour is used for, per GitHub theme
# "page" is GitHub's own background; an image that should not show a box uses it
DARK = {
    "page": "#0d1117",
    "floor": GRID,
    "seam": mix(BG, GRID, 0.45),
    "block": GOLD,
    "glow": GOLD_LIGHT,
    "text": INK,
    "quiet": DIM,
    "number": GOLD,
    "radar": GOLD,
    # a day with no contributions, then four steps up to the busiest
    "levels": [GRID, mix(GRID, GOLD_DARK, 0.6), GOLD_DARK, GOLD_MID, GOLD],
}
LIGHT = {
    "page": "#ffffff",
    "floor": mix(PAPER, PAPER_GRID, 0.5),
    "seam": PAPER_GRID,
    "block": GOLD,
    "glow": GOLD_LIGHT,
    "text": BG,
    "quiet": DIM,
    "number": GOLD_DARK,
    "radar": GOLD_MID,
    # on paper the busiest day is the darkest gold
    "levels": [mix(PAPER, PAPER_GRID, 0.5), GOLD_LIGHT, GOLD, GOLD_MID, GOLD_DARK],
}
THEMES = {"dark": DARK, "light": LIGHT}

# the terminal is the same dark window in both themes
TERMINAL = {
    "card": BG,
    "edge": GRID2,
    "title": DIM,
    "prompt": GOLD,
    "typed": INK,
    "printed": mix(INK, DIM, 0.28),
    "listed": GOLD_LIGHT,
    "bar": GOLD,
    "track": GRID,
    "lights": (GOLD_DARK, GOLD, GOLD_LIGHT),
}


def graph_settings():
    """Settings for yoshi389111/github-profile-3d-contrib, one drawing per theme."""
    return [
        {
            "type": "normal",
            "fileName": f"profile-{name}.svg",
            "backgroundColor": t["page"],
            "foregroundColor": t["text"],
            "strongColor": t["number"],
            "weakColor": t["quiet"],
            "radarColor": t["radar"],
            "growingAnimation": True,
            "contribColors": t["levels"],
        }
        for name, t in THEMES.items()
    ]


def main():
    path = Path(__file__).resolve().parent.parent / ".github" / "profile-3d-contrib.json"
    path.write_text(json.dumps(graph_settings(), indent=2) + "\n", encoding="utf-8")
    print(f"{path.name}  written")


if __name__ == "__main__":
    main()
