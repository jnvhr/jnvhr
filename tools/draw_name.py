#!/usr/bin/env python3
"""Draws the name banner at the top of the profile README.

    python3 tools/draw_name.py

"JNVHR" stands in green blocks on a slab, seen from the same angle and in
the same colours as the 3D contribution graph below it (the angle lives in
view.py). Writes assets/name-dark.svg and assets/name-light.svg.
No dependencies.
"""
from pathlib import Path

from view import COS_PITCH, ground

TEXT = "JNVHR"

# 5 x 7 letters, top row first
FONT = {
    "J": ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
}

EDGE = 22.0  # height of one block on the page
SIZE = EDGE / COS_PITCH  # its true edge, before the camera foreshortens it
LEVELS = 7  # blocks in a full-height stroke
SIDE, BETWEEN = 1, 2  # empty columns at each end and between letters
DEPTH, WALL = 3, 1  # slab rows, and the row the letters stand on
THICK = 9.0  # slab
SEAM = 0.06  # gap around each floor tile, in cells
PAD = 12.0

THEMES = {
    # floor and greens are GitHub's own contribution colours for each theme
    "dark": {"floor": "#21262d", "seam": "#161b22", "block": "#39d353", "glow": "#9cf5b0"},
    "light": {"floor": "#ebedf0", "seam": "#d1d9e0", "block": "#40c463", "glow": "#aaf0bb"},
}


def darker(colour, k):
    """The shading the contribution graph uses for the sides of a block."""
    f = 0.7**k
    r, g, b = (int(colour[i : i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % (round(r * f), round(g * f), round(b * f))


def n(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def pt(u, v, z=0.0):
    """Column u, row v, height z (already in page units) -> a point on the page."""
    x, y = ground(u, v, SIZE)
    return (x, y - z)


def poly(points):
    return "M" + "L".join(f"{n(x)} {n(y)}" for x, y in points) + "Z"


def layout():
    """Number of columns, and (column, level) for every block; level 0 is the floor."""
    blocks, col = [], SIDE
    for ch in TEXT:
        for r, row in enumerate(FONT[ch]):
            blocks += [(col + c, LEVELS - 1 - r) for c, bit in enumerate(row) if bit == "#"]
        col += 5 + BETWEEN
    return col - BETWEEN + SIDE, blocks


def draw(theme):
    t = THEMES[theme]
    cols, blocks = layout()
    left, top = pt(0, DEPTH)[0], pt(0, 0)[1] - LEVELS * EDGE
    w = pt(cols, 0)[0] - left + 2 * PAD
    h = pt(cols, DEPTH)[1] + THICK - top + 2 * PAD
    ox, oy = PAD - left, PAD - top

    s = SEAM
    tiles = "".join(
        poly([pt(c + s, r + s), pt(c + 1 - s, r + s), pt(c + 1 - s, r + 1 - s), pt(c + s, r + 1 - s)])
        for c in range(cols)
        for r in range(DEPTH)
    )
    slab = poly([pt(0, 0), pt(cols, 0), pt(cols, DEPTH), pt(0, DEPTH)])
    edge_left = poly([pt(0, DEPTH), pt(cols, DEPTH), pt(cols, DEPTH, -THICK), pt(0, DEPTH, -THICK)])
    edge_right = poly([pt(cols, DEPTH), pt(cols, 0), pt(cols, 0, -THICK), pt(cols, DEPTH, -THICK)])

    # one block, drawn once: the three faces you can see
    back, right, front, left = pt(0, 0), pt(1, 0), pt(1, 1), pt(0, 1)
    up = lambda p: (p[0], p[1] - EDGE)
    faces = {
        "l": poly([left, front, up(front), up(left)]),  # faces the reader
        "r": poly([front, right, up(right), up(front)]),
        "u": poly([up(back), up(right), up(front), up(left)]),
    }

    body = []
    # back to front, bottom to top, so nearer blocks cover the ones behind
    for c, k in sorted(blocks):
        x, y = pt(c, WALL, k * EDGE)
        drop = 0.2 + c * 0.05 + k * 0.035
        body.append(
            f'<g transform="translate({n(x)} {n(y)})"><g class="b" style="animation-delay:{n(drop)}s">'
            f'<use xlink:href="#l" class="l" style="animation-delay:{n(3.2 + c * 0.08)}s"/>'
            f'<use xlink:href="#r" class="r"/><use xlink:href="#u" class="u"/></g></g>'
        )

    line = darker(t["block"], 1.4)
    css = (
        f"use{{stroke:{line};stroke-width:.6;stroke-linejoin:round}}"
        f".l{{fill:{darker(t['block'], 0.5)};animation:glow 8s ease-in-out infinite}}"
        f".r{{fill:{darker(t['block'], 1)}}}.u{{fill:{t['block']}}}"
        f"@keyframes glow{{0%,10%,100%{{fill:{darker(t['block'], 0.5)}}}4%{{fill:{t['glow']}}}}}"
        ".b{animation:drop .7s cubic-bezier(.2,.9,.3,1) both}"
        f"@keyframes drop{{from{{opacity:0;transform:translateY({n(-2.2 * EDGE)}px)}}}}"
        "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'viewBox="0 0 {n(w)} {n(h)}" width="{n(w)}" height="{n(h)}" role="img" aria-label="jnvhr">'
        f"<title>jnvhr</title><style>{css}</style>"
        f'<defs>{"".join(f"""<path id="{k}" d="{d}"/>""" for k, d in faces.items())}</defs>'
        f'<g transform="translate({n(ox)} {n(oy)})">'
        f'<path d="{edge_left}" fill="{darker(t["floor"], 0.5)}"/>'
        f'<path d="{edge_right}" fill="{darker(t["floor"], 1)}"/>'
        f'<path d="{slab}" fill="{t["seam"]}"/>'
        f'<path d="{tiles}" fill="{t["floor"]}"/>'
        f'{"".join(body)}</g></svg>\n'
    )


def main():
    out = Path(__file__).resolve().parent.parent / "assets"
    out.mkdir(exist_ok=True)
    for theme in THEMES:
        data = draw(theme)
        (out / f"name-{theme}.svg").write_text(data, encoding="utf-8")
        print(f"name-{theme}.svg  {len(data) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
