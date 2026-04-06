# Conformance Matrix (v1)

| Capability | iOS SDK | Android SDK | Notes |
|---|---|---|---|
| Endpoint contracts | ✅ | ✅ | Partner API and deprecations covered |
| Typed DTO schemas | ✅ | ⚠️ (partial) | Android mission DTO parity in progress |
| Mission state machine | ✅ | ✅ | Added state machine primitive in both |
| Error taxonomy | ✅ | ⚠️ (partial) | Android has broader SDK errors; mapping alignment pending |
| Retry/backoff policy | ✅ | ✅ | iOS pipeline + Android queue/uploader |
| Idempotency per image | ✅ | ✅ (state machine primitive) | Android integration wiring pending |
| Queue durability invariants | ✅ | ✅ | iOS durable queue primitive + Android queue persistence |
| Workflow tests claim->upload->confirm->submit | ✅ | ✅ | Added dedicated state-machine tests |

Legend:
- ✅ implemented
- ⚠️ partially implemented / integration pending
