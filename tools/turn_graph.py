#!/usr/bin/env python3
"""Re-stages the calendar in the 3D contribution graph for the profile README.

    python3 tools/turn_graph.py profile-3d-contrib/*.svg

github-profile-3d-contrib always draws a true isometric view: the scene
turned 45 degrees. This rewrites only the calendar:

  * it is turned to the camera angle in view.py, the one the name banner
    uses, by changing where each day sits and how its three faces shear;
  * the camera comes closer, with today pinned at the right edge. A year
    does not fit at that size, so the oldest weeks fade out past the left
    edge;
  * it is set at the height where no day and no tower touches the radar,
    the language ring, its legend or the totals. Those stay exactly where
    the generator put them. If the towers ever leave no such height, the
    calendar is drawn smaller, down to the size at which a year fits.

A file that does not look the way version 0.9.3 writes it is left as it
is, so a surprise in the input costs the new staging, never the image.
No dependencies.
"""
import math
import re
import sys
from pathlib import Path

from view import COS_PITCH, ground

# ---- how the generator lays the calendar out
STEP_X = 20.0  # one week moves right by this, one day moves left by it
STEP_Y = STEP_X * math.tan(math.radians(30))  # and both move down by this
RISE = 1.15  # page units per unit of block height
CELL = 20.0  # one day, tile plus seam
TILE = 18.0  # the tile itself

# ---- what else is on the page, where the generator puts it (page is 1280 x 850)
# things above the calendar, as (left, right, bottom)
ABOVE = [
    (800.0, 1160.0, 446.0),  # radar, down to its lower labels
    (755.0, 1205.0, 300.0),  # radar, its side labels
    (1040.0, 1270.0, 26.0),  # the date range
]
# things below it, as (left, right, top)
BELOW = [
    (335.0, 475.0, 596.0),  # language legend
    (310.0, 800.0, 800.0),  # totals
]
RING = (170.0, 650.0, 117.0)  # language ring: centre x, centre y, radius
CLEAR = 16.0  # the least gap to leave around all of them

# ---- how we lay the calendar out
SIZES = (28.0, 27.0, 26.0, 25.0, 24.0, 23.0, 22.2)  # true edge of one day, largest first
TODAY_X = 1252.0  # right end of the newest week
FADE = 180.0  # when the calendar runs off the left edge, it fades in over this much

DAY = re.compile(r'<g transform="translate\(([-\d.]+) ([-\d.]+)\)">(.*?)</g>', re.S)
FACE = {
    "top": re.compile(r'transform="[^"]*"(?= class="cont-top-)'),
    "left": re.compile(r'transform="[^"]*"(?= class="cont-left-)'),
    "right": re.compile(r'transform="[^"]*"(?= class="cont-right-)'),
}
BLOCK_HEIGHT = re.compile(r'height="([\d.]+)"[^>]*class="cont-left-')
GROW = re.compile(r'(<animateTransform[^>]*values=")[^"]*(")')
GROW_FROM = re.compile(r'attributeName="height" values="([\d.]+);')
CALENDAR = re.compile(r'<g>(?=<g transform="translate\([-\d.]+ [-\d.]+\)">)')


def n(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


FADE_DEFS = (
    f'<defs><linearGradient id="far" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{n(FADE)}" y2="0">'
    '<stop offset="0" stop-color="#000"/><stop offset="1" stop-color="#fff"/></linearGradient>'
    '<mask id="fade" maskUnits="userSpaceOnUse" x="-400" y="-400" width="2080" height="1650">'
    '<rect x="-400" y="-400" width="2080" height="1650" fill="url(#far)"/></mask></defs>'
)


class Camera:
    """The lattice for one size of day."""

    def __init__(self, size, weeks):
        k = size / CELL
        self.wx, self.wy = ground(1, 0, k)  # one unit along a week, toward the lower right
        self.dx, self.dy = ground(0, 1, k)  # one unit along a day, toward the reader
        self.rise = k * COS_PITCH
        self.ox = TODAY_X - weeks * CELL * self.wx  # far corner of the oldest week

    def spot(self, week, day):
        """Where a day's left corner sits, before the calendar's height is chosen."""
        return (
            self.ox + CELL * (week * self.wx + day * self.dx),
            CELL * (week * self.wy + day * self.dy),
        )

    def room(self, days):
        """(lowest, highest) the calendar may sit so that nothing touches a chart."""
        lowest, highest = -math.inf, math.inf
        for week, day, h in days:
            x, y = self.spot(week, day)
            left, right = x, x + TILE * (self.wx - self.dx)
            top = y - h * self.rise - TILE * self.dy  # back corner of the block's roof
            bottom = y + TILE * self.wy  # front corner of its foot
            for a, b, edge in ABOVE:
                if left < b and right > a:
                    lowest = max(lowest, edge + CLEAR - top)
            for a, b, edge in BELOW:
                if left < b and right > a:
                    highest = min(highest, edge - CLEAR - bottom)
            cx, cy, r = RING
            if left < cx + r and right > cx - r:
                nearest = min(max(cx, left), right)  # where the ring reaches highest under this block
                highest = min(highest, cy - math.sqrt(r * r - (nearest - cx) ** 2) - CLEAR - bottom)
        return lowest, highest


def turn(svg):
    """The same drawing with the calendar re-staged; None if it is not what we expect."""
    found = list(DAY.finditer(svg))
    if "skewY(" not in svg or len(found) < 300 or len(CALENDAR.findall(svg)) != 1:
        return None

    # 1. read every day off the generator's lattice
    read, first = [], None
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
        read.append((round(week), round(day), h))
    week0, day0 = min(d[0] for d in read), min(d[1] for d in read)
    days = [(week - week0, day - day0, h) for week, day, h in read]
    weeks = max(d[0] for d in days) + 1

    # 2. the largest size at which the calendar clears every chart
    for size in SIZES:
        cam = Camera(size, weeks)
        lowest, highest = cam.room(days)
        if lowest <= highest:
            break
    oy = (lowest + highest) / 2  # the same gap on both sides; if nothing fit, the same overlap

    # 3. move every day
    faces = {
        "top": f'transform="matrix({n(-cam.dx)} {n(-cam.dy)} {n(cam.wx)} {n(cam.wy)} 0 0)"',
        "left": f'transform="matrix({n(cam.wx)} {n(cam.wy)} 0 {n(cam.rise)} 0 0)"',
        "right": f'transform="matrix({n(-cam.dx)} {n(-cam.dy)} 0 {n(cam.rise)} {n(TILE * cam.wx)} {n(TILE * cam.wy)})"',
    }
    out, at = [], 0
    for m, (week, day, h) in zip(found, days):
        inner = m[3]
        gx, gy = cam.spot(week, day)
        gy += oy
        for name, rx in FACE.items():
            inner = rx.sub(faces[name], inner)
        start = GROW_FROM.search(inner)
        if start:  # the block grows on load: it rises from the floor height to its own
            h0 = float(start[1])
            inner = GROW.sub(
                lambda g: f"{g[1]}{n(gx)} {n(gy - h0 * cam.rise)};{n(gx)} {n(gy - h * cam.rise)}{g[2]}", inner
            )
        out += [svg[at : m.start()], f'<g transform="translate({n(gx)} {n(gy - h * cam.rise)})">{inner}</g>']
        at = m.end()
    svg = "".join(out) + svg[at:]

    # 4. if the oldest weeks run off the page, let them fade rather than stop dead
    if cam.spot(0, 7)[0] < 0:
        svg = svg.replace("</style>", "</style>" + FADE_DEFS, 1)
        svg = CALENDAR.sub('<g mask="url(#fade)">', svg)
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
