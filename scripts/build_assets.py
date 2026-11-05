"""Render the static profile assets (hero, headline, stack, projects, links, footer).

Usage:
    python scripts/build_assets.py

All content comes from profile.json; edit that file and re-run. Output goes to
assets/static/<name>-<dark|light>.svg. Standard library only.
"""

from __future__ import annotations

from theme import (
    MONO,
    ROOT,
    SANS,
    card_frame,
    chip,
    esc,
    load_profile,
    mono_width,
    svg_open,
    wrap,
    write_themed,
)

OUT = ROOT / "assets" / "static"


# --------------------------------------------------------------------------- hero


def render_hero(p: dict, theme: str, t: dict[str, str]) -> str:
    W, H = 1200, 340
    gid = "hero"
    s = [svg_open(W, H, f"{p['name']} — {p['role_prefix']}, {p['role_accent']}")]
    s.append(card_frame(W, H, t, gid, accent=False))
    s.append(
        "<defs>"
        f'<pattern id="{gid}-grid" width="32" height="32" patternUnits="userSpaceOnUse">'
        f'<path d="M32 0H0V32" fill="none" stroke="{t["grid"]}" stroke-width="1"/></pattern>'
        f'<radialGradient id="{gid}-glow-a" cx=".78" cy=".2" r=".55">'
        f'<stop offset="0" stop-color="{t["cyan"]}" stop-opacity="{".16" if theme == "dark" else ".10"}"/>'
        f'<stop offset="1" stop-color="{t["cyan"]}" stop-opacity="0"/></radialGradient>'
        f'<radialGradient id="{gid}-glow-b" cx=".95" cy=".95" r=".5">'
        f'<stop offset="0" stop-color="{t["violet"]}" stop-opacity="{".14" if theme == "dark" else ".08"}"/>'
        f'<stop offset="1" stop-color="{t["violet"]}" stop-opacity="0"/></radialGradient>'
        f'<linearGradient id="{gid}-text" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{t["cyan"]}"/><stop offset=".6" stop-color="{t["blue"]}"/>'
        f'<stop offset="1" stop-color="{t["violet"]}"/></linearGradient>'
        f'<linearGradient id="{gid}-fade" x1="0" y1="0" x2="1" y2="0">'
        '<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".45" stop-color="#fff" stop-opacity=".9"/>'
        '<stop offset="1" stop-color="#fff" stop-opacity="1"/></linearGradient>'
        f'<mask id="{gid}-mask"><rect width="{W}" height="{H}" fill="url(#{gid}-fade)"/></mask>'
        f'<clipPath id="{gid}-clip"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="13"/></clipPath>'
        "<style>"
        ".flow{stroke-dasharray:4 7;animation:flow 1.6s linear infinite}"
        "@keyframes flow{to{stroke-dashoffset:-22}}"
        ".pulse{animation:pulse 2.4s ease-in-out infinite;transform-origin:center;transform-box:fill-box}"
        "@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.35;transform:scale(.8)}}"
        "@media (prefers-reduced-motion:reduce){.flow,.pulse{animation:none}}"
        "</style>"
        "</defs>"
    )
    s.append(
        f'<g clip-path="url(#{gid}-clip)">'
        f'<rect width="{W}" height="{H}" fill="url(#{gid}-grid)" mask="url(#{gid}-mask)"/>'
        f'<rect width="{W}" height="{H}" fill="url(#{gid}-glow-a)"/>'
        f'<rect width="{W}" height="{H}" fill="url(#{gid}-glow-b)"/>'
        "</g>"
    )

    # Left column: identity.
    x = 64
    s.append(
        f'<text x="{x}" y="78" font-family="{MONO}" font-size="17" fill="{t["muted"]}">'
        f'<tspan fill="{t["cyan"]}">~</tspan> $ whoami</text>'
    )
    s.append(
        f'<text x="{x - 3}" y="146" font-family="{SANS}" font-size="60" font-weight="700" '
        f'letter-spacing="-1.5" fill="{t["text"]}">{esc(p["name"])}</text>'
    )
    s.append(
        f'<text x="{x}" y="192" font-family="{SANS}" font-size="27" font-weight="500" fill="{t["muted"]}">'
        f'{esc(p["role_prefix"])}  <tspan fill="{t["faint"]}">/</tspan>  '
        f'<tspan fill="url(#{gid}-text)" font-weight="600">{esc(p["role_accent"])}</tspan></text>'
    )
    stack_line = "  ·  ".join(p["core_stack"])
    s.append(
        f'<text x="{x}" y="236" font-family="{MONO}" font-size="18" fill="{t["text"]}" opacity=".82">'
        f"{esc(stack_line)}</text>"
    )
    s.append(f'<line x1="{x}" y1="262" x2="{x + 420}" y2="262" stroke="{t["border"]}"/>')
    s.append(
        f'<circle class="pulse" cx="{x + 5}" cy="291" r="5" fill="{t["cyan"]}"/>'
        f'<text x="{x + 20}" y="297" font-family="{MONO}" font-size="16.5" fill="{t["muted"]}">'
        f'{esc(p["location"])}  <tspan fill="{t["faint"]}">·</tspan>  {esc(p["timezone"])}  '
        f'<tspan fill="{t["faint"]}">·</tspan>  <tspan fill="{t["text"]}">{esc(p["availability"])}</tspan></text>'
    )

    # Right column: a tiny request-flow diagram (client -> API -> Postgres / LLM).
    def node(nx: float, ny: float, label: str, sub: str, color: str) -> str:
        w, h = NODE_W, 58
        return (
            f'<rect x="{nx}" y="{ny}" width="{w}" height="{h}" rx="10" fill="{t["surface"]}" '
            f'stroke="{t["chip_border"]}"/>'
            f'<rect x="{nx}" y="{ny + 14}" width="2.5" height="{h - 28}" rx="1" fill="{color}"/>'
            f'<text x="{nx + 16}" y="{ny + 25}" font-family="{MONO}" font-size="15.5" font-weight="600" '
            f'fill="{t["text"]}">{esc(label)}</text>'
            f'<text x="{nx + 16}" y="{ny + 45}" font-family="{MONO}" font-size="12.5" fill="{t["muted"]}">'
            f"{esc(sub)}</text>"
        )

    cx, ax, rx = 690, 866, 1046
    cy, ay = 143, 143
    py, ly = 70, 216
    s.append(f'<g fill="none" stroke-width="1.6" stroke-linecap="round">')
    s.append(f'<path class="flow" d="M{cx + NODE_W} {cy + 29}H{ax}" stroke="{t["cyan"]}"/>')
    s.append(
        f'<path class="flow" d="M{ax + NODE_W} {ay + 20}C{ax + 150} {ay + 20} {rx - 22} {py + 29} {rx} {py + 29}" '
        f'stroke="{t["blue"]}"/>'
    )
    s.append(
        f'<path class="flow" d="M{ax + NODE_W} {ay + 34}C{ax + 150} {ay + 34} {rx - 22} {ly + 29} {rx} {ly + 29}" '
        f'stroke="{t["violet"]}"/>'
    )
    s.append("</g>")
    s.append(
        f'<text x="{(cx + NODE_W + ax) / 2}" y="{cy + 18}" text-anchor="middle" font-family="{MONO}" '
        f'font-size="12" fill="{t["faint"]}">HTTPS</text>'
    )
    s.append(node(cx, cy, "client", "REST · JSON", t["muted"]))
    s.append(node(ax, ay, "FastAPI", "auth · schemas", t["cyan"]))
    s.append(node(rx, py, "PostgreSQL", "SQLAlchemy", t["blue"]))
    s.append(node(rx, ly, "LLM", "JSON output", t["violet"]))
    s.append("</svg>")
    return "".join(s)


