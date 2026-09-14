# ADR 0004: Synthetic inputs, minimised uploads and explicit erasure

Status: Accepted, retrospective

Recorded: 14 September 2026

## Context

The simulation needs saved work and feedback for progress and lecturer review. Real resumes, conversational disclosures and mail attachments can contain identifying details. The old deployment also stored mail files outside its durable volume.

## Decision

Ask students to use invented personas and synthetic resumes. Filter matching contact details and provide an editable web-resume text preview. Process web resumes in memory and retain feedback. Rebuild mail uploads as filtered text PDFs with generated filenames on the data volume.

Retain simulation records for review and provide operator-triggered erasure and inactivity-based cohort purging. Remove dependent records transactionally, invalidate sessions and retry queued file/WAL cleanup. Apply a separate retention policy to backups and exports.

## Alternatives

- Retaining original resumes and mail PDFs preserves layout but stores more identifying information and document metadata.
- Keeping no simulation history reduces retention but prevents the implemented journey reports and contextual feedback.
- A scheduled purge would reduce reliance on operator action, but no automatic retention scheduler ships in this baseline.

## Consequences

Filtered PDFs lose their original layout and images. Filtering can miss names and context, so participation is pseudonymous rather than guaranteed anonymous. A chosen cloud provider receives prompts; separate hiring desks and external tools have their own data handling.

Operators must run retention cleanup, inspect pending erasure work and expire backups. Restoring a snapshot can reintroduce erased data. See [privacy and access](../privacy.md) and the [0.3.0 migration record](../../PRIVACY-RELEASE.md).

## Implementation history and evidence

- 11 September 2026: API [b986f2d](https://github.com/michael-borck/workready-api/commit/b986f2d) added persona profiles and resume contact redaction; jobs [a0a1855](https://github.com/michael-borck/workready-jobs/commit/a0a1855) supplied synthetic sample resumes.
- 14 September 2026: the [pre-release audit](../../AUDIT-2026-09-14.md) documented incomplete deletion and overstated privacy claims.
- 14 September 2026: API [7a56fac](https://github.com/michael-borck/workready-api/commit/7a56fac) added the 0.3.0 upload/session/erasure safeguards. Matching portal [900bd80](https://github.com/michael-borck/workready-portal/commit/900bd80) and jobs [ce94f0a](https://github.com/michael-borck/workready-jobs/commit/ce94f0a) changes supplied reviewed-upload flows.

The release record contains migration and verification observations. Neither the earlier redaction feature nor the later release makes filtering complete or retention automatic.
