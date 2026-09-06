#!/usr/bin/env python3
"""Render assets/hero-{dark,light}.svg: an animated seascape with a small boat.

Night sky in dark mode, daylight in light mode. Pure SVG + SMIL, no scripts,
no external fonts. Run once, commit the output.
"""
import random
from pathlib import Path

W, H = 860, 280
SEA_Y = 200          # baseline of the first wave layer
WAVELEN, AMP = 120, 7
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"

THEMES = {
    "dark": dict(sky=("#0b1020", "#131c38"), text="#e6edf3", muted="#9aa4b2",
                 waves=("#1e3a8a", "#1d4ed8", "#3b82f6"), hull="#f1f5f9", sail="#cbd5e1",
                 night=True),
    "light": dict(sky=("#dbeafe", "#f8fbff"), text="#1f2328", muted="#59636e",
                  waves=("#bfdbfe", "#93c5fd", "#60a5fa"), hull="#1f2328", sail="#ffffff",
                  night=False),
}


def wave_path(y: float, amp: float) -> str:
    """One full-width repeating wave, twice the canvas so it can scroll seamlessly."""
    d = [f"M0,{y}"]
    x = 0
    while x < W * 2:
        d.append(f"q{WAVELEN/4},{-amp*2} {WAVELEN/2},0 t{WAVELEN/2},0")
        x += WAVELEN
    d.append(f"V{H} H0 Z")
    return " ".join(d)


def render(theme: dict) -> str:
    rng = random.Random(7)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f'role="img" aria-label="Matteo Di Mattia, full-stack engineer">',
         '<defs>',
         f'<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
         f'<stop offset="0" stop-color="{theme["sky"][0]}"/><stop offset="1" stop-color="{theme["sky"][1]}"/></linearGradient>',
         f'<clipPath id="frame"><rect width="{W}" height="{H}" rx="14"/></clipPath>',
         '</defs>',
         '<g clip-path="url(#frame)">',
         f'<rect width="{W}" height="{H}" fill="url(#sky)"/>']

    if theme["night"]:
        for _ in range(48):
            x, y = rng.uniform(0, W), rng.uniform(8, SEA_Y - 30)
            r = rng.choice((0.8, 1.0, 1.3))
            dur = rng.uniform(2.0, 4.5)
            o.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="#e6edf3">'
                     f'<animate attributeName="opacity" values="0.15;1;0.15" dur="{dur:.1f}s" '
                     f'begin="{rng.uniform(0, 3):.1f}s" repeatCount="indefinite"/></circle>')
        o.append('<circle cx="740" cy="62" r="26" fill="#f5f3c1" opacity="0.95"/>'
                 '<circle cx="752" cy="54" r="24" fill="#131c38"/>')  # crescent
    else:
        o.append('<circle cx="740" cy="62" r="40" fill="#fde68a" opacity="0.45"/>'
                 '<circle cx="740" cy="62" r="24" fill="#fbbf24"/>')

    # text
    o.append(f'<text x="48" y="104" font-family="{FONT}" font-size="42" font-weight="700" fill="{theme["text"]}">Matteo Di Mattia</text>')
    o.append(f'<text x="50" y="136" font-family="{FONT}" font-size="17" fill="{theme["muted"]}">Full-stack engineer · Rust, TypeScript, Lua</text>')
    o.append(f'<text x="50" y="162" font-family="{FONT}" font-size="15" fill="{theme["muted"]}">'
             f'Building the tools that keep AI coding agents on course.'
             f'<animate attributeName="opacity" from="0" to="1" begin="0.8s" dur="0.8s" fill="freeze"/></text>')

    def wave(i, y, amp, dur, opacity):
        return (f'<path d="{wave_path(y, amp)}" fill="{theme["waves"][i]}" opacity="{opacity}">'
                f'<animateTransform attributeName="transform" type="translate" from="0 0" to="-{WAVELEN} 0" '
                f'dur="{dur}s" repeatCount="indefinite"/></path>')

    o.append(wave(0, SEA_Y, AMP, 11, 0.9))

    # boat: bobbing and rolling, sitting between the back and front wave layers
    hull, sail = theme["hull"], theme["sail"]
    o.append(f'<g transform="translate(600,{SEA_Y + 4})">'
             f'<g><animateTransform attributeName="transform" type="translate" values="0 0;0 5;0 0" dur="4s" repeatCount="indefinite"/>'
             f'<g><animateTransform attributeName="transform" type="rotate" values="-3 40 0;3 40 0;-3 40 0" dur="4s" repeatCount="indefinite"/>'
             f'<rect x="38" y="-64" width="3" height="66" fill="{hull}"/>'
             f'<path d="M43,-60 L43,-8 L86,-8 Z" fill="{sail}" stroke="{hull}" stroke-width="1.5" stroke-linejoin="round"/>'
             f'<path d="M36,-56 L36,-12 L8,-12 Z" fill="{sail}" stroke="{hull}" stroke-width="1.5" stroke-linejoin="round" opacity="0.9"/>'
             f'<path d="M0,0 L84,0 L72,16 L12,16 Z" fill="{hull}"/>'
             f'</g></g></g>')

    o.append(wave(1, SEA_Y + 22, AMP + 2, 8, 0.85))
    o.append(wave(2, SEA_Y + 46, AMP, 6, 0.9))
    o.append('</g></svg>')
    return "\n".join(o)


if __name__ == "__main__":
    for name, theme in THEMES.items():
        path = Path(__file__).resolve().parent.parent / "assets" / f"hero-{name}.svg"
        path.write_text(render(theme), encoding="utf-8")
        print(f"wrote {path.name}")
