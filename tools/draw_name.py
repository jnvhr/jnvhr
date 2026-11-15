#!/usr/bin/env python3
"""Draws the name banner at the top of the profile README.

    python3 tools/draw_name.py

"JNVHR" stands in gold blocks on a slab, seen from the same angle and in
the same colours as the 3D contribution graph below it. Around the name a
small story loops: a spark at the left flashes, a pulse of light runs along
the slab under the letters, and when it reaches the right end a rocket
lifts off. A new rocket then drops onto the pad. Idea to execution.

The angle lives in view.py and the colours in palette.py. Writes
assets/name-dark.svg and assets/name-light.svg. No dependencies.
"""
from pathlib import Path

from palette import THEMES, darker
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
# the two props, top row first. In the rocket: A accent, # hull, o window
SPARK = [".#.", "###", ".#."]
ROCKET = [".A.", "###", "#o#", "###", "A.A"]
FLAME = [".#.", ".#."]  # hangs below the rocket, lit only in flight
SPARK_FLOATS = 2  # levels of air under the spark

EDGE = 22.0  # height of one block on the page
SIZE = EDGE / COS_PITCH  # its true edge, before the camera foreshortens it
LEVELS = 7  # blocks in a full-height stroke
SIDE, BETWEEN, APART = 1, 2, 2  # empty columns: at each end, between letters, between name and props
DEPTH, WALL, TRACK = 3, 1, 2  # slab rows; the row the blocks stand on; the row the pulse runs along
THICK = 9.0  # slab
SEAM = 0.06  # gap around each floor tile, in cells
PAD = 12.0

# the loop, in seconds
INTRO = 3.0  # the name builds itself first
LOOP = 10.0
SPARK_AT = 0.5  # the spark flashes
STEP = 0.06  # the pulse takes this long per column
FLIGHT = 300.0  # how far the rocket climbs, in page units


