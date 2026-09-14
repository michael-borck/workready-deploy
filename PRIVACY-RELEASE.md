# Session and privacy release

> Dated 0.3.0 rollout record, deployed 14 September 2026. Counts, image revisions and backup observations describe that release. For current procedures, use [operations](docs/operations.md), [configuration](docs/configuration.md) and [privacy](docs/privacy.md).

This is a coordinated API/frontend release, not a live hotfix. Old clients that
send contractor codes in URLs will receive 410 and must refresh. No production
data needs to be reset. Session-table creation is idempotent at startup.

The API health response identifies this release as `0.3.0`.

## Verification status

Deployed on 14 September 2026. The API reports `0.3.0`, and the portal,
job board, six company sites and primer have matching published clients.

The deployed API source revision is `7a56fac`. The initial release image was
`ghcr.io/michael-borck/workready:bd85574`, with registry digest
`sha256:c5139e8257978cd943a5884865ac8e028bb33ab175e175b0123f59ccbc71d411`.
The VPS Compose override now uses the public GitHub image for pull-based updates.

Pre-release backup: `/home/michael/workready-backups/release-0.3.0-20260914`.
It is outside the repositories, with a private directory and protected files.
The database integrity check passed. All original record counts were preserved:
6 students, 52 codes, 2 applications and 8 messages. There were no stored or
orphaned mail attachments to migrate. The previous image remains available as
`workready:pre-030-20260914`.

After deployment, live API tests verified session login, ownership checks,
filtered preview/application submission, logout, revocation and legacy URL
rejection. A real Chrome session verified the published portal and job-board
login, persona, reviewed PDF application and sign-out. These checks used new
synthetic identities; all verification records and codes were erased afterward.
Record counts were checked again and matched the pre-release backup.

Passed locally:

- 13 API privacy/contract tests, including an anonymous-request matrix over
  all private routes, cross-student access, session revocation, erasure,
  upload boundaries, lunchroom booking and final-task resubmission.
- 5 console tests for local authentication, CSRF/Origin/Host boundaries,
  selective publishing, stale plans, admin proxying and pacing validation.
- 4 JavaScript session tests, including late responses after sign-out.
- A headless Chrome run using an isolated test API: bad-code dialog and
  keyboard focus, persona setup, filtered PDF review, job-board application,
  interview, task submission, sign-out, mobile sign-in width, and applications
  through all six company sites. Assessment outcomes were synthetic fixtures;
  no cloud-model quality or production load claim follows from this test.
- Primer playthrough through all eight scene tags.
- All six company-site builds, job-board build and source diff checks.

The local browser tests intercepted network requests. The separate post-release
checks used only newly issued synthetic production identities, which were then
erased. Existing students' records were not used for testing.

## Implemented boundaries

- Contractor codes are exchanged through `POST /api/v1/auth/login` for an
  opaque bearer session. Only its SHA-256 hash and expiry are stored. Code
  revocation is checked on every private request. Logout invalidates the token.
  Admin student-record URLs use numeric student IDs. Code inspection and
  revocation use POST bodies, so management URLs do not expose the code either.
- Student tokens are tab-scoped in sessionStorage, not durable localStorage.
  The enrolment code is cleared and never used as an email address. Each site
  requires its own sign-in; there is no reusable credential in cross-site links.
- All private API routes share authentication and object ownership, including
  transcript, calendar, inbox and lunchroom reads. JSON cannot override a
  path's ownership check. Responses use `Cache-Control: no-store`.
- Invalid sessions and over-limit login requests are rejected before document
  parsing/model calls. Requests are limited to 6 MB; PDFs to 5 MB and 20 pages.
- Resume review includes an in-memory filtered preview. The student can edit
  residual personal details before assessment. Mail PDFs are reconstructed
  from filtered text, given unique storage names, and kept in the data volume.
  Names and identifying context can still remain. This is not anonymisation.
- Complete student deletion removes relational children and sessions, revokes
  the code, and queues file erasure. Pending filesystem work is reported and
  retried with `POST /api/v1/admin/erasure/retry`.
