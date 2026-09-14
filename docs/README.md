# Documentation index and maintenance

[Project home](../README.md)

## Canonical guides

| Document | Owns |
|---|---|
| [Architecture](architecture.md) | Repository boundaries, runtime, data flow, student journey and implementation limits |
| [Configuration](configuration.md) | Setting names/defaults, precedence, content sources and what must be rebuilt |
| [Privacy](privacy.md) | Credentials, saved data, provider boundaries, retention and erasure responsibilities |
| [Operations](operations.md) | Build/publish workflow, VPS topology, verification, backups and recovery |
| [ADRs](adr/README.md) | Why accepted design choices exist, alternatives and consequences |
| [Console guide](../console/README.md) | Day-to-day console controls and local startup |

These guides describe the 0.3.0 baseline reviewed on 14 September 2026. Deployment-specific values can change; the configuration guide identifies the implementation files that define them.

## Historical records

- [0.3.0 privacy release](../PRIVACY-RELEASE.md): rollout evidence, backup location and the legacy attachment migration. Its observations are dated, not a live inventory.
- [14 September audit](../AUDIT-2026-09-14.md): findings before the privacy release. Preserve it as an audit snapshot, not a list of current defects.
- [API design archive](https://github.com/michael-borck/workready-api/blob/main/docs/README.md): the original authentication and stage implementation proposals.
- [Deployment recipe clarification](../DEPLOY-TIERS.md): supersedes the old tier proposal's unsupported claims.

## Updating documentation

1. Change the guide that owns the fact. Link to it from other documents instead of maintaining a second explanation.
2. Keep component READMEs specific to that repository. Add a link back to the project home.
3. Record a meaningful architecture change in an ADR. New proposals start as `Proposed`; implemented decisions are `Accepted`. Superseded decisions retain their history and link to their successor.
4. Separate current behaviour, release-specific evidence and future work. Do not describe a plan as shipped functionality.
5. Verify commands against the current file layout. A successful API call with substituted fields is not proof that the browser sends a valid request.
6. Use absolute GitHub URLs between repositories. Relative links work within a repository; `../workready-api/...` is not a sibling-repository link on GitHub.
7. Never add live access codes, tokens, student records or unprotected backup contents to documentation. Use unmistakable placeholders.

Use the source code and deployment inspection to resolve discrepancies, then correct the owning guide. The operational rules must be understandable without private chat history or an assistant's personal memory files.
