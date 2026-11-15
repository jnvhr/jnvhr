#!/usr/bin/env python3
"""Draws the terminal under the name on the profile README.

    python3 tools/draw_intro.py

A terminal types three commands and prints what they return. Edit ABOUT,
BUILT and COMMANDS to change what it says. It is drawn twice from the same
words: assets/intro-wide.svg spans the page, and assets/intro-narrow.svg
wraps the same text for phones, where the wide one would be too small to
read. No dependencies: the text is set in whatever monospace font the
reader's system has.
"""
from html import escape
from pathlib import Path

ABOUT = ["I don't keep a list of ideas.", "I keep a list of things I built."]
BUILT = ["browser-tools/", "native-mac-app/", "encrypted-chat/", "music-video.py"]
COMMANDS = {"about": "cat about.txt", "built": "ls built/", "next": "idea --next | build | ship"}
PROMPT = "~ $ "
TITLE = "jnvhr"

LAYOUTS = {
    # sentences per line, listing entries per row, cells in the progress bar
    "wide": {"font": 20.0, "about": 2, "built": 4, "bar": 44},
    "narrow": {"font": 18.0, "about": 1, "built": 2, "bar": 18},
}
GUTTER = 3  # characters between two columns of a listing

INK = {
    "card": "#010409", "edge": "#30363d", "title": "#8b949e",
    "prompt": "#39d353", "typed": "#f0f6fc", "printed": "#c9d1d9", "listed": "#7ee787",
    "bar": "#39d353", "track": "#0e4429",
}
LIGHTS = ("#ff5f57", "#febc2e", "#28c840")

KEY = 0.055  # seconds per keystroke
PAUSE = 0.9  # between a command's output and the next prompt
BUILD = 5.0  # one run of the progress bar


