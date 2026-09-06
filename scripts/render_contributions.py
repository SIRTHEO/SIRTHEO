#!/usr/bin/env python3
"""Render assets/contributions-{dark,light}.svg from the public contribution
calendar. No token: it reads the same page the profile shows. Runs daily from
.github/workflows/contributions.yml.
"""
import re
import sys
import urllib.request
from datetime import date, timedelta
from pathlib import Path

USER = sys.argv[1] if len(sys.argv) > 1 else "SIRTHEO"
CELL, GAP, PAD = 11, 3, 14
PALETTE = {
    "dark": ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"],
    "light": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"],
}
TEXT = {"dark": "#8b949e", "light": "#59636e"}


def fetch_days() -> dict:
    url = f"https://github.com/users/{USER}/contributions"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (profile-readme)"})
    html = urllib.request.urlopen(req, timeout=30).read().decode()
    days = {}
    for m in re.finditer(r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*data-level="(\d)"', html):
        days[date.fromisoformat(m.group(1))] = int(m.group(2))
    if not days:
        raise SystemExit("no contribution cells found: the page layout changed")
    return days


def render(days: dict, theme: str) -> str:
    last = max(days)
    first = last - timedelta(days=last.weekday() + 1 + 52 * 7)  # sunday, 53 weeks back
    weeks = 53
    width = PAD * 2 + weeks * (CELL + GAP) - GAP
    height = PAD * 2 + 7 * (CELL + GAP) - GAP + 18
    total = sum(1 for d, lvl in days.items() if d > last - timedelta(days=365) and lvl > 0)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Contribution calendar">']
    d = first
    for w in range(weeks):
        for r in range(7):
            if d <= last:
                lvl = days.get(d, 0)
                x, y = PAD + w * (CELL + GAP), PAD + r * (CELL + GAP)
                delay = (w + r) * 0.018
                out.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{PALETTE[theme][lvl]}" opacity="0">'
                           f'<animate attributeName="opacity" to="1" begin="{delay:.3f}s" dur="0.25s" fill="freeze"/></rect>')
            d += timedelta(days=1)
    out.append(f'<text x="{PAD}" y="{height - 6}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" '
               f'font-size="11" fill="{TEXT[theme]}">{total} active days in the last year · rendered {date.today().isoformat()}</text>')
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    days = fetch_days()
    for theme in PALETTE:
        path = Path(__file__).resolve().parent.parent / "assets" / f"contributions-{theme}.svg"
        path.write_text(render(days, theme), encoding="utf-8")
        print(f"wrote {path.name} ({len(days)} days)")
