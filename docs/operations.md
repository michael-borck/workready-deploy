# Operations

[Project home](../README.md) · [Architecture](architecture.md) · [Configuration](configuration.md) · [Privacy](privacy.md)

This is the current operating guide. The [0.3.0 release record](../PRIVACY-RELEASE.md) is dated rollout evidence, not the default deployment recipe for every machine.

## Deployed topology

As verified on 14 September 2026:

- Public static sites use GitHub Pages. The primer is branch-published from `main` at `/`; the other static sites use their Pages workflows.
- `ssh vps` reaches `srv858112`, with IPv4 `31.97.67.189` at that verification date.
- WorkReady's Compose project is `~/homelab/workready`, containing `docker-compose.yml`, its deployed override, `.env`, `data/`, and the `workready-deploy/` checkout.
- The API service/container is `workready-api`, using the public `ghcr.io/michael-borck/workready` image. It runs uvicorn only.
- The API joins `caddy_default`. The shared `caddy` service owns ports 80/443 and proxies `workready-api.eduserver.au` to `workready-api:8000`.
- The host's `data/` maps to `/opt/workready/data`, including the database and filtered mail PDFs.
- `simulation-staff` is a separate CloudCore service. It is not WorkReady's lecturer dashboard.

Verify DNS, actual container configuration and the running version before changing infrastructure. Host addresses and container IPs are not permanent constants.

## Build and publish static sites

| Repository | Build | What Pages publishes |
|---|---|---|
| `workready-deploy` project landing page | No build; edit `site/` | `site/` via the project Pages workflow, after Pages is enabled |
| `workready-portal` | No asset build; run its JavaScript checks | Repository root via Pages workflow |
| `workready-jobs` | `python3 build.py` | Checked-in `dist/` via Pages workflow |
| Each company | `uv run --quiet --with pyyaml --with jinja2 --with markdown python3 site/build.py` | Checked-in `dist/` via Pages workflow |
| `workready-primer` | `bash build.sh` after Ink edits | Repository root from the Pages branch setting |

Run these commands from the named repository. Company/job-board Pages workflows upload the artifacts; they do not run their Python builders. The primer's branch publication does not compile Ink. Include generated outputs in the source change that needs them.

Review each repository's `git status` and diff. Stage only the intended files and outputs, commit them, and push `main` when ready to publish. Use the [local console](../console/README.md) for its supported content workflow, or Git directly for code changes.

Publishing a static company site does not refresh the API's baked-in personas or startup job cache. If runtime data changed, also build and deploy the API image after publishing its inputs.

## Project landing page

The public overview lives in [`site/`](../site/index.html). It introduces the journey and links to the student portal, primer, job board, six company sites and project guides. It is separate from the student portal at `https://workready.eduserver.au/`.

Edit `site/index.html` for copy and destinations, `site/assets/style.css` for layout, and the SVG files for illustration and favicon. All assets are local. The page uses native links and expandable FAQ sections, with no JavaScript, third-party fonts, analytics or API requests. Visiting one of its linked services is subject to that service's data handling.

Preview from this repository:

```bash
python3 -m http.server 8080 --bind 127.0.0.1 --directory site
```

Open `http://127.0.0.1:8080`. Check desktop/mobile layouts, keyboard navigation, FAQ expansion and link destinations before publication. Asset URLs are relative so the same page works at a GitHub project subpath or a custom domain.

### First publication

1. If Pages is not yet enabled for this repository, set **Settings → Pages → Source** to **GitHub Actions**. Publication currently uses this method; do not switch back to **Deploy from a branch**, which publishes a different folder and overwrites the page.
2. Commit and push the reviewed `site/` files and `.github/workflows/pages.yml` to `main`.
3. Check the **Publish project landing page** workflow. It uploads only `site/` and deploys it with the standard Pages actions. A push changing the page/workflow triggers publication; manual dispatch is also available.
4. Open `https://michael-borck.github.io/workready-deploy/` after the run succeeds.

The repository's container-build workflow is separate and also runs on pushes to `main`. Publishing the project page does not recreate the VPS API container.

### DNS and an optional custom domain

Start with the standard GitHub Pages address. No DNS record or `CNAME` file is needed. Keep `workready.eduserver.au` pointing at the student portal.

If a dedicated overview address is wanted later, choose a different hostname, such as `about.workready.eduserver.au`. Add that exact name in **Settings → Pages → Custom domain**, then create a DNS `CNAME` from the chosen hostname to **`michael-borck.github.io`**. A DNS CNAME target is a hostname, not `https://...` and not a path ending in `/workready-deploy/`.

