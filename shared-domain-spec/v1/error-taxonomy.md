# Error Taxonomy

Transport:
- invalid URL
- invalid response/non-HTTP
- request failed (`4xx/5xx`)

Auth:
- unauthorized (`401`)

Rate limiting:
- rate limited (`429`)

Server:
- server error (`5xx`) with extracted message

Domain/state:
- invalid state transition
- no images
- image encoding failure

Retryability guidance:
- retryable: transient `5xx`, network transport instability
- non-retryable: invalid transition, malformed request, unauthorized
