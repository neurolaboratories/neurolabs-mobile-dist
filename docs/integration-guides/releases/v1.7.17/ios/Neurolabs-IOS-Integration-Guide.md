# Neurolabs iOS SDK - Integration Guide

## 1. Scope
This guide is for partner iOS apps integrating `NeurolabsSDK` through Swift Package Manager.

## 2. Release History

No public API contract has been broken since v1.1.9. New options have been
added with backwards-compatible defaults. Recommended defaults: strict
shelf guidance with overlays disabled, `liveQualityEnabled: true`,
`autoCloseAfterCapture: true` for single-capture parity flows.
`NLCameraConfiguration.captureRange(...)` is the preferred helper for
custom-camera flows that need a minimum capture count and a higher
maximum cap. `showsCapturedCountLabel` hides the `N captured` chip in
custom camera and multi-capture flow UIs.

### v1.7.17
No initialiser changes. The new options are stored properties set after
`init` and are additive for the ABI.

Behaviour changes, with no opt-in:
- An offline chip on the default and AR camera, on by default (section 7).
- "Review shelf" pages through a sweep of more than 8 bays and lists the
  walk's brands and products under "On this shelf" (section 9).
- The bridge (`NLNativeMultiBayConfig`, WebView and Cordova) carries a
  continuous AR sweep's plan of up to 30 bays (section 9).

New APIs:
- `NLCameraConfiguration.showsOfflineIndicator` (section 7).
- `NLCameraConfiguration.arBoxUnmatchedColor` (section 13).
- `NeurolabsSDKCore.productDetailsSource`: product names for a camera opened
  by `openNativeCaptureUI` (section 13).
- The bridge keys `showsOfflineIndicator` and `arBoxUnmatchedColor` on
  `NLNativeCaptureConfig` and `NLNativeCaptureOptions`.

### v1.7.16
No initialiser changes. New per-camera options are stored properties set
after `init` and default to the old behaviour; the retained-photo settings
and `prefetchPolicy` are process-wide statics.

Behaviour changes, with no opt-in:
- A new capture is refused with `STORAGE_LOW` when the queue's directory has
  under 500 MB free (section 6). There is no switch to turn this off.
- Captures are sized to a 4032 px long edge at JPEG 0.9 when the host sets no
  `maxImageDimension` / `imageCompressionQuality`, and the org's remote
  `sdkCapture` values can resize them further for hosts that set nothing
  (section 7).
- The AR shutter queues ARKit's 12 MP still instead of the ~1920x1440 video
  frame (section 13).

New APIs:
- `finalReview`: an end-of-session review on the default camera (section 7).
- Retained photos: `NLConfiguration.maxRetainedPhotos`,
  `retainedPhotoExpiryDays`, the `retainedPhotosHigh` delegate methods,
  `STORAGE_LOW`, `NLQueueStatus.retainedCount` / `retainedBytes` (section 6).
- `NLDetectorModels.prefetchPolicy` and the image-only quality checks while
  there is no detector (section 7).
- Capture images default to 4032 px / JPEG 0.9, overridable per org by the
  remote config (section 7).
- AR options: `arBoxStyle`, `arBoxHighlightColor`, `arCoverageStyle`,
  `arCoverageOutlineColor`, `arBoxPersistence`, `arLiveLabels`,
  `arLiveCount`, `productDetailsSource`; 12 MP AR stills (section 13);
  `NLMultiBayOptions.maxSupportedContinuousBays` (section 9).

### v1.3.2
- Mixpanel ingestion routes to the EU region via
  `NLAnalyticsContext.resolveMixpanelEndpoint(fallback: .mixpanelEndpointEU)`
  at SDK construction; the `NLMixpanelAnalyticsTracker` default itself
  stays on the standard US endpoint so partners reusing the class for
  their own US-region projects are unaffected. Endpoint can be overridden
  via the `NLMixpanelEndpoint` Info.plist key or the
  `NL_MIXPANEL_ENDPOINT` environment variable (env wins over plist).
- Mixpanel `time` field is now serialized as a JSON number (epoch
  seconds). Previously `time` was sent as a string, which Mixpanel
  rejected with `{"status":0,"error":"time field must be a number"}`,
  silently dropping every event.
- `NLCustomCameraView.saveAllCaptures` keeps the Done button responsive:
  the synchronous `FileManager.removeItem` loop for staged-capture files
  moved into a `Task.detached(priority: .utility)` block, and the Done
  label swaps to an inline `ProgressView` while
  `isPersistingCaptures == true`. Opacity remains at 1 during persist so
  the indicator stays visible.
- New `NLOperationsCatalogClient` (in `ProductAuditKit`) for the
  operations product catalog, with `BarcodeLookupIdentity` normalising
  UPC-E/EAN-8/UPC-A/EAN-13 to GTIN-14 end-to-end.
  `NLOperationsCatalogError.invalidBarcode` / `.invalidSearchQuery` /
  `.malformedResponse` are thrown rather than crashing the host with
  `precondition`.
