# ADR 0003: Contractor codes and expiring sessions

Status: Accepted, retrospective

Recorded: 14 September 2026

## Context

Students need access to their own simulation without a real-name account. Earlier private URLs used a contractor code as both identity and credential. Ownership checks were inconsistent, and URLs could expose reusable credentials.

## Decision

Use an issued contractor code for login only. Exchange it for a random opaque bearer session with a stored hash and absolute expiry. Store the browser token in `sessionStorage`. Check session identity, record ownership and conversation kind on private routes.

Keep the real roster mapping with the lecturer. Revoke all related sessions when an enrolment code is revoked. Logout invalidates the current session and clears browser activity. Return 410 for retired code-bearing private URLs.

## Alternatives

- Reusing the code on every request leaves a long-lived enrolment credential exposed to routine client handling.
- Named accounts or institutional SSO could support account recovery and staff roles but introduce identity integration and additional data handling.
- Self-contained tokens reduce database lookup needs but make immediate revocation more involved. The current SQLite-backed session table supports that directly.

## Consequences

Each website origin has a separate session; no cross-domain SSO is implemented. Students may need to enter their code again on the job board or company site. Session storage reduces persistence but does not protect a token from script execution in a compromised origin.

Admin access still uses a separate shared token. This decision does not provide named lecturer accounts or cohort-scoped authorisation. See [privacy and access](../privacy.md#identity-and-access-control) and the [API authentication code](https://github.com/michael-borck/workready-api/blob/main/workready_api/auth.py).

## Implementation history and evidence

- 11 September 2026: API [4288e35](https://github.com/michael-borck/workready-api/commit/4288e35) replaced email identity with issued contractor codes. Its message explicitly deferred JWT sessions. This was the identity change, not the completed session boundary.
- 11 September 2026: API [f357395](https://github.com/michael-borck/workready-api/commit/f357395) added ownership guards and rate limiting. The subsequent audit found remaining gaps.
- 14 September 2026: API [7a56fac](https://github.com/michael-borck/workready-api/commit/7a56fac) implemented opaque hashed sessions and shared private-route protection. Portal [900bd80](https://github.com/michael-borck/workready-portal/commit/900bd80) and jobs [ce94f0a](https://github.com/michael-borck/workready-jobs/commit/ce94f0a) adopted the session contract.

The first identity commit's claim to remove all real-world PII was too broad. The current decision provides pseudonymous access; it does not make student-authored content anonymous. See [ADR 0004](0004-data-handling-and-retention.md).
