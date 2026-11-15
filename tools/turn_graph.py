#!/usr/bin/env python3
"""Re-stages the 3D contribution graph for the profile README.

    python3 tools/turn_graph.py profile-3d-contrib/*.svg

github-profile-3d-contrib always draws a true isometric view (the scene
turned 45 degrees) with its charts tucked around the calendar. This:

  * turns the calendar to the camera angle in view.py, the one the name
    banner uses, by rewriting where each day sits and how its faces shear;
  * brings the camera closer, with today anchored at the right edge. A year
    no longer fits at this size, so the oldest weeks fade out past the left
    edge;
  * moves the radar, the language ring and the totals below the calendar,
    where the towers, which only grow upward, can never reach them.

A file that does not look the way version 0.9.3 writes it is left as it
is, so a surprise in the input costs the new staging, never the image.
No dependencies.
"""
import math
import re
import sys
from pathlib import Path

from view import COS_PITCH, ground

# ---- how the generator lays things out
STEP_X = 20.0  # one week moves right by this, one day moves left by it
STEP_Y = STEP_X * math.tan(math.radians(30))  # and both move down by this
RISE = 1.15  # page units per unit of block height
CELL = 20.0  # one day, tile plus seam; the tile itself is 18
PAGE = (1280, 850)

# ---- how we lay them out
SIZE = 28.0  # true edge of one day; 22.2 would fit the whole year
TODAY = (1252.0, 397.0)  # far corner of the newest week
FADE = 180.0  # the calendar fades in over this much of the left edge
HEIGHT = 650  # of the page
CHARTS = 0.9  # the radar and the ring are drawn a little smaller
RADAR = (225.0, 478.0)  # centre
RING = (533.0, 383.0)  # top left of the ring and its legend
TOTALS = (445.0, 622.0)  # shift right, and the new baseline

DAY = re.compile(r'<g transform="translate\(([-\d.]+) ([-\d.]+)\)">(.*?)</g>', re.S)
FACE = {
    "top": re.compile(r'transform="[^"]*"(?= class="cont-top-)'),
    "left": re.compile(r'transform="[^"]*"(?= class="cont-left-)'),
    "right": re.compile(r'transform="[^"]*"(?= class="cont-right-)'),
}
BLOCK_HEIGHT = re.compile(r'height="([\d.]+)"[^>]*class="cont-left-')
GROW = re.compile(r'(<animateTransform[^>]*values=")[^"]*(")')
GROW_FROM = re.compile(r'attributeName="height" values="([\d.]+);')


