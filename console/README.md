# WorkReady Console

A **local-only** dashboard for editing simulation content and deploying it —
so content changes can be walked through with a colleague and shipped with
one click, no git knowledge required.

## Run it

```bash
cd workready-deploy/console
uv run --with fastapi --with uvicorn uvicorn app:app --port 7788
```

Open <http://127.0.0.1:7788> — loopback only, never exposed to the network.

Optional shared token (if someone joins remotely over a tunnel):

```bash
CONSOLE_TOKEN=some-secret uv run --with fastapi --with uvicorn uvicorn app:app --port 7788
# then open http://127.0.0.1:7788?token=some-secret
```

## What it edits

| Panel | Files |
|---|---|
| Company culture & facts | `<company>/brief.yaml` |
| Job listings | `<company>/jobs.json`, `content/jobs/*.md` |
| Employee personas | `<company>/content/employees/*.md` |
| Sign-in journey steps | `workready-portal/config.js` (`JOURNEY_STEPS`) |
| Primer story | `workready-primer/workready.ink` |

## The workflow

1. **Edit** a file → **Save**
2. **Build** the affected site (or "Build all") → preview at `/preview/<company>/`
3. **Deploy site content** → commits + pushes every dirty repo; GitHub Pages
   redeploys the live sites within a minute
4. **Redeploy API container** — only needed if `workready-api` files changed
   (e.g. nothing on a pure content day). Uses `--no-cache` deliberately: the
   container image clones the repos at build time, so a cached rebuild would
   ship stale code.

## What lives elsewhere

- **Student management** (codes, force-state, journey reports): the bundled
  **`/admin`** page — talks to the live API with `WORKREADY_ADMIN_TOKEN`.
  admin.html is intentionally no longer published on GitHub Pages.
- **Code changes**: normal git workflow; the console is for content only.

## Requirements

- The workspace checkout this console operates on (default: two directories
  up — override with `WORKREADY_HOME`)
- `ssh vps` access for the API deploy (alias configurable via `WORKREADY_VPS`)
- GitHub push credentials for the repos
