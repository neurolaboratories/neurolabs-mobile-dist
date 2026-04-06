# DTO Schemas (Canonical)

Mission status:
- String-valued enum wrapper (`rawValue`) to preserve forward compatibility.

Mission:
- `id`
- `status`
- `start_time`, `end_time`
- `outlet`
- `distance_km`
- `schema_version`
- `mission_subsections[]`

Prepare upload response:
- `data.image_id`
- `data.upload_url`
- `data.storage_path`
- `data.expires_in_seconds`
- optional `data.upload_token`, `data.instructions`

Confirm upload response:
- `data.image_id`
- `data.storage_path`
- `data.confirmed`
- optional `data.file_size_bytes`

Submit response:
- `data.mission_id`
- `data.submission_id`
- `data.status`
- `data.submitted_at`

Outlet details/creation:
- normalized outlet identity and geo fields
- optional subsection and thumbnail fields

Validation:
- Missing required fields => invalid response classification.
- Unknown enum string values are preserved as raw strings (no hard failure).