NODE_W = 134


# ---------------------------------------------------------------------- headline


def render_typing(p: dict, theme: str, t: dict[str, str]) -> str:
    """Typewriter headline using SMIL, so it animates inside GitHub's <img> sandbox."""
    W, H = 960, 52
    size = 21
    char_w = size * 0.6
    type_s, hold_s, delete_s, gap_s = 0.055, 2.4, 0.022, 0.35
    lines = p["typing_lines"]

    slots = []
    total = 0.0
    for line in lines:
        n = len(line)
        start = total
        typed = start + n * type_s
        held = typed + hold_s
        deleted = held + n * delete_s
        total = deleted + gap_s
        slots.append((line, start, typed, held, deleted))

    s = [svg_open(W, H, "Headline: " + " | ".join(lines))]
    s.append(
        "<defs>"
        f'<linearGradient id="tp-grad" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{t["cyan"]}"/><stop offset=".6" stop-color="{t["blue"]}"/>'
        f'<stop offset="1" stop-color="{t["violet"]}"/></linearGradient>'
        "</defs>"
    )
    baseline = H / 2 + size * 0.36
    for i, (line, start, typed, held, deleted) in enumerate(slots):
        n = len(line)
        full = n * char_w
        x0 = (W - full - 2 * char_w) / 2  # leave room for the "> " prompt
        tx = x0 + 2 * char_w

        # Keyframes: one step per character while typing and deleting.
        frames: list[tuple[float, float]] = [(0.0, 0.0)]
        if start > 0:
            frames.append((start, 0.0))
        for k in range(1, n + 1):
            frames.append((start + k * type_s, k * char_w))
        frames.append((held, full))
        for k in range(1, n + 1):
            frames.append((held + k * delete_s, full - k * char_w))
        if deleted < total:
            frames.append((total, 0.0))
        times = ";".join(f"{ft / total:.5f}" for ft, _ in frames)
        widths = ";".join(f"{fw:.1f}" for _, fw in frames)
        cursor_x = ";".join(f"{tx + fw:.1f}" for _, fw in frames)
        if start > 0:
            vis_times = f"0;{start / total:.5f};{deleted / total:.5f}"
            vis_values = "hidden;visible;hidden"
        else:
            vis_times = f"0;{deleted / total:.5f}"
            vis_values = "visible;hidden"

        s.append(
            f'<clipPath id="tp-clip-{i}"><rect x="{tx:.1f}" y="0" width="0" height="{H}">'
            f'<animate attributeName="width" values="{widths}" keyTimes="{times}" dur="{total:.2f}s" '
            'calcMode="discrete" repeatCount="indefinite"/></rect></clipPath>'
        )
        s.append(
            f'<g visibility="{"visible" if start == 0 else "hidden"}">'
            f'<animate attributeName="visibility" values="{vis_values}" keyTimes="{vis_times}" '
            f'dur="{total:.2f}s" calcMode="discrete" repeatCount="indefinite"/>'
            f'<text x="{x0:.1f}" y="{baseline:.1f}" font-family="{MONO}" font-size="{size}" '
            f'fill="{t["faint"]}">&gt;</text>'
            f'<text x="{tx:.1f}" y="{baseline:.1f}" font-family="{MONO}" font-size="{size}" '
            f'textLength="{full:.1f}" lengthAdjust="spacingAndGlyphs" fill="url(#tp-grad)" '
            f'clip-path="url(#tp-clip-{i})" font-weight="500">{esc(line)}</text>'
            f'<rect y="{H / 2 - size * 0.62:.1f}" width="2" height="{size * 1.15:.1f}" fill="{t["cyan"]}">'
            f'<animate attributeName="x" values="{cursor_x}" keyTimes="{times}" dur="{total:.2f}s" '
            'calcMode="discrete" repeatCount="indefinite"/>'
            '<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.5;1" dur="1s" '
            'repeatCount="indefinite"/></rect>'
            "</g>"
        )
    s.append("</svg>")
    return "".join(s)


