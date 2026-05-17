# RoboCup Links Automation

This repository now supports one-step event link updates via GitHub web UI.

## Quick update flow

1. Open the event form:
   - https://github.com/margauxmedwards/robocuplinks/issues/new?template=new-event-links.yml
2. Fill event links and submit.
3. The workflow automatically:
   - updates `redirects.json`
   - regenerates redirect HTML files under `r/`
  - regenerates static QR image files under `qr/`
   - commits changes back to `main`

## Prefilled issue creation

You can pre-format issue creation with query parameters. The repository homepage now includes an "Open prefilled form" button that builds this URL for you.
You can also paste one JSON object into the homepage and click "Fill fields from JSON" to auto-build the issue fields before opening the prefilled form.

Supported JSON shape:

```json
{
  "eventSlug": "qld-2026",
  "eventOverview": "https://example.com/event-overview",
  "links": {
    "Onstage": "https://example.com/onstage",
    "Line": "https://example.com/line",
    "Maze": "https://example.com/maze",
    "Soccer": "https://example.com/soccer",
    "Sumo": "https://example.com/sumo"
  }
}
```

Direct pattern:

```text
https://github.com/margauxmedwards/robocuplinks/issues/new?template=new-event-links.yml&event_slug=qld-2026&event_overview=https%3A%2F%2Fexample.com%2Fevent&paste_links=Onstage%3A%20https%3A%2F%2Fexample.com%2Fonstage%0ALine%3A%20https%3A%2F%2Fexample.com%2Fline
```

Use URL encoding for spaces and new lines (for example `%20` and `%0A`).

## What each form field creates

- `Event slug`: base path, for example `qld-2026`
- `Event overview URL`:
  - `r/<slug>.html`
  - `r/<slug>/index.html`
- `Paste links (Name: URL)`: one line per link, for example `Onstage: https://...`
- `Line URL`: `r/<slug>/line.html`
- `Maze URL`: `r/<slug>/maze.html`
- `OnStage URL`: `r/<slug>/onstage.html`
- `Soccer URL`: `r/<slug>/soccer.html`
- `Sumo URL`: `r/<slug>/sumo.html`
- `Extra links`: one line per `slug,url` -> `r/<slug>/<slug>.html`

If `Paste links (Name: URL)` is provided, names such as `Onstage`, `Line`, `Maze`, `Soccer`, and `Sumo` map to their standard short-link slugs automatically.

## Static QR files

- Every redirect in `redirects.json` generates a QR image at a matching path under `qr/`.
- Example:
  - `r/qld/line.html` -> `qr/r/qld/line.png`
- Each QR image includes the short-link URL printed below the code in a consistent format.
- Stale QR files are removed automatically when redirects are removed.

## Workflows

- `Apply Event Links From Issue`
  - Trigger: issue with label `event-links`
  - Parses form values and updates links
  - Closes the issue automatically after a successful commit
- `Update Redirect Links`
  - Trigger: push to `redirects.json` or script/workflow files
  - Regenerates redirect HTML files

## Local command

To regenerate redirect files manually:

```bash
python3 scripts/update_redirects.py --config redirects.json
```

The command now regenerates both redirect HTML and static QR image files.
