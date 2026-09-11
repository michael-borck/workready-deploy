# WorkReady — 10-minute live demo script

**Config on the VPS:** all feedback delays = 0 → everything lands instantly.
**Codes:** issue more any time at `workready.eduserver.au/admin.html` (token in `~/homelab/workready/.env`).

## Pre-demo checklist (2 min before)

- [ ] Tabs open, in order: **Portal** → **seek.jobs** → **Primer** → **NexusPoint** → **admin.html**
- [ ] Admin tab: token already saved (sessionStorage keeps it)
- [ ] Resume file on desktop: `workready-jobs/samples/ava-mitchell-security-analyst.pdf`
- [ ] Scratch file with the paste-blocks below (cover letter, interview answers, task submission)
- [ ] A fresh code, e.g. `WR-MR4A-5GV6` (list in `/tmp/demo-codes.txt`)
- [ ] Remember: the portal polls every 30 s — **clicking a nav item refreshes instantly**

---

## 0:00 — Hook + Primer (~1 min, Primer tab)

> "Before students touch the simulation, they rehearse the *idea* of it in interactive fiction."

- Play one choice, show the shadow-path ("here's what would have happened if…"), then bail out.
- One line: *fifteen minutes, safe-to-fail, replayable.*

## 1:00 — Sign in with a code (~1 min, Portal tab)

- Type `WR-MR4A-5GV6` → Sign in.
- **Persona modal appears**: "Pick any name you like" → type `Ava Mitchell`.
- Point at the derived mailbox: `ava.mitchell@student.workready.eduserver.au`.
- **Privacy beat**: *"The server stores a random code and this fiction — no email, no real name.
  The mapping between code and human lives in my spreadsheet, nowhere else."*

## 2:00 — Apply on seek.jobs (~90 s, seek.jobs tab)

- Open **NexusPoint Systems → Junior Security Analyst** → Quick Apply.
- Name: `Ava Mitchell` · Code: pre-filled from portal handoff.
- **Upload** `ava-mitchell-security-analyst.pdf` from the desktop.
- Paste cover letter:

> I am excited to apply for this role because it aligns closely with my studies, my project
> experience and my career goals, and I would love to contribute to your team while learning
> from your senior people.

- Submit. *"Real employers don't reply in three seconds — we've compressed time, but the
  uncertainty is a feature. In a real cohort this takes hours."*

## 3:30 — The outcome (~1 min, Portal tab)

- Click **Inbox** (personal) → open the application response.
- Read the fit score + a strength and a gap aloud.
- **If it failed instead** (typed a too-short cover letter): show the rejection feedback, say
  *"failure is data — and the world keeps moving"*, then quietly force-pass via admin
  (`admin.html → student → Force state → resume_pass`) and move on. Do not dwell.

## 4:30 — The interview (~90 s, Portal tab)

- Interview view → Start. The hiring manager opens.
- Paste these one at a time (each scores well with the stub assessor):

1. `I have used SIEM dashboards in my security unit and shadowed a SOC analyst during work experience.`
2. `When an alert fires I verify the signal, check the runbook, contain the affected host and escalate with a clear timeline.`
3. `I keep stakeholders updated early and document every step so the incident review has solid evidence.`
4. `I want to build incident-response depth and cloud security skills in a team like yours.`
5. `I researched NexusPoint's client base and I am genuinely keen to learn from your senior analysts.`

- Click **End interview** → debrief + score. **HIRED** — the sidebar grows work items and the
  whole portal re-themes to NexusPoint's brand.
- *"They got the job — but in a cohort, half the room won't, and that's the lesson."*

## 6:00 — Work tasks (~90 s, Portal tab)

- Mentor's welcome + first task brief in the **work inbox**.
- **Tasks** nav → three cards, only task 1 unlocked. Open the full brief.
- Paste submission:

> I monitored the alert queue, verified signals against the runbook, escalated with a documented
> timeline and drafted the client summary with recommendations.

- Submit → "under review" → feedback + task 2 unlock arrive. Task 2's submission triggers the
  **mid-placement coaching invite** — mention it, don't run it.

## 7:30 — The lunchroom (~90 s, Portal tab)

- Lunchroom invitation in the work inbox → pick a slot → **Enter the lunchroom**.
- Colleagues chat in beats. Type a reply **@mentioning someone** — their next beat pulls forward.
- *"The social layer. Most sims skip it; most internships are decided here."*
- If asked about missing it: students can decline twice — the characters notice.

## 9:00 — Tease + lecturer view (~1 min, admin tab)

- Mention **exit interview** (Stage 6): reflective, with HR, scored on self-awareness — "leave
  them wanting it."
- **admin.html** → student → **Journey report**: the printable lecturer artefact, resume to
  exit, every stage.
- *"No AI grading. The simulation assesses; the lecturer grades."*

## 9:45 — Close (deck)

- Privacy recap: code-only identity, redacted resumes, fictional inboxes.
- Config recap: same system, one env file = demo afternoon or 12-week placement.
- Fire-drill line: *"Every graduate rehearses a fire drill. Why not their first internship?"*

---

## Contingency card

| What goes wrong | Play |
|---|---|
| Resume rejected | Show the feedback email — it's good content. Force-pass via admin, move on |
| Interview score low → rejected | Same: honest debrief, then admin `interview_pass` |
| Lunchroom quiet | `@mention` a character by name; beats also keep flowing — move the story on |
| Portal feels stale | Click any nav item — instant refresh (30 s background poll) |
| Anything hard-broken | Fall back to the deck, slides 6–8 (privacy + config) — they sell themselves |
