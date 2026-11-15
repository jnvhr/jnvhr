#!/usr/bin/env python3
"""Draws the animated header of the profile README: the name banner and the terminal under it.

    python3 tools/draw_hero.py

The story, which begins when the terminal has typed its last command:

  idea      the spark comes down and rests on the slab
  building  a line of light runs from the tile it touched to the rocket,
            and the terminal's bar fills in step with it
  shipped   the rocket lifts off, leaves the picture, and comes back down

When the rocket has landed the bar clears and the loop starts again.

Writes four pictures into assets/:

  banner-dark.svg, banner-light.svg       the README picks one by the reader's theme
  terminal-wide.svg, terminal-narrow.svg  ... and one by the width of the page

The banner and the terminal are separate files, so each runs on its own
clock. They stay in step because the README loads them together and both
follow the one story timed here; every terminal layout enters its last
command at the same moment, so one banner serves them all. Do not merge them
into one file shown as two views (hero.svg#banner, hero.svg#terminal) to
share a clock: Safari gives such an <img> the shape of the whole file.

The angle lives in view.py and the colours in palette.py. No dependencies:
the terminal's text is set in whatever monospace font the reader's system has.
"""
from html import escape
from pathlib import Path

from palette import TERMINAL, THEMES, darker
from view import COS_PITCH, ground

# ------------------------------------------------------------------ the banner

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
DEPTH, WALL, TRACK = 3, 1, 2  # slab rows; the row the blocks stand on; the row the line runs along
THICK = 9.0  # slab
SEAM = 0.06  # gap around each floor tile, in cells
PAD = 12.0

# ------------------------------------------------------------------ the terminal

ABOUT = ["I don't keep a list of ideas.", "I keep a list of things I built."]
BUILT = ["browser-tools/", "native-mac-app/", "encrypted-chat/", "music-video.py"]
COMMANDS = {"about": "cat about.txt", "built": "ls built/", "next": "idea --next | build | ship"}
STAGES = ("idea", "building", "shipped")  # what the bar says in each act of the story
PROMPT = "~ $ "
TITLE = "jnvhr"

LAYOUTS = {
    # sentences per line, listing entries per row, cells in the progress bar
    "wide": {"font": 20.0, "about": 2, "built": 4, "bar": 44},
    "narrow": {"font": 18.0, "about": 1, "built": 2, "bar": 18},
}
GUTTER = 3  # characters between two columns of a listing
KEY = 0.05  # seconds per keystroke
PAUSE = 0.8  # between a command's output and the next prompt

# ------------------------------------------------------------------ the story, in seconds

LOOP = 10.0
SPARK_AT = 0.9  # the spark touches the slab, this long into a loop
REST = 0.55  # ... and stays on it this long
LINE_AFTER = 0.25  # the line leaves this long after the touch
STEP = 0.055  # the line takes this long per tile
CLIMB = 1.9  # lift-off to out of the picture
AWAY = 1.4  # out of sight
DESCENT = 2.2  # back in at the top, down to the pad
LEAD = 0.2  # the first loop starts this long before the last key of the last command