def n(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def pt(u, v, z=0.0):
    """Column u, row v, height z (already in page units) -> a point on the page."""
    x, y = ground(u, v, SIZE)
    return (x, y - z)


def poly(points):
    return "M" + "L".join(f"{n(x)} {n(y)}" for x, y in points) + "Z"


def stamp(art, col, floor=0):
    """(column, level, character) for every filled cell of a small picture."""
    return [
        (col + c, floor + len(art) - 1 - r, ch)
        for r, row in enumerate(art)
        for c, ch in enumerate(row)
        if ch != "."
    ]


def layout():
    """Where everything stands: column count, then the spark, the name, the rocket and its flame."""
    col = SIDE
    spark = stamp(SPARK, col, SPARK_FLOATS)
    col += len(SPARK[0]) + APART
    name = []
    for ch in TEXT:
        name += stamp(FONT[ch], col)
        col += 5 + BETWEEN
    col += APART - BETWEEN
    rocket = stamp(ROCKET, col)
    flame = stamp(FLAME, col, -len(FLAME))
    pad = col + len(ROCKET[0]) // 2  # the column the pulse stops at
    return col + len(ROCKET[0]) + SIDE, spark, name, rocket, flame, pad


def draw(theme):
    t = THEMES[theme]
    cols, spark, name, rocket, flame, pad = layout()
    left, top = pt(0, DEPTH)[0], pt(0, 0)[1] - LEVELS * EDGE
    w = pt(cols, 0)[0] - left + 2 * PAD
    h = pt(cols, DEPTH)[1] + THICK - top + 2 * PAD
    ox, oy = PAD - left, PAD - top

    s = SEAM
    tile = lambda c, r: poly([pt(c + s, r + s), pt(c + 1 - s, r + s), pt(c + 1 - s, r + 1 - s), pt(c + s, r + 1 - s)])
    tiles = "".join(tile(c, r) for c in range(cols) for r in range(DEPTH) if r != TRACK)
    slab = poly([pt(0, 0), pt(cols, 0), pt(cols, DEPTH), pt(0, DEPTH)])
    edge_left = poly([pt(0, DEPTH), pt(cols, DEPTH), pt(cols, DEPTH, -THICK), pt(0, DEPTH, -THICK)])
    edge_right = poly([pt(cols, DEPTH), pt(cols, 0), pt(cols, 0, -THICK), pt(cols, DEPTH, -THICK)])

    # when the pulse passes a column, counted from the start of a loop
    passes = lambda c: SPARK_AT + max(0, c - SIDE - 1) * STEP
    lands = passes(pad)  # ... and when it reaches the rocket
    pc = lambda seconds: n(100 * seconds / LOOP)  # a moment in the loop, as a keyframe percentage

    # the track: one tile per column, each lit as the pulse goes by
    track = "".join(
        f'<path class="p" style="animation-delay:{n(INTRO + passes(c))}s" d="{tile(c, TRACK)}"/>'
        for c in range(SIDE, pad + 1)
    ) + f'<path fill="{t["floor"]}" d="{"".join(tile(c, TRACK) for c in list(range(SIDE)) + list(range(pad + 1, cols)))}"/>'

    # one block, drawn once: the three faces you can see
    back, right, front, left_ = pt(0, 0), pt(1, 0), pt(1, 1), pt(0, 1)
    up = lambda p: (p[0], p[1] - EDGE)
    faces = {
        "l": poly([left_, front, up(front), up(left_)]),  # faces the reader
        "r": poly([front, right, up(right), up(front)]),
        "u": poly([up(back), up(right), up(front), up(left_)]),
    }

    def block(c, k, kind, drop=None, lit=None):
        """One block at column c, level k. kind picks its colours."""
        x, y = pt(c, WALL, k * EDGE)
        fall = f' class="b" style="animation-delay:{n(drop)}s"' if drop is not None else ""
        glow = f' style="animation-delay:{n(lit)}s"' if lit is not None else ""
        return (
            f'<g transform="translate({n(x)} {n(y)})"><g{fall}>'
            f'<use xlink:href="#l" class="{kind}l"{glow}/><use xlink:href="#r" class="{kind}r"/>'
            f'<use xlink:href="#u" class="{kind}u"/></g></g>'
        )

    # back to front, bottom to top, so nearer blocks cover the ones behind
    order = lambda cells: sorted(cells, key=lambda cell: (cell[0], cell[1]))
    drop = lambda c, k: 0.2 + c * 0.045 + max(k, 0) * 0.035
    the_spark = "".join(block(c, k, "s", drop(c, k)) for c, k, _ in order(spark))
    the_name = "".join(block(c, k, "n", drop(c, k), INTRO + passes(c)) for c, k, _ in order(name))
    kinds = {"#": "h", "A": "n", "o": "s"}
    the_rocket = "".join(block(c, k, kinds[ch], drop(c, k)) for c, k, ch in order(rocket))
    the_flame = "".join(block(c, k, "s") for c, k, _ in order(flame))

    gold, sp, hull = t["block"], t["spark"], t["rocket"]
    shade = lambda kind, colour: (
        f".{kind}l{{fill:{darker(colour, 0.5)}}}.{kind}r{{fill:{darker(colour, 1)}}}.{kind}u{{fill:{colour}}}"
    )
    off, climb, gone = lands + 0.15, lands + 2.0, lands + 2.3  # lift-off, top of the climb, faded out
    back_at, down_at = LOOP - 1.8, LOOP - 0.9  # the next rocket appears, and lands
    css = (
        "use{stroke:#000;stroke-opacity:.34;stroke-width:.6;stroke-linejoin:round}"
        + shade("n", gold) + shade("s", sp) + shade("h", hull)
        # the name builds itself once
        + ".b{animation:drop .7s cubic-bezier(.2,.9,.3,1) backwards}"
        f"@keyframes drop{{from{{opacity:0;transform:translateY({n(-2.2 * EDGE)}px)}}}}"
        # the pulse: along the track, and up the letters it passes
        f".p{{fill:{t['floor']};animation:pulse {LOOP}s linear infinite}}"
        f"@keyframes pulse{{0%,9%,100%{{fill:{t['floor']}}}.6%{{fill:{sp}}}3.5%{{fill:{gold}}}}}"
        f".nl{{animation:lit {LOOP}s ease-in-out infinite}}"
        f"@keyframes lit{{0%,9%,100%{{fill:{darker(gold, 0.5)}}}3%{{fill:{t['glow']}}}}}"
        # the spark hovers, and flares when it fires
        ".hover{animation:hover 2.6s ease-in-out infinite alternate}@keyframes hover{to{transform:translateY(-7px)}}"
        f".flare{{animation:flare {LOOP}s ease-out {n(INTRO)}s infinite}}"
        f"@keyframes flare{{0%,{pc(SPARK_AT - 0.35)}%,{pc(SPARK_AT + 0.9)}%,100%{{opacity:1}}{pc(SPARK_AT)}%{{opacity:.25}}{pc(SPARK_AT + 0.12)}%{{opacity:1}}}}"
        # the rocket: waits, lifts off when the pulse lands, and a new one drops onto the pad
        f".fly{{animation:fly {LOOP}s linear {n(INTRO)}s infinite}}"
        f"@keyframes fly{{0%,{pc(off)}%{{transform:translateY(0);opacity:1;animation-timing-function:cubic-bezier(.55,0,.9,.45)}}"
        f"{pc(climb)}%{{transform:translateY({n(-FLIGHT)}px);opacity:1}}"
        f"{pc(gone)}%{{transform:translateY({n(-FLIGHT * 1.12)}px);opacity:0}}"
        f"{pc(back_at)}%{{transform:translateY({n(-3 * EDGE)}px);opacity:0;animation-timing-function:cubic-bezier(.2,.9,.3,1)}}"
        f"{pc(down_at)}%,100%{{transform:translateY(0);opacity:1}}}}"
        f".burn{{animation:burn {LOOP}s steps(1) {n(INTRO)}s infinite}}"
        f"@keyframes burn{{0%{{opacity:0}}{pc(lands)}%{{opacity:1}}{pc(gone)}%,100%{{opacity:0}}}}"
        ".flick{animation:flick .13s steps(1) infinite}@keyframes flick{50%{opacity:.55}}"
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
        f'<path d="{tiles}" fill="{t["floor"]}"/>{track}'
        f'<g class="hover"><g class="flare">{the_spark}</g></g>'
        f"{the_name}"
        f'<g class="fly"><g class="burn" opacity="0"><g class="flick">{the_flame}</g></g>{the_rocket}</g>'
        "</g></svg>\n"
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
