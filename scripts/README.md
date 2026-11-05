# Profile assets

Every image in the profile README is an SVG generated from code, in a dark and a
light variant. The README picks one with `<picture>` and `prefers-color-scheme`,
which GitHub maps to the viewer's theme.

| Script | Output | Source of truth |
| --- | --- | --- |
| `build_assets.py` | `assets/static/*.svg`: hero, headline, stack, project cards, links, footer | `profile.json` |
| `build_stats.py` | `assets/generated/*.svg`: activity, languages, contribution calendar | GitHub GraphQL API (public data) |
| `validate.py` | — | Checks every SVG parses and every README image exists in both themes |
| `theme.py` | — | Shared colors, fonts and SVG helpers |

Standard library only, Python 3.10+.

## Common edits

- **Change text, stack or projects:** edit `profile.json`, then run `python scripts/build_assets.py`.
  The bio and the links table are plain Markdown in `README.md`.
- **Add a project:** add an entry to `projects` in `profile.json`, rebuild, and add a
  `<picture>` block plus a table row in `README.md`.
- **Change colors:** edit `THEMES` in `theme.py` and rebuild both scripts.
- **Exclude a repo from the language card:** add it to `stats.exclude_repos`.

## Automation

`.github/workflows/profile-assets.yml` runs daily, on manual dispatch, and on pushes
that touch `profile.json` or `scripts/`. It rebuilds everything with the workflow's
built-in `GITHUB_TOKEN` (no personal token needed) and commits only if an asset changed.
If the GitHub API call fails, the previous activity cards are kept.

To run the stats locally: `GITHUB_TOKEN=<token> python scripts/build_stats.py`.
`--placeholder` writes "awaiting first sync" cards without calling the API.
