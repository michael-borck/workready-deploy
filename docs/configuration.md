# Configuration and content

[Project home](../README.md) · [Architecture](architecture.md) · [Operations](operations.md)

Baseline: API 0.3.0. This guide owns the setting names, defaults and publication rules. Runtime code remains authoritative if a value changes.

## Four different kinds of configuration

| Kind | Where | Takes effect |
|---|---|---|
| API environment | VPS Compose files/environment; local API process environment | When the API process/container is recreated with the new values |
| Console pacing selection | [`pacing.json`](../pacing.json) | The console's API update writes and applies a Compose override |
| Runtime company/job data | `workready-api/jobs/<company>.json`, plus shipped company copies and character prompt files | New image/content deployment and API startup/cache reload |
| Website/story content | Company templates/content, portal `config.js`, job-board `src/`, primer `.ink`/assets | Build where required, then publish the affected static site |

Student code issuance, revocation, reset, erasure and reporting are database operations through the lecturer page. They do not require an image rebuild.

## Pacing presets and precedence

`SIMULATION_PRESET` accepts `custom`, `workshop` or `semester`. An unrecognised preset prevents API startup. Preset values are defined in [`scheduling.py`](https://github.com/michael-borck/workready-api/blob/main/workready_api/scheduling.py).

For the preset-aware numeric/boolean settings, precedence is:

1. Explicit environment value.
2. Selected preset's value.
3. Code default.

An invalid explicit numeric value falls back to its default in the current helper. Validate configuration before publishing; do not rely on that fallback as an operator interface.

| Setting | `custom` default | `workshop` | `semester` |
|---|---|---|---|
| `INTERVIEW_BOOKING_ENABLED` | false | false | true |
| `RESUME_FEEDBACK_DELAY_MINUTES` | 0 | 0 | 180 |
| `RESUME_FEEDBACK_DELAY_JITTER_MINUTES` | 0 | default | 120 |
| `INTERVIEW_FEEDBACK_DELAY_MINUTES` | 0 | 0 | 60 |
| `TASK_DEADLINE_DAYS` | 7 | 1 | 14 |
| `TASK_NEXT_TASK_DELAY_MINUTES` | 0 | 0 | 1440 |
| `TASK_FEEDBACK_DELAY_MINUTES` | 0 | 0 | 120 |
| `TASK_FEEDBACK_DELAY_JITTER_MINUTES` | 0 | default | 60 |
| `LUNCHROOM_INVITE_LEAD_HOURS` | 24 | 0 | 24 |
| `LUNCHROOM_TIME_OF_DAY_START` / `END` | 12 / 14 | 0 / 23 | default |
| `LUNCHROOM_EARLY_ENTRY_MINUTES` | 5 | 1440 | default |
| `LUNCHROOM_BEAT_INTERVAL_SECONDS` | 25 | 6 | default |
| `LUNCHROOM_BEAT_JITTER_SECONDS` | 10 | 1 | default |

"Default" means the preset does not change that value. These presets affect pacing; they do not guarantee a fixed session duration. Company hours, slot availability, the number of templates and student actions also matter. There is no single duration field that derives an entire twelve-week curriculum.

An explicit `TASK_FEEDBACK_DELAY_MINUTES=0` in Compose overrides the semester default. The console expands the preset into its Compose override to avoid that particular drift. Merely restarting a container does not apply a changed Compose environment; recreate it using the intended file set.

### What the console can edit in `pacing.json`

```json
{
  "SIMULATION_PRESET": "workshop",
  "TASK_DEADLINE_DAYS": 1
}
```

The current allowlist is `SIMULATION_PRESET`, `TASK_DEADLINE_DAYS`, `TASK_NEXT_TASK_DELAY_MINUTES`, `TASK_FEEDBACK_DELAY_MINUTES`, `RESUME_FEEDBACK_DELAY_MINUTES`, `INTERVIEW_FEEDBACK_DELAY_MINUTES` and `LUNCHROOM_INVITE_LEAD_HOURS`. Numeric values must be integers from 0 to 86400. Other API settings are not editable through this JSON file. See `validate_pacing()` in [`console/app.py`](../console/app.py).

## API setting reference

### Identity, storage and models

| Variable | Default | Meaning |
|---|---|---|
| `STUDENT_SESSION_HOURS` | 8 | Absolute lifetime of a newly issued student session |
| `LOGIN_REQUESTS_PER_MINUTE` | 10 | Per-client-IP login request budget, checked before credential validation |
| `WORKREADY_ADMIN_TOKEN` | unset | Shared admin API credential; blank disables admin endpoints with 503 |
| `WORKREADY_DB` | `workready.db` relative to the process directory | SQLite location; deployed path is `/opt/workready/data/workready.db` |
| `WORKREADY_ATTACHMENTS_DIR` | database directory + `attachments` | Filtered mail PDF storage; deployed under the data volume |
| `RETENTION_DAYS` | 120 | Inactivity threshold used by the operator-triggered cohort purge; not an automatic deletion schedule |
| `SITES_DIR` | parent of the API repository in the normal sibling checkout | Content lookup root; deployed bundled image uses `/opt/workready` |
| `LLM_PROVIDER` | `stub` | `stub`, `ollama`, `anthropic` or `openrouter` |
| `LLM_MODEL` | provider-dependent | Use a model supported by the selected provider; an example-file value can override the provider's code default |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Local or remote Ollama endpoint |
| `OLLAMA_API_KEY` | unset | Optional Ollama authentication |
| `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY` | unset | Credentials for the selected cloud provider |

`USE_LLM` and `OLLAMA_MODEL` in older instructions are not the current provider/model selectors. Explicitly set `LLM_PROVIDER` and, when needed, `LLM_MODEL`. Missing keys for a selected cloud provider can cause errors; choosing `stub` is the deliberate no-model mode.

The shared VPS uses `WORKREADY_TRUSTED_PROXY_IPS` in the privacy Compose override to populate uvicorn's `FORWARDED_ALLOW_IPS`. The console discovers the Caddy container address for its deployment command. Recheck trust settings when proxy/network topology changes. Classroom NATs may put many legitimate students behind one IP.

Implementation limits that are constants, not environment controls: 6 MiB request bodies, 5 MiB/20-page PDFs, and 60 authenticated student writes per minute per student/IP bucket. Budgets are process-local. See [`auth.py`](https://github.com/michael-borck/workready-api/blob/main/workready_api/auth.py), [`pdf.py`](https://github.com/michael-borck/workready-api/blob/main/workready_api/pdf.py) and the [privacy guide](privacy.md).

### Interviews and calendar

| Variable | Default | Meaning |
|---|---|---|
| `INTERVIEW_BOOKING_ENABLED` | false | Scheduled booking flow versus walk-up interviews |
| `BUSINESS_HOURS_START`, `BUSINESS_HOURS_END` | 9, 17 | Global local-time hours, with company overrides where used |
| `BUSINESS_DAYS` | `1,2,3,4,5` | ISO weekdays, Monday = 1 |
| `TIMEZONE` | `Australia/Perth` | Simulation scheduling timezone |
| `SLOT_DURATION_MINUTES`, `SLOTS_OFFERED` | 30, 4 | Booking slot generation |
| `EARLIEST_BOOKING_HOURS`, `LATEST_BOOKING_DAYS` | 2, 14 | Booking horizon |
| `LATE_GRACE_MINUTES`, `MAX_MISSED_INTERVIEWS` | 5, 3 | Lateness/missed-booking behaviour |
| `MAX_RESCHEDULES`, `RESCHEDULE_LIMIT_MODE` | 1, `hard` | Reschedule cap; `soft` tracks without enforcing the cap |
| `PUBLIC_HOLIDAYS` | bundled WA 2026–2027 list | Comma-separated ISO dates replace the default list |
| `RESUME_FEEDBACK_DELAY_MINUTES` / `_JITTER_MINUTES` | 0 / 0 | Resume outcome presentation delay and variation |
| `INTERVIEW_FEEDBACK_DELAY_MINUTES` / `_JITTER_MINUTES` | 0 / 0 | Interview outcome presentation delay and variation |

The jitter names are, for example, `RESUME_FEEDBACK_DELAY_JITTER_MINUTES`. `INTERVIEW_INVITATION_DELAY_MINUTES` is still declared but has no runtime consumer in this baseline. Do not use it as a working scheduling control.

### Tasks and lifecycle

| Variable | Default | Meaning |
|---|---|---|
| `TASKS_PER_STUDENT` | 3 | Requested number of available task templates, not an unlimited generator |
| `TASK_DEADLINE_DAYS` | 7 | Deadline offset from task visibility |
| `TASK_NEXT_TASK_DELAY_MINUTES` / `_JITTER_MINUTES` | 0 / 0 | Delay before later work is revealed after an accepted submission |
| `TASK_FEEDBACK_DELAY_MINUTES` / `_JITTER_MINUTES` | 0 / 0 | Delay before mentor feedback is shown |
| `MAX_CYCLES` | 3 | Placement-attempt limit |
| `BLOCK_ON_RESUME_FAILURE` | `role` | Blocking rule used for a rejected resume |
| `BLOCK_ON_INTERVIEW_FAILURE` | `company` | Blocking rule used for a rejected interview |
| `BLOCK_ON_TASK_FAILURE` | `company` | Blocking policy for applicable placement-failure records |

Blocking values are `none`, `role` or `company`. Declaring a policy does not add a missing failure transition. Current task resubmissions do not themselves close the placement. Resigned and completed applications also affect future company availability. Read [`blocking.py`](https://github.com/michael-borck/workready-api/blob/main/workready_api/blocking.py) when changing lifecycle rules.

Late task submissions are accepted and lateness is passed to the reviewer. Actual assigned task count is limited by available templates. Coaching currently keys off the second passed task. Bonus-task generation from the early design document is not implemented.

### Lunchroom

All variables below start with `LUNCHROOM_`.

| Suffix | Default | Meaning |
|---|---|---|
| `INVITES` | 3 | Maximum invitations per application |
| `DECLINE_LIMIT` | 2 | Declines/misses threshold for a gentle mentor check-in; further declines remain possible |
| `TRIGGER` | `task_review` | Current task-review invitation hook; other strings are not a complete alternative scheduler |
| `INCLUDE_MENTOR`, `PARTICIPANT_COUNT` | false, 3 | Participant selection |
| `INVITE_LEAD_HOURS`, `INVITE_HORIZON_DAYS` | 24, 5 | Proposed-slot window |
| `TIME_OF_DAY_START`, `TIME_OF_DAY_END`, `SLOTS_OFFERED` | 12, 14, 3 | Lunchtime window and offered slots |
| `EARLY_ENTRY_MINUTES`, `LATE_ENTRY_HOURS` | 5, 24 | Entry window around an accepted slot |
| `SOFT_CAP`, `HARD_CAP` | 18, 25 | Message-count caps, not minutes |
| `BEAT_INTERVAL_SECONDS`, `BEAT_JITTER_SECONDS` | 25, 10 | Character-message pacing |
| `OPENING_DELAY_SECONDS` | 5 | First character beat after activation |
| `MENTION_RESCHEDULE_SECONDS` | 8 | Pull-forward target after an `@mention` |
| `BEATS_PER_CHAR_MIN`, `BEATS_PER_CHAR_MAX` | 3, 5 | Planned contribution range |
| `OCCASIONS` | empty | Optional comma-separated allowlist of supported occasion names |

Use actual supported occasions from [`lunchroom.py`](https://github.com/michael-borck/workready-api/blob/main/workready_api/lunchroom.py), rather than assuming arbitrary strings create scenarios.

## Content sources and publication

| Change | Edit | Build/publish requirement |
|---|---|---|
| Company website profile | `<company>/brief.yaml`, relevant `site/templates/` | Rebuild company `dist/`, review it, then publish the company repository |
| Website employee biography or policy | `<company>/content/employees/*.md`, `content/docs/**/*.md` | Rebuild/publish company site; these are fictional workplace materials |
| Runtime roles, hours, task templates, embedded manager persona | `workready-api/jobs/<company>.json` | Synchronise company copy, rebuild affected site, publish source changes, build/pull API image |
| Mail/chat/lunchroom character voice | `<company>/content/employees/<slug>-prompt.txt` | Publish company repository and rebuild/pull the API image; cached prompts need a process refresh |
| Job-ad Markdown source | `<company>/content/jobs/*.md` | Re-export/synchronise `jobs.json`; changing Markdown alone does not change exported listings |
| Portal six-step copy, links, themes | `workready-portal/config.js` | Publish portal; no HTML build required |
| Job-board code/config/style | `workready-jobs/src/` | Run `python3 build.py`; publish `src/` and generated `dist/` changes |
| Primer narrative | `workready-primer/workready.ink` | Run `bash build.sh`; publish source and generated story/runtime |
| Primer illustrations/player | `assets/scenes/`, `index.html` | Publish primer; recompile Ink only if its source/tags changed |

### Keep runtime exports consistent

The console's canonical runtime authoring source is `workready-api/jobs/<company>.json`. When selected in a console plan, it is copied to the company's `jobs.json` before its website is built. The API loader checks `<SITES_DIR>/<company>/jobs.json` first and `<SITES_DIR>/<company>.json` second. The installer supplies the flat copies from the API repository. A stale company-root export can therefore win over a newer flat file.

For manual edits, reconcile both copies before building the release. On a fresh company clone with no `jobs.json`, copy its canonical API export to the company root as a build input. Do not assume that editing `brief.yaml` runs Ensayo or regenerates any export; there is no automatic generator stage in the API startup.

Ensayo is an upstream authoring tool referenced in historical plans, not a prerequisite for running the already-exported simulation. The console does not expose every prompt file or every environment setting. Its current file allowlist is in [`console/app.py`](../console/app.py).

## Local console configuration

| Variable | Default | Meaning |
|---|---|---|
| `WORKREADY_HOME` | sibling workspace above `workready-deploy` | Local repositories the console edits |
| `CONSOLE_TOKEN` | random key printed at startup | Local console unlock key; separate from API admin credentials |
| `WORKREADY_API_BASE` | `https://workready-api.eduserver.au` | Trusted API upstream for the admin proxy and health checks |
| `WORKREADY_VPS` | `vps` | SSH alias used by the console |
| `WORKREADY_VPS_DIR` | `homelab/workready` | Path relative to the SSH user's home |

The console binds its UI to `127.0.0.1:7788` and static previews to `localhost:7789` via `run.py`. It uses fixed eight-hour local sessions. The key belongs in the login form, not a URL. See the [console guide](../console/README.md).

## Browser origins and optional hiring desks

Portal/job-board API URLs live in their config files; company forms declare a `data-api-base`. The shared session client is served by the portal. Content Security Policy declarations and API CORS settings must agree with the intended deployment origins. Changing only `localStorage.workready_api_base` is not a complete local-development configuration.

Hiring desks use [`chatbot-embeds.json`](../chatbot-embeds.json), company build context and [`setup-chatbots.py`](../setup-chatbots.py). They are separate from the API's `LLM_PROVIDER` setting. External widgets are excluded from careers/application and staff pages in the current templates. Changing the API to stub mode does not disable a separately hosted hiring desk.
