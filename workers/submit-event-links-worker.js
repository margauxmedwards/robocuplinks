export default {
  async fetch(request, env) {
    const corsHeaders = buildCorsHeaders(request, env);

    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: corsHeaders });
    }

    if (request.method !== 'POST') {
      return jsonResponse({ error: 'Method not allowed.' }, 405, corsHeaders);
    }

    let payload;
    try {
      payload = await request.json();
    } catch {
      return jsonResponse({ error: 'Invalid JSON body.' }, 400, corsHeaders);
    }

    const password = String(payload.password || '').trim();
    if (!password) {
      return jsonResponse({ error: 'Admin password is required.' }, 400, corsHeaders);
    }
    if (!env.ADMIN_PASSWORD) {
      return jsonResponse({ error: 'Server is missing ADMIN_PASSWORD.' }, 500, corsHeaders);
    }
    if (password !== env.ADMIN_PASSWORD) {
      return jsonResponse({ error: 'Invalid admin password.' }, 401, corsHeaders);
    }

    const owner = String(payload.repo_owner || env.GH_OWNER || '').trim();
    const repo = String(payload.repo_name || env.GH_REPO || '').trim();
    const slug = slugify(String(payload.event_slug || ''));

    if (!owner || !repo) {
      return jsonResponse({ error: 'Repository owner/name is required.' }, 400, corsHeaders);
    }
    if (!slug) {
      return jsonResponse({ error: 'event_slug is required.' }, 400, corsHeaders);
    }
    if (!env.GH_TOKEN) {
      return jsonResponse({ error: 'Server is missing GH_TOKEN.' }, 500, corsHeaders);
    }

    const dispatchBody = {
      ref: 'main',
      inputs: {
        password,
        event_slug: slug,
        event_overview: sanitize(payload.event_overview),
        line_url: sanitize(payload.line_url),
        maze_url: sanitize(payload.maze_url),
        onstage_url: sanitize(payload.onstage_url),
        soccer_url: sanitize(payload.soccer_url),
        sumo_url: sanitize(payload.sumo_url)
      }
    };

    const endpoint = `https://api.github.com/repos/${owner}/${repo}/actions/workflows/dispatch-event-links.yml/dispatches`;
    const ghResp = await fetch(endpoint, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${env.GH_TOKEN}`,
        Accept: 'application/vnd.github+json',
        'Content-Type': 'application/json',
        'X-GitHub-Api-Version': '2022-11-28'
      },
      body: JSON.stringify(dispatchBody)
    });

    if (ghResp.status !== 204) {
      let message = `GitHub API returned ${ghResp.status}.`;
      try {
        const errorBody = await ghResp.json();
        if (errorBody && errorBody.message) {
          message = errorBody.message;
        }
      } catch {
        // Keep default message when response is not JSON.
      }
      return jsonResponse({ error: message }, ghResp.status, corsHeaders);
    }

    const runsUrl = `https://github.com/${owner}/${repo}/actions/workflows/dispatch-event-links.yml`;
    return jsonResponse({ ok: true, runs_url: runsUrl }, 200, corsHeaders);
  }
};

function sanitize(value) {
  return String(value || '').trim();
}

function slugify(input) {
  return String(input || '')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

function buildCorsHeaders(request, env) {
  const requestOrigin = request.headers.get('Origin') || '';
  const allowedOrigin = String(env.ALLOWED_ORIGIN || '').trim();

  const allowOrigin = allowedOrigin || requestOrigin || '*';
  return {
    'Access-Control-Allow-Origin': allowOrigin,
    'Access-Control-Allow-Methods': 'POST,OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    Vary: 'Origin'
  };
}

function jsonResponse(body, status, extraHeaders = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      ...extraHeaders
    }
  });
}