Wait for GitHub's DNS check and certificate provisioning, then enable **Enforce HTTPS**. With this Actions publication method, configure the custom domain in repository settings; a committed `CNAME` file is not required. Update published overview links when adopting the new address. GitHub's [custom-domain guide](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site) covers domain verification and troubleshooting.

## Build the bundled API image on GitHub

The bundled image is built by [`.github/workflows/build.yml`](../.github/workflows/build.yml) in this repository. It runs `install.sh`, which clones the application/company repositories during image construction. It also runs the API privacy tests before publishing the image.

1. Publish every required application/content repository first.
2. Trigger the bundled build by pushing a deploy-repository change or dispatching the workflow:

   ```bash
   gh workflow run build.yml --repo michael-borck/workready-deploy --ref main
   gh run list --repo michael-borck/workready-deploy --workflow build.yml --limit 5
   ```

3. Watch the matching run and check its result:

   ```bash
   gh run watch RUN_ID --repo michael-borck/workready-deploy --exit-status
   ```

Replace `RUN_ID` with the run you just requested. The console automates this request/wait/pull sequence.

The API repository has its own Docker workflow and smaller API image; it is not the bundled image used by this VPS deployment. Pushing only the API repository does not automatically rebuild `ghcr.io/michael-borck/workready`.

Tags include `latest` and a short deploy-repository commit tag. A workflow dispatch can rebuild the same recipe against newer input repositories, so a short recipe tag is not an immutable record of every dependency. Record the registry digest and source revisions for a release you may need to reproduce.

Use GitHub-built images for routine VPS updates. A previous VPS rebuild stalled downloading the unused bundled Caddy dependency. Also, a cached local build can retain old cloned repositories even after source pushes. Restarting the container does not run `git pull` or rebuild anything.

## Update the existing VPS

### Standard deployed Compose path

After the relevant GitHub image build succeeds:

```bash
ssh vps
git -C ~/homelab/workready/workready-deploy pull --ff-only
docker compose --project-directory ~/homelab/workready pull
docker compose --project-directory ~/homelab/workready up -d --no-build
curl --fail --silent --show-error https://workready-api.eduserver.au/health
```

The project directory selects the VPS's actual Compose files, including its auto-loaded override. A pull updates the image; `up` recreates the service when needed. `git pull` updates recipes/docs, not a running container. `docker compose restart` does not apply changed environment or image configuration.

### If using the local console's pacing deployment

The console uses an explicit Compose file set: the VPS base file, `workready-deploy/compose.privacy.yml`, and its generated `compose.pacing.yml`. Explicit `-f` files do not automatically include `docker-compose.override.yml`.

Prefer the console for subsequent updates to a console-managed pacing configuration. If operating manually, use the same file set and inspect its selected image/settings first. Do not accidentally drop the pacing overlay by switching to the standard command above. The console selects the image produced by its requested GitHub run; a manual pull of that tag alone does not select a different release.

Keep `.env` and generated secret-bearing configuration private and out of Git. The existing VPS maps its `WR_TOKEN` variable to the API's `WORKREADY_ADMIN_TOKEN`. Code reads the latter. [Configuration](configuration.md) documents session limits, trusted proxy settings and provider selection.

## Coordinated API and frontend releases

Changes to login/request formats must be released together. For the 0.3.0 transition, old code-bearing URLs return 410; old cached browser clients need a refresh.

1. Run the checks below and prepare a compatible image and static outputs.
2. Back up data and preserve any legacy out-of-volume attachments before replacing a container.
3. Use a WorkReady-only maintenance response when necessary to prevent writes during the cutover. Do not stop unrelated services on the shared VPS.
4. Publish the portal's shared session client and the matching job-board/company clients. Check Pages workflow results and actual public assets.
5. Deploy the new API image with the intended Compose files, storage paths and proxy trust settings.
6. Verify health, authentication, ownership denials, upload flow and preserved records. Reopen routing once the compatible pieces are ready.
7. Run any production smoke checks with newly issued synthetic identities, then erase them. Record the release/digest and backup location.

Versioned script URLs reduce mixed-version browser caches. They do not make separate GitHub Pages publications atomic.

## Caddy and troubleshooting

The VPS's active Caddy setup is separate from this repository's bundled [Caddyfile](../Caddyfile). Its host file is `~/homelab/caddy/Caddyfile`, mounted into the shared container at `/etc/caddy/Caddyfile`.

