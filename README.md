# RoboCup Links Automation

This repo supports two submission modes:

1. Open the admin page.
2. Fill links (or paste JSON) and submit.
3. If bot endpoint is configured: bot triggers dispatch workflow.
4. If bot endpoint is not configured: page opens a prefilled GitHub issue.
5. GitHub Actions updates canonical short links and commits changes.

In bot mode, the browser never stores a GitHub token and submissions are not tied to the submitter's GitHub profile.
In fallback issue mode, submissions are tied to the GitHub account that opens/submits the issue.

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
- Dispatch workflow (bot endpoint target): `.github/workflows/dispatch-event-links.yml`
- Redirect/QR generator workflow: `.github/workflows/update-redirect-links.yml`

## Bot endpoint setup

Deploy the Worker in `workers/submit-event-links-worker.js` and configure `window.RCLINKS_BOT_ENDPOINT` in `index.html`.

Detailed setup steps are in `workers/README.md`.

### Password behavior

- Bot mode (`window.RCLINKS_BOT_ENDPOINT` set): password is required.
- Fallback issue mode (no endpoint configured): password is not required.

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
