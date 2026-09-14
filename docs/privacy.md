# Privacy and access

[Project home](../README.md) · [Configuration](configuration.md) · [Operations](operations.md)

WorkReady uses **pseudonymous participation and data minimisation**. It does not guarantee anonymity. The following describes the 0.3.0 implementation, not a legal compliance certification or proof of model quality.

## What the student should be told

> Use an invented persona and a supplied synthetic resume. WorkReady saves simulation activity for learning and lecturer review. Contact filtering can miss identifying details. Cloud AI providers receive filtered prompts when selected. Ask your lecturer about retention and deletion.

The student-facing [data-handling page](https://github.com/michael-borck/workready-portal/blob/main/privacy.html) should remain consistent with this guide. It must acknowledge that identifying material can persist and selected external providers receive prompts.

## Identity and access control

- An issued contractor code is an enrolment credential. The lecturer keeps the real roster mapping separately.
- `POST /api/v1/auth/login` exchanges the code for a random opaque session. The server stores a SHA-256 hash and expiry, not the session token itself.
- Student session tokens are tab/origin-scoped in browser `sessionStorage`. Server expiry is authoritative; browser session restoration is not a retention guarantee.
- The student, company and job-board sites have separate sessions. There is no shared-origin cookie or cross-site SSO handoff containing the contractor code.
- Private API routes check authentication, ownership and relevant session kind. Completed placement records are read-only through normal student actions.
- Code revocation prevents use of all sessions tied to that code. Logout invalidates the specific session; the portal discards late callbacks and replaces the page to clear old views.
- Admin student-record URLs use numeric IDs; code inspection/revocation put the credential in POST bodies.

Request budgets and upload limits are documented in [configuration](configuration.md#identity-storage-and-models). They are bounded process-local controls. Multi-worker scaling requires a shared limiting strategy and correct trusted-proxy configuration.

## What is retained

| Data | Current handling |
|---|---|
| Codes/cohorts and chosen persona | Stored in SQLite; a self-declared name can still identify its author |
| Session hashes and expiry | Stored server-side; expired entries are cleaned during session initialisation/login |
| Applications and assessment feedback | Stored for progress and lecturer reporting |
| Interviews, coaching, exit conversations | Transcripts and feedback are stored |
| Personal/work messages and Teams-style chat | Stored as simulation messages; deletion from a mailbox can be a soft delete |
| Task submissions | Body, feedback and extracted attachment text are stored |
| Web resume uploads | Processed in memory, shown as filtered review text, used for assessment; no original resume archive is created by that path |
| Mail attachments | Rebuilt as filtered text PDFs with generated filenames under the durable attachment directory |
| Hosting/operational metadata | Hosting providers and infrastructure process ordinary connection metadata; inspect deployment logging separately |

The PDF filter catches matching email addresses, phone formats, some links and explicitly labelled personal-detail lines. Names, unlabelled addresses and identifying context may remain. Filtering an upload is not equivalent to making it anonymous. A student can also disclose identifying information in conversation or a task body.

The web application flow provides a filtered-text preview so the student can remove residual details before assessment. Mail attachment reconstruction discards original layout, images and document metadata. These are deliberate functional trade-offs.

## Model and external-service boundaries

The main API can run in `stub` mode without calling an LLM. Ollama may be local or remote. Selecting Anthropic/OpenRouter sends prompts and conversation context to that provider. Filtering is applied at relevant input/model boundaries but cannot guarantee all identifiers are removed.

AnythingLLM hiring desks are a separate deployment. Their provider, logs, retention and workspace configuration need their own review. The external widget is not loaded on sensitive application/staff pages, but the rest of its deployment is not covered by the API's stub setting.

Talk Buddy, Career Compass and optional upstream authoring tools have their own data handling. Static primer art is generated during authoring, not from a student's live input. Review a new integration before expanding the privacy claim to include it.

## Lecturer and publishing-console access

The public student portal does not publish `admin.html`. Hiding a page is not the security control: admin API requests require `WORKREADY_ADMIN_TOKEN` and are refused when it is missing or wrong.

The local console has a separate unlock key, an HttpOnly/SameSite session cookie, Host/Origin checks and CSRF protection. It holds an entered API admin token in its server-side local session and proxies admin calls. The browser does not retain that API admin token in `sessionStorage`.

Static previews run on a separate origin and restrict network connections and form submission. They are visual previews, not a live simulation environment. The console stages reviewed paths and generated outputs rather than every dirty repository file.

A shared operator/admin credential is still used. A cohort filter is a reporting filter, not per-lecturer authorisation. Named accounts, scoped permissions and a staff audit model are required before delegating independent institutional administration.

## Retention and erasure

`RETENTION_DAYS` defaults to 120 days of inactivity. **This is not a scheduled deletion job.** The operator must select an appropriate period and invoke or schedule `POST /api/v1/admin/cohorts/{cohort}/purge-expired`.

The admin erase operation removes the student's dependent records and sessions, revokes the enrolment code and queues file cleanup. SQLite secure deletion is enabled; erasure attempts to truncate the WAL. An active reader or filesystem failure can leave cleanup pending. Check the returned `complete`, `files_pending_cleanup` and `wal_checkpoint_pending` fields or use the lecturer page's cleanup action. `POST /api/v1/admin/erasure/retry` retries pending cleanup.

Resetting a student is different from erasing their identity: reset clears their journey and sessions but keeps the student record. Mailbox soft deletion is different from both.

Backups have their own expiry. Erasing the live database does not erase snapshots, copied uploads, logs or previously exported reports. Keep those out of Git/public web roots, restrict their access, and document disposal. A backup restoration can reintroduce erased data or previously valid credentials; reconcile it before reopening access.

The original 0.2 deployment placed mail attachments outside the durable volume. Preserve those files before replacing an old container. The [0.3.0 release record](../PRIVACY-RELEASE.md) contains the dated migration evidence; the [operations guide](operations.md#backup-and-recovery) covers ongoing procedures.

## Verification and remaining responsibilities

The release added private-route, ownership, session-race, upload, erasure and console-boundary regression tests. Run them when changing authentication or storage; see [operations](operations.md#checks-before-publishing). Use new synthetic identities for production smoke checks and erase them afterward.

A passing test suite is not a guarantee about arbitrary future content, a cloud provider's retention, backup policy, institutional permissions or high-concurrency behaviour. Those remain operator and pilot-review responsibilities.

Design rationale: [ADR 0003](adr/0003-contractor-codes-and-sessions.md), [ADR 0004](adr/0004-data-handling-and-retention.md) and [ADR 0005](adr/0005-local-publishing-console.md).
