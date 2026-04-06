# Retry and Idempotency Rules

Retry policy defaults:
- `maxAttempts = 3`
- `initialBackoffMs = 300`
- `backoffMultiplier = 2.0`

Retry scope:
- claim: retry allowed for transient failures
- upload+confirm: retry allowed; implementation may re-run whole step
- submit: retry allowed for transient failures

Idempotency:
- Optional per-image idempotency key (`capture UUID` recommended)
- If key already resolved to image ID in same pipeline/session, skip duplicate upload
- Submit should use stable image IDs from prior confirmed uploads
