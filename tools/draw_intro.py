#!/usr/bin/env python3
"""Draws the terminal card under the name on the profile README.

    python3 tools/draw_intro.py

A small terminal types three commands and prints what they return. Edit
SESSION to change what it says; everything else follows from it. Writes
assets/intro.svg. No dependencies: the text is set in whatever monospace
font the reader's system has.
"""
from html import escape
from pathlib import Path

# what the terminal shows, top to bottom
SESSION = [
    ("type", "cat about.txt"),
    ("print", "I don't keep a list of ideas."),
    ("print", "I keep a list of things I built."),
    ("gap",),
    ("type", "ls built/"),
    ("list", ["browser-tools/", "native-mac-app/"]),
    ("list", ["encrypted-chat/", "music-video.py"]),
    ("gap",),
    ("type", "idea --next | build | ship"),
    ("bar",),
]
PROMPT = "~ $ "

FONT = 18.0
ADVANCE = FONT * 0.6  # one character
LINE = 29.0
PAD_X, PAD_TOP, PAD_BOTTOM = 26.0, 30.0, 24.0
TITLE_BAR = 40.0
COLUMN = 18  # where the second column of a listing starts, in characters
BAR_CELLS = 18

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


def draw():
    width = max(
        len(PROMPT) + len(step[1]) if step[0] == "type"
        else len(step[1]) if step[0] == "print"
        else COLUMN + len(step[1][-1]) if step[0] == "list"
        else BAR_CELLS + 10
        for step in SESSION if step[0] != "gap"
    )
    w = 2 * PAD_X + (width + 2) * ADVANCE  # two characters of slack: system fonts differ in width
    h = TITLE_BAR + PAD_TOP + (len(SESSION) - 1) * LINE + PAD_BOTTOM + 6

    body, clock, bar_css = [], 0.5, ""
    for row, step in enumerate(SESSION):
        y = TITLE_BAR + PAD_TOP + row * LINE
        if step[0] == "type":
            keys = "".join(
                f'<tspan class="k" style="animation-delay:{n(clock + 0.25 + i * KEY)}s">{escape(ch)}</tspan>'
                for i, ch in enumerate(step[1])
            )
            body.append(
                f'<text x="{n(PAD_X)}" y="{n(y)}"><tspan class="k" fill="{INK["prompt"]}" '
                f'style="animation-delay:{n(clock)}s">{PROMPT}</tspan><tspan fill="{INK["typed"]}">{keys}</tspan></text>'
            )
            clock += 0.25 + len(step[1]) * KEY + 0.3
        elif step[0] == "print":
            body.append(
                f'<text class="o" style="animation-delay:{n(clock)}s" x="{n(PAD_X)}" y="{n(y)}" '
                f'fill="{INK["printed"]}">{escape(step[1])}</text>'
            )
            clock += 0.16
        elif step[0] == "list":
            for col, name in enumerate(step[1]):
                body.append(
                    f'<text class="o" style="animation-delay:{n(clock)}s" x="{n(PAD_X + col * COLUMN * ADVANCE)}" '
                    f'y="{n(y)}" fill="{INK["listed"]}">{escape(name)}</text>'
                )
            clock += 0.16
        elif step[0] == "gap":
            clock += PAUSE
        elif step[0] == "bar":
            bw, bh, by = BAR_CELLS * ADVANCE, 15.0, y - 13.5
            seams = "".join(f"M{n(PAD_X + i * ADVANCE)} {n(by - 1)}v{n(bh + 2)}" for i in range(1, BAR_CELLS))
            label_x = PAD_X + (BAR_CELLS + 2) * ADVANCE
            body.append(
                f'<g class="o" style="animation-delay:{n(clock)}s">'
                f'<rect x="{n(PAD_X)}" y="{n(by)}" width="{n(bw)}" height="{n(bh)}" fill="{INK["track"]}"/>'
                f'<rect class="run" style="animation-delay:{n(clock)}s" x="{n(PAD_X)}" y="{n(by)}" width="{n(bw)}" '
                f'height="{n(bh)}" fill="{INK["bar"]}" transform="translate({n(PAD_X)} 0) scale(.67 1) translate({n(-PAD_X)} 0)"/>'
                f'<path d="{seams}" stroke="{INK["card"]}" stroke-width="2"/>'
                f'<text class="busy" style="animation-delay:{n(clock)}s" x="{n(label_x)}" y="{n(y)}" fill="{INK["printed"]}">building</text>'
                f'<text class="done" style="animation-delay:{n(clock)}s" x="{n(label_x)}" y="{n(y)}" fill="{INK["bar"]}" fill-opacity="0">shipped</text>'
                "</g>"
            )
            bar_css = (
                f".run{{transform-origin:{n(PAD_X)}px 0;animation:run {BUILD}s steps({BAR_CELLS}) infinite backwards}}"
                "@keyframes run{0%{transform:scaleX(0)}72%,100%{transform:scaleX(1)}}"
                f".busy{{animation:busy {BUILD}s steps(1) infinite}}@keyframes busy{{0%{{fill-opacity:1}}72%,100%{{fill-opacity:0}}}}"
                f".done{{animation:done {BUILD}s steps(1) infinite}}@keyframes done{{0%{{fill-opacity:0}}72%,100%{{fill-opacity:1}}}}"
            )

    css = (
        f'text{{font:{n(FONT)}px ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;white-space:pre}}'
        ".k{animation:key .01s linear backwards}@keyframes key{from{fill-opacity:0}}"
        ".o{animation:out .3s ease-out backwards}@keyframes out{from{opacity:0}}"
        + bar_css
        + "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
    )
    lights = "".join(f'<circle cx="{22 + i * 20}" cy="{n(TITLE_BAR / 2)}" r="6" fill="{c}"/>' for i, c in enumerate(LIGHTS))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n(w)} {n(h)}" width="{n(w)}" height="{n(h)}" '
        f'role="img" aria-label="A terminal session" xml:space="preserve">'
        f"<title>A terminal session</title><style>{css}</style>"
        f'<rect x="1" y="1" width="{n(w - 2)}" height="{n(h - 2)}" rx="12" fill="{INK["card"]}" stroke="{INK["edge"]}" stroke-width="2"/>'
        f'<path d="M2 {n(TITLE_BAR)}H{n(w - 2)}" stroke="{INK["edge"]}" stroke-width="1.5"/>{lights}'
        f'<text x="{n(w / 2)}" y="{n(TITLE_BAR / 2 + 5)}" text-anchor="middle" fill="{INK["title"]}" style="font-size:14px">jnvhr</text>'
        f'{"".join(body)}</svg>\n'
    )


def main():
    out = Path(__file__).resolve().parent.parent / "assets"
    out.mkdir(exist_ok=True)
    data = draw()
    (out / "intro.svg").write_text(data, encoding="utf-8")
    print(f"intro.svg  {len(data) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