- `NLBDemoApp` gains an in-app settings sheet on `CustomCameraDemoView`
  (gear icon, top-right). Sliders / steppers / toggles for every tunable
  knob, bindings wired to existing `@AppStorage` properties so saved
  values survive across launches.
- Mixpanel event identity hardened: per-install distinct id persisted in
  `UserDefaults`, `$insert_id` (UUID4) on every event for server-side
  dedup, response body surfaced when `debugLogging` is true.

### v1.3.1
- Restrict barcode symbologies to retail formats (EAN-13, EAN-8, UPC-A,
  UPC-E) so the scanner stops emitting non-product codes during
  capture.

### v1.3.0
- Angle-off warning threshold relaxed to 12° for less aggressive
  blocking during normal in-store motion.
- Multi-capture preview deletion: persisted thumbnails are removed when
  the matching capture is dropped.
- AVFoundation preview recovery hardened against backgrounding /
  interruption.

### v1.2.8
- `ProductAuditKit` test targets added (no public API change).

### v1.2.6 / v1.2.7
- Product Audit (onboarding) MVP: serialise `AVAssetWriter` finalize and
  `OCRSmartRotationProvider` work via in-flight `Task`, off-actor
  keyframe JPEG writes, completedStepIDs reflect steps that actually
  ran, step transitions serialised via pending-transition queue.

### v1.2.5
- New `showsSequenceCounterLabel` option in the native capture API for
  toggling the on-screen sequence counter.
- Persistent custom-camera tuning in the demo app (precursor to the
  v1.3.2 settings sheet) — preferences survive across runs via
  `UserDefaults`.
- AVFoundation preview recovery improved on capture failure.
- Strict-rejection preview freeze regression fixed.

### v1.2.4
- Release build / Swift 6 archive blockers resolved.

### v1.2.3
- `NLCameraConfiguration.captureRange(...)` helper for bounded
  multi-capture flows.
- 0.5×/1× lens switcher built on AVFoundation, default camera mode
  starts on the ultra-wide lens when available. Tap-to-focus, lens
  switch fallback covered by unit tests.
- Custom-camera startup, lens switching, and guidance responsiveness
  improvements; camera preview shown during warmup, capture button
  gated until ready.
- Default task routing config uses `taskUUID`.
- Recommended custom-camera parity flow remains strict shelf guidance
  with overlays disabled, `liveQualityEnabled: true`,
  `autoCloseAfterCapture: true` with a single required capture.

### v1.2.2
- Analytics tracking + opt-out, partner/device context, Mixpanel
  defaults, Sentry integration with privacy-safe defaults.

### v1.2.1
- Initial lens switcher, memory fixes, bottom-bar centering and UI
  polish.

### v1.2.0
- Docs aligned to v1.1.9 requirements baseline; no SDK code change.

### v1.1.9 (baseline)
- Init and per-session routing use `taskUUID`.
- Native detector/model warmup enforced in `init` and guarded in
  `openCamera`.
- `autoCloseAfterCapture: true` keeps preview enabled and closes after
  Save confirmation.

## 3. Requirements
- iOS 17.0+ (SDK package declares `.iOS(.v17)`)
- Xcode 16.4+ (release toolchain baseline)
- Swift 5.9+ (Swift 6 toolchains supported)

## 4. Install (SPM)
Add package dependency (mobile-dist or direct distribution manifest) and link `NeurolabsSDK`.

## 5. SDK Initialization + Warmup

Uploads use the **operations platform** with a **single key**: the `apiKey`
passed to `init` seeds the operations credential automatically, and every
capture routes through the resumable operations mission flow
(`init-resumable → chunked PUT → complete` per image, `submit` per session)
against `api.operations.neurolabs.ai`. No base URL or separate credential call
is needed; use `setOperationsApiKey(_:baseURL:)` only to rotate the key or to
point at a non-production host (staging/dev).

```swift
import NeurolabsSDK

final class CaptureCoordinator {
    let sdk = NeurolabsSDKCore(configuration: .init(
        apiKey: "<OPERATIONS_API_KEY>",
        debugLogging: true,
        taskUUID: "<DEFAULT_TASK_UUID>" // optional IR-task override (never a mission id)
    ))

    func prepare() {
        // SDK starts image pipeline preparation during init.
        // Optional: observe loading progress through delegate.
    }
}
```

## 6. Queue Management

```swift
Task {
    await sdk.setAutoSyncEnabled(true)
    await sdk.setWifiOnlyUploadsEnabled(false)
    await sdk.setDeletePhotosOnUploadSuccess(true)
    await sdk.setMaxQueueSize(200)
    await sdk.setUploadRetryCount(5)

    let status = await sdk.getQueueStatus()
    print("pending=\(status.pendingCount) failed=\(status.failedCount)")

    await sdk.flushQueue()
    await sdk.retryFailedUploads()
}
```

