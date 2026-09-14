# ADR 0006: Configurable pacing and lazy delivery

Status: Accepted, retrospective

Recorded: 14 September 2026

## Context

A short demonstration and a spread-out placement need different delays. Feedback, task visibility, interview booking and lunchroom conversation already use persisted timing fields. The deployment has no durable worker queue.

## Decision

Provide `custom`, `workshop` and `semester` presets. Allow explicit environment values to override preset defaults. The local console expands its supported preset settings into a Compose override.

Persist due times and deliver or reveal events during relevant reads/polls. Keep this distinction explicit: mail reply work also uses in-process FastAPI `BackgroundTasks`, which is not a durable scheduler.

## Alternatives

- Hard-coded instant responses make demos simple but remove pacing choices.
- A single duration setting would require a curriculum scheduling model that does not exist today.
- A durable worker queue could deliver work without browser polling and retry interrupted jobs, at the cost of another service and job lifecycle.

## Consequences

Presets are starting values, not guarantees about elapsed course length. Company hours, student actions and available templates affect progression. Individual environment values can unintentionally override a preset, so inspect the effective Compose settings.

Lazy delivery depends on client activity. In-process background work can be interrupted by a restart. Task count is bounded by templates, and coaching currently depends on the second passed task. See [configuration](../configuration.md#pacing-presets-and-precedence) and [architecture](../architecture.md).

## Implementation history and evidence

- 10 April 2026: API [943495e](https://github.com/michael-borck/workready-api/commit/943495e) added appointments, business hours and feedback delays.
- 13 April 2026: API [1bbced6](https://github.com/michael-borck/workready-api/commit/1bbced6) added completion-gated tasks and calendar support. API [cbce529](https://github.com/michael-borck/workready-api/commit/cbce529) persisted planned lunchroom beats and generated due replies through lazy delivery.
- 14 September 2026: API [7a56fac](https://github.com/michael-borck/workready-api/commit/7a56fac) added the literal `PRESETS` table and explicit-environment precedence. Deploy [bd85574](https://github.com/michael-borck/workready-deploy/commit/bd85574) added console pacing validation and expansion into its deployment override.

The timestamp-based mechanisms predate the named presets. The April commit's coaching-on-submission description also predates the current passed-task gate; use the current source and configuration guide for progression rules.