# ------------------------------------------------------------------------- stack


def render_stack(p: dict, theme: str, t: dict[str, str]) -> str:
    W = 1200
    label_w, pad_x = 170, 44
    chip_size, chip_h, gap, line_gap, row_pad = 16, 29, 10, 10, 15
    rows = p["stack"]

    # Lay out chips first so rows can wrap onto a second line when needed.
    layout = []
    for row in rows:
        lines: list[list[tuple[str, float]]] = [[]]
        x = pad_x + label_w
        for item in row["items"]:
            w = mono_width(item, chip_size) + 22
            if x + w > W - pad_x and lines[-1]:
                lines.append([])
                x = pad_x + label_w
            lines[-1].append((item, x))
            x += w + gap
        layout.append(lines)

    H = 36 + sum(len(ls) * chip_h + (len(ls) - 1) * line_gap + 2 * row_pad for ls in layout) + 22
    s = [svg_open(W, H, "Tech stack: " + "; ".join(f"{r['group']}: {', '.join(r['items'])}" for r in rows))]
    s.append(card_frame(W, H, t, "stack"))
    y = 36
    for i, (row, lines) in enumerate(zip(rows, layout)):
        top = y + row_pad
        s.append(
            f'<text x="{pad_x}" y="{top + chip_h / 2 + 5}" font-family="{MONO}" font-size="14" '
            f'letter-spacing="1.8" fill="{t["cyan"] if i % 2 == 0 else t["violet"]}">'
            f'{esc(row["group"].upper())}</text>'
        )
        for k, line in enumerate(lines):
            for item, x in line:
                markup, _ = chip(x, top + k * (chip_h + line_gap), item, t, size=chip_size)
                s.append(markup)
        y = top + len(lines) * chip_h + (len(lines) - 1) * line_gap + row_pad
        if i < len(rows) - 1:
            s.append(
                f'<line x1="{pad_x}" y1="{y}" x2="{W - pad_x}" y2="{y}" '
                f'stroke="{t["border"]}" stroke-dasharray="2 5" opacity=".7"/>'
            )
    s.append("</svg>")
    return "".join(s)