### Inspecting the queue at launch

Before you inspect, withdraw or discard queued work at launch, wait for the
queue to finish loading the records an earlier launch left on disk:

```swift
Task {
    await sdk.awaitQueueHydrated() // the whole pass; returns at once once it has run
    for item in await sdk.getQueuedItems() where item.sessionId == abandonedSessionId {
        await sdk.removeQueuedItem(item.id)
    }
}
```

- It returns once the whole pass has finished, also when the load failed (the
  queue then holds what it could read). After a re-`configure()` it also waits
  for the replaced instance's queue to stop, so what it reports is settled.
- A setter that rebuilds the queue (`setMaxQueueSize(_:)`,
  `setUploadRetryCount(_:)`, a new operations key or base URL) starts a new
  pass; the call waits for the queue that is current when it returns.
- On an instance that `configure()` replaced it returns at once. Call it on
  `NeurolabsSDKCore.shared`.

### Retained photos and low storage (v1.7.16)

Only pending, uploading and failed items take a `maxQueueSize` slot. Uploaded
photos the queue keeps on the device (keep-photos mode,
`setDeletePhotosOnUploadSuccess(false)`, or photos kept until their session's
submit) never fill the queue; two process-wide settings bound them instead:

```swift
NLConfiguration.maxRetainedPhotos = 500     // default 500, must be > 0
NLConfiguration.retainedPhotoExpiryDays = 14 // default nil = off, must be > 0

let status = await sdk.getQueueStatus()
print("kept=\(status.retainedCount) bytes=\(status.retainedBytes)")
```

- From 80% of `maxRetainedPhotos` (rounded up) the SDK calls
  `neurolabsSDK(_:retainedPhotosHigh:limit:)` on `NeurolabsSDKDelegate` once
  per crossing (re-armed when the count drops back below) with an
  `NLRetainedPhotos` (`count`, `bytes`, `oldestCreatedAt`). The queue-level
  twin is `queueManager(_:retainedPhotosHigh:limit:)` on
  `NLQueueManagerDelegate`. Both have default empty implementations. At the
  limit the SDK only logs; it never refuses a capture for retained photos.
- `retainedPhotoExpiryDays` deletes a kept uploaded photo captured at least
  that many days ago, files included, at the next flush or launch. Photos
  kept only for a submit never expire.
- A new capture is refused with `STORAGE_LOW` (retryable) when the queue's
  directory has under 500 MB free. It reaches you through
  `didEncounterError` and the failed capture result, as `QUEUE_FULL` does,
  and it is a client condition (`NLError.clientConfigurationCodes`), never
  reported to the SDK's Sentry.

## 7. Open Custom Camera

```swift
import UIKit
import NeurolabsSDK

var capture = NLCaptureConfiguration()
capture.confidenceThreshold = 0.25
capture.iouThreshold = 0.45
capture.maxCaptures = 1
capture.guidanceMode = .strict
capture.showDetectionOverlays = false
capture.showCapturedRegions = false

let config = NLCameraConfiguration.captureRange(
    capture,
    minimumCaptures: 1,
    maximumCaptures: 5,
    cameraMode: .default,
    showCapturePreview: true,
    showPreviewInStrictMode: true,
    showsCapturedCountLabel: false,
    enableValidation: true,
    showAlignmentGuidance: true,
    enableARDetections: false,
    liveQualityEnabled: true,
    liveQualityFPS: 6
)

let handlers = NLCustomCameraHandlers(
    onSave: { capture in
        // Custom post-processing hook for each accepted capture
        // return .performDefault -> SDK also enqueues upload
        // return .skipDefault -> app takes full ownership
        return .performDefault
    },
    onSaveAll: { captures in
        // Batch hook (multi-capture flow)
        return .performDefault
    }
)

sdk.openCustomCameraUI(
    configuration: config,
    handlers: handlers,
    onClose: {
        print("Camera closed")
    }
)
```

Recommended capture payload notes:
- `liveQualityEnabled: true` is the key for pill/rotation/warning/error guidance behavior in the custom camera.
- Keep shelf capture mode with strict guidance and overlays disabled for the custom-camera guidance UI path.
- Use `NLCameraConfiguration.captureRange(...)` to express a minimum capture requirement plus a larger maximum cap.
- Use `showsCapturedCountLabel = false` to hide the count chip when you do not want `N captured` shown.
- `guidanceMode: .guidance` should only be used as a temporary fallback if a partner explicitly wants looser guidance than the parity path.

### Offline chip (v1.7.17)

The default and AR camera show a small chip while the upload queue sees no
network: "Offline · uploads queued" (or "Offline" with nothing queued), and
"Waiting for Wi-Fi · uploads queued" while Wi-Fi-only uploads hold photos on
a cellular network. It hides while the network is unknown and when the host
uploads the photos itself (`uploadsEnabled == false`). It is informational
only and never gates the shutter.

