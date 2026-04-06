# Endpoint Contracts

Base:
- Partner API base URL: `/functions/v1/partner-api` (or environment override)

Mission:
1. `POST /missions/{mission_id}/claim`
2. `POST /missions/{mission_id}/prepare-upload`
3. `PUT  {signed_upload_url}`
4. `POST /missions/{mission_id}/confirm-upload`
5. `POST /missions/{mission_id}/submit`
6. `GET  /missions/{mission_id}`
7. `GET  /missions/available?lat={lat}&lng={lng}&radius_m={radius}`

Outlet:
1. `GET  /outlets/nearby?lat={lat}&lng={lng}&radius_m={radius}`
2. `GET  /outlets/{outlet_id}`
3. `POST /outlets/prepare-upload`
4. `POST /outlets`

Health / deprecation:
1. `GET /health`
2. `GET /deprecations/{feature_key}`

Auth:
- Bearer API key in `Authorization` header where required.
