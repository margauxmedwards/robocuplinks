# Bot Endpoint (Cloudflare Worker)

This worker receives admin form submissions and triggers the GitHub Actions workflow using a server-side token.

## Why

- No user PAT in browser
- No issue authored by individual users
- Deployments run as automation (`github-actions[bot]`)

## Deploy

1. Install Wrangler:

```bash
npm install -g wrangler
```

2. Create a Worker project directory and copy `workers/submit-event-links-worker.js`.

3. Set secrets:

```bash
wrangler secret put GH_TOKEN
wrangler secret put ADMIN_PASSWORD
```

4. Set vars in `wrangler.toml`:

```toml
name = "robocup-links-bot"
main = "submit-event-links-worker.js"
compatibility_date = "2026-05-17"

[vars]
GH_OWNER = "margauxmedwards"
GH_REPO = "robocuplinks"
ALLOWED_ORIGIN = "https://margauxmedwards.github.io"
```

5. Deploy:

```bash
wrangler deploy
```

6. Set endpoint URL in `index.html` by defining `window.RCLINKS_BOT_ENDPOINT` before the main script:

```html
<script>
  window.RCLINKS_BOT_ENDPOINT = "https://robocup-links-bot.<subdomain>.workers.dev/submit-event-links";
</script>
```

## GitHub token scopes

Use a fine-grained token stored only in Worker secrets with this repo selected and:

- Actions: Read and write
- Contents: Read and write

## Request payload

`POST /submit-event-links`

```json
{
  "repo_owner": "margauxmedwards",
  "repo_name": "robocuplinks",
  "password": "...",
  "event_slug": "bne-2026",
  "event_overview": "https://example.com",
  "line_url": "https://example.com/line",
  "maze_url": "https://example.com/maze",
  "onstage_url": "https://example.com/onstage",
  "soccer_url": "https://example.com/soccer",
  "sumo_url": "https://example.com/sumo"
}
```
