# ADR 0008: Character context from stored conversations

Status: Accepted, retrospective

Recorded: 14 September 2026

## Context

A colleague replying only to the latest message repeats information and loses continuity with the student's work. WorkReady already stores messages, task submissions and stage feedback. Long conversations also need a way to reduce the history sent to a model.

## Decision

Build character reply context from stored simulation records. For mail/chat, combine the character persona, delivered conversation history and relevant placement context. Assemble history within the student/application boundary, then select messages involving the character.

Summarise older history when it exceeds the thread threshold and retain recent messages verbatim. The current shared context builder uses a 24,000-character thread threshold and keeps the latest four messages. It regenerates summaries per reply rather than maintaining a separate permanent memory store.

Use the configured API model path for replies and summaries. AnythingLLM hiring desks remain a separate integration. This decision does not require model fine-tuning or a vector database for student conversation memory.

## Alternatives

- Stateless replies send less history but cannot reliably refer to earlier exchanges.
- Sending every message verbatim preserves detail but lets prompt size grow with conversation length.
- A separate retrieval or persistent-summary store could handle larger histories but introduces indexing, staleness and deletion responsibilities.

## Consequences

Characters can refer to earlier conversations and work, but summarisation may omit or distort details. It adds model calls and latency. In the shared builder, a failed summary returns a brief prior-message count; stub mode supplies a deterministic generic summary. These fallbacks do not guarantee that a subsequent model reply succeeds.

The threshold bounds when thread summarisation starts, not the size of the complete prompt or the model's token budget. Persona and task context add more text. Character selection currently uses name/email heuristics within the student/application scope, so similar character names can mix context. This is not a precise character-ID memory model.

Summarising a prompt does not erase stored transcripts. Selected cloud providers receive conversation and placement context, subject to the filtering limits in [privacy and access](../privacy.md). See [ADR 0004](0004-data-handling-and-retention.md) for retention and erasure.

## Implementation history and evidence

- 13 April 2026: API [d82a81e](https://github.com/michael-borck/workready-api/commit/d82a81e) added stored thread history to character email replies.
- 13 April 2026: API [a27c973](https://github.com/michael-borck/workready-api/commit/a27c973) added long-thread summarisation and a recent-message tail to the mail path.
- 15 April 2026: API [cb763a6](https://github.com/michael-borck/workready-api/commit/cb763a6) introduced task-aware character context; [7f1dc50](https://github.com/michael-borck/workready-api/commit/7f1dc50) corrected asynchronous handling and thread filtering.

Current behaviour is defined in [`context_builder.py`](https://github.com/michael-borck/workready-api/blob/main/workready_api/context_builder.py) and [`mail.py`](https://github.com/michael-borck/workready-api/blob/main/workready_api/mail.py). Their summarisation paths differ. The original mail fallback and cost claims should not be treated as guarantees for every current conversation path.
