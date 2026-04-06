# Queue Durability Invariants

Invariant 1:
- Mission submission jobs are durably persisted before background processing.

Invariant 2:
- Job metadata and payload bytes are atomically written (or not visible as complete).

Invariant 3:
- On restart, pending jobs are discoverable and loadable.

Invariant 4:
- Completion removes durable artifacts for that job.

Invariant 5:
- Idempotency keys survive reload path via persisted metadata.

Invariant 6:
- Durable queueing does not imply synchronous upload completion.