def n(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


FADE_DEFS = (
    f'<defs><linearGradient id="far" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{n(FADE)}" y2="0">'
    '<stop offset="0" stop-color="#000"/><stop offset="1" stop-color="#fff"/></linearGradient>'
    f'<mask id="fade" maskUnits="userSpaceOnUse" x="-400" y="-400" width="{PAGE[0] + 800}" height="{PAGE[1] + 800}">'
    f'<rect x="-400" y="-400" width="{PAGE[0] + 800}" height="{PAGE[1] + 800}" fill="url(#far)"/></mask></defs>'
)

# everything besides the calendar: (pattern, how many times it must appear, replacement)
STAGE = [
    (rf'width="{PAGE[0]}" height="{PAGE[1]}" viewBox="0 0 {PAGE[0]} {PAGE[1]}"', 1,
     lambda m: f'width="{PAGE[0]}" height="{HEIGHT}" viewBox="0 0 {PAGE[0]} {HEIGHT}"'),
    (rf'(<rect x="0" y="0" width="{PAGE[0]}" height="){PAGE[1]}(" class="fill-bg">)', 1,
     lambda m: f"{m[1]}{HEIGHT}{m[2]}"),
    (r"</style>", 1, lambda m: "</style>" + FADE_DEFS),
    (r'<g>(?=<g transform="translate\([-\d.]+ [-\d.]+\)">)', 1, lambda m: '<g mask="url(#fade)">'),
    (r'<g transform="translate\(980, 284\.5\)">', 1,
     lambda m: f'<g transform="translate({n(RADAR[0])}, {n(RADAR[1])}) scale({CHARTS})">'),
    (r'<g transform="translate\(40, 520\)">', 1,
     lambda m: f'<g transform="translate({n(RING[0])}, {n(RING[1])}) scale({CHARTS})">'),
    (r'(<text [^>]*? x=")([\d.]+)(" y=")830(")', 4,
     lambda m: f"{m[1]}{n(float(m[2]) + TOTALS[0])}{m[3]}{n(TOTALS[1])}{m[4]}"),
    (r'(<g transform="translate\()([\d.]+), 802(\), scale\(2\)">)', 2,
     lambda m: f"{m[1]}{n(float(m[2]) + TOTALS[0])}, {n(TOTALS[1] - 28)}{m[3]}"),
]


def turn(svg):
    """The same drawing, re-staged; None if it is not what we expect."""
    found = list(DAY.finditer(svg))
    if "skewY(" not in svg or len(found) < 300:
        return None
    if any(len(re.findall(pattern, svg)) != count for pattern, count, _ in STAGE):
        return None

    # 1. read every day off the generator's lattice
    days, first = [], None
    for m in found:
        x, y, inner = float(m[1]), float(m[2]), m[3]
        height = BLOCK_HEIGHT.search(inner)
        if not height or any(len(rx.findall(inner)) != 1 for rx in FACE.values()):
            return None
        h = float(height[1])
        floor = y + h * RISE  # where the block meets the lattice
        first = first or (x, floor)
        along, across = (floor - first[1]) / STEP_Y, (x - first[0]) / STEP_X
        week, day = (along + across) / 2, (along - across) / 2
        if abs(week - round(week)) > 0.05 or abs(day - round(day)) > 0.05:
            return None
        days.append((m, round(week), round(day), h))
    week0 = min(d[1] for d in days)
    day0 = min(d[2] for d in days)
    weeks = max(d[1] for d in days) - week0 + 1

    # 2. the new lattice, with the newest week's far corner pinned at TODAY
    k = SIZE / CELL
    wx, wy = ground(1, 0, k)  # one unit along a week, toward the lower right
    dx, dy = ground(0, 1, k)  # one unit along a day, toward the reader
    rise = k * COS_PITCH
    ox, oy = TODAY[0] - weeks * CELL * wx, TODAY[1] - weeks * CELL * wy
    faces = {
        "top": f'transform="matrix({n(-dx)} {n(-dy)} {n(wx)} {n(wy)} 0 0)"',
        "left": f'transform="matrix({n(wx)} {n(wy)} 0 {n(rise)} 0 0)"',
        "right": f'transform="matrix({n(-dx)} {n(-dy)} 0 {n(rise)} {n(18 * wx)} {n(18 * wy)})"',
    }

    out, at = [], 0
    for m, week, day, h in days:
        week, day, inner = week - week0, day - day0, m[3]
        gx = ox + CELL * (week * wx + day * dx)
        gy = oy + CELL * (week * wy + day * dy)
        for name, rx in FACE.items():
            inner = rx.sub(faces[name], inner)
        start = GROW_FROM.search(inner)
        if start:  # the block grows on load: it rises from the floor height to its own
            h0 = float(start[1])
            inner = GROW.sub(
                lambda g: f"{g[1]}{n(gx)} {n(gy - h0 * rise)};{n(gx)} {n(gy - h * rise)}{g[2]}", inner
            )
        out += [svg[at : m.start()], f'<g transform="translate({n(gx)} {n(gy - h * rise)})">{inner}</g>']
        at = m.end()
    svg = "".join(out) + svg[at:]

    # 3. everything around it
    for pattern, _, new in STAGE:
        svg = re.sub(pattern, new, svg)
    return svg


def main():
    for name in sys.argv[1:]:
        path = Path(name)
        staged = turn(path.read_text(encoding="utf-8"))
        if staged is None:
            print(f"{name}: left as it is (already staged, or not the expected drawing)")
        else:
            path.write_text(staged, encoding="utf-8")
            print(f"{name}: staged")


if __name__ == "__main__":
    main()
