# Architecture decision records

[Project home](../../README.md) · [Current architecture](../architecture.md)

These records explain decisions that affect several WorkReady components. Operational instructions belong in the [guides](../README.md).

## Decisions

| ADR | Decision | Status |
|---|---|---|
| [0001](0001-multiple-repositories.md) | Keep independent component repositories and one documentation home | Accepted, retrospective |
| [0002](0002-github-pages-and-vps.md) | Publish static sites on GitHub Pages and run the API behind shared VPS Caddy | Accepted, retrospective |
| [0003](0003-contractor-codes-and-sessions.md) | Exchange contractor codes for expiring student sessions | Accepted, retrospective |
| [0004](0004-data-handling-and-retention.md) | Use synthetic inputs, minimise uploads and support explicit erasure | Accepted, retrospective |
| [0005](0005-local-publishing-console.md) | Keep publishing and lecturer access in a local console | Accepted, retrospective |
| [0006](0006-simulation-pacing.md) | Use configurable presets and persisted, lazily delivered events | Accepted, retrospective |
| [0007](0007-api-owned-postings-and-eligibility.md) | Keep postings and student eligibility in the API | Accepted, retrospective |
| [0008](0008-character-context-from-stored-conversations.md) | Build character context from stored conversations and summarise older history | Accepted, retrospective |
| [0009](0009-formative-evidence-without-an-aggregate-grade.md) | Report formative evidence without an automatic aggregate grade | Accepted, retrospective |
| [0010](0010-self-contained-ink-primer.md) | Publish a self-contained Ink primer with vendored runtime and assets | Accepted, retrospective |

Recorded on 14 September 2026 against the 0.3.0 baseline. These are retrospective descriptions of the implementation, not records of an earlier formal approval meeting. Their alternatives are comparisons made while documenting the system.

## Reading the evidence

Each record has an implementation-history section with commit links and current-source or release evidence. Dates in that section use the UTC author dates returned by GitHub. They identify implementation milestones, not necessarily deployment dates or formal approval dates.

Commit messages explain intent but can contain superseded claims. Check their diffs and the current implementation before carrying a claim into an ADR. In particular, code-based identity preceded session protection, and the original primer's `file://` claim exceeded what browser fetch rules guarantee. Deployment observations belong to a dated release record rather than being inferred from a source commit.

## Adding a record

Use the next unused four-digit number and a descriptive filename. Include status, recording date, context, decision, alternatives, consequences and implementation history. Link to the relevant commits and source or guide that shows how the decision works. Keep recording dates separate from implementation and deployment dates. For a proposed decision, distinguish existing evidence from planned work.

New proposals start as `Proposed`. Mark a decision `Accepted` when agreed and implemented as described. If a later decision replaces it, mark the old one `Superseded by ADR NNNN` and retain both records. Do not turn a speculative feature in an old design into an accepted decision merely because the file exists.