- An API root 404 is not a failed health check. Use `/health`.
- A student 401 concerns a missing/expired/revoked session. Re-entering an issued code obtains a new session; the old code-in-URL method is not supported.
- A 429 means a request budget was exceeded. Check `Retry-After`, classroom NAT behaviour and trusted proxy configuration.
- A 502 usually indicates proxy/upstream trouble. Verify the `workready-api` container and its network before changing the Caddyfile.
- If DNS targets the wrong server, correct that before debugging application routes.
- A bind-mounted single file can retain an old inode after an editor replaces the host file. Compare the host and container views if a Caddy reload says "unchanged" unexpectedly. Plan any container restart with the other hosted services in mind.
- Caddy's JSON API uses `PATCH` to replace an existing array element; `POST` can append. Verify the effective WorkReady route and do not overwrite unrelated route changes.

The current privacy override disables uvicorn access logs. Proxy logging is a separate setting. Avoid logging credentials, request bodies or tokens while troubleshooting.

## Backup and recovery

The console does not create or encrypt backups. Before a stateful release:

1. Choose a private backup directory outside repositories and web roots, with restricted directory/file permissions.
2. Freeze writes or use SQLite's backup API for a consistent database snapshot. Do not copy a live `workready.db` alone and assume its WAL is included.
3. Preserve attachments and the deployment configuration needed for recovery. Keep secret-bearing `.env`/container metadata protected.
4. Run `PRAGMA integrity_check` on the backup, record its checksum and compare record counts after migration.
5. Keep a known previous image or digest and state which database version it can safely use.

For legacy 0.2 mail files outside the data volume, use [`scripts/migrate_attachments.py`](https://github.com/michael-borck/workready-api/blob/main/scripts/migrate_attachments.py) with the preserved legacy root, database, durable destination and any required container-prefix mappings. Check its missing-file count. It must run offline against the intended database. The [release record](../PRIVACY-RELEASE.md) records the completed 0.3.0 migration observations.

If a health check fails, keep the service in maintenance and inspect logs, image revision and storage. An image rollback does not roll back the database. Restoring a backup can reintroduce erased data and old credentials; reconcile them before reopening. Do not expose the known-unprotected 0.2 API as a routine rollback target.

Choose a backup-expiry policy alongside the cohort-retention policy. Neither is implemented as an automatic schedule by the local console. See [privacy and access](privacy.md#retention-and-erasure).

## Checks before publishing

From the sibling workspace, run each block in its named repository.

API:

```bash
uv sync --frozen
uv run python -m unittest discover -s tests -v
uv run --with playwright python tests/browser_flow.py
```

The browser test needs all eleven sibling repositories and the company sites' built `dist/` outputs. It intercepts network requests and uses synthetic assessment fixtures; it does not submit to production. On machines without the script's default Chrome executable, set `BROWSER_EXECUTABLE` or install Playwright Chromium.

Portal:

```bash
node --check app.js
node --test tests/session.test.cjs
```

Console, from `workready-deploy/console`:

```bash
uv run python -m unittest test_console -v
```

Also rebuild affected static sites, check generated diffs and exercise the actual browser forms. These checks verify contracts and selected journeys, not educational validity, every mobile layout or large-cohort capacity.

## Local development and preview

For an isolated API, from `workready-api`:

```bash
uv sync --frozen
WORKREADY_DB=/tmp/workready-local.db SITES_DIR="$PWD/jobs" LLM_PROVIDER=stub \
  uv run uvicorn workready_api.app:app --host 127.0.0.1 --port 8000 --no-access-log
```

This uses the API's flat job exports. For full character prompts, point `SITES_DIR` at the sibling workspace and synchronise company-root exports first. The API does not implicitly read the repository's `.env` file in this command. Export the required settings or use an explicit environment-loading method. Use the API tests or create local-only issued codes before attempting login.

A generic static server is useful for visual inspection, but the frontends' API URLs, CSP and API CORS must all agree before it becomes a functional local deployment. Some clients load the shared session script from the portal host. Do not assume opening `index.html` directly or changing one localStorage value isolates the simulation from production.

For safe company-site visual previews, use the console's separate `localhost:7789` preview server. Its policy deliberately blocks production API submissions. For a functional integration check, use the isolated browser harness above.

The standalone primer can be served from its own directory with `python3 -m http.server 8080`. It fetches its compiled JSON and assets locally; a `file://` URL may be blocked by browser fetch policy.

## Alternative all-in-one recipe

The root [`docker-compose.yml`](../docker-compose.yml) starts a service named `workready` that owns ports 80/443 and runs the bundled Caddy plus API. It requires the domain/environment setup and frontend origin configuration to agree. This is a different topology from the existing `workready-api` service behind shared Caddy.

The recipe is not a verified zero-config path-routed demo. Its Caddyfile uses virtual hosts. The proposed builtin keyword chatbot and automatic path-mode configuration were not implemented. Use [DEPLOY-TIERS.md](../DEPLOY-TIERS.md) for the distinction, not the old tier proposal as a deployment guarantee.
