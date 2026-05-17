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

The prefilled button now creates a complete issue body (with all expected headings) plus the `event-links` label, so details are preserved reliably even if Issue Form field-prefill is inconsistent.

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

- `Event slug`: used for issue tracking and commit message context.
- `Event overview URL`:
  - `r/index.html`
  - `r/event.html`
- `Paste links (Name: URL)`: one line per link, for example `Onstage: https://...`
- `Line URL`: `r/line.html`
- `Maze URL`: `r/maze.html`
- `OnStage URL`: `r/onstage.html`
- `Soccer URL`: `r/soccer.html`
- `Sumo URL`: `r/sumo.html`
- `Extra links`: one line per `slug,url` -> `r/<slug>.html`

If `Paste links (Name: URL)` is provided, names such as `Onstage`, `Line`, `Maze`, `Soccer`, and `Sumo` map to their standard short-link slugs automatically.

Each new event overwrites these same canonical paths so existing QR codes keep working without regeneration.

## Static QR files

- Every redirect in `redirects.json` generates a QR image at a matching path under `qr/`.
- Example:
  - `r/qld/line.html` -> `qr/r/qld/line.png`
- Each QR image includes the short-link URL printed below the code in a consistent format.
- Stale QR files are removed automatically when redirects are removed.

## Workflows

- `Apply Event Links From Issue`
  - Trigger: issue with label `event-links` or title starting with `Event links:`
  - Parses form values and updates links
  - Closes the issue automatically after a successful commit
- `Update Redirect Links`
  - Trigger: push to `redirects.json` or script/workflow files
  - Regenerates redirect HTML files

## Local command

To regenerate redirect files manually:

```bash
pixi run update-redirects
```

The command now regenerates both redirect HTML and static QR image files.

## Environment management (Pixi)

This repo uses `pixi.toml` for a reproducible Python environment in both local development and GitHub Actions.

- Install Pixi once: https://pixi.sh/latest/
- Run scripts inside Pixi:

```bash
pixi run python scripts/apply_event_from_issue.py --issue-body issue-body.md --redirects redirects.json
pixi run update-redirects
```

This avoids runtime drift (for example Python 3.14 vs Pillow wheel compatibility) because the workflows and local runs share the same pinned environment.
