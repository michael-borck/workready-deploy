# ADR 0002: GitHub Pages and a shared VPS

Status: Accepted, retrospective

Recorded: 14 September 2026

## Context

The student interfaces and fictional company websites are static. Simulation state, model calls and private records need a backend. The existing VPS already hosts other services behind Caddy.

## Decision

Publish the static sites on GitHub Pages. Run the WorkReady API in Docker on the VPS, behind the existing shared Caddy service. Keep SQLite and filtered attachments on a persistent volume. Build the bundled image in GitHub Actions and pull it from public GHCR for routine updates.

The root all-in-one Compose recipe remains an alternative deployment. It does not describe the shared VPS's active service or port ownership.

## Alternatives

- Hosting every site inside the bundled image would provide one publication unit but tie static edits to backend deployment and require different origin configuration.
- Managed database and application services could replace the VPS, but are not part of this deployment.
- Building on the VPS avoids a registry dependency but uses its resources, can stall on build downloads and can reuse stale cloned inputs through caching.

## Consequences

Static publishing is independent of API uptime. Browser origins, CSP, CORS and shared script versions need coordination. Company/job workflows upload checked-in `dist/`; the primer publishes `main` at the repository root without compiling Ink.

The shared proxy must be maintained without disrupting other services. A backend contract change needs a coordinated frontend release. Record image digests and source revisions for recovery. See [operations](../operations.md).

## Implementation history and evidence

- 9 April 2026: NexusPoint [52fe2e7](https://github.com/michael-borck/nexuspoint-systems/commit/52fe2e7) added its Pages workflow; API [3de0818](https://github.com/michael-borck/workready-api/commit/3de0818) added Docker/GHCR publication. These establish hosting components, not the date of the current topology's deployment.
- 10 April 2026: API [9c516ff](https://github.com/michael-borck/workready-api/commit/9c516ff) fixed zero postings caused by the `/data` bind mount hiding packaged job files. That API image moved jobs to `/app/jobs` and kept persistent state under `/data`. Those historical paths differ from the bundled image's current paths, but the separation still matters.
- 14 September 2026: deploy [15829c3](https://github.com/michael-borck/workready-deploy/commit/15829c3) changed console updates to GitHub-built images and recorded the shared-VPS rollout.

The [release record](../../PRIVACY-RELEASE.md) and deployment inspection establish the actual shared Caddy/API arrangement. The original all-in-one recipe alone cannot prove what ran on the VPS.