- Local admin credentials are held server-side by the console proxy, not in
  the browser's sessionStorage. The console uses HttpOnly/SameSite cookies,
  Host/Origin checks, CSRF tokens and a serialised selective-publishing plan.

## Before replacing the old container

1. Freeze writes and take a consistent SQLite backup using SQLite's backup API
   or a stopped database. Include the attachment store. Do not copy a live
   WAL database file alone and assume it is consistent.
2. Preserve legacy attachments from the old container's working directory.
   The old default stored them outside the volume. Replacing that container
   before preservation can lose them.
3. Run `workready-api/scripts/migrate_attachments.py` with the preserved root,
   database path and new durable attachment directory. Check its missing-file
   count. Use `--remove-originals` only after the migrated files and database
   have been verified. Run this offline with the new code/dependencies.
   When migrating host-side copies, use `--legacy-prefix` for the original
   container working directory and `--stored-prefix /opt/workready/data/attachments`
   so SQLite records paths visible to the new container, not host-only paths.
4. Decide the cohort retention period and backup expiry. The supplied target
   is 120 days of inactivity. The purge is operator-triggered, not an automatic
   background job. Schedule authenticated
   `POST /api/v1/admin/cohorts/{cohort}/purge-expired` if that policy is wanted.
   Keep protected backups outside public repositories and expire them too.
5. Rotate previously exposed demo enrolment codes where appropriate. Historical
   URL logs are not erased by this release. The Compose override disables new
   uvicorn access logs; check reverse-proxy logging independently.

## Verification and rollout

From `workready-api`:

```bash
uv run python -m unittest discover -s tests -v
```

From `workready-portal`:

```bash
node --test tests/session.test.cjs
```

From `workready-deploy/console`:

```bash
uv run python -m unittest test_console -v
```

Build all six company sites and the job board. Refresh the portal, job board
and each company application page against the new API in a staging deployment.
Verify keyboard modal handling and mobile uploads in real browsers. Check the
local `/admin` proxy with a test admin credential.

Publish the portal's shared `session.js` and compatible clients together with
the API. Company applications and the job board load that shared client from
the portal host. During a transition, cached old clients may need a hard refresh.
Use the existing shared-Caddy network and merge `compose.privacy.yml` after the
VPS Compose file. Back up before recreating. Keep the prior image for rollback;
do not roll back to known-unprotected API routes for a real-data cohort.

The content console publishes reviewed content, requests the GitHub Actions
image build, then pulls the release image to the VPS. It retains a rollback
image and reports failed health checks. It does not automatically roll back
database changes or perform another breaking source-code migration.

Routine VPS updates, after the GitHub image build completes:

```bash
docker compose --project-directory ~/homelab/workready pull
docker compose --project-directory ~/homelab/workready up -d --no-build
```

Use the explicit release image/digest for recovery. Restoring the old API should
only be done under maintenance because that version had known access-control
gaps. Backup expiry remains an operator responsibility.

## Operational limits and follow-up checks

- Process-local request budgets are appropriate to the current single-worker
  API. Add a shared edge limiter before running multiple workers. Configure
  trusted proxy addresses explicitly; never trust arbitrary forwarding headers.
  Set `WORKREADY_TRUSTED_PROXY_IPS` for the shared Caddy deployment and tune the
  login budget for classroom NATs where many students share one public IP.
- External hiring-desk widgets are not loaded on application/staff pages.
  Company application sessions are revoked after submission. The separate bot
  service still needs provider/retention review; no conversations were sent
  to it as part of these code changes.
- The workload remains a single SQLite deployment. No concurrency benchmark,
  educational scoring validation or “unlimited scale” claim is made.
- `workshop` and `semester` are pacing presets, not guarantees that a full
  journey takes a fixed number of minutes/weeks. Explicit timing environment
  values override preset defaults. The console's Compose override expands
  the chosen preset to avoid stale literal values in the old Compose file.
- A shared local operator/admin credential is still used. Named lecturer
  accounts and delegated cohort permissions need a separate staff identity
  design before independent institutional administration.
