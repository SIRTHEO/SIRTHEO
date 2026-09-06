#!/usr/bin/env python3
"""Render assets/tide-{dark,light}.svg: GitHub activity as a tide chart,
one point per week over the last 52 weeks.

No token: it reads the public contribution calendar the profile shows.
Runs nightly from .github/workflows/refresh.yml.
"""
import re
import sys
import urllib.request
from datetime import date, timedelta
from pathlib import Path

USER = sys.argv[1] if len(sys.argv) > 1 else "SIRTHEO"
W, H = 860, 220
L, R, TOP, BASE = 40, 820, 40, 160
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
THEMES = {
    "dark": dict(line="#60a5fa", fill="#1d4ed8", text="#e6edf3", muted="#9aa4b2", grid="#30363d"),
    "light": dict(line="#2563eb", fill="#93c5fd", text="#1f2328", muted="#59636e", grid="#d0d7de"),
}


def fetch_days() -> dict:
    url = f"https://github.com/users/{USER}/contributions"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (profile-readme)"})
    for attempt in range(3):  # the page is large and the read occasionally comes back short
        try:
            html = urllib.request.urlopen(req, timeout=30).read().decode()
            break
        except Exception:
            if attempt == 2:
                raise
    ids = {m.group(2): (date.fromisoformat(m.group(1)), int(m.group(3)))
           for m in re.finditer(r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*?id="([^"]+)"[^>]*data-level="(\d)"', html)}
    if not ids:  # attribute order may differ
        ids = {m.group(1): (date.fromisoformat(m.group(2)), int(m.group(3)))
               for m in re.finditer(r'id="([^"]+)"[^>]*data-date="(\d{4}-\d{2}-\d{2})"[^>]*data-level="(\d)"', html)}
    counts = {}
    for m in re.finditer(r'<tool-tip[^>]*for="([^"]+)"[^>]*>\s*(No|\d+) contributions?', html):
        counts[m.group(1)] = 0 if m.group(2) == "No" else int(m.group(2))
    days = {}
    for cid, (d, level) in ids.items():
        days[d] = counts.get(cid, level)  # level as a fallback if tooltips move
    if not days:
        raise SystemExit("no contribution cells found: the page layout changed")
    return days


def weekly(days: dict) -> list[tuple[date, int]]:
    last = max(days)
    end = last + timedelta(days=6 - (last.weekday() + 1) % 7)  # saturday of the current week
    start = end - timedelta(days=52 * 7 - 1)
    weeks = []
    for i in range(52):
        a = start + timedelta(days=7 * i)
        weeks.append((a, sum(days.get(a + timedelta(days=k), 0) for k in range(7))))
    return weeks


def smooth_path(pts: list[tuple[float, float]]) -> str:
    d = [f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"]
    for i in range(1, len(pts)):
        (x0, y0), (x1, y1) = pts[i - 1], pts[i]
        cx = (x0 + x1) / 2
        d.append(f"C{cx:.1f},{y0:.1f} {cx:.1f},{y1:.1f} {x1:.1f},{y1:.1f}")
    return " ".join(d)


def approx_length(pts) -> float:
    return sum(((pts[i][0] - pts[i-1][0]) ** 2 + (pts[i][1] - pts[i-1][1]) ** 2) ** 0.5 for i in range(1, len(pts))) * 1.15


def render(weeks, theme) -> str:
    peak = max(c for _, c in weeks) or 1
    total = sum(c for _, c in weeks)
    xs = [L + (R - L) * i / 51 for i in range(52)]
    pts = [(x, BASE - (BASE - TOP) * c / peak) for x, (_, c) in zip(xs, weeks)]
    line = smooth_path(pts)
    area = line + f" L{R},{BASE} L{L},{BASE} Z"
    length = approx_length(pts)
    hi = max(range(52), key=lambda i: weeks[i][1])
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Weekly GitHub activity, last 52 weeks">',
         '<defs><linearGradient id="tide" x1="0" y1="0" x2="0" y2="1">'
         f'<stop offset="0" stop-color="{theme["fill"]}" stop-opacity="0.55"/><stop offset="1" stop-color="{theme["fill"]}" stop-opacity="0.05"/></linearGradient></defs>']
    # month ticks
    for i, (a, _) in enumerate(weeks):
        if a.day <= 7:
            o.append(f'<line x1="{xs[i]:.1f}" y1="{BASE}" x2="{xs[i]:.1f}" y2="{BASE + 5}" stroke="{theme["grid"]}"/>')
            o.append(f'<text x="{xs[i]:.1f}" y="{BASE + 20}" font-family="{FONT}" font-size="11" fill="{theme["muted"]}" text-anchor="middle">{a.strftime("%b")}</text>')
    o.append(f'<line x1="{L}" y1="{BASE}" x2="{R}" y2="{BASE}" stroke="{theme["grid"]}"/>')
    o.append(f'<path d="{area}" fill="url(#tide)"><animate attributeName="opacity" from="0" to="1" begin="1.6s" dur="0.8s" fill="freeze"/></path>')
    o.append(f'<path d="{line}" fill="none" stroke="{theme["line"]}" stroke-width="2.5" stroke-linecap="round" '
             f'stroke-dasharray="{length:.0f}">'
             f'<animate attributeName="stroke-dashoffset" from="{length:.0f}" to="0" begin="0.2s" dur="2.2s" fill="freeze"/></path>')
    # high tide: a dot on the peak, the label in the top-left corner so it never leaves the frame
    hx, hy = pts[hi]
    o.append(f'<g><animate attributeName="opacity" from="0" to="1" begin="2.4s" dur="0.5s" fill="freeze"/>'
             f'<circle cx="{hx:.1f}" cy="{hy:.1f}" r="4.5" fill="{theme["line"]}"/>'
             f'<text x="{L}" y="{TOP - 16}" font-family="{FONT}" font-size="12" fill="{theme["text"]}">'
             f'High tide · {weeks[hi][1]} contributions in the week of {weeks[hi][0].strftime("%b %-d")}</text></g>')
    o.append(f'<text x="{L}" y="{H - 12}" font-family="{FONT}" font-size="12" fill="{theme["muted"]}">'
             f'Tide chart · {total} contributions over the last 52 weeks · redrawn {date.today().strftime("%b %-d, %Y")}</text>')
    o.append("</svg>")
    return "\n".join(o)


if __name__ == "__main__":
    weeks = weekly(fetch_days())
    for name, theme in THEMES.items():
        path = Path(__file__).resolve().parent.parent / "assets" / f"tide-{name}.svg"
        path.write_text(render(weeks, theme), encoding="utf-8")
        print(f"wrote {path.name} · {sum(c for _, c in weeks)} contributions, peak {max(c for _, c in weeks)}")
