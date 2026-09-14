# ADR 0007: API-owned postings and eligibility

Status: Accepted, retrospective

Recorded: 14 September 2026

## Context

The job board originally baked listings into a JavaScript bundle. Agency postings, confidential employers and student-specific application restrictions need runtime state. A static listing bundle cannot determine whether a student has already applied or which employer details they may see.

## Decision

Load the board's postings from the WorkReady API and derive eligibility from server-held application history. Keep job-board assets static. Its builder copies `src/` into `dist/` without embedding a jobs bundle.

The API combines company/job exports with posting records. It supports direct and agency listings, and controls confidential-employer disclosure using the authenticated student's reveal state. Quick Apply identifies the posting in an authenticated API request. Client badges and disabled buttons explain restrictions; backend checks enforce them.

## Alternatives

- Baked-in listings work for public browsing but require a site rebuild for content changes and cannot own student-specific eligibility.
- Client-only eligibility checks could change the interface but would allow callers to bypass restrictions through direct requests.
- A separately managed recruitment service would add another store and synchronisation contract to this fictional simulation.

## Consequences

The board needs the API for live listings and applications. Content authors must update the runtime exports and refresh the API; publishing the board alone does not reload jobs. Company exports and canonical API exports must remain consistent because the loader prefers the company-root copy when both are present.

Confidentiality applies to the posting response and reveal rules. It is not a claim that the fictional employer is secret everywhere on its public website. There are no real employer accounts or production recruitment workflows.

See [content publication](../configuration.md#content-sources-and-publication), [session access](0003-contractor-codes-and-sessions.md) and [the board guide](https://github.com/michael-borck/workready-jobs/blob/main/README.md).

## Implementation history and evidence

- 10 April 2026: API [cea9c0e](https://github.com/michael-borck/workready-api/commit/cea9c0e) introduced posting records, agency listings, blocking and confidential reveal. API [7d1c02b](https://github.com/michael-borck/workready-api/commit/7d1c02b) added public posting responses.
- 10 April 2026: jobs [8574bb0](https://github.com/michael-borck/workready-jobs/commit/8574bb0) replaced baked-in data with runtime requests and simplified the builder to static copying.
- 14 September 2026: jobs [ce94f0a](https://github.com/michael-borck/workready-jobs/commit/ce94f0a) adopted session-based Quick Apply. The April commit's email-in-URL and localStorage identity approach is superseded.

Current implementation evidence is in API [`app.py`](https://github.com/michael-borck/workready-api/blob/main/workready_api/app.py), [`blocking.py`](https://github.com/michael-borck/workready-api/blob/main/workready_api/blocking.py), [`jobs.py`](https://github.com/michael-borck/workready-api/blob/main/workready_api/jobs.py) and the board's [`build.py`](https://github.com/michael-borck/workready-jobs/blob/main/build.py).