# ---------------------------------------------------------------------- projects


def render_project(project: dict, theme: str, t: dict[str, str]) -> str:
    W, H = 600, 330
    gid = f"pj-{project['id']}"
    pad = 30
    s = [svg_open(W, H, f"{project['name']} — {project['tag']}", project["description"])]
    s.append(card_frame(W, H, t, gid))
    s.append(
        f'<text x="{pad}" y="50" font-family="{MONO}" font-size="13" letter-spacing="1.2" '
        f'fill="{t["cyan"]}">{esc(project["tag"].upper())}</text>'
    )
    status = project["status"]
    sw = mono_width(status, 12.5) + 32
    s.append(
        f'<rect x="{W - pad - sw:.1f}" y="31" width="{sw:.1f}" height="26" rx="13" fill="none" '
        f'stroke="{t["chip_border"]}"/>'
        f'<circle cx="{W - pad - sw + 13:.1f}" cy="44" r="3.5" fill="{t["violet"]}"/>'
        f'<text x="{W - pad - sw + 22:.1f}" y="48.5" font-family="{MONO}" font-size="12.5" '
        f'fill="{t["muted"]}">{esc(status)}</text>'
    )
    s.append(
        f'<text x="{pad - 1}" y="100" font-family="{SANS}" font-size="35" font-weight="700" '
        f'letter-spacing="-.6" fill="{t["text"]}">{esc(project["name"])}</text>'
    )
    for j, line in enumerate(wrap(project["description"], 60)[:4]):
        s.append(
            f'<text x="{pad}" y="{138 + j * 25}" font-family="{SANS}" font-size="17" '
            f'fill="{t["muted"]}">{esc(line)}</text>'
        )
    x, y = pad, 245
    for item in project["tech"]:
        markup, w = chip(x, y, item, t, size=13)
        if x + w > W - pad:
            break
        s.append(markup)
        x += w + 7
    s.append(f'<line x1="{pad}" y1="{H - 38}" x2="{W - pad}" y2="{H - 38}" stroke="{t["border"]}"/>')
    s.append(
        f'<text x="{pad}" y="{H - 15}" font-family="{MONO}" font-size="13.5" fill="{t["faint"]}">'
        f'{esc(project["footer"])}</text>'
        f'<text x="{W - pad}" y="{H - 16}" text-anchor="end" font-family="{MONO}" font-size="13" '
        f'fill="{t["cyan"]}">↗</text>'
    )
    s.append("</svg>")
    return "".join(s)


# ------------------------------------------------------------------------- links

ICONS = {
    # Simple stroked glyphs drawn in a 16x16 box; no third-party logos.
    "portfolio": '<circle cx="8" cy="8" r="6.5"/><path d="M1.5 8h13M8 1.5c2 2 2.8 4.2 2.8 6.5S10 12.5 8 14.5M8 1.5C6 3.5 5.2 5.7 5.2 8S6 12.5 8 14.5"/>',
    "linkedin": '<rect x="1.5" y="1.5" width="13" height="13" rx="2.5"/><path d="M5 7v4.5M5 4.6v.1M8 11.5V7M8 9c0-1.4.8-2 1.8-2s1.7.6 1.7 2v2.5"/>',
    "email": '<rect x="1.5" y="3" width="13" height="10" rx="2"/><path d="m2 4 6 5 6-5"/>',
    "resume": '<path d="M4 1.5h5.5L13 5v9.5H4z"/><path d="M9.5 1.5V5H13M6.5 8.5h4M6.5 11h4"/>',
}


