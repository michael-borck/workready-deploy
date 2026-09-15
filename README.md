# WorkReady

**Start here for the whole project.** This repository is the documentation and operations home for WorkReady, an educational internship simulation. It also contains the publishing console, deployment recipes and presentation materials.

Students use issued contractor codes and invented personas to practise applying for a role, interviewing, completing work, communicating with colleagues and reflecting on a placement. The employers are fictional. WorkReady is not an official university service or a real recruitment platform.

The public project overview is in [`site/`](site/index.html). Its GitHub Pages address is `https://michael-borck.github.io/workready-deploy/` once publication is enabled. The student portal remains at [workready.eduserver.au](https://workready.eduserver.au/). See [landing-page setup](docs/operations.md#project-landing-page) for preview and hosting instructions.

## Read this first

| I want to… | Start with |
|---|---|
| Edit or publish the public project overview | [Landing-page setup](docs/operations.md#project-landing-page) |
| Understand the repositories and student journey | [Architecture](docs/architecture.md) |
| Change timing, organisation hours, tasks or personas | [Configuration and content](docs/configuration.md) |
| Understand identity, saved data and deletion | [Privacy and access](docs/privacy.md) |
| Build, publish, operate or recover the system | [Operations](docs/operations.md) |
| Edit content with a colleague or manage students | [Local console](console/README.md) |
| Understand why an architectural choice was made | [Architecture decision records](docs/adr/README.md) |
| Present or demonstrate WorkReady | [Slide deck](deck/index.html) and [demo script](deck/demo-script.md) |
| Review the 0.3.0 rollout | [Release record](PRIVACY-RELEASE.md) |

The [documentation index](docs/README.md) explains which document owns each topic and how to keep the guides current.

## Current system

The documented baseline is **API 0.3.0**, deployed on 14 September 2026.

- GitHub Pages serves the portal, job board, primer and six company sites.
- A Docker container runs the API on the VPS reached by `ssh vps`, under `~/homelab/workready`.
- The VPS's shared Caddy proxies `workready-api.eduserver.au` to `workready-api:8000` on `caddy_default`.
- SQLite and filtered mail attachments live in a persistent data volume.
- The local console runs on your computer. Its `/admin` page manages students through a server-side API proxy; it is not published as part of the student portal.

The API currently uses `stub` responses and the `custom` pacing preset. These are deployment settings, not product guarantees. Check `/health` and `/api/v1/privacy` before relying on a live configuration.

Participation is **pseudonymous, not guaranteed anonymous**. Use synthetic material. Contact filtering can miss identifying details, and cloud AI providers receive prompts when selected. See [privacy and access](docs/privacy.md).

## Repository map

Keep these **11 independent repositories as siblings** when using the console. The containing `workready/` folder is a workspace, not a monorepo or a Git superproject.

| Repository | Responsibility |
|---|---|
| [workready-deploy](https://github.com/michael-borck/workready-deploy) | This project home, guides, ADRs, publishing console and image build |
| [workready-api](https://github.com/michael-borck/workready-api) | Sessions, simulation state, assessment, conversations, records and admin API |
| [workready-portal](https://github.com/michael-borck/workready-portal) | Student workstation and shared browser session client |
| [workready-jobs](https://github.com/michael-borck/workready-jobs) | Fictional seek.jobs board and Quick Apply |
| [workready-primer](https://github.com/michael-borck/workready-primer) | Standalone Ink story, player and cartoon scene assets |
| [nexuspoint-systems](https://github.com/michael-borck/nexuspoint-systems) | Fictional cybersecurity and IT employer |
| [ironvale-resources](https://github.com/michael-borck/ironvale-resources) | Fictional mining employer |
| [meridian-advisory](https://github.com/michael-borck/meridian-advisory) | Fictional consulting employer |
| [metro-council-wa](https://github.com/michael-borck/metro-council-wa) | Fictional Western Australian local council |
| [southern-cross-financial](https://github.com/michael-borck/southern-cross-financial) | Fictional financial-planning employer |
| [horizon-foundation](https://github.com/michael-borck/horizon-foundation) | Fictional not-for-profit employer |

Example workspace:

```text
workready/
  workready-deploy/    # start here
  workready-api/
  workready-portal/
  workready-jobs/
  workready-primer/
  <six company repositories>/
```

Each component README covers its local files and build commands. Project-wide facts live here rather than being copied into all eleven repositories.

## Which dashboard?

| Interface | Audience and purpose |
|---|---|
| [Student portal](https://workready.eduserver.au/) | Students follow their own journey |
| Local console at `http://127.0.0.1:7788` | An operator edits files, reviews a build plan and publishes changes |
| Local console `/admin` | A lecturer issues/revokes codes, reviews records and manages student state |

The console is an operating tool. **This README and `docs/` are the documentation home.** The separate `simulation-staff` service on the VPS belongs to the CloudCore project, not WorkReady.

To start the console, from this repository:

```bash
uv run --project console python console/run.py
```

It prints a local unlock key. The API admin token is a separate credential. Read the [console guide](console/README.md) before publishing.

## Publishing in one paragraph

Build changed company sites and the job board locally and include their generated output when publishing. GitHub Pages publishes the checked-in artifacts. For the API, push all required source/content changes first, then request the bundled image build in this repository. Once it succeeds, the VPS pulls that image and recreates the API container. A frontend/API contract change needs a coordinated release. The [operations guide](docs/operations.md) has the commands and explains Compose overrides.

The root `docker-compose.yml` and bundled Caddy are an **alternative all-in-one deployment recipe**. They are not the Compose setup used by the existing shared VPS. Do not run that recipe on the VPS's occupied ports 80/443.

## Design history and future work

ADRs record accepted decisions and their consequences. Historical specifications and the [pre-release audit](AUDIT-2026-09-14.md) remain useful context but do not override the current guides. There is no promised implementation schedule for named lecturer accounts, LMS integration, real outbound messaging or multi-node scaling; these remain follow-up work.

Licensed under the [MIT License](LICENSE). The fictional organisations' policy documents are simulation content, not the software's operational or privacy policy.