def n(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def chunks(items, size):
    return [items[i : i + size] for i in range(0, len(items), size)]


def session(layout):
    """The terminal's rows for one layout, top to bottom."""
    rows = [("type", COMMANDS["about"])]
    rows += [("print", " ".join(part)) for part in chunks(ABOUT, layout["about"])]
    rows += [("gap",), ("type", COMMANDS["built"])]
    rows += [("list", row) for row in chunks(BUILT, layout["built"])]
    rows += [("gap",), ("type", COMMANDS["next"]), ("bar",)]
    return rows


def draw(name):
    layout = LAYOUTS[name]
    font = layout["font"]
    advance, line = font * 0.6, round(font * 1.6)
    pad_x, pad_top, pad_bottom, title_bar = font * 1.45, font * 1.7, font * 1.35, font * 2.2
    column = max(len(b) for b in BUILT) + GUTTER
    rows = session(layout)

    width = max(
        len(PROMPT) + len(r[1]) if r[0] == "type"
        else len(r[1]) if r[0] == "print"
        else (len(r[1]) - 1) * column + len(r[1][-1]) if r[0] == "list"
        else layout["bar"] + 10
        for r in rows if r[0] != "gap"
    )
    w = 2 * pad_x + (width + 2) * advance  # two characters of slack: system fonts differ in width
    h = title_bar + pad_top + (len(rows) - 1) * line + pad_bottom + 6

    body, clock, bar_css = [], 0.5, ""
    for i, row in enumerate(rows):
        y = title_bar + pad_top + i * line
        if row[0] == "type":
            keys = "".join(
                f'<tspan class="k" style="animation-delay:{n(clock + 0.25 + j * KEY)}s">{escape(ch)}</tspan>'
                for j, ch in enumerate(row[1])
            )
            body.append(
                f'<text x="{n(pad_x)}" y="{n(y)}"><tspan class="k" fill="{INK["prompt"]}" '
                f'style="animation-delay:{n(clock)}s">{PROMPT}</tspan><tspan fill="{INK["typed"]}">{keys}</tspan></text>'
            )
            clock += 0.25 + len(row[1]) * KEY + 0.3
        elif row[0] == "print":
            body.append(
                f'<text class="o" style="animation-delay:{n(clock)}s" x="{n(pad_x)}" y="{n(y)}" '
                f'fill="{INK["printed"]}">{escape(row[1])}</text>'
            )
            clock += 0.16
        elif row[0] == "list":
            for col, entry in enumerate(row[1]):
                body.append(
                    f'<text class="o" style="animation-delay:{n(clock)}s" x="{n(pad_x + col * column * advance)}" '
                    f'y="{n(y)}" fill="{INK["listed"]}">{escape(entry)}</text>'
                )
            clock += 0.16
        elif row[0] == "gap":
            clock += PAUSE
        elif row[0] == "bar":
            cells = layout["bar"]
            bw, bh, by = cells * advance, font * 0.83, y - font * 0.75
            seams = "".join(f"M{n(pad_x + j * advance)} {n(by - 1)}v{n(bh + 2)}" for j in range(1, cells))
            label_x = pad_x + (cells + 2) * advance
            body.append(
                f'<g class="o" style="animation-delay:{n(clock)}s">'
                f'<rect x="{n(pad_x)}" y="{n(by)}" width="{n(bw)}" height="{n(bh)}" fill="{INK["track"]}"/>'
                f'<rect class="run" style="animation-delay:{n(clock)}s" x="{n(pad_x)}" y="{n(by)}" width="{n(bw)}" '
                f'height="{n(bh)}" fill="{INK["bar"]}" transform="translate({n(pad_x)} 0) scale(.67 1) translate({n(-pad_x)} 0)"/>'
                f'<path d="{seams}" stroke="{INK["card"]}" stroke-width="2"/>'
                f'<text class="busy" style="animation-delay:{n(clock)}s" x="{n(label_x)}" y="{n(y)}" fill="{INK["printed"]}">building</text>'
                f'<text class="done" style="animation-delay:{n(clock)}s" x="{n(label_x)}" y="{n(y)}" fill="{INK["bar"]}" fill-opacity="0">shipped</text>'
                "</g>"
            )
            bar_css = (
                f".run{{transform-origin:{n(pad_x)}px 0;animation:run {BUILD}s steps({cells}) infinite backwards}}"
                "@keyframes run{0%{transform:scaleX(0)}72%,100%{transform:scaleX(1)}}"
                f".busy{{animation:busy {BUILD}s steps(1) infinite}}@keyframes busy{{0%{{fill-opacity:1}}72%,100%{{fill-opacity:0}}}}"
                f".done{{animation:done {BUILD}s steps(1) infinite}}@keyframes done{{0%{{fill-opacity:0}}72%,100%{{fill-opacity:1}}}}"
            )

    css = (
        f'text{{font:{n(font)}px ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;white-space:pre}}'
        ".k{animation:key .01s linear backwards}@keyframes key{from{fill-opacity:0}}"
        ".o{animation:out .3s ease-out backwards}@keyframes out{from{opacity:0}}"
        + bar_css
        + "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
    )
    r = font / 3
    lights = "".join(
        f'<circle cx="{n(pad_x - r + j * r * 3.3 + r)}" cy="{n(title_bar / 2)}" r="{n(r)}" fill="{c}"/>'
        for j, c in enumerate(LIGHTS)
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n(w)} {n(h)}" width="{n(w)}" height="{n(h)}" '
        f'role="img" aria-label="A terminal session" xml:space="preserve">'
        f"<title>A terminal session</title><style>{css}</style>"
        f'<rect x="1" y="1" width="{n(w - 2)}" height="{n(h - 2)}" rx="12" fill="{INK["card"]}" stroke="{INK["edge"]}" stroke-width="2"/>'
        f'<path d="M2 {n(title_bar)}H{n(w - 2)}" stroke="{INK["edge"]}" stroke-width="1.5"/>{lights}'
        f'<text x="{n(w / 2)}" y="{n(title_bar / 2 + font * 0.28)}" text-anchor="middle" fill="{INK["title"]}" '
        f'style="font-size:{n(font * 0.78)}px">{escape(TITLE)}</text>'
        f'{"".join(body)}</svg>\n'
    )


def main():
    out = Path(__file__).resolve().parent.parent / "assets"
    out.mkdir(exist_ok=True)
    for name in LAYOUTS:
        data = draw(name)
        (out / f"intro-{name}.svg").write_text(data, encoding="utf-8")
        print(f"intro-{name}.svg  {len(data) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
