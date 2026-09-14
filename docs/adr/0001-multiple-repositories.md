# ADR 0001: Independent repositories and one documentation home

Status: Accepted, retrospective

Recorded: 14 September 2026

## Context

WorkReady has eleven Git repositories with separate publication targets. Company sites have their own content and designs; the API, portal and primer use different build tools. Project-wide instructions had drifted across component READMEs and an API-owned system map.

## Decision

Keep the repositories independent and arrange local checkouts as siblings. Use `workready-deploy` as the project home for architecture, configuration, privacy, operations and ADRs. Each component README documents its own files and commands and links back to that home.

Use absolute GitHub links between repositories. The parent workspace is not a Git superproject. The console works across a fixed list of sibling repositories.

## Alternatives

- A monorepo would make cross-component commits atomic, but would require restructuring existing publication workflows and history.
- A submodule superproject could pin source revisions, but adds another checkout/update workflow.
- Independent documentation in every repository keeps instructions nearby but has already produced contradictory descriptions.

## Consequences

Components can publish independently. A coordinated release still needs several commits, build results and source revisions. The bundled image clones multiple repositories, so its recipe commit alone does not identify all inputs.

Maintainers update the guide that owns a fact and link to it. See the [repository map](../../README.md#repository-map) and [documentation maintenance rules](../README.md#updating-documentation).

## Implementation history and evidence

- 9 April 2026: separate initial commits for the [API](https://github.com/michael-borck/workready-api/commit/596e417), [portal](https://github.com/michael-borck/workready-portal/commit/4ba253e) and [primer](https://github.com/michael-borck/workready-primer/commit/028b717) establish independent repository histories.
- 12 April 2026: deploy [3fc8ad8](https://github.com/michael-borck/workready-deploy/commit/3fc8ad8) introduced an installer that clones nine application/company repositories. This is evidence of multi-repository assembly, not of the current shared-VPS topology.
- 11 September 2026: deploy [03cbc0c](https://github.com/michael-borck/workready-deploy/commit/03cbc0c) added the local editor/deploy runner across sibling checkouts.

The single documentation home was chosen during the 14 September consolidation recorded here. The earlier commits establish repository boundaries; they do not establish an earlier decision to centralise documentation.