```swift
config.showsOfflineIndicator = false // default true
```

On the bridge, `showsOfflineIndicator` (`Bool?`) on `NLNativeCaptureOptions`
and `NLNativeCaptureConfig` resolves options, then config, then `true`.

### Capture image size (v1.7.16)

With no `maxImageDimension` / `imageCompressionQuality` set by the host, a
capture is sized to a 4032 px long edge at JPEG quality 0.9. Each knob
resolves on its own: the host value (`NLCameraConfiguration`, which
`NLNativeCaptureOptions` then `NLNativeCaptureConfig` resolve into), then
the org's remote config, then the SDK default.

- The org values are `sdkCapture.maxImageDimension` and
  `sdkCapture.imageCompressionQuality` in `GET /v1/recognition-config`. They
  apply only inside 1024-4032 px and 0.5-1.0; anything else is ignored (not
  clamped) and that knob keeps the default. They are read at capture time, so
  a config fetched after the camera opened applies to the next shot.
- The tightest cap wins, the aspect ratio holds and nothing is upscaled.
  Inside every cap an image keeps its bytes when the resolved quality is at
  least 0.9; a lower one (an org's 0.7, say) re-encodes it at full size.
  Width and height caps (`maxImageWidth`, `maxImageHeight`) stay host-only.
- To ship the camera's JPEG untouched, set the host values: a
  `maxImageDimension` of 0 or less means no cap, and an
  `imageCompressionQuality` of 1 or more keeps an in-cap image's bytes. Host
  values always win over the org's remote config.

### End-of-session review: finalReview (v1.7.16)

`finalReview` gives the default (non-AR) camera without a multi-bay plan one
review at the end of the session instead of a preview per shot:

```swift
var config = NLCameraConfiguration.captureRange(
    capture, minimumCaptures: 1, maximumCaptures: 10, cameraMode: .default
)
config.finalReview = true // set after init; default false

// SDK-managed / bridge: the same key, options over config, then false
var options = NLNativeCaptureOptions(allowManualFinish: true)
options.finalReview = true
sdk.openNativeCaptureUI(config: nativeConfig, sessionId: sessionId,
                        options: options)
```

- There is no per-shot preview, whatever `showCapturePreview` says. Done, or
  reaching the count that ends the session (`maxCaptures`, the auto-close
  target, or the required count when there is no Done button), opens
  **Review** with every photo.
- Tapping a photo opens it ("Photo 1 of 2"): quality readout, Crop, Delete,
  Previous / Next and "Back to review". A crop keeps the capture's
  `captureId`; a delete reports `onCaptureDeleted` with source `.review`.
- **Confirm** saves the photos left, in capture order with crops applied,
  through your `onSaveAll` / `onSave` handlers or the upload queue, and the
  session result is delivered as usual. **Back to camera** keeps the photos
  and keeps capturing.
- The close button (X) on an opened photo goes back to Review and discards
  nothing. The close button on Review, or the camera screen's own, closes the
  camera: every photo not yet confirmed is discarded (staged files and the
  recovery journal deleted) and the session ends as cancelled, with nothing
  queued. Without `finalReview` those photos would already have been queued
  at the shutter.
- A host `onClose` handler (`NLCustomCameraHandlers.onClose`) can intercept
  that close: the SDK discards and closes only when it returns
  `.performDefault`.
- Nothing from the session is saved or queued before Confirm. The photos stay
  staged on the device (and survive an app kill) until then.
- The AR camera and multi-bay sessions ignore it and keep their own flows.

### Camera-only integration

If your app presents `NLCustomCameraViewController` without creating a `NeurolabsSDKCore`, register an operations credential for the detector download first. Without it (or a core) the standalone camera has no detector: capture works, but live detection, the shelf guidance cues and the overlay stay off, and the camera says "Detector unavailable. You can still capture." (reason `no_credentials`), not "Detector downloading".

```swift
NLDetectorModels.setCredentials(apiKey: operationsKey)              // production
// NLDetectorModels.setCredentials(authProvider: provider, baseURL: stagingURL)
```

The call is idempotent (the same key again changes nothing, so a failure's retry wait still holds), a new key retries at once, and the most recent call wins, this one or a core's. A base that is not absolute https with a host is refused.

For a signed-in rep's bearer, follow this lifecycle:

- **At sign-in,** call `setCredentials(authProvider:)` with one provider for that rep. You can call it again on each camera open, as long as you pass that same instance. A new provider per call refreshes each time, and the new bearer counts as a new key, which clears the retry wait.
- **On account switch,** call it with a new provider.
- **On sign-out,** make the provider's `token()` throw. There is no unregister, and a capture session asks the last provider again while the model is not on the device yet.

The download needs about 195 MB free (3.5 times the model: the archive, its unpacked copy and the compiled model are on disk at once during the install). With less it fails with `insufficient_storage` and is retried at the next capture session. After an install the SDK deletes older model versions. If the installed model will not load, the SDK deletes it and downloads it once more; if that copy fails too, the status is `load_failed` until the app restarts. A server answer that is not the model (a captive portal's page, a body of the wrong length) is `download_failed`, retried after a minute, not `sha_mismatch`.

### Detector download network policy (v1.7.16)

The SDK downloads the ~56 MB detector by itself (core start, a credential
change, `setCredentials`, a capture session opening). To keep that off
cellular:

```swift
NLDetectorModels.prefetchPolicy = .unmeteredOnly // default .anyNetwork
// set it before creating a NeurolabsSDKCore or registering credentials
```

- With `.unmeteredOnly` those downloads run only on a network that is neither
  expensive (cellular, a personal hotspot) nor in Low Data Mode (Low Data
  Mode holds it on Wi-Fi too). A held download starts by itself when such a
  network appears, or at once when the policy goes back to `.anyNetwork`.
- While it waits, `NLDetectorModels.status(for:)` is `.notDownloaded` and
  `NLDetectorModels.statusReason(for:)` is `waiting_for_unmetered_network`
  (`NLDetectorPrefetchNetworkPolicy.waitingForUnmeteredNetworkReason`), not
  a failure. An explicit `NLDetectorModels.prefetch(_:)` ignores the policy,
  and a model already on the device is used on any network.

**Quality checks without a detector (option B).** While the detector is not
ready (downloading, waiting for an unmetered network, no credential, or
failed), the camera runs only the checks that need no detections: hold
steady / tap to focus, too dark, too bright, glare, backlight, a finger over
the lens, perspective skew, rotate the phone and the multi-bay overlap cues.
Point at a shelf, framing, shelf-row, price-tag and product-sharpness rules
stay off, and strict mode never refuses a photo for too few detections. The
tick after the downloaded model swaps in mid-session turns the full set on,
with no restart.

## 8. WebView Bridge Example

The same capture-range options are available through the native bridge models:

```swift
let config = NLNativeCaptureConfig(
    guidanceMode: .strict,
    showCloseButton: false,
    maxCaptures: 5,
    allowManualFinish: true,
    minCapturesBeforeDone: 1,
    showsCapturedCountLabel: false,
    cameraMode: .default
)

neurolabsSDK.openNativeCaptureUI(config: config, sessionId: sessionId)
```

Use `NLNativeCaptureOptions` with the same field names when the bridge payload is built from JS or other app code.

## 9. Multi-Bay Capture (Long Shelves)

Multi-bay capture handles shelves too long for a single photo: the user
side-steps along the shelf and captures one overlapping photo per bay,
the SDK guides the side-step, dedups the overlap on device, and reports
merged product counts across bays in a single session result.

Enable it by setting `NLCameraConfiguration.multiBay` (nil = feature off,
the default):

```swift
var config = NLCameraConfiguration()
config.multiBay = NLMultiBayOptions(
    minBays: 2,                   // minimum bays before the session can finish (default 1)
    maxBays: 4,                   // maximum bays per session (default 8; init clamps to 8)
    targetOverlapFraction: 0.30,  // fraction of the previous bay kept visible (default 0.30)
    minDetectionConfidence: 0.5,  // confidence floor for merge/count participation (default 0.5)
    onDeviceDedup: true,          // run overlap dedup at session finish (default true)
    generatePreview: true,        // compose the display-only stitched preview (default true)
    previewMaxDimension: 2048     // preview long-edge cap (default 2048, clamped 512...4096)
)

sdk.openCustomCameraUI(configuration: config, handlers: handlers)
```

**Long continuous AR sweeps (v1.7.16).** A continuous (shutter-free) sweep on
the AR camera commits a bay on every auto-capture, so it may plan up to
`NLMultiBayOptions.maxSupportedContinuousBays` (30). `init` still clamps to
`maxSupportedBays` (8); set `maxBays` after init. The capture screen clamps
it to `minBays...30` for `captureMode == .continuous` on the AR camera and to
8 otherwise, and logs a clamp. From v1.7.17 the bridge
(`NLNativeMultiBayConfig`, used by the WebView bridge and Cordova) resolves
`maxBays` the same way when the camera opens; in v1.7.16 it clamped to 8 on
every mode.

```swift
var options = NLMultiBayOptions(minBays: 2)
options.maxBays = 20 // after init; honoured only for a continuous AR sweep
config.cameraMode = .ar
config.captureMode = .continuous
config.multiBay = options
```

**"Review shelf" for long sweeps (v1.7.17).** Past 8 bays the AR flow's
review shows the shelf as pages of consecutive bays (9 → 5 + 4,
30 → 8 + 8 + 7 + 7), each stitched when the rep turns to it, with Previous /
Next and a swipe. Up to 8 bays nothing changes, and
`NLMultiBayResult.previewImageData` is still the one panorama. No API change.

**"On this shelf" (v1.7.17).** The same review lists the walk's facings by
brand, with each brand's share of the recognised products, and by SKU. A
facing counts as recognised at a match of 0.6 or more. It needs on-device
recognition (section 12) and a `productDetailsSource` for names and brands;
without recognition it shows the product total only. No API change.

On the WebView bridge the same options travel as
`NLNativeCaptureOptions.multiBay` (`NLNativeMultiBayConfig`): every field
is optional and absent fields take the `NLMultiBayOptions` defaults. The
field names are camelCase and identical across iOS, Android, and Cordova.

Reading merged results:
- Native session result: `NLCaptureSessionResult.multiBay`
  (`NLMultiBayResult?`, nil unless the session ran multi-bay) carries
  `bays: [NLBaySummary]`, `mergedProducts: [NLMergedProduct]`,
  `countsByLabel: [String: Int]`, the stitched preview
  (`previewImageData` / `previewImageFileUri`), and `dedupTrusted`.
- Use `NLMultiBayResult.productCount` for a product tally — it sums only
  `sku_single` + `sku_multipack`; `countsByLabel` also carries
  price/promo/poster buckets, so summing every label over-counts
  products.
- Bridge / SDK-managed flows: the `native_capture_result` payload carries
  `multiBay: NLNativeMultiBayResultSummary` with `countsByLabel`,
  `baysCount`, `dedupTrusted`, and `previewImageFileUri`. Preview bytes
  are intentionally not sent over the bridge; the file URI is present
  only when a stable spilled file exists.

Meaning of `dedupTrusted`:
- `true` — counts and `mergedProducts` are on-device deduped: each
  physical product instance is counted once across overlapping bays.
- `false` — an adjacent-pair alignment broke, the dedup timed out, or
  `onDeviceDedup` was disabled; counts are then the per-bay sum (an
  upper bound), not a deduped count.

Upload semantics:
- Each bay photo uploads as a normal capture through the operations
  queue (resumable mission flow, one image per capture).
- On `stopSession` the mission submit attaches a compact merge summary
  (`{bays, counts_by_label, dedup_trusted, sdk_version,
  ref_homographies}`) as structured `client_metadata.device_dedup` plus,
  transitionally, a `notes` duplicate for older backends — so the
  backend can re-dedup authoritatively.
- SDK-managed flows (`openNativeCaptureUI`, `openCustomCameraUI`,
  bridge-driven capture) record that summary automatically. Only hosts
  presenting their own custom capture UI must pass
  `NLMultiBayResult.submitNotesJSON()` to
  `setMultiBaySubmitNotes(_:forSession:)` before `stopSession(_:)`.

Config-only mode:
- There is no partner-facing in-camera mode toggle. The Single ↔
  Multi-bay capture-mode chip and sheet are internal demo/debug chrome
  gated behind `NLSDKDebug.internalCameraToolsEnabled` (default `false`;
  never enable it in partner builds). Partners control the mode purely
  via configuration: `multiBay` set = multi-bay session, `multiBay = nil`
  = single-bay session.
- The Neurolabs demo app enables that chrome only in local Debug builds;
  TestFlight/Release demo builds default to single-bay exactly like
  partner builds. The multi-bay feature itself is fully available in all
  builds via configuration — only the demo defaults changed.

## 10. Post-Processing Hooks
- `onSave` receives each approved capture.
- `onSaveAll` receives final batch in multi-capture mode.
- `onUploadRequested` exists but default queueing is done in `onSave` / `onSaveAll` path.

```swift
let handlers = NLCustomCameraHandlers(
    onSave: { capture in
        MyPostProcessor.shared.enqueue(capture)
        return .skipDefault
    }
)
```

### Photo deleted (experimental)

`onSave` / `onSaveAll` only ever see the final set. To hear about each photo
the rep deletes, set `NLCameraConfiguration.onCaptureDeleted`:

```swift
var config = NLCameraConfiguration()
config.onCaptureDeleted = { deletion in
    // deletion.captureId      the same id onCapture / onSave saw
    // deletion.remainingCount captures still in the session, pending + accepted
    // deletion.source         .review | .captureStrip | .bayPeek
    MyVisitLog.shared.photoDeleted(deletion.captureId, remaining: deletion.remainingCount)
}
```

- Fires exactly once per delete the rep makes, on the main actor, after the
  capture has left the session and its files are gone.
- `source` is `.review` for the review sheet and the final review grid, and
  `.captureStrip` for the per-tile delete on the capture strip. `.bayPeek` is
  reserved for the AR per-bay peek, which has no delete on iOS today.
- It does not fire for the SDK's own discards: a retake, a strict-quality
  reject, a capture your `onCapture` took with `.skipDefault`, the camera
  closing, or the upload queue removing a photo (including
  delete-on-upload-success).
- Nil, the default, sends nothing. It is a stored property, not an `init`
  parameter, so it is additive and ABI-safe. The Android SDK has the same
  contract under the same names.

## 11. Delegate/Event Callbacks

```swift
final class SDKDelegate: NeurolabsSDKDelegate {
    func neurolabsSDK(_ sdk: NeurolabsSDKCore, didEncounterError error: NLError, sessionId: String?, messageId: String?) {}
    func neurolabsSDK(_ sdk: NeurolabsSDKCore, didChangeQueueStatus status: NLQueueStatus) {}
    func neurolabsSDK(_ sdk: NeurolabsSDKCore, didUpdateLoadingProgress progress: NLLoadingProgress) {}
}

sdk.delegate = SDKDelegate()
```

`neurolabsSDK(_:didProduceCaptureResult:for:sessionId:)` is optional (it has
a default empty implementation). Since 1.7.13 `openNativeCaptureUI` calls it
once for every capture it saves, after trying to queue it:

- `success` is `true` when the capture was queued, and `message` is
  "Capture saved and queued for upload.".
- `success` is `false` when it could not be queued. `message` says why, and the
  same error also arrives on `didEncounterError`.
- `detections` are the capture's detections, whether or not they are uploaded
  (`sendDetectionsMetadata`). `capturedRegions` is empty.
- It arrives after `didEnqueue` for the same capture. A capture the queue
  already holds is not reported again.

The whole session's result still arrives once, at the end, on
`onSendNativeCaptureResult`. A camera you open yourself with
`openCustomCameraUI` reports through your own handlers, not this callback.

## 12. On-Device Recognition (v1.7.1)

Per-account, config-gated: your operations API key resolves YOUR org's
recognition config and vector dataset — enabling an account is a backend
flip, no app change. Every stage degrades gracefully; capture is never
blocked by recognition.

Source consumers (SwiftPM products `RecognitionBootstrap`,
`RecognitionEngine`, `RecognitionInterface`):

```swift
import RecognitionBootstrap
import RecognitionInterface

let bootstrap = NLRecognitionBootstrap(configuration: .init(
    operationsApiKey: "<your operations key>",
    sdkVersion: NLConstants.sdkVersion
))
// Wrap the components at the SDK boundary (see NLRecognitionProviderBox docs):
if let c = await bootstrap.build() {
    sdk.setRecognitionProvider(NLRecognitionProviderBox(
        isReady: c.isReady,
        recognize: { pb, dets, size in
            await c.recognize(pb, dets.map {
                NLProviderDetection(label: $0.label, score: $0.score, bbox: $0.bbox, id: $0.id)
            }, size)
        }
    ))
}
// bootstrap.status / onStatusChange → "provider: ready (N items)" etc.
```

**Short-lived session tokens.** When your bearer is a session token rather
than a fixed key, pass an auth provider and a stable identity instead:

```swift
extension MySessionTokens: NLRecognitionAuthProvider {} // token() + invalidate()

let bootstrap = NLRecognitionBootstrap(configuration: try .init(
    authProvider: sessionTokens,
    offlineIdentity: rep.id, // stable across tokens; never empty
    sdkVersion: NLConstants.sdkVersion
))
```

The bootstrap asks the provider for the bearer on every request. A 401 calls
`invalidate()` and retries once; a second 401 turns recognition off. The
offline record is named after a hash of `offlineIdentity`, so a cold start
with no token (the provider throws) still builds from the last sync. Use a
new bootstrap when the rep changes.

**Offline (stores with no signal).** Each build that completes online saves
the recognition config and the snapshot's signed manifest for your
credential. A later build that cannot reach the Operations API (offline,
timeout, DNS, captive portal, 5xx) builds from it for 7 days after the last
full sync (`NLRecognitionBootstrap.offlineCacheTTL`), if the cached embedder
and every shard pass their checks. `bootstrap.offlineSnapshotDate` is then
the sync time, and `bootstrap.statusSummary` reads
`provider: ready (offline, N items, snapshot from YYYY-MM-DD)`. A 401/403
still turns recognition off and deletes the cached build; a "disabled"
config stays off. Have the rep open the app online once a day so the 7 days
restart. A build that ended unavailable is retried by a later `build()`
(after 60 s, or 1 h for a definitive failure) and, after a network failure,
on reconnect; call `build()` again when `onStatusChange` reports `.ready`.
The cache lives in `Application Support/nl-catalog-snapshots` (excluded
from backup).

The embedder (the pinned DINOv3-ConvNeXt-tiny export, 768-d) is downloaded
by the SDK through `GET /v1/device-models` with your operations key, checked
against the sha256 pinned in source, compiled on the device and cached. Do
not bundle it: the SDK never scans the app bundle for a model (decision M5).
When the model can't be had (not entitled, offline, a failed download or
compile) the build is skipped as `embedder unavailable (<reason>)`.
`embedderModelURL` is the only local override, for air-gapped or bench
setups, and it must still be a 768-d ConvNeXt export.

Binary consumers: `RecognitionInterface` / `RecognitionEngine` /
`RecognitionEngineQdrant` ship as xcframeworks on neurolabs-mobile-dist
from v1.7.1; the bootstrap itself is source-only this release — wire the
chain per the `NLRecognitionProviderBox` documentation.

Tap-to-product-card: captures expose per-detection matches via
`sdk.recognitionMatches(forCapture:)`; drop the SDK's
`NLDetectionInspectorView(photo:title:detailsSource:)` onto your review
screen and feed it an `NLProductDetailsSource` wrapping ProductAuditKit's
`NLProductDetailsResolver` (one-liner on the source type's docs). Offline
or unresolved products fall back to a UUID + similarity row automatically.

## 13. AR Camera Options (v1.7.16)

All are stored properties on `NLCameraConfiguration`, set after `init`, with
the same keys on `NLNativeCaptureConfig` and `NLNativeCaptureOptions`
(resolved options, then config, then the default), except
`productDetailsSource` (see below). Every default keeps the earlier look.
Wire values decode leniently: "standard" is an alias of "quiet", an unknown
value reads as the default and a malformed colour draws the default colour.

```swift
var config = NLCameraConfiguration()
config.cameraMode = .ar
config.arBoxStyle = .highlight             // .quiet (default), .identity, .highlight
config.arBoxHighlightColor = "#22C55E"     // #RRGGBB, default #22C55E
config.arBoxUnmatchedColor = "#FACC15"     // #RRGGBB, default #FACC15
config.arCoverageStyle = .tintAndOutline   // .tint (default), .outline, .tintAndOutline
config.arCoverageOutlineColor = "#FACC15"  // #RRGGBB, default #FACC15
config.arBoxPersistence = .session         // .standard (default), .session
config.arLiveLabels = true                 // experimental, default false
config.arLiveCount = true                  // experimental, default false
config.productDetailsSource = detailsSource // names for arLiveLabels
```

- `arBoxStyle = .highlight` draws every world-locked box as a solid outline
  in `arBoxHighlightColor`, with no fill. `NLARBoxStyle` is non-frozen: an
  exhaustive `switch` over it needs `@unknown default`.
- With `arLiveLabels` on and a ready recognition provider, a highlight box
  that is stable, has been looked at, and has no product name latched on it
  (no match, or every look below 0.6) is drawn in `arBoxUnmatchedColor`
  instead. A box not looked at yet stays `arBoxHighlightColor`. With the
  labels off, every box keeps `arBoxHighlightColor`.
- `arCoverageStyle` shows the captured shelf as a tint, an outline on the
  fitted shelf plane in `arCoverageOutlineColor` around the captured bays, or
  both. With no plane fit yet every style shows the tint.
- `arBoxPersistence = .session` keeps every box that settled for the rest of
  the session as a dimmed outline (at most 300). `.standard` fades a box once
  tracking drops it. Presentation only: counts and coverage are unchanged.
- `arLiveLabels` draws the top-1 product name on each stable box, only at a
  match score of 0.6 or more. It needs a ready recognition provider
  (`setRecognitionProvider(_:)`, section 12) and `productDetailsSource` (an
  `NLProductDetailsSource`, the seam `NLDetectionInspectorView` takes) to turn
  catalog UUIDs into names. Without either there are no labels.
- `productDetailsSource` on `NLCameraConfiguration` reaches a camera you
  open with `openCustomCameraUI` or present as
  `NLCustomCameraViewController(configuration:)` (the camera-only path,
  section 7). `openNativeCaptureUI` builds its own configuration, so from
  v1.7.17 a bridge host sets `NeurolabsSDKCore.productDetailsSource` before
  opening the camera instead; a source on the configuration wins. It cannot
  travel in the bridge's JSON. Before v1.7.17 `arLiveLabels` showed no names
  through `openNativeCaptureUI`.
- `arLiveCount` shows a "~ N products" chip: the distinct stable boxes seen
  this session. It is an estimate; the review keeps the exact deduplicated
  count.

**12 MP AR stills.** The AR shutter (single, multi-bay, guided and
continuous) queues ARKit's full-resolution still
(`ARSession.captureHighResolutionFrame`, 12 MP on current iPhones) instead
of the ~1920x1440 video frame, while tracking keeps running. It goes through
the same image sizing (4032 px / JPEG 0.9 by default, section 7). No API
change.

- It falls back to the video frame when there is no running session
  (`no_session`), on an ARKit error (`capture_error`), with no still within
  1.5 s (`timeout`), for a still in the other orientation
  (`orientation_mismatch`), or for a still no larger than the video frame
  (`not_larger`). The reason goes to the device log only.
- Until ARKit returns the still, the shutter shows a spinner and is
  disabled, so a second tap does nothing and nothing is queued.

## 14. Notes
- Per-session routing is supported via native capture config task UUID overrides.
- Ensure `NSCameraUsageDescription` is present in app `Info.plist`.
