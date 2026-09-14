# ADR 0009: Formative evidence without an aggregate grade

Status: Accepted, retrospective

Recorded: 14 September 2026

## Context

WorkReady collects several kinds of assessment evidence. Resume/interview feedback concerns role fit, tasks concern submitted work, and exit reflection concerns the student's understanding of their experience. Combining these outputs into one score would imply a grading rule and validation that the project has not established.

## Decision

Provide a structured per-application journey report with stage evidence and a chronological timeline. Show the available scores, feedback and coaching/reflection records, including partial journeys. Leave any final grading judgement to the lecturer.

Keep exit reflection distinct from hiring assessment. The exit conversation uses an HR character different from the hiring manager and draws on the earlier journey. Simulation progression and completion remain application state; they do not constitute an academic grade.

## Alternatives

- A weighted aggregate would be easy to export but requires defensible weighting, calibration and a policy for incomplete or repeated stages.
- A completion-only report would be simpler but omit the evidence a lecturer needs to understand the student's decisions and progress.
- An immediate LMS grade pass-back would require both a grading policy and an integration that are absent from this baseline.

## Consequences

Lecturers can inspect how the journey developed and interpret stage feedback in context. The report does not provide a validated final mark or replace human assessment. A future gradebook integration must distinguish completion, individual formative scores and lecturer-assigned grades.

The report contains retained student activity and uses admin access. Shared-token and retention limits still apply; see [privacy](../privacy.md) and [ADR 0005](0005-local-publishing-console.md).

## Implementation history and evidence

- 13 April 2026: API [cbce529](https://github.com/michael-borck/workready-api/commit/cbce529) introduced journey reports, coaching and exit reflection. Its commit message explicitly states that there is no aggregate grade and that lecturers make the judgement. It also records the intent behind using a different HR character for reflection.
- 13 April 2026: portal [aa2775a](https://github.com/michael-borck/workready-portal/commit/aa2775a) added the matching journey-report and conversation views.

Current [`journey_report.py`](https://github.com/michael-borck/workready-api/blob/main/workready_api/journey_report.py) returns stage sections and a timeline, without an aggregate-grade field. [`exit_interview.py`](https://github.com/michael-borck/workready-api/blob/main/workready_api/exit_interview.py) implements the reflective conversation. The historical teaching intent is not evidence that the assessment has been educationally validated.
