# Neurolabs Shared Domain Spec v1

Status: draft-in-use  
Owners: SDK team (iOS + Android)

This directory is the platform-agnostic source of truth for the mission submission domain.

Included:
- `endpoint-contracts.md`
- `dto-schemas.md`
- `mission-state-machine.md`
- `error-taxonomy.md`
- `retry-idempotency.md`
- `queue-durability-invariants.md`
- `conformance-matrix.md`

Scope:
- Mission flow: `claim -> upload -> confirm -> submit`
- Outlet photo flow (prepare-upload/create-outlet) contracts
- Durable queue behavior for mission submissions

Non-scope:
- UI/view-model state
- Navigation/routing
- Product-specific feature flags
- Partner-specific UX text/policy
