#!/usr/bin/env python3
"""Render assets/intro-{dark,light}.svg: a terminal card that types itself.

Pure SVG + SMIL, no JavaScript, no external fonts, so GitHub renders the
animation as-is. Run once, commit the output.
"""
from pathlib import Path
from xml.sax.saxutils import escape

WIDTH, PAD, LINE_H, FONT = 760, 28, 30, 15
CHAR_DELAY, LINE_GAP = 0.055, 0.45  # seconds per character, pause after output

# (prompt line typed char by char, output line shown at once)
SCRIPT = [
    ("whoami", "Matteo Di Mattia · full-stack engineer"),
    ("cat focus", "rust · typescript · lua · postgres"),
    ("sailor status", "building flows you can read, measure and stop"),
]

THEMES = {
    "dark": dict(bg="#0d1117", border="#30363d", fg="#e6edf3", muted="#8b949e",
                 prompt="#3fb950", accent="#79c0ff", dots=("#ff5f57", "#febc2e", "#28c840")),
    "light": dict(bg="#ffffff", border="#d0d7de", fg="#1f2328", muted="#59636e",
                  prompt="#1a7f37", accent="#0969da", dots=("#ff5f57", "#febc2e", "#28c840")),
}


def render(theme: dict) -> str:
    rows = 1 + 2 * len(SCRIPT)  # a header row + prompt/output pairs
    height = PAD * 2 + 22 + rows * LINE_H
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" role="img" aria-label="Matteo Di Mattia, full-stack engineer">',
        f'<rect x="0.5" y="0.5" width="{WIDTH-1}" height="{height-1}" rx="12" fill="{theme["bg"]}" stroke="{theme["border"]}"/>',
    ]
    for i, c in enumerate(theme["dots"]):
        out.append(f'<circle cx="{PAD + i*20}" cy="{PAD}" r="6" fill="{c}"/>')
    out.append(f'<text x="{WIDTH/2}" y="{PAD+5}" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="12" fill="{theme["muted"]}">theo@sirtheo — zsh</text>')

    font = f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="{FONT}"'
    t = 0.6  # timeline cursor in seconds
    y = PAD + 22 + LINE_H
    for cmd, output in SCRIPT:
        # prompt, always visible once its line starts
        out.append(f'<text x="{PAD}" y="{y}" {font} fill="{theme["prompt"]}" opacity="0">~ ❯'
                   f'<animate attributeName="opacity" to="1" begin="{t:.2f}s" dur="0.01s" fill="freeze"/></text>')
        # command typed one character at a time
        spans = []
        for j, ch in enumerate(cmd):
            spans.append(f'<tspan opacity="0">{escape(ch)}<animate attributeName="opacity" to="1" '
                         f'begin="{t + j*CHAR_DELAY:.2f}s" dur="0.01s" fill="freeze"/></tspan>')
        t_done = t + len(cmd) * CHAR_DELAY
        out.append(f'<text x="{PAD + 34}" y="{y}" {font} fill="{theme["fg"]}" xml:space="preserve">{"".join(spans)}</text>')
        # output appears after a short "execution" pause
        t_out = t_done + 0.25
        y += LINE_H
        color = theme["accent"] if cmd == "whoami" else theme["muted"]
        out.append(f'<text x="{PAD}" y="{y}" {font} fill="{color}" opacity="0">{escape(output)}'
                   f'<animate attributeName="opacity" to="1" begin="{t_out:.2f}s" dur="0.15s" fill="freeze"/></text>')
        y += LINE_H
        t = t_out + LINE_GAP

    # blinking cursor on the final prompt line, appears when everything is typed
    out.append(f'<text x="{PAD}" y="{y}" {font} fill="{theme["prompt"]}" opacity="0">~ ❯'
               f'<animate attributeName="opacity" to="1" begin="{t:.2f}s" dur="0.01s" fill="freeze"/></text>')
    out.append(f'<rect x="{PAD + 36}" y="{y - FONT + 2}" width="9" height="{FONT + 2}" fill="{theme["fg"]}" opacity="0">'
               f'<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.01;0.5;0.51;1" '
               f'begin="{t:.2f}s" dur="1.1s" repeatCount="indefinite"/></rect>')
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    for name, theme in THEMES.items():
        path = Path(__file__).resolve().parent.parent / "assets" / f"intro-{name}.svg"
        path.write_text(render(theme), encoding="utf-8")
        print(f"wrote {path.relative_to(path.parents[1])}")
