"""Render GitHub activity cards from real, public GitHub data.

Usage:
    GITHUB_TOKEN=... python scripts/build_stats.py            # live data (used by the workflow)
    python scripts/build_stats.py --placeholder               # "awaiting first sync" cards

Writes assets/generated/{overview,languages,contributions}-{dark,light}.svg.
The numbers come straight from the GitHub GraphQL API; nothing is estimated.
If the API call fails, the script exits non-zero and leaves existing cards untouched.
Standard library only.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from datetime import date, datetime, timezone

from theme import MONO, ROOT, SANS, card_frame, esc, load_profile, svg_open, write_themed

OUT = ROOT / "assets" / "generated"

QUERY = """
query($login: String!) {
  user(login: $login) {
    createdAt
    followers { totalCount }
    repositories(ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false, first: 100) {
      totalCount
      nodes {
        name
        languages(first: 12, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalRepositoriesWithContributedCommits
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount weekday } }
      }
    }
  }
}
"""


def fetch(login: str, token: str) -> dict:
    body = json.dumps({"query": QUERY, "variables": {"login": login}}).encode()
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "profile-stats-generator",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    return payload["data"]["user"]


def summarize(user: dict, cfg: dict) -> dict:
    excluded = set(cfg.get("exclude_repos", []))
    totals: dict[str, int] = {}
    for repo in user["repositories"]["nodes"]:
        if repo["name"] in excluded:
            continue
        for edge in repo["languages"]["edges"]:
            totals[edge["node"]["name"]] = totals.get(edge["node"]["name"], 0) + edge["size"]
    ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    limit = cfg.get("max_languages", 6)
    top, rest = ranked[:limit], ranked[limit:]
    if rest:
        top.append(("Other", sum(size for _, size in rest)))
    grand = sum(size for _, size in top) or 1

    cc = user["contributionsCollection"]
    days = [d for w in cc["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
    return {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "metrics": [
            ("Contributions", cc["contributionCalendar"]["totalContributions"], "last 12 months"),
            ("Commits", cc["totalCommitContributions"], "last 12 months"),
            ("Pull requests", cc["totalPullRequestContributions"], "last 12 months"),
            ("Public repos", user["repositories"]["totalCount"], "non-fork"),
        ],
        "languages": [(name, size / grand) for name, size in top],
        "days": days,
    }


# --------------------------------------------------------------------- renderers


def _caption(t: dict, W: int, H: int, text: str) -> str:
    return (
        f'<text x="{W - 30}" y="{H - 20}" text-anchor="end" font-family="{MONO}" font-size="13" '
        f'fill="{t["faint"]}">{esc(text)}</text>'
    )


def _heading(t: dict, label: str) -> str:
    return (
        f'<text x="30" y="50" font-family="{MONO}" font-size="14" letter-spacing="1.6" '
        f'fill="{t["cyan"]}">{esc(label.upper())}</text>'
    )


def _waiting(t: dict, W: int, H: int) -> str:
    return (
        f'<text x="{W / 2}" y="{H / 2 + 6}" text-anchor="middle" font-family="{MONO}" font-size="16" '
        f'fill="{t["muted"]}">Awaiting first sync from the stats workflow</text>'
    )


def render_overview(data: dict | None, theme: str, t: dict) -> str:
    W, H = 600, 260
    title = "GitHub activity"
    if data:
        title += ": " + ", ".join(f"{label} {value}" for label, value, _ in data["metrics"])
    s = [svg_open(W, H, title), card_frame(W, H, t, "ov"), _heading(t, "GitHub activity")]
    if not data:
        s += [_waiting(t, W, H), "</svg>"]
        return "".join(s)
    colors = [t["cyan"], t["blue"], t["violet"], t["text"]]
    for i, (label, value, note) in enumerate(data["metrics"]):
        col, row = i % 2, i // 2
        x, y = 30 + col * 280, 112 + row * 76
        s.append(
            f'<rect x="{x}" y="{y - 31}" width="2.5" height="56" rx="1" fill="{colors[i]}"/>'
            f'<text x="{x + 16}" y="{y}" font-family="{SANS}" font-size="34" font-weight="700" '
            f'fill="{t["text"]}">{value:,}</text>'
            f'<text x="{x + 16}" y="{y + 22}" font-family="{MONO}" font-size="14" fill="{t["muted"]}">'
            f'{esc(label)} <tspan fill="{t["faint"]}">· {esc(note)}</tspan></text>'
        )
    s += [_caption(t, W, H, f"public data · updated {data['updated']}"), "</svg>"]
    return "".join(s)


def render_languages(data: dict | None, theme: str, t: dict) -> str:
    W, H = 600, 260
    title = "Languages"
    if data:
        title += ": " + ", ".join(f"{n} {p:.1%}" for n, p in data["languages"])
    s = [svg_open(W, H, title), card_frame(W, H, t, "lg"), _heading(t, "Languages by code size")]
    if not data or not data["languages"]:
        s += [_waiting(t, W, H), "</svg>"]
        return "".join(s)
    palette = [t["cyan"], t["blue"], t["violet"], "#38bdf8" if theme == "dark" else "#0284c7",
               "#818cf8" if theme == "dark" else "#4f46e5", t["muted"], t["faint"]]
    bar_x, bar_y, bar_w = 30, 74, W - 60
    s.append(f'<clipPath id="lg-bar"><rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="10" rx="5"/></clipPath>')
    s.append('<g clip-path="url(#lg-bar)">')
    x = float(bar_x)
    for i, (_, share) in enumerate(data["languages"]):
        w = bar_w * share
        s.append(f'<rect x="{x:.2f}" y="{bar_y}" width="{w + 0.5:.2f}" height="10" fill="{palette[i % len(palette)]}"/>')
        x += w
    s.append("</g>")
    for i, (name, share) in enumerate(data["languages"]):
        col, row = i // 4, i % 4
        lx, ly = 30 + col * 280, 124 + row * 28
        s.append(
            f'<circle cx="{lx + 5}" cy="{ly - 4}" r="4.5" fill="{palette[i % len(palette)]}"/>'
            f'<text x="{lx + 18}" y="{ly}" font-family="{MONO}" font-size="15" fill="{t["text"]}">{esc(name)}</text>'
            f'<text x="{lx + 250}" y="{ly}" text-anchor="end" font-family="{MONO}" font-size="15" '
            f'fill="{t["muted"]}">{share:.1%}</text>'
        )
    s += [_caption(t, W, H, "public, non-fork repositories"), "</svg>"]
    return "".join(s)


def render_contributions(data: dict | None, theme: str, t: dict) -> str:
    W, H = 1200, 262
    total = sum(d["contributionCount"] for d in data["days"]) if data else 0
    s = [svg_open(W, H, f"Contribution calendar: {total} contributions in the last year" if data else "Contribution calendar"),
         card_frame(W, H, t, "cc"), _heading(t, "Contributions · last 12 months")]
    if not data:
        s += [_waiting(t, W, H), "</svg>"]
        return "".join(s)
    s.append(
        f'<text x="{W - 30}" y="46" text-anchor="end" font-family="{SANS}" font-size="17" fill="{t["muted"]}">'
        f'<tspan fill="{t["text"]}" font-weight="700">{total:,}</tspan> contributions</text>'
    )
    days = data["days"]
    peak = max((d["contributionCount"] for d in days), default=0) or 1
    ramp = [t["empty"], t["cyan"], t["blue"], t["violet"]]

    def fill(count: int) -> tuple[str, float]:
        if count == 0:
            return ramp[0], 1.0
        level = count / peak
        if level <= 0.25:
            return t["cyan"], 0.35
        if level <= 0.5:
            return t["cyan"], 0.7
        if level <= 0.75:
            return t["blue"], 0.95
        return t["violet"], 1.0

    cell, gap = 15, 4
    weeks = (len(days) + 6) // 7 + 1
    grid_w = weeks * (cell + gap)
    x0 = (W - grid_w) / 2 + 14
    y0 = 84
    first = date.fromisoformat(days[0]["date"])
    offset = days[0]["weekday"]  # GitHub weeks start on Sunday (weekday 0)
    last_month = None
    for d in days:
        dd = date.fromisoformat(d["date"])
        col = ((dd - first).days + offset) // 7
        row = d["weekday"]
        color, opacity = fill(d["contributionCount"])
        x, y = x0 + col * (cell + gap), y0 + row * (cell + gap)
        s.append(
            f'<rect x="{x:.1f}" y="{y}" width="{cell}" height="{cell}" rx="3.5" fill="{color}" '
            f'fill-opacity="{opacity}"><title>{d["contributionCount"]} on {d["date"]}</title></rect>'
        )
        if row == 0 and dd.month != last_month and dd.day <= 7:
            last_month = dd.month
            s.append(
                f'<text x="{x:.1f}" y="{y0 - 10}" font-family="{MONO}" font-size="12.5" '
                f'fill="{t["faint"]}">{dd.strftime("%b")}</text>'
            )
    for row, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        s.append(
            f'<text x="{x0 - 10:.1f}" y="{y0 + row * (cell + gap) + 11}" text-anchor="end" '
            f'font-family="{MONO}" font-size="12.5" fill="{t["faint"]}">{label}</text>'
        )
    lx = W - 30 - 5 * 16 - 44
    ly = H - 32
    s.append(f'<text x="{lx - 8}" y="{ly + 10}" text-anchor="end" font-family="{MONO}" font-size="13" fill="{t["faint"]}">less</text>')
    for i, (c, o) in enumerate([(ramp[0], 1), (t["cyan"], .35), (t["cyan"], .7), (t["blue"], .95), (t["violet"], 1)]):
        s.append(f'<rect x="{lx + i * 16}" y="{ly}" width="12" height="12" rx="3" fill="{c}" fill-opacity="{o}"/>')
    s.append(f'<text x="{lx + 5 * 16 + 4}" y="{ly + 10}" font-family="{MONO}" font-size="13" fill="{t["faint"]}">more</text>')
    s.append(
        f'<text x="30" y="{ly + 10}" font-family="{MONO}" font-size="13" fill="{t["faint"]}">'
        f"public contributions · updated {esc(data['updated'])}</text>"
    )
    s.append("</svg>")
    return "".join(s)


# -------------------------------------------------------------------------- main


def write_all(data: dict | None) -> None:
    for stem, renderer in (
        ("overview", render_overview),
        ("languages", render_languages),
        ("contributions", render_contributions),
    ):
        for path in write_themed(OUT, stem, lambda n, t, r=renderer: r(data, n, t)):
            print(path.relative_to(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--placeholder", action="store_true", help="write 'awaiting sync' cards, no API call")
    args = parser.parse_args()

    if args.placeholder:
        write_all(None)
        return 0

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("GITHUB_TOKEN is not set; refusing to render without real data.", file=sys.stderr)
        return 1
    profile = load_profile()
    try:
        user = fetch(profile["login"], token)
    except Exception as exc:  # network, auth or GraphQL error: keep the last good cards
        print(f"GitHub API request failed, cards left unchanged: {exc}", file=sys.stderr)
        return 1
    write_all(summarize(user, profile.get("stats", {})))
    return 0


if __name__ == "__main__":
    sys.exit(main())
