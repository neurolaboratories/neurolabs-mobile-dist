# Mission State Machine

Canonical workflow:
1. `IDLE`
2. `CLAIMED`
3. `UPLOADED_CONFIRMED` (one or more images uploaded and confirmed)
4. `SUBMITTED`

Allowed transitions:
- `IDLE -> CLAIMED`
- `CLAIMED -> UPLOADED_CONFIRMED`
- `UPLOADED_CONFIRMED -> UPLOADED_CONFIRMED` (additional uploads)
- `UPLOADED_CONFIRMED -> SUBMITTED`

Invalid transitions:
- `IDLE -> SUBMITTED`
- `CLAIMED -> SUBMITTED` without any confirmed image
- Any transition out of `SUBMITTED` in same session/pipeline

Notes:
- Upload+confirm can be implemented as one atomic SDK operation internally.
- Public semantics must remain equivalent to `upload` then `confirm`.
