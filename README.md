# RoboCup Links Automation

This repo now uses one process only:

1. Open the admin page.
2. Fill links (or paste JSON) and open the prefilled GitHub issue.
3. GitHub Actions updates canonical short links and commits changes.

## Canonical links (stable)

These paths are reused for every event and overwritten with the latest URLs:

- `r/index.html`
- `r/event.html`
- `r/line.html`
- `r/maze.html`
- `r/onstage.html`
- `r/soccer.html`
- `r/sumo.html`

Because links are stable, QR codes for these paths can stay the same across events.
Existing QR PNG files are treated as long-lived assets and are not regenerated during normal event updates; only the redirect targets change underneath them.

## Event update workflow

- Issue template: `.github/ISSUE_TEMPLATE/new-event-links.yml`
- Processor workflow: `.github/workflows/apply-event-links-from-issue.yml`
- Redirect/QR generator workflow: `.github/workflows/update-redirect-links.yml`

## Environment

Runtime is managed by Pixi (`pixi.toml`).

Useful commands:

```bash
pixi run python scripts/apply_event_from_issue.py --issue-body issue-body.md --redirects redirects.json
pixi run update-redirects
```

If you ever need to intentionally rebuild the QR images, run:

```bash
pixi run python scripts/update_redirects.py --config redirects.json --refresh-qr
```