def render_link(link: dict, theme: str, t: dict[str, str]) -> str:
    size = 14
    W = int(mono_width(link["label"], size) + 92)
    H = 44
    gid = f"ln-{link['id']}"
    s = [svg_open(W, H, link["label"])]
    s.append(
        f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{t["cyan"]}"/><stop offset="1" stop-color="{t["violet"]}"/>'
        "</linearGradient></defs>"
        f'<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="{(H - 1.5) / 2}" '
        f'fill="{t["surface"]}" stroke="url(#{gid})" stroke-width="1.5"/>'
        f'<g transform="translate(20 14)" fill="none" stroke="{t["cyan"]}" stroke-width="1.4" '
        f'stroke-linecap="round" stroke-linejoin="round">{ICONS[link["id"]]}</g>'
        f'<text x="46" y="{H / 2 + 5}" font-family="{MONO}" font-size="{size}" font-weight="500" '
        f'fill="{t["text"]}">{esc(link["label"])}</text>'
        f'<text x="{W - 22}" y="{H / 2 + 5}" text-anchor="end" font-family="{MONO}" font-size="13" '
        f'fill="{t["faint"]}">↗</text>'
    )
    s.append("</svg>")
    return "".join(s)


# ------------------------------------------------------------------------ footer


def render_footer(p: dict, theme: str, t: dict[str, str]) -> str:
    W, H = 1200, 110
    s = [svg_open(W, H, f"{p['name']} · {p['role_prefix']} · {p['location']}")]
    s.append(
        "<defs>"
        '<linearGradient id="ft-line" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{t["cyan"]}" stop-opacity="0"/>'
        f'<stop offset=".25" stop-color="{t["cyan"]}"/><stop offset=".5" stop-color="{t["blue"]}"/>'
        f'<stop offset=".75" stop-color="{t["violet"]}"/>'
        f'<stop offset="1" stop-color="{t["violet"]}" stop-opacity="0"/></linearGradient>'
        '<linearGradient id="ft-shine" x1="0" y1="0" x2="1" y2="0">'
        '<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".9"/>'
        '<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        "<style>.shine{animation:shine 6s ease-in-out infinite}"
        "@keyframes shine{0%{transform:translateX(-200px)}60%,100%{transform:translateX(1200px)}}"
        "@media (prefers-reduced-motion:reduce){.shine{display:none}}</style>"
        "</defs>"
    )
    s.append(f'<rect x="100" y="24" width="1000" height="1.5" fill="url(#ft-line)"/>')
    if theme == "dark":
        s.append('<rect class="shine" x="0" y="23.5" width="160" height="2.5" fill="url(#ft-shine)" opacity=".5"/>')
    s.append(
        f'<text x="{W / 2}" y="66" text-anchor="middle" font-family="{SANS}" font-size="20" font-weight="600" '
        f'fill="{t["text"]}">{esc(p["name"])}<tspan fill="{t["faint"]}" font-weight="400">  ·  </tspan>'
        f'<tspan fill="{t["muted"]}" font-weight="500">Backend &amp; AI Engineering</tspan></text>'
        f'<text x="{W / 2}" y="94" text-anchor="middle" font-family="{MONO}" font-size="14.5" '
        f'fill="{t["faint"]}">{esc(p["location"])}  ·  building reliable software, one endpoint at a time</text>'
    )
    s.append("</svg>")
    return "".join(s)


# -------------------------------------------------------------------------- main


def main() -> None:
    p = load_profile()
    written = []
    written += write_themed(OUT, "hero", lambda n, t: render_hero(p, n, t))
    written += write_themed(OUT, "headline", lambda n, t: render_typing(p, n, t))
    written += write_themed(OUT, "stack", lambda n, t: render_stack(p, n, t))
    for project in p["projects"]:
        written += write_themed(OUT, f"project-{project['id']}", lambda n, t, pr=project: render_project(pr, n, t))
    for link in p["links"]:
        written += write_themed(OUT, f"link-{link['id']}", lambda n, t, ln=link: render_link(ln, n, t))
    written += write_themed(OUT, "footer", lambda n, t: render_footer(p, n, t))
    for path in written:
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
