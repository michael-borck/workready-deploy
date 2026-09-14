# ADR 0005: Local publishing and lecturer console

Status: Accepted, retrospective

Recorded: 14 September 2026

## Context

An operator needs to edit content across repositories, review generated changes, publish sites and update the API. Lecturer actions require an admin credential that should not be part of the public student portal.

## Decision

Run the console on the operator's computer, bound to loopback. Use a startup unlock key, local server-side sessions and request-origin/CSRF checks. Keep entered API admin credentials in the local server session and proxy admin requests.

Review a selected-file publication plan before staging and publishing. Serve static previews from a separate origin with production submissions blocked. Build the API image through the deploy repository's GitHub workflow, wait for the result, then update the VPS.

## Alternatives

- Manual Git, builds and SSH remain possible, but require the operator to track cross-repository generated outputs and configuration themselves.
- A publicly hosted staff service would support remote collaboration but needs named users, scoped authorisation and a staff audit model.
- A same-origin content preview would simplify serving but expose console authority to previewed scripts.

## Consequences

The console requires local repository checkouts, build tools, GitHub CLI access and SSH access for deployment. It edits an allowlist rather than every possible runtime setting. Preview mode is for appearance, not a functional production-connected simulation.

The shared API admin token is still broad authority; cohort filters are not security boundaries. The console does not implement backup scheduling. See the [console guide](../../console/README.md) and [operations](../operations.md).

## Implementation history and evidence

- 11 September 2026: deploy [03cbc0c](https://github.com/michael-borck/workready-deploy/commit/03cbc0c) introduced the local content editor and deploy runner. Portal [b371d2f](https://github.com/michael-borck/workready-portal/commit/b371d2f) removed `admin.html` from public publication.
- 14 September 2026: deploy [bd85574](https://github.com/michael-borck/workready-deploy/commit/bd85574) hardened local sessions, preview isolation and reviewed-file publication, and documented the privacy rollout.
- 14 September 2026: deploy [15829c3](https://github.com/michael-borck/workready-deploy/commit/15829c3) replaced VPS-side image building with GitHub workflow dispatch/wait and image pulling.

The local-console choice preceded its hardened implementation. Removing a public admin page did not itself secure admin requests; the server-side credential checks and local proxy remain the access controls.
