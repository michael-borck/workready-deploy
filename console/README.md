# WorkReady local console

[Project home](../README.md) · [Configuration](../docs/configuration.md) · [Operations](../docs/operations.md) · [Privacy](../docs/privacy.md)

## Start

```bash
cd workready-deploy/console
uv run python run.py
```

Open `http://127.0.0.1:7788` and enter the local console key printed in that terminal. `CONSOLE_TOKEN` can supply a persistent key instead. Do not put the key in the URL. The console requires a local login, a same-origin request and a CSRF token for mutations.

`run.py` also serves static previews at `http://localhost:7789/<company>/`. Previews use a different origin and restrict network connections to themselves. They cannot submit applications to the production API. They are visual previews, not an end-to-end functional test environment.

## Content and publishing

1. Open a file, edit it and save.
2. Tick only the files you intend to publish.
3. Build the selected files and review the generated deployment plan and diff.
4. Publish that plan. Only the reviewed paths and their generated outputs are staged.

The console refuses staged work, overlapping builds and a plan whose files changed after review. It never force-pushes. If a push fails, inspect the local commit and use the explicit retry-push action after resolving the remote difference. Clean repositories with unpushed commits are not silently forgotten.

The runtime's canonical job exports are `workready-api/jobs/<company>.json`. These contain job descriptions, business-hour overrides, task templates and embedded manager personas. The console copies a selected export into the matching company build input before rendering its website.

Company biographies and `brief.yaml` edit website content. They do not automatically regenerate an AI persona or exported job description. Edit the runtime export when changing those behaviours. This distinction is shown in the file list.

`workready-deploy/pacing.json` selects `custom`, `workshop` or `semester`, with a small allowlist of timing overrides. Runtime changes take effect when the API is redeployed. The console builds a Compose override from the API's preset table so old hardcoded timing values do not silently override the selection. See [pacing configuration](../docs/configuration.md#pacing-presets-and-precedence) and the [0.3.0 release record](../PRIVACY-RELEASE.md).

## Student management

Open `/admin` from the console header. Unlock the console first, then enter the API's admin token once. The local server holds that credential in its expiring session and proxies only `/api/v1/admin/*` requests. The browser does not keep the API admin token in sessionStorage or send it directly to the remote API. This avoids the old localhost CORS failure.

The console key and API admin token serve different purposes. Locking the console discards its session and its server-held admin credential.

## API deployment

The deployment action starts and waits for the GitHub Actions image build, then pulls that release image onto the VPS. It retains the previous running image as `workready:rollback`, recreates the service without building locally, and checks the public health response. This avoids reinstalling Caddy and other image-build dependencies on the VPS. A failed health check is an error, not a successful publish. Inspect logs and storage compatibility before using the rollback image.

The machine running the console needs an authenticated `gh` CLI as well as Git and SSH access. Publish content before requesting the image build; GitHub builds the committed repository versions.

`WORKREADY_HOME` selects the local checkout, `WORKREADY_VPS` selects the SSH alias, `WORKREADY_VPS_DIR` is relative to the remote user's home, and `WORKREADY_API_BASE` selects the trusted API upstream. The defaults match the existing `vps` / `homelab/workready` deployment.

The console does not create or encrypt backups. Take a consistent backup and migrate legacy attachments before replacing an old API container. See [backup and recovery](../docs/operations.md#backup-and-recovery) and [retention and erasure](../docs/privacy.md#retention-and-erasure).

## Tests

```bash
uv run python -m unittest test_console -v
```
