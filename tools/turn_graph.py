#!/usr/bin/env python3
"""Turns the 3D contribution graph to the camera angle in view.py.

    python3 tools/turn_graph.py profile-3d-contrib/*.svg

github-profile-3d-contrib always draws a true isometric view: the scene
turned 45 degrees. This rewrites where each day sits and how its three
faces are sheared, so the graph is seen from the same angle as the name
banner. The radar, the language ring and the totals are not touched.

A file that does not look the way version 0.9.3 writes it is left as it
is, so a surprise in the input costs the new angle, never the image.
No dependencies.
"""
import math
import re
import sys
from pathlib import Path

from view import COS_PITCH, ground

# how the generator lays the calendar out
STEP_X = 20.0  # one week moves right by this, one day moves left by it
STEP_Y = STEP_X * math.tan(math.radians(30))  # and both move down by this
RISE = 1.15  # page units per unit of block height
CELL = 20.0  # one day, tile plus seam; the tile itself is 18

# how it is laid out after the turn
SIZE = 22.2  # true edge of one day, sized so 53 weeks still fit the page
FAR_CORNER = (142.0, 268.0)  # where the first day lands

DAY = re.compile(r'<g transform="translate\(([-\d.]+) ([-\d.]+)\)">(.*?)</g>', re.S)
FACE = {
    "top": re.compile(r'transform="[^"]*"(?= class="cont-top-)'),
    "left": re.compile(r'transform="[^"]*"(?= class="cont-left-)'),
    "right": re.compile(r'transform="[^"]*"(?= class="cont-right-)'),
}
HEIGHT = re.compile(r'height="([\d.]+)"[^>]*class="cont-left-')
GROW = re.compile(r'(<animateTransform[^>]*values=")[^"]*(")')
GROW_FROM = re.compile(r'attributeName="height" values="([\d.]+);')


def n(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def turn(svg):
    """The same drawing seen from the new angle, or None if it is not what we expect."""
    days = list(DAY.finditer(svg))
    if "skewY(" not in svg or len(days) < 300:
        return None

    k = SIZE / CELL
    wx, wy = ground(1, 0, k)  # one unit along a week, toward the lower right
    dx, dy = ground(0, 1, k)  # one unit along a day, toward the reader
    rise = k * COS_PITCH
    faces = {
        "top": f'transform="matrix({n(-dx)} {n(-dy)} {n(wx)} {n(wy)} 0 0)"',
        "left": f'transform="matrix({n(wx)} {n(wy)} 0 {n(rise)} 0 0)"',
        "right": f'transform="matrix({n(-dx)} {n(-dy)} 0 {n(rise)} {n(18 * wx)} {n(18 * wy)})"',
    }

    out, at, first = [], 0, None
    for m in days:
        x, y, inner = float(m[1]), float(m[2]), m[3]
        height = HEIGHT.search(inner)
        if not height or any(len(rx.findall(inner)) != 1 for rx in FACE.values()):
            return None
        h = float(height[1])
        floor = y + h * RISE  # where the block meets the lattice
        first = first or (x, floor)
        along, across = (floor - first[1]) / STEP_Y, (x - first[0]) / STEP_X
        week, day = (along + across) / 2, (along - across) / 2
        if abs(week - round(week)) > 0.05 or abs(day - round(day)) > 0.05:
            return None

        gx = FAR_CORNER[0] + CELL * (week * wx + day * dx)
        gy = FAR_CORNER[1] + CELL * (week * wy + day * dy)
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
    return "".join(out) + svg[at:]


def main():
    for name in sys.argv[1:]:
        path = Path(name)
        turned = turn(path.read_text(encoding="utf-8"))
        if turned is None:
            print(f"{name}: left as it is (already turned, or not the expected drawing)")
        else:
            path.write_text(turned, encoding="utf-8")
            print(f"{name}: turned")


if __name__ == "__main__":
    main()
