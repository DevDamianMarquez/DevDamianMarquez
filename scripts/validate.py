"""Sanity checks for the profile: every SVG parses, and every local image the
README references exists in both themes.

Usage:
    python scripts/validate.py
"""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET

from theme import ROOT

SVG_NS = "{http://www.w3.org/2000/svg}"


def main() -> int:
    errors: list[str] = []

    svgs = sorted((ROOT / "assets").rglob("*.svg"))
    for path in svgs:
        rel = path.relative_to(ROOT)
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            errors.append(f"{rel}: invalid XML ({exc})")
            continue
        if root.tag != f"{SVG_NS}svg":
            errors.append(f"{rel}: root element is not <svg>")
        if root.find(f"{SVG_NS}title") is None:
            errors.append(f"{rel}: missing <title> (accessibility)")
        if re.search(r"(href|src)=\"https?://", path.read_text(encoding="utf-8")):
            errors.append(f"{rel}: references an external resource (GitHub blocks these in SVG images)")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    refs = set(re.findall(r'(?:src|srcset)="(\./assets/[^"]+|assets/[^"]+)"', readme))
    for ref in sorted(refs):
        if not (ROOT / ref.removeprefix("./")).is_file():
            errors.append(f"README.md: missing image {ref}")
        for a, b in (("-dark.svg", "-light.svg"), ("-light.svg", "-dark.svg")):
            if ref.endswith(a) and ref.replace(a, b) not in refs:
                errors.append(f"README.md: {ref} has no {b[1:-4]} counterpart")

    alts = re.findall(r"<img\b[^>]*>", readme)
    for tag in alts:
        if 'alt="' not in tag or 'alt=""' in tag:
            errors.append(f"README.md: <img> without alt text: {tag[:80]}")

    for e in errors:
        print("✗", e)
    print(f"Checked {len(svgs)} SVGs and {len(refs)} README image references: "
          f"{'OK' if not errors else f'{len(errors)} problem(s)'}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