def n(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def chunks(items, size):
    return [items[i : i + size] for i in range(0, len(items), size)]


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


def scene():
    """Where everything on the slab stands, and the times of the story within one loop."""
    col = SIDE
    spark = stamp(SPARK, col, SPARK_FLOATS)
    touch = col + len(SPARK[0]) // 2  # the column whose tile the spark comes down on
    col += len(SPARK[0]) + APART
    name = []
    for ch in TEXT:
        name += stamp(FONT[ch], col)
        col += 5 + BETWEEN
    col += APART - BETWEEN
    rocket = stamp(ROCKET, col)
    flame = stamp(FLAME, col, -len(FLAME))
    pad = col + len(ROCKET[0]) // 2  # the column the line ends at
    cols = col + len(ROCKET[0]) + SIDE

    line_at = SPARK_AT + LINE_AFTER
    passes = lambda c: line_at + max(0, c - touch) * STEP  # when the line passes a column
    lands = passes(pad) + STEP  # ... and reaches the tile under the rocket
    off = lands + 0.15  # lift-off
    out = off + CLIMB  # the last of the flame leaves the picture
    back = out + AWAY  # the nose comes back in
    down = back + DESCENT  # touchdown
    assert down < LOOP - 0.6, "the flight does not fit in one loop"
    return {
        "cols": cols, "spark": spark, "name": name, "rocket": rocket, "flame": flame,
        "touch": touch, "pad": pad, "line_at": line_at, "passes": passes, "lands": lands,
        "off": off, "out": out, "back": back, "down": down,
    }


def pc(seconds):
    """A moment in the loop, as a keyframe percentage."""
    return n(100 * seconds / LOOP)


def theme_css(name):
    """One theme's colours for the banner, as variables."""
    t = THEMES[name]
    return (
        f":root{{--floor:{t['floor']};--seam:{t['seam']};--e1:{darker(t['floor'], 0.5)};--e2:{darker(t['floor'], 1)};"
        f"--n:{t['block']};--n1:{darker(t['block'], 0.5)};--n2:{darker(t['block'], 1)};"
        f"--s:{t['spark']};--s1:{darker(t['spark'], 0.5)};--s2:{darker(t['spark'], 1)};"
        f"--h:{t['rocket']};--h1:{darker(t['rocket'], 0.5)};--h2:{darker(t['rocket'], 1)};--glow:{t['glow']}}}"
    )


def banner(sc, start):
    """The name on its slab: (markup, css, width, height). `start` is when the first loop begins."""
    cols, touch, pad, passes = sc["cols"], sc["touch"], sc["pad"], sc["passes"]
    left, top = pt(0, DEPTH)[0], pt(0, 0)[1] - LEVELS * EDGE
    w = pt(cols, 0)[0] - left + 2 * PAD
    h = pt(cols, DEPTH)[1] + THICK - top + 2 * PAD
    ox, oy = PAD - left, PAD - top

    s = SEAM
    tile = lambda c, r: poly([pt(c + s, r + s), pt(c + 1 - s, r + s), pt(c + 1 - s, r + 1 - s), pt(c + s, r + 1 - s)])
    lit = [(c, TRACK) for c in range(touch, pad + 1)] + [(pad, WALL)]  # the tiles the line lights, in order
    tiles = "".join(tile(c, r) for c in range(cols) for r in range(DEPTH) if (c, r) not in lit)
    slab = poly([pt(0, 0), pt(cols, 0), pt(cols, DEPTH), pt(0, DEPTH)])
    edge_left = poly([pt(0, DEPTH), pt(cols, DEPTH), pt(cols, DEPTH, -THICK), pt(0, DEPTH, -THICK)])
    edge_right = poly([pt(cols, DEPTH), pt(cols, 0), pt(cols, 0, -THICK), pt(cols, DEPTH, -THICK)])

    # the line: the tile the spark touches, the track in front of the letters, then in under the rocket
    track = f'<path class="p0" d="{tile(*lit[0])}"/>' + "".join(
        f'<path class="p" style="animation-delay:{n(start + (sc["lands"] if cell == lit[-1] else passes(cell[0])))}s" d="{tile(*cell)}"/>'
        for cell in lit[1:]
    )

    # one block, drawn once: the three faces you can see
    back, right, front, left_ = pt(0, 0), pt(1, 0), pt(1, 1), pt(0, 1)
    up = lambda p: (p[0], p[1] - EDGE)
    faces = {
        "l": poly([left_, front, up(front), up(left_)]),  # faces the reader
        "r": poly([front, right, up(right), up(front)]),
        "u": poly([up(back), up(right), up(front), up(left_)]),
    }

    def block(c, k, kind, drop=None, lit_at=None, row=WALL):
        """One block at column c, level k. kind picks its colours."""
        x, y = pt(c, row, k * EDGE)
        fall = f' class="b" style="animation-delay:{n(drop)}s"' if drop is not None else ""
        glow = f' style="animation-delay:{n(lit_at)}s"' if lit_at is not None else ""
        return (
            f'<g transform="translate({n(x)} {n(y)})"><g{fall}>'
            f'<use xlink:href="#l" class="{kind}l"{glow}/><use xlink:href="#r" class="{kind}r"/>'
            f'<use xlink:href="#u" class="{kind}u"/></g></g>'
        )

    # back to front, bottom to top, so nearer blocks cover the ones behind
    order = lambda cells: sorted(cells, key=lambda cell: (cell[0], cell[1]))
    drop = lambda c, k: 0.2 + c * 0.045 + max(k, 0) * 0.035
    the_spark = "".join(block(c, k, "s", drop(c, k), row=TRACK) for c, k, _ in order(sc["spark"]))
    the_name = "".join(block(c, k, "n", drop(c, k), start + passes(c)) for c, k, _ in order(sc["name"]))
    kinds = {"#": "h", "A": "n", "o": "s"}
    the_rocket = "".join(block(c, k, kinds[ch], drop(c, k)) for c, k, ch in order(sc["rocket"]))
    the_flame = "".join(block(c, k, "s") for c, k, _ in order(sc["flame"]))

    reach = SPARK_FLOATS * EDGE  # how far the spark comes down to touch the slab
    # the rocket never fades: it flies out past the top of the picture and back in again
    foot = oy + pt(pad + 2, WALL + 1)[1] + len(FLAME) * EDGE  # lowest point of rocket and flame, on the page
    flight = foot + 12
    line_at, lands, off, out, back_in, down = (sc[k] for k in ("line_at", "lands", "off", "out", "back", "down"))
    shade = lambda kind: f".{kind}l{{fill:var(--{kind}1)}}.{kind}r{{fill:var(--{kind}2)}}.{kind}u{{fill:var(--{kind})}}"
    css = (
        "use{stroke:#000;stroke-opacity:.34;stroke-width:.6;stroke-linejoin:round}"
        ".fl{fill:var(--floor)}.sm{fill:var(--seam)}.e1{fill:var(--e1)}.e2{fill:var(--e2)}"
        + shade("n") + shade("s") + shade("h")
        # the name builds itself once
        + ".b{animation:drop .7s cubic-bezier(.2,.9,.3,1) backwards}"
        f"@keyframes drop{{from{{opacity:0;transform:translateY({n(-2.2 * EDGE)}px)}}}}"
        # the line: along the track, and up the letters it passes
        f".p{{fill:var(--floor);animation:pulse {LOOP}s linear infinite}}"
        "@keyframes pulse{0%,9%,100%{fill:var(--floor)}.6%{fill:var(--s)}3.5%{fill:var(--n)}}"
        # the tile the spark touches lights on contact and stays lit until the line has left it
        f".p0{{fill:var(--floor);animation:touch {LOOP}s linear {n(start)}s infinite}}"
        f"@keyframes touch{{0%,{pc(SPARK_AT - 0.02)}%,{pc(line_at + 0.9)}%,100%{{fill:var(--floor)}}"
        f"{pc(SPARK_AT)}%,{pc(line_at)}%{{fill:var(--s)}}{pc(line_at + 0.35)}%{{fill:var(--n)}}}}"
        f".nl{{animation:lit {LOOP}s ease-in-out infinite}}"
        "@keyframes lit{0%,9%,100%{fill:var(--n1)}3%{fill:var(--glow)}}"
        # the spark: winds up, comes down, rests on the slab while the line leaves, springs back, then drifts
        f".tap{{animation:tap {LOOP}s ease-in-out {n(start)}s infinite}}"
        "@keyframes tap{0%,100%{transform:translateY(0)}"
        f"{pc(SPARK_AT - 0.6)}%{{transform:translateY(-6px);animation-timing-function:cubic-bezier(.55,0,.85,.6)}}"
        f"{pc(SPARK_AT)}%{{transform:translateY({n(reach)}px);animation-timing-function:linear}}"
        f"{pc(SPARK_AT + REST)}%{{transform:translateY({n(reach)}px);animation-timing-function:cubic-bezier(.2,.8,.3,1)}}"
        f"{pc(SPARK_AT + REST + 0.7)}%{{transform:translateY(-7px)}}"
        "40%,76%{transform:translateY(0)}58%,90%{transform:translateY(-7px)}}"
        # the rocket: waits, lifts off when the line lands, and lands again, braking as it comes down
        f".fly{{animation:fly {LOOP}s linear {n(start)}s infinite}}"
        f"@keyframes fly{{0%,{pc(off)}%{{transform:translateY(0);animation-timing-function:cubic-bezier(.55,0,.9,.45)}}"
        f"{pc(out)}%,{pc(back_in)}%{{transform:translateY({n(-flight)}px);animation-timing-function:cubic-bezier(.12,.5,.3,1)}}"
        f"{pc(down)}%,100%{{transform:translateY(0)}}}}"
        # its flame burns from ignition to touchdown
        f".burn{{animation:burn {LOOP}s steps(1) {n(start)}s infinite}}"
        f"@keyframes burn{{0%{{opacity:0}}{pc(lands)}%{{opacity:1}}{pc(down)}%,100%{{opacity:0}}}}"
        ".flick{animation:flick .13s steps(1) infinite}@keyframes flick{50%{opacity:.55}}"
    )
    markup = (
        f'<defs>{"".join(f"""<path id="{k}" d="{d}"/>""" for k, d in faces.items())}</defs>'
        f'<g transform="translate({n(ox)} {n(oy)})">'
        f'<path class="e1" d="{edge_left}"/><path class="e2" d="{edge_right}"/>'
        f'<path class="sm" d="{slab}"/><path class="fl" d="{tiles}"/>{track}'
        f'<g class="tap">{the_spark}</g>{the_name}'
        f'<g class="fly"><g class="burn" opacity="0"><g class="flick">{the_flame}</g></g>{the_rocket}</g>'
        "</g>"
    )
    return markup, css, w, h


def typing(layout, enter=None):
    """The terminal's rows with the time each appears, and when the last key of the last command falls.

    Given `enter`, the pauses between commands stretch or shrink so that the last key falls then.
    """
    rows = [("type", COMMANDS["about"])]
    rows += [("print", " ".join(part)) for part in chunks(ABOUT, layout["about"])]
    rows += [("gap",), ("type", COMMANDS["built"])]
    rows += [("list", row) for row in chunks(BUILT, layout["built"])]
    rows += [("gap",), ("type", COMMANDS["next"]), ("bar",)]

    def run(pause):
        clock, timed, last = 0.5, [], 0.0
        for row in rows:
            timed.append((row, clock))
            if row[0] == "type":
                last = clock + 0.25 + len(row[1]) * KEY
                clock = last + 0.3
            elif row[0] in ("print", "list"):
                clock += 0.16
            elif row[0] == "gap":
                clock += pause
        return timed, last

    timed, last = run(PAUSE)
    if enter is not None:
        pause = PAUSE + (enter - last) / sum(row[0] == "gap" for row in rows)
        assert pause > 0.3, "this layout cannot type its commands in the time the story gives it"
        timed, last = run(pause)
    return timed, last


def terminal(layout, timed, sc, start):
    """The terminal window: (markup, css, width, height). Its bar follows the banner's story."""
    ink, font = TERMINAL, layout["font"]
    advance, line = font * 0.6, round(font * 1.6)
    pad_x, pad_top, pad_bottom, title_bar = font * 1.45, font * 1.7, font * 1.35, font * 2.2
    column = max(len(b) for b in BUILT) + GUTTER
    cells = layout["bar"]

    width = max(
        len(PROMPT) + len(r[1]) if r[0] == "type"
        else len(r[1]) if r[0] == "print"
        else (len(r[1]) - 1) * column + len(r[1][-1]) if r[0] == "list"
        else cells + 2 + max(len(s) for s in STAGES)
        for r, _ in timed if r[0] != "gap"
    )
    w = 2 * pad_x + (width + 2) * advance  # two characters of slack: system fonts differ in width
    h = title_bar + pad_top + (len(timed) - 1) * line + pad_bottom + 6

    body = []
    for i, (row, at) in enumerate(timed):
        y = title_bar + pad_top + i * line
        if row[0] == "type":
            keys = "".join(
                f'<tspan class="k" style="animation-delay:{n(at + 0.25 + j * KEY)}s">{escape(ch)}</tspan>'
                for j, ch in enumerate(row[1])
            )
            body.append(
                f'<text x="{n(pad_x)}" y="{n(y)}"><tspan class="k" fill="{ink["prompt"]}" '
                f'style="animation-delay:{n(at)}s">{PROMPT}</tspan><tspan fill="{ink["typed"]}">{keys}</tspan></text>'
            )
        elif row[0] == "print":
            body.append(
                f'<text class="o" style="animation-delay:{n(at)}s" x="{n(pad_x)}" y="{n(y)}" '
                f'fill="{ink["printed"]}">{escape(row[1])}</text>'
            )
        elif row[0] == "list":
            for col, entry in enumerate(row[1]):
                body.append(
                    f'<text class="o" style="animation-delay:{n(at)}s" x="{n(pad_x + col * column * advance)}" '
                    f'y="{n(y)}" fill="{ink["listed"]}">{escape(entry)}</text>'
                )
        elif row[0] == "bar":
            bw, bh, by = cells * advance, font * 0.83, y - font * 0.75
            seams = "".join(f"M{n(pad_x + j * advance)} {n(by - 1)}v{n(bh + 2)}" for j in range(1, cells))
            label_x = pad_x + (cells + 2) * advance
            colours = (ink["listed"], ink["printed"], ink["bar"])
            labels = "".join(
                f'<text class="st{j}" x="{n(label_x)}" y="{n(y)}" fill="{c}"'
                + ("" if j == 1 else ' fill-opacity="0"')  # without motion, the bar is caught mid-build
                + f">{escape(stage)}</text>"
                for j, (stage, c) in enumerate(zip(STAGES, colours))
            )
            body.append(
                f'<g class="o" style="animation-delay:{n(at)}s">'
                f'<rect x="{n(pad_x)}" y="{n(by)}" width="{n(bw)}" height="{n(bh)}" fill="{ink["track"]}"/>'
                f'<rect class="run" x="{n(pad_x)}" y="{n(by)}" width="{n(bw)}" height="{n(bh)}" fill="{ink["bar"]}" '
                f'transform="translate({n(pad_x)} 0) scale(.67 1) translate({n(-pad_x)} 0)"/>'
                f'<path d="{seams}" stroke="{ink["card"]}" stroke-width="2"/>{labels}</g>'
            )

    # the bar keeps the banner's time: empty while the spark comes down, filling while the line runs,
    # full while the rocket is away, cleared when it has landed
    a, b, d = pc(sc["line_at"]), pc(sc["lands"]), pc(sc["down"])
    loop = f"{LOOP}s steps(1) {n(start)}s infinite"
    css = (
        f'text{{font:{n(font)}px ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;white-space:pre}}'
        ".k{animation:key .01s linear backwards}@keyframes key{from{fill-opacity:0}}"
        ".o{animation:out .3s ease-out backwards}@keyframes out{from{opacity:0}}"
        f".run{{transform-box:fill-box;transform-origin:left center;animation:run {LOOP}s linear {n(start)}s infinite}}"
        f"@keyframes run{{0%,{a}%{{transform:scaleX(0);animation-timing-function:steps({cells},end)}}"
        f"{b}%,{d}%{{transform:scaleX(1);animation-timing-function:steps(1,end)}}"
        f"{pc(sc['down'] + 0.05)}%,100%{{transform:scaleX(0)}}}}"
        f".st0{{animation:st0 {loop}}}@keyframes st0{{0%,{d}%,100%{{fill-opacity:1}}{a}%{{fill-opacity:0}}}}"
        f".st1{{animation:st1 {loop}}}@keyframes st1{{0%,{b}%,100%{{fill-opacity:0}}{a}%{{fill-opacity:1}}}}"
        f".st2{{animation:st2 {loop}}}@keyframes st2{{0%,{d}%,100%{{fill-opacity:0}}{b}%{{fill-opacity:1}}}}"
    )
    r = font / 3
    lights = "".join(
        f'<circle cx="{n(pad_x + j * r * 3.3)}" cy="{n(title_bar / 2)}" r="{n(r)}" fill="{c}"/>'
        for j, c in enumerate(ink["lights"])
    )
    markup = (
        f'<rect x="1" y="1" width="{n(w - 2)}" height="{n(h - 2)}" rx="12" fill="{ink["card"]}" stroke="{ink["edge"]}" stroke-width="2"/>'
        f'<path d="M2 {n(title_bar)}H{n(w - 2)}" stroke="{ink["edge"]}" stroke-width="1.5"/>{lights}'
        f'<text x="{n(w / 2)}" y="{n(title_bar / 2 + font * 0.28)}" text-anchor="middle" fill="{ink["title"]}" '
        f'style="font-size:{n(font * 0.78)}px">{escape(TITLE)}</text>'
        f'{"".join(body)}'
    )
    return markup, css, w, h


def picture(markup, css, w, h, label):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'viewBox="0 0 {n(w)} {n(h)}" role="img" aria-label="{label}">'
        f"<title>{label}</title>"
        f"<style>{css}@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}</style>"
        f"{markup}</svg>\n"
    )


def draw():
    """Every picture, by file name."""
    sc = scene()
    enter = typing(LAYOUTS["wide"])[1]
    start = enter - LEAD  # the spark starts down as the command is entered

    files = {}
    markup, css, w, h = banner(sc, start)
    for theme in THEMES:
        files[f"banner-{theme}.svg"] = picture(markup, theme_css(theme) + css, w, h, "jnvhr")
    for name, layout in LAYOUTS.items():
        timed, _ = typing(layout, enter)  # the one banner needs every layout to enter its last command together
        markup, css, w, h = terminal(layout, timed, sc, start)
        files[f"terminal-{name}.svg"] = picture(f'<g xml:space="preserve">{markup}</g>', css, w, h, "terminal")
    return files


def main():
    out = Path(__file__).resolve().parent.parent / "assets"
    out.mkdir(exist_ok=True)
    for name, data in draw().items():
        (out / name).write_text(data, encoding="utf-8")
        print(f"{name}  {len(data) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
