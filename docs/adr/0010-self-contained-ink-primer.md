# ADR 0010: A self-contained Ink primer

Status: Accepted, retrospective

Recorded: 14 September 2026

## Context

Students need a short introduction to the internship journey before using the stateful simulation. The primer may run independently or inside an embedded frame. A live model, API login or CDN runtime would add dependencies to an authored branching story.

## Decision

Author the primer in Ink and publish its compiled JSON with a browser player, a vendored inkjs runtime and static scene assets. Branches, tone variants and alternative-outcome passages are authored in advance. Story text and artwork do not require live model generation.

Keep the primer independent of contractor-code login and API placement state. Provide a parent-frame completion message as an integration hook. Publish generated story/runtime files alongside their sources because the primer's Pages publication does not compile Ink.

## Alternatives

- A CDN runtime avoids vendoring but introduces an external runtime request that restrictive networks or outages may block.
- Live-generated scenes could vary on each playthrough but require provider access, data handling and review of unpredictable outputs.
- An API-coupled primer could record completion centrally but would require identity and a completion contract that the standalone player does not need.

## Consequences

The same authored choices can be rehearsed across deployments without model variability. Maintainers must rebuild Ink changes and review all affected tone variants and alternative paths. Vendored dependencies need explicit updates.

Self-contained assets do not guarantee that opening `index.html` via `file://` works. The player fetches its story JSON, so serve the directory over HTTP. Assets can be served locally without the WorkReady backend, but no service-worker offline cache is claimed.

The `postMessage` hook is not SCORM or gradebook reporting. An embedding application must validate and handle the message. Primer completion does not change the student's API journey. See the [primer guide](https://github.com/michael-borck/workready-primer/blob/main/README.md) and [ADR 0009](0009-formative-evidence-without-an-aggregate-grade.md).

## Implementation history and evidence

- 9 April 2026: primer [028b717](https://github.com/michael-borck/workready-primer/commit/028b717) introduced the interactive fiction player and story.
- 9 April 2026: primer [cf59da7](https://github.com/michael-borck/workready-primer/commit/cf59da7) replaced the jsDelivr runtime with `lib/ink.js` and declared the build dependency. Its broader `file://` claim is qualified above.
- 9 April 2026: primer [6d79966](https://github.com/michael-borck/workready-primer/commit/6d79966) added a hook to rebuild staged Ink changes.
- 11 September 2026: primer [5ff4931](https://github.com/michael-borck/workready-primer/commit/5ff4931) added saved cartoon artwork generated during authoring.

Current [`build.sh`](https://github.com/michael-borck/workready-primer/blob/main/build.sh) vendors the runtime and compiles the story. [`index.html`](https://github.com/michael-borck/workready-primer/blob/main/index.html) loads those assets and emits completion information to a parent frame.
