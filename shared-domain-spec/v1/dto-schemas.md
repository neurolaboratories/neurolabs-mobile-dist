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

Capture requests:
- Catalog page:
  - `total`
  - `requests[]`
- Request item:
  - `id`
  - optional `parent_id`
  - optional `title`
  - optional `barcode`
  - optional `created_at`
  - optional `status`
  - optional `thumbnail_url`
- Metadata fields:
  - `field_name`
  - optional `regex`
- Submission draft:
  - optional `request_id`
  - `metadata{string->string}`
  - `files[]` with `upload_field_name`, `filename`, `mime_type`, `metadata_field_name`

Validation:
- Missing required fields => invalid response classification.
- Unknown enum string values are preserved as raw strings (no hard failure).
