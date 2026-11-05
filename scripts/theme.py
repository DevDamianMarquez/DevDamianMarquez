"""Shared design tokens and small SVG helpers for every generated asset.

Each asset is rendered twice, once per GitHub theme. The README picks the
right file with <picture> + prefers-color-scheme, which GitHub maps to the
viewer's selected theme.
"""

from __future__ import annotations

import json
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent

THEMES: dict[str, dict[str, str]] = {
    "dark": {
        "bg_from": "#0a0f1c",
        "bg_to": "#0d1526",
        "surface": "#0e1624",
        "border": "#1d2a3d",
        "grid": "#142033",
        "text": "#e6edf3",
        "muted": "#8b98a9",
        "faint": "#56657a",
        "chip_bg": "#101b2b",
        "chip_border": "#22344d",
        "cyan": "#22d3ee",
        "blue": "#3b82f6",
        "violet": "#a78bfa",
        "empty": "#151f2e",
    },
    "light": {
        "bg_from": "#ffffff",
        "bg_to": "#f5f8fc",
        "surface": "#ffffff",
        "border": "#d8dfe9",
        "grid": "#eaf0f6",
        "text": "#0f172a",
        "muted": "#4f5d70",
        "faint": "#8a98ab",
        "chip_bg": "#f2f6fa",
        "chip_border": "#d3dce8",
        "cyan": "#0891b2",
        "blue": "#2563eb",
        "violet": "#7c3aed",
        "empty": "#edf1f6",
    },
}

SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, Helvetica, Arial, sans-serif"
MONO = "'JetBrains Mono', 'SFMono-Regular', 'Cascadia Code', Consolas, 'Liberation Mono', Menlo, monospace"

# Monospace glyphs are ~0.6em wide in every font of the stack above, which
# lets layout code size chips and typing animations without measuring text.
MONO_RATIO = 0.6


def load_profile() -> dict:
    return json.loads((ROOT / "profile.json").read_text(encoding="utf-8"))


def esc(text: str) -> str:
    return escape(text, {'"': "&quot;"})


def mono_width(text: str, size: float) -> float:
    return len(text) * size * MONO_RATIO


def svg_open(width: int, height: int, title: str, desc: str = "") -> str:
    desc_el = f"<desc>{esc(desc)}</desc>" if desc else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">'
        f"<title>{esc(title)}</title>{desc_el}"
    )


def card_frame(width: int, height: int, t: dict[str, str], gid: str, accent: bool = True) -> str:
    """Rounded panel with a soft gradient background and optional accent rule."""
    parts = [
        "<defs>",
        f'<linearGradient id="{gid}-bg" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{t["bg_from"]}"/><stop offset="1" stop-color="{t["bg_to"]}"/>'
        "</linearGradient>",
        f'<linearGradient id="{gid}-accent" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{t["cyan"]}"/><stop offset=".55" stop-color="{t["blue"]}"/>'
        f'<stop offset="1" stop-color="{t["violet"]}"/></linearGradient>',
        "</defs>",
        f'<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="14" '
        f'fill="url(#{gid}-bg)" stroke="{t["border"]}"/>',
    ]
    if accent:
        parts.append(
            f'<rect x="24" y=".5" width="{width - 48}" height="2" rx="1" fill="url(#{gid}-accent)" opacity=".9"/>'
        )
    return "".join(parts)


def chip(x: float, y: float, label: str, t: dict[str, str], size: float = 12.5) -> tuple[str, float]:
    """Monospace pill. Returns the markup and the chip width."""
    pad = 11
    w = mono_width(label, size) + pad * 2
    h = size + 13
    markup = (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{h / 2:.1f}" '
        f'fill="{t["chip_bg"]}" stroke="{t["chip_border"]}"/>'
        f'<text x="{x + w / 2:.1f}" y="{y + h / 2 + size * 0.35:.1f}" text-anchor="middle" '
        f'font-family="{MONO}" font-size="{size}" fill="{t["text"]}">{esc(label)}</text>'
    )
    return markup, w


def wrap(text: str, max_chars: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if len(candidate) > max_chars and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def write_themed(directory: Path, stem: str, render) -> list[Path]:
    """Render `render(theme_name, tokens)` for both themes into <stem>-<theme>.svg."""
    directory.mkdir(parents=True, exist_ok=True)
    written = []
    for name, tokens in THEMES.items():
        path = directory / f"{stem}-{name}.svg"
        path.write_text(render(name, tokens) + "\n", encoding="utf-8")
        written.append(path)
    return written
