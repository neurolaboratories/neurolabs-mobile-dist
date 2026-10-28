# Neurolabs Android SDK - Integration Guide

## 1. Scope
This guide is for partner Android apps integrating `neurolabs-android-sdk` directly.

## 2. Release History

No public API contract has been broken since v1.1.9. New options have been
added with backwards-compatible defaults; integrations on v1.1.9 keep
working as is. Recommended defaults: strict shelf guidance with
`validationPreset = IOS_PARITY`, `liveQualityChecksEnabled = true`,
`autoCloseAfterCapture = true` for single-capture parity flows.

### v1.7.27
No `NLConfiguration` changes, no new APIs and no removals: `sdk.api` is
unchanged.

Behaviour changes, with no opt-in:
- A guided (shutter) multi-bay walk, and any multi-bay session on the default
  camera, may plan up to 20 bays: `NLMultiBayOptions.MAX_SUPPORTED_BAYS` is 20
  (it was 8), and `sanitized()` and the capture screen clamp `maxBays` to it.
  The default stays 8 bays. A host that asked for 9–20 bays and was clamped to
  8 now gets what it asked for (section 8). A continuous AR sweep keeps its
  30. `MAX_SUPPORTED_BAYS` is a `const val`: code that reads it sees 20 only
  once it is recompiled against v1.7.27.

### v1.7.26
No `NLConfiguration` changes and no removals. New APIs are additive: `sdk.api`
only gains lines. Nothing is required.

New, all optional:
- An `NLProductCaptureCameraHost` overload with `onCameraFailure` reports why
  the product-capture camera could not run: `NLProductCaptureCameraFailure`
  with a `reason` (`PERMISSION_DENIED`, `CAMERA_IN_USE`,
  `CAMERA_UNAVAILABLE`, `CONFIGURATION_INVALID`), a `message` and
  `retryable` (section 10, "Product-capture camera failures").
- `NLRecognitionBootstrap.Configuration.mirrorGate` holds a recognition
  snapshot until your catalogue mirror has reached it, and
  `NLRecognitionBootstrap.joinDegraded` says when one activated without it
  (section 11, "Catalogue-mirror gate").

Behaviour changes, with no opt-in:
- `stopSession` waits for the session's `enqueueCapture` calls already
  running, at most 5 s, before the KPI stop run and the mission submit
  (section 12, "Queue before you stop the session").
- A long-lived operations client binds the credential when it is built. Read
  `sdk.operationsClient` again after a key, auth-provider or base change: a
  client kept from before fails every request with a retryable
  `NLOperationsError.Transport` and sends nothing.
- The background product-capture retry sends only to the SDK's current
  operations base, under the credential it was scheduled with. With a catalog
  base other than the operations base, pending uploads wait for a foreground
  `retryPendingUploads`.
- The detector says what to do: the `insufficient_storage` chip says how much
  space to free, the AR walk shows one detector message at a time and waits at
  most once per process for a loading model, and a new credential clears an
  earlier failure's wait at once.

### v1.7.25
No `NLConfiguration` changes and no removals. New APIs are additive: `sdk.api`
only gains lines. Nothing is required.

New, all optional:
- `computeVisitKpis(sessionId, context, storeContext)` computes a finished
  session's visit KPIs from its id, for hosts that have only the id, such as
  Cordova. An id the SDK holds nothing for throws the new
  `VISIT_KPIS_SESSION_UNKNOWN` (section 12, "Visit KPIs by session id").
- `NeurolabsSDKCore.defaultProductNamesEnabled` (default `true`) lets the SDK
  name the AR live labels' products when the camera has no
  `productDetailsSource`. Experimental, and the live labels stay off by
  default (section 7).

Behaviour changes, with no opt-in:
- The AR live labels run the recognition provider, as on iOS, and stop while
  the organisation's on-device recognition switch is off (section 7).
- A crop forgets the recognition of the photo as shot, and a photo that had
  a pass is recognised again on the crop (section 11).
- `priceReadings(forCaptureId)[].pairedDetectionId` pairs with the same shelf
  geometry as K16 (section 12, "KPI rules").
- An operations retry never sends a rotated credential to the old host: a
  request whose base, key or auth provider changed after its first attempt
  is aborted. A queued upload aborted this way reports the new retryable
  code `UPLOAD_CREDENTIALS_CHANGED` and uploads under the new credential.

### v1.7.24
No `NLConfiguration` changes and no removals. New APIs are additive, and
`NLCameraConfiguration`, `NLNativeCaptureConfig`, `NLNativeCaptureOptions`,
`CaptureScreenConfig` and `NLNativeMultiBayResultSummary` keep their 1.7.23
constructor and `copy` as hidden overloads, so compiled hosts still link.
Nothing is required.

New, all optional:
- `multiBayCountSource` (`NLMultiBayCountSource.AGGREGATOR`, the default, or
  `AR_TRACKLETS`) picks which count an AR multi-bay result serves.
  Experimental (section 8).
- `arLiveKPIRings` (default off) shows three live KPI rings on the AR
  multi-bay camera. Experimental (section 7).
- `computeVisitKpis(..., storeContext = NLVisitKpiHostStoreContext(...))`
  computes visit KPIs on a store context you supply, never submitted
  (section 12).
- `NLInspectorMatchPolicy.boxName(match, product)` gives the name to draw on
  a box, only at or above the recognition floor (section 11).

Behaviour changes, with no opt-in:
- With your own capture UI, a visit that spans an app kill now counts every
  photo once you call `stopSession` after the relaunch (section 12).
- K16 price-tag coverage pairs tags by shelf geometry, so it no longer reads
  about 0 % on full-resolution photos, and `add_tag` actions fall (section
  12). The compliance KPIs K9-K11 and the actions N4/N5 are unchanged, now
  pinned to shared reference rows.
- AR long walks stay inside the track budget: facings out of view are
  archived, not dropped, and the AR counts read higher on long walks. The
  AR walk waits up to 45 s for the live detector, and a continuous preset
  runs continuous; reps see the Guided / Auto chooser once more after the
  update (section 7).
- The inspector names a box only at or above the recognition floor (0.5),
  and "On this shelf" says "No catalogue matches" when nothing matched
  (sections 8 and 11).

### v1.7.23
No public API changes: `sdk.api` is unchanged since v1.7.22.

If you embed the camera (`NLCustomCameraView`, or `NLCaptureActivity` opened
from an `NLCameraConfiguration`) and set no shelf type: an absent type is no
longer read as `SHELF`, as on iOS. With no `maxCaptures`, one photo now
completes the session (it was three), the strict "too similar" reject is
off, and the shelf overlay's distance, angle and panning cues are gone. Set
`shelfType = NLShelfType.SHELF` to keep the shelf behaviour (section 7).

Behaviour changes, with no opt-in:
- Snapshot manifests must be signed. The SDK pins the backend's snapshot
  keys (the staging key only on a Neurolabs staging operations host), and a
  manifest that is unsigned, signed by another key or altered fails to load,
  so recognition stays off for that build (section 11). Every live manifest
  has been signed since 18 Oct 2026, and older SDKs ignore the signature. A
  snapshot an older SDK cached for offline use is unsigned and is not used
  offline; the next online load replaces it. An `NLCatalogSnapshotLoader`
  built with the default verifier now refuses unsigned manifests.
- With your own capture UI (`NLCustomCameraView`, or photos you queue with
  `enqueueCapture`), `stopSession` computes the visit's KPIs once and
  `device_kpis` rides the submit under the usual rules. A visit that spans
  an app kill gets a partial count (section 12, "Visit KPIs"). Set the
  context on the session you stop.
- `quality.capture_verdicts` counts a capture as `warn` when its quality
  check judged it not acceptable or flagged a warning.
- Tapping a bay on "Review shelf", or a photo on the default camera's
  "Review", shows the photo's quality summary under it.
- The AR count v2 runs in shadow behind the internal `V2` fusion profile,
  which is off; `V1` is unchanged.

### v1.7.22
No `NLConfiguration` changes and no removals. New APIs are additive, and the
1.7.21 `NLCustomCameraView` / `NLCaptureScreen` signatures stay as hidden
overloads, so compiled hosts still link. One source change:
`NLCaptureDeletionSource` gains `RETAKE`, so a `when` over it with no `else`
branch must handle the new entry.

If your app keeps photos from `onCapture`:
- A retake now reaches `onCaptureDeleted` with source `RETAKE`: drop that
  photo. A crop reaches the new `onCaptureCropReplaced` (a trailing parameter
  on `NLCustomCameraView` and `NLCaptureScreen`, or
  `NeurolabsSDKCore.onCaptureCropReplaced` for `NLCaptureActivity`) with the
  cropped photo: swap your copy of `replacedCaptureId`. Both are experimental.
- A photo your app keeps and never enqueues is not recognised (that is iOS
  only). The suspend
  `NeurolabsSDKCore.recognizeCapture(captureId, imageData, detections)`
  recognises it without queueing it (section 11).

Recognition matches: the SDK recognises a capture where it is enqueued, which
on Android mostly comes after `onCaptureComplete`. Read them with
`sdk.recognitionMatches(forCaptureId)` once the capture is enqueued;
`CapturedImageData.recognitionMatches` on the delivered captures is filled
only for a capture recognised by then. The multi-bay realogram's
`product_id` (`NLCaptureActivity` rebuilds it after its save loop) and the
visit KPIs now carry the matches.

Behaviour changes, with no opt-in:
- "Face the shelf straight on" (the shelf-row yaw leg) fires above 12° and
  clears at 9° or less (was 8° and 5°). Every org's `config_hash` in
  `guidance_config_applied` changes with this release.
- With `uploadsEnabled = false`, a credential no longer fetches
  `GET /v1/config` for the queue or posts an owed mission submit.
- A commit recognises every detection whatever `sendDetectionsMetadata` says.
- A negative `NLDetectionOptions.maxDetections` keeps no detections, as on
  iOS, instead of throwing `IllegalArgumentException`.
- The AR live "~ N products" chip counts SKU facings only, and shutter
  presses during limited ARCore tracking are not fused. Served counts are
  unchanged.

New APIs: `NLCaptureCropReplacement`, `onCaptureCropReplaced` (camera
parameter and core), `NeurolabsSDKCore.recognizeCapture(...)`, and
`NLARSessionRecording` (experimental, armed process-wide with
`NLARSessionRecording.armed`).

### v1.7.21
No `NLConfiguration` changes. New APIs are additive. One breaking removal:
`NLOnnxYoloDetector`, `NLOnnxYoloConfig` and `ModelExportInstructions` are
gone. The ONNX detector was a stub that never returned a detection; if your
app called it directly, use the SDK's built-in detection instead.

Behaviour changes, with no opt-in:
- An embedded camera (`NLCustomCameraView`, `NLCaptureScreen`) that leaves
  the composition (a navigation push, a tab switch) pauses and resumes on
  return; its photos are kept. The session ends on close, Done, a new
  `sessionId` or the Activity finishing (section 7).
- A camera that cannot start reports `onError` with the new code
  `CAMERA_UNAVAILABLE`, once per session. It is not sent to Sentry.
- `CapturedImageData.validationResult` and
  `NLNativeCaptureResult.validationResult` carry the quality verdict (null
  when nothing validated the capture).
- Image quality reads luma as Rec.601, as on iOS: a saturated colour can get
  a different verdict than on 1.7.20. No threshold changed. With both
  overlays off and no preset the camera uses `LENIENT`, as iOS does, and
  `minDetectionCount` (`FRIDGE`, or a custom value) gates captures.
- The org's quality knobs, capture-image size and guidance disables follow
  the remote config during a session; a host's own values still win.
- Photos of an SDK capture session killed before Done are held and offered
  at the next SDK capture screen ("Unsaved photos", Save or Discard), not
  uploaded on their own.

New APIs (section 12):
- Store context: `prefetchStoreContext(outletIds)`,
  `storeContextStatus(outletId)`, `setStoreContextIdentity(identity)`,
  `clearStoreContextCache()`.
- Visit KPIs: `NeurolabsSDKDelegate.onVisitKpis(result, sessionId)` (default
  no-op), `setVisitKpisEnabled(enabled)` (on by default),
  `setVisitKpiContext(sessionId, context)`,
  `computeVisitKpis(sessionId, captures, multiBay, context)`.

### v1.3.2
- Mixpanel ingestion endpoint now resolves via `NLAnalyticsDefaults.MIXPANEL_ENDPOINT_EU`
  at SDK construction; events flow into the EU region project as expected.
  The standalone `MixpanelAnalyticsTracker` class keeps the US endpoint as
  its default so partners reusing it for their own US-region projects are
  unaffected.
- `CaptureViewModel.onFinishPressed` now claims `isFinishing` synchronously,
  wraps every disk read (pending review reload, capture reload, temp-file
  cleanup) in `withContext(Dispatchers.IO)`, and offloads `spillCaptureToDisk`
  from `commitCapture` — the Done button stays responsive throughout
  multi-capture sequences and shows an inline `CircularProgressIndicator`
  while persistence is in flight.
- Embedded custom-camera demo gained an in-app settings sheet (gear icon,
  top-right of the camera). Sliders for detection thresholds, capture min /
  max, live-quality FPS; switches for every boolean knob; SharedPreferences-backed
  persistence across launches.

### v1.3.1
- Fix for an uncatchable native `SIGSEGV` in
  `com.google.ai.edge.litert.Model.nativeLoadAsset` that triggered when the
  TFLite asset was stored compressed in the APK, missing, or zero length.
  `NLLiteRTYoloDetector` now probes the asset with `AssetManager.openFd`
  first and, on failure, extracts the asset to `noBackupFilesDir` and loads
  it via the file-path overload.

### v1.3.0
- Relaxed guidance thresholds (perspective skew floor raised, angle-off
  warning relaxed) for less aggressive blocking during normal in-store
  motion. Android lint passes restored.

### v1.2.8
- Onboarding flow: same-barcode relookup is allowed after a completed
  attempt so partners can retake without restarting the session.

### v1.2.7
- Lint compatibility fix for product capture; no API change.

### v1.2.6
- Onboarding: partner-overridable operations lookup client and capture
  debug exports (frame dump for offline review).
- Demo: scrollable launcher on small devices, nav-bar inset respected on
  the product-capture back button.

### v1.2.5
- `NLNativeCaptureConfig` / `NLCustomCameraView` expose
  `showsSequenceCounterLabel` to toggle the on-screen sequence counter.

### v1.2.4
- New capture range controls: `allowManualFinish`, `minCapturesBeforeDone`,
  and `maxCaptures` plumbed through `NLNativeCaptureConfig` for bounded
  multi-capture flows with a Done button.
- iOS-camera parity work: tap-to-focus, lens-switcher hardening, tightened
  quality validation thresholds.

### v1.2.3
- `NLNativeCaptureConfig.cameraMode = AR | DEFAULT` lets partners pick
  between the ARKit/ARCore pipeline and the AVFoundation/CameraX 0.5×/1×
  lens-switcher path.
- `init` accepts `analyticsEnabled`, `sentryEnabled`, `sentryDsn` so partner
  apps can opt out of telemetry or point Sentry at their own project.
- Default validation thresholds (blur, glare, perspective) tightened.

### v1.2.2
- Internal: Android plugin integration handling refactor; no public API
  change.

### v1.2.1
- iOS camera-style UI parity polish, lens-switcher state machine
  hardening, demo Sentry auto-init disabled.

### v1.2.0
- Internal scaffolding for v1.2.x: capture range controls landed in
  v1.2.4, lens switcher in v1.2.4–v1.2.5, missions policy preset, retry +
  idempotency conformance fixture.

### v1.1.9 (baseline)
- No public API contract break.
- Default task routing config uses `taskUUID`.
- Recommended custom-camera shelf payload remains strict shelf guidance
  with `validationPreset = IOS_PARITY`.
- `liveQualityChecksEnabled` remains the key switch for pill / rotation /
  warning / error guidance behavior.
- `autoCloseAfterCapture = true` remains the recommended parity flow for
  single accepted captures.

## 3. Requirements
- `minSdk 26`
- JDK 17
- Kotlin 2.x

## 4. Install

```kotlin
// app/build.gradle.kts
dependencies {
    implementation(files("libs/neurolabs-android-sdk-v1.1.x.aar"))
}
```

If you consume a local `.aar`, include required runtime deps (Compose/CameraX/serialization/etc.) or use the provided integration gradle script from the Cordova plugin setup.

## 5. SDK Initialization + Warmup

```kotlin
import ai.neurolabs.sdk.core.*
import kotlinx.coroutines.launch

class MainApp : Application() {
    override fun onCreate() {
        super.onCreate()

        val config = NLConfiguration.production(
            apiKey = BuildConfig.NL_API_KEY,
            taskUUID = BuildConfig.NL_TASK_UUID,
            debugLogging = BuildConfig.DEBUG
        )

        NeurolabsSDKCore.configure(this, config)
    }
}

// e.g. in first Activity/VM
val sdk = NeurolabsSDKCore.shared ?: return
lifecycleScope.launch {
    sdk.initialize()   // the SDK's one detector, all_in_one
    sdk.waitForFullyLoaded()
}
```

**The detector is downloaded, not bundled (1.7.13+).** The SDK ships no model, so it adds about 6.5 MB to your app. Its one detector, `all_in_one` (YOLO11l-Seg at 960 px, 12 classes: SKUs, `sinc` multipacks, prices, promos, posters, gaps, every row type and `shelf_strip`), comes from the Operations API, per org, with the operations key (or auth provider) you already configure: a signed URL, a sha256-verified, resumable, cached 55.6 MB download. The SDK prefetches it at start-up, when the credential changes and when a capture session opens. The old model names (`NLBModel.tflite`, `yolo11l_seg_sam.tflite`, …) and every `NLYoloModelVariant` now mean `all_in_one`.

**The first launch needs network for detection.** Until the model is on the device, capture works without a detector: the shutter, the queue and the light/glare/contrast checks work, `waitForFullyLoaded()` returns, `modelPreparationState` stays `LOADING`, detection throws the retryable `DETECTOR_UNAVAILABLE`, and the capture screen shows "Detector downloading. You can still capture." (no boxes, no "Point at a shelf", no AR anchors). When the model lands it is swapped in mid-session. `NLDetectorModels.status(context)` gives the state and, after a failure, the failure and its code in `reason`, the same codes as iOS: `no_credentials`, `not_entitled`, `unknown_model`, `pin_mismatch`, `sha_mismatch` (an hour before the API is asked again) and `api_unavailable`, `download_failed` (60 s; `compile_failed` is iOS-only), plus `insufficient_storage` (no wait: the next capture session or `prefetch` asks again) and `load_failed` (a fresh copy that still will not load; not retried until the next launch). New operations credentials clear the wait. With no operations credential and no model on the device, the SDK does not fetch on its own and the status stays `NOT_DOWNLOADED` until a credential is set (1.7.14). To have it before the first session (on Wi-Fi, after the operations credential is set):

```kotlin
lifecycleScope.launch { NLDetectorModels.prefetch(context) }
```

**Keep the SDK's own download off cellular (1.7.16+).** By default the SDK downloads the detector on any network. Set `NLDetectorModels.prefetchPolicy = NLDetectorPrefetchNetworkPolicy.UNMETERED_ONLY` before `NeurolabsSDKCore.configure(...)` and its own downloads (start-up, credential change, a waiting `initialize`, a capture session opening) wait for an unmetered network (Wi-Fi, Ethernet; a carrier's temporarily unmetered network only with Data Saver off) and start by themselves when one becomes the default network. Meanwhile `status` is `NOT_DOWNLOADED` with `reason` `waiting_for_unmetered_network`, and the camera runs without a detector ("Detector unavailable. You can still capture."). An explicit `NLDetectorModels.prefetch(context)` ignores the policy, so call it when you do want the cellular download (for example when the rep opens the camera with no detector yet).

Allow `api.operations.neurolabs.ai` and `storage.googleapis.com` in any egress allowlist. The detector reads its input size and class order from the model, and live frames are sized to it. It costs about 2.25× the pixels per frame of a 640-px model, so check the live frame rate on your lowest-end device first.

## 6. Queue Management

```kotlin
val sdk = NeurolabsSDKCore.shared ?: return

// runtime queue behavior
sdk.setAutoSyncEnabled(true)
sdk.setWifiOnlyUploadsEnabled(false)
sdk.setDeletePhotosOnUploadSuccess(true)
sdk.setMaxQueueSize(200)
sdk.setUploadRetryCount(5)

// lifecycle actions
lifecycleScope.launch {
    sdk.flushQueue()
    sdk.retryFailedUploads()
}

val status = sdk.getQueueStatus()
println("pending=${status.pendingCount} failed=${status.failedCount}")
```

`retryFailedUploads()` gives failed photos a fresh cycle, except a mission refusal that cannot succeed as sent (`wrong_status`, `submission_mismatch`, `mission_not_found`, `invalid_subsection_name`, `invalid_subsection_id`, or any `not_claimed_by_*`); `flushQueue(force = true)` and `retryQueuedItems(ids)` still revive those. Since 1.7.20 a call within 60 s of the previous one does nothing, so a retry button or timer cannot reset every backoff; the SDK reports the calls hourly (`queue_manual_retry`).

### Inspecting the queue at launch

After `configure()` the queue loads the records an earlier process left on disk in the background. Until that pass ends, `getQueuedItems()` can be empty or partial, and `removeQueuedItem(id)` or `clearUploadQueue()` can miss records that are still on disk. Before you inspect, withdraw or discard queued work at launch, wait for the pass:

```kotlin
import ai.neurolabs.sdk.core.awaitQueueHydrated

lifecycleScope.launch {
    sdk.awaitQueueHydrated() // the whole pass; returns at once once it has run
    sdk.getQueuedItems()
        .filter { it.sessionId == abandonedSessionId }
        .forEach { sdk.removeQueuedItem(it.id) }
}
```

- It returns once the whole pass has finished, also when the load failed (the queue then holds what it could read).
- A setter that rebuilds the queue (`setOperationsAuthApiKey`, `setOperationsBaseUrl`, `setMaxQueueSize`, `setUploadRetryCount`) starts a new pass; the call waits for the queue that is current when it returns.
- On an instance that was released (`release()`, or replaced by a `configure()` with a different configuration) it throws `IllegalStateException`. Call it on the instance `configure()` returned.

### Visits, owners and submits (1.7.15)

A host that tracks visits, or signs several users in on one device, can use these calls (see the 1.7.15 changelog entry for the full rules):

```kotlin
import ai.neurolabs.sdk.core.*

lifecycleScope.launch {
    // One queue per user and environment instead of per apiKey. Returns the new core;
    // set credentials on it. The previous owner's work stays on the device, untouched.
    val sdk = NeurolabsSDKCore.switchQueueOwner(context, config, "prod:$userId")

    // Asked once when a call is refused (409/403) because the mission's claim was lost.
    sdk.setOperationsReclaimHandler { missionId -> reclaimMission(missionId) }
    launch { sdk.submitEvents.collect { event -> /* NLSubmitEvent.Submitted / Abandoned */ } }

    sdk.openSession(sessionId)        // the orphan sweep never submits it on its own
    sdk.openOperationsSessions()      // at launch: stop or discard each open session
    sdk.queuedSessions()              // every session until its submit is confirmed
    sdk.owedSubmits()                 // submits the SDK still owes
    sdk.retryQueuedItems(listOf(id))  // retry chosen failed items only
    sdk.discardOperationsSession(sessionId) // or discardAllOperationsWork()
}
```

- Each queued photo carries `NLQueuedItem.missionId` (the session's mission, stamped at enqueue), `lastErrorCode` / `lastErrorMessage` and `bytesSent`.
- `clearUploadQueue()` drops queued items and notes and, since 1.7.20 (as on iOS), the uploaded-but-unsubmitted image ids with the submits still owed for them. It does not wait for uploads in flight; `discardAllOperationsWork` does (`discardOperationsSession` drops one visit).
- The embedded camera (`NLCustomCameraView`, `NLCaptureScreen`) takes `onCapture: ((CapturedImageData) -> Unit)?`, called once per photo as it joins the session; key copies by `captureId`.

### Kept photos and low storage (1.7.16)

Uploaded photos no longer take a `maxQueueSize` slot, in any mode. A host that keeps photos after upload (`setDeletePhotosOnUploadSuccess(false)`) or for a submit can bound them (see the 1.7.16 changelog entry for the full rules):

```kotlin
import ai.neurolabs.sdk.core.NLConfiguration

NLConfiguration.maxRetainedPhotos = 500        // default; a warning only, never refuses a capture
NLConfiguration.retainedPhotoExpiryDays = 14   // default null (off); photos kept for a submit never expire
```

- From 80% of `maxRetainedPhotos` the SDK calls `NeurolabsSDKDelegate.onRetainedPhotosHigh(retained, limit)` once per crossing. `NLQueueStatus.retainedCount` / `retainedBytes` report the kept photos.
- A new capture is refused with `NLCaptureErrorCodes.STORAGE_LOW` (retryable) when the queue's storage has under 500 MB free. It reaches the host through `onError` and the failed `onCaptureResult`, as `QUEUE_FULL` does.
- Since 1.7.20 the SDK's own camera asks the queue before it takes a photo: a photo that would be refused for `STORAGE_LOW` or `QUEUE_FULL` is not taken, the camera tells the rep why, and the host gets `onError` with no capture id (no failed `onCaptureResult`, since there is no photo).

### Uploads after the app is backgrounded

The queue's WorkManager drain keeps uploading while the app's process lives, also in the background. After the process is killed, uploads resume when the host next initialises the SDK (for most apps, the next open). iOS differs: a flush there gets iOS's background grace period (about 30 s), then resumes on the next foreground.

### What reaches the backend

What the operations upload carries:
- Per capture: the JPEG (the full frame, sized by `maxImageDimension` / `imageCompressionQuality`), with its task and bay (`subsection_name`).
- Per capture, after the JPEG uploads: its capture metadata (capture contract v1, `PUT .../images/{imageId}/capture-metadata`), for captures the SDK camera took: shutter time, SDK/device/OS, camera mode, photo size, an EXIF subset (no GPS, no serial numbers), device attitude, camera intrinsics and, on the AR camera, its pose. The detector's boxes only with `sendDetectionsMetadata`. Location only with `NLConfiguration.captureGeolocation` AND a location permission your app declares (`ACCESS_FINE_LOCATION` or `ACCESS_COARSE_LOCATION`) and holds; the SDK declares none and never asks. The ARCore depth map only with `NLConfiguration.captureDepth`. Both default off. It goes up from its own retrying outbox and never holds up the photo or the submit. Your app reads the same record on `NLNativeCaptureResult.captureMetadata`.
- Per session: the mission submit's `client_metadata.device_dedup` summary for a multi-bay session (section 8).

What stays on the device:
- The capture's detections always reach your app (`CapturedImageData.detections`, `onCapture`, the capture result); `sendDetectionsMetadata` decides only whether they are kept in the queue record and uploaded with the capture metadata.
- `enablePreviewCropping` trims only the review thumbnail, to the area the detections cover. The uploaded photo is always the full frame, as on iOS. Up to 1.7.17 Android uploaded the trimmed photo.
- AR session recordings (`.nlrec`, the AR component's recording API) are tooling for replay and calibration. They are not a capture output and are never uploaded.

## 7. Open Custom Camera (Native Capture UI)

```kotlin
import ai.neurolabs.sdk.models.*
import ai.neurolabs.sdk.ui.openNativeCaptureUI

val sessionId = UUID.randomUUID().toString()

val config = NLNativeCaptureConfig(
    guidanceMode = NLCaptureGuidanceMode.STRICT,
    validationPreset = NLValidationPreset.IOS_PARITY,
    confidenceThreshold = 0.25f,
    iouThreshold = 0.45f,
    maxCaptures = 5,
    allowManualFinish = true,
    minCapturesBeforeDone = 2,
    showsCapturedCountLabel = false,
    showAlignmentGuidance = true,
    enableValidation = true,
    autoCloseAfterCapture = true,
    showDetections = false,
    showCapturedRegions = false,
    liveQualityChecksEnabled = true,
    liveQualityTargetFps = 6
)

val options = NLNativeCaptureOptions(
    type = NLShelfType.SHELF,
    taskUUID = "<TASK_UUID_FOR_THIS_SESSION>",
    sendDetectionsMetadata = true,
    enablePreviewCropping = true,
    maxImageDimension = 1920,
    imageCompressionQuality = 0.85f
)

sdk.openNativeCaptureUI(
    context = this,
    sessionId = sessionId,
    config = config,
    options = options
)
```

Recommended capture payload notes:
- `liveQualityChecksEnabled = true` is the key for pill/rotation/warning/error guidance behavior.
- Keep `type = NLShelfType.SHELF` and `guidanceMode = NLCaptureGuidanceMode.STRICT` for full shelf guidance checks.
- Keep `showDetections = false` and `showCapturedRegions = false` to stay on the custom-camera guidance UI path.
- `guidanceMode = NLCaptureGuidanceMode.GUIDANCE` should only be used as a temporary fallback if a partner specifically needs looser Android behavior while a strict-guidance regression is being fixed.

### End-of-session review (1.7.16)

`finalReview = true` (on `NLNativeCaptureConfig` or `NLNativeCaptureOptions`, options first; or `NLCameraConfiguration.finalReview`) gives the default (non-AR) camera without a multi-bay plan one review at the end instead of a per-shot preview:

- Done, or the count where the session would end today (`maxCaptures`, the auto-close target, or the required count), opens "Review". A tap on a photo opens it with Crop, Delete and Previous / Next. Delete fires `onCaptureDeleted` with source `REVIEW`.
- Nothing is queued or uploaded before Confirm. The photos are staged on disk, so they survive the process being killed. Confirm queues the remaining photos in capture order, crops applied.
- Default `false`: every other session, and every host that does not set it, is unchanged.

### Embedded camera: shelf type (1.7.23)

`NLCustomCameraView`, and `NLCaptureActivity` opened from an
`NLCameraConfiguration`, keep an absent `shelfType` absent, as iOS does: with
no `maxCaptures` one photo completes the session, the strict "too similar"
reject is off, and the shelf overlay's distance, angle and panning cues do not
run ("Point at a shelf" still does). Set `shelfType = NLShelfType.SHELF` for
the shelf behaviour. `NLCaptureActivity` opened with an `NLNativeCaptureConfig`
still reads an absent type as a shelf.

### Embedded camera: who owns the photo files (1.7.19)

`NLCaptureActivity` / `openNativeCaptureUI` queue the photos themselves; nothing below applies to them. When you embed the camera (`NLCustomCameraView`, `NLCaptureScreen`), `onCaptureComplete` hands the session's photos to you:

- Each `CapturedImageData.imageFilePath` stays on disk after the camera leaves the composition. Read it, show it, or pass its bytes to `enqueueCapture` (which copies them into the upload queue) whenever you are ready, including after you have closed the camera.
- The files are yours from then on. Release them once you are done: `sdk.acknowledgeCaptures(sessionId)` for the whole session, or `sdk.releaseCapture(captureId)` one by one.
- Files you never release are deleted at the next SDK start or capture session once they are 24 hours old, so disk cannot leak.
- Photos the session discarded before `onCaptureComplete` (a retake, a deletion, ✕ before Done) are never delivered; the SDK deletes them.

```kotlin
NLCustomCameraView(
    sdk = sdk,
    sessionId = sessionId,
    onClose = { showCamera = false },
    onCaptureComplete = { captures ->
        showCamera = false                       // closing first is safe
        scope.launch(Dispatchers.IO) {
            captures.forEach { capture ->
                sdk.enqueueCapture(sessionId, capture.captureId, capture.resolveImageData(), capture.detections, NLCaptureContext())
            }
            sdk.acknowledgeCaptures(sessionId)   // done with the files
        }
    },
)
```

Before 1.7.19 the camera deleted these files when it left the composition, so a host that enqueued or read them after closing it lost the photos without an error.

### Embedded camera lifecycle (1.7.21)

- Leaving the composition (a navigation push, a tab switch) pauses the embedded camera: the camera closes and the session's photos stay. Coming back reopens the camera and the live checks. The session ends on close, Done, a new `sessionId`, or the Activity finishing.
- A configuration change (dark mode, font scale, multi-window, a fold) rebinds the camera to the recreated Activity, so the preview stays live.
- A camera that cannot start raises `onError` with `NLCaptureErrorCodes.CAMERA_UNAVAILABLE` once per session and tells the rep "The camera could not start. Another app may be using it."
- `CapturedImageData.validationResult` (`isAcceptable`, `overallScore`, `issues`) carries the quality verdict; null when nothing validated the capture. A strict failure never reaches `onCapture`.
- The SDK unbinds only its own CameraX use cases, so a camera your app runs (a barcode scanner, say) keeps running.

### Offline chip (1.7.17)

The default and AR camera show a small chip while the upload queue sees no network: "Offline · uploads queued" (or "Offline" with nothing queued), and "Waiting for Wi-Fi · uploads queued" while Wi-Fi-only uploads hold photos on a metered network. It hides while the network is unknown and when the host uploads the photos itself (`uploadsEnabled = false`). It is informational only and never gates the shutter. On by default; turn it off with `NLCameraConfiguration(showsOfflineIndicator = false)`, or on the bridge with `showsOfflineIndicator` (`Boolean?`) on `NLNativeCaptureOptions` / `NLNativeCaptureConfig` (options, then config, then `true`).

### AR boxes the live labels have not matched (1.7.17)

Under `arBoxStyle = NLARBoxStyle.HIGHLIGHT`, with `arLiveLabels` on and a ready recognition provider, a stable box that has been looked at and has no product name latched on it (no match, or every look below 0.6) is drawn in `arBoxUnmatchedColor` (`#RRGGBB`, default `#FACC15`) instead of `arBoxHighlightColor`. A box not looked at yet keeps the highlight colour. The key is on `NLCameraConfiguration` and, as `String?`, on `NLNativeCaptureConfig` / `NLNativeCaptureOptions` (options, then config, then the default). Nothing changes while `arLiveLabels` is off.

With recognition off there are no product names or unmatched colour, and a box is told apart from its neighbours by its position, not by which product it is: two identical facings that touch can be harder to keep apart. From 1.7.18 appearance helps there; see the next subsection.

### AR box identity with recognition off (1.7.18)

With on-device recognition off, the AR overlay tells touching boxes apart by appearance as well as position. `CaptureScreenConfig.arAppearanceWithoutRecognition` (default `true`; `Boolean?` of the same name on `NLNativeCaptureConfig` / `NLNativeCaptureOptions`, options, then config, then `true`) uses the same ConvNeXt model as recognition, downloaded for appearance only through `GET /v1/device-models` for an org Operations grants it to (on-device recognition on, or the org's `ar_appearance_embedder` flag), and a colour histogram until the model is on the device, if it cannot be fetched, or for any other org. `NLDetectorModels.prefetchPolicy` applies to the download. Only the AR camera starts it; the default camera never does.

### Full-resolution AR stills (1.7.18, experimental)

`arHighResolutionStills = true` (on `CaptureScreenConfig` and `NLCameraConfiguration`; `Boolean?` on the bridge types, then `false`) takes each AR photo as a JPEG still of up to 4032 px through ARCore's Shared Camera, beside tracking, instead of ARCore's CPU image (about 2.1 MP). The org's `sdkCapture.arHighResolutionStills = false` vetoes it. It needs API 29+ and a Shared Camera session the phone accepts; anything else, and any failure at capture time, keeps the CPU image for that photo, so a capture never fails because of it. Two failed stills in a row switch it off for the session. Off by default until the device spike passes.

Names for the live labels come from `NLCameraConfiguration.productDetailsSource` (an `NLProductDetailsResolver`). It is in-process only, never in the bridge's JSON: it reaches `NLCustomCameraView(cameraConfiguration = …)` and `NLCaptureActivity.open` / `createIntent(context, sessionId, cameraConfiguration)`. (iOS sets the same source on `NeurolabsSDKCore.productDetailsSource` for `openNativeCaptureUI`.)

### Live labels: the recognition provider and default names (1.7.25, experimental)

`arLiveLabels` stays off by default and experimental.

- **Which provider labels.** The live labels run the SDK's recognition provider (the one `NLRecognitionBootstrap.start` installs, or yours from `setRecognitionProvider`), and stop while the organisation's on-device recognition switch is off. They never use the AR appearance fallback (the colour histogram or the appearance-only embedder), which cannot name a product. So with no recognition provider there are no labels and no box turns `arBoxUnmatchedColor`. A provider that recognises but cannot embed still labels. This is iOS's rule; before 1.7.25 Android ran the labels on the appearance provider.
- **Names without a `productDetailsSource`.** When the camera configuration has no `productDetailsSource`, the SDK names the matched catalog UUIDs itself, for the live labels and "On this shelf":
  - It asks `GET /v1/catalog-items?canonical_uuids=` on the operations host, at most 100 UUIDs a request, with the SDK's own operations credential (the API key, or your `setOperationsAuthProvider` bearer). The request never leaves the operations origin; a redirect to another host drops the credential.
  - It keeps the names on the device: names only (no brand, image URL or barcode), in `noBackupFilesDir/nl-product-names/`, one file per organisation credential, named by a salted hash of the operations host and the API key (or, with an auth provider, the identity you pass to `setStoreContextIdentity`). With an auth provider and no identity, names stay in memory for that credential only.
  - A name is used for 7 days, then asked again. Offline, the last known name is used for up to 30 days. A product with no name shows no label text; the SDK never guesses. At most 5,000 names a credential, least recently used first out.
  - "On this shelf" gets names only from this source; brands read "Unknown brand" unless your own source supplies them.
- **Your source wins.** A `productDetailsSource` you set is always used instead. To turn the default off (no requests, nothing kept), set `sdk.defaultProductNamesEnabled = false` before opening the camera (it is read when the camera opens) (Java: `NLDefaultProductNamesKt.setDefaultProductNamesEnabled(sdk, false)`). iOS: `NeurolabsSDKCore.defaultProductNamesEnabled`.

### AR walks: detector, track budget and the mode chooser (1.7.24)

- **The walk waits for the detector.** On an AR multi-bay session with live
  detection, capture (auto and manual) is held under "Getting ready...
  Loading the product detector" until the live detector has loaded, for 45 s
  at most. After that, or at once when the detector cannot load, the walk
  goes on with "Detector unavailable. You can still capture."
- **Long walks stay inside the track budget.** A settled facing whose whole
  footprint is out of view is archived, not kept live, and comes back under
  its old id when the camera returns. Price tags, promos and posters get at
  most 64 of the 256 live tracks. Archived facings still count: under `V1`
  the finish counts them next to the live anchors, so `ar_anchor_counts`
  reads higher on long walks than in 1.7.23. The live "~ N products" chip
  reads higher too, because births are no longer refused and more facings
  turn solid. A facing seen square on turns solid after one press.
- **A continuous preset runs continuous.** A Guided / Auto pick from the
  chooser applies only while the host asks for the capture mode it was made
  under. A pick stored by an earlier version applies to nothing, so reps see
  the chooser once more after the update.
- No API change.

### Live KPI rings (1.7.24, experimental)

`arLiveKPIRings = true` (on `NLCameraConfiguration` and `CaptureScreenConfig`;
`Boolean?` on `NLNativeCaptureConfig` / `NLNativeCaptureOptions`, options,
then config, then `false`) shows three small rings under the AR multi-bay
camera's status chip: the SKU facings counted so far, filled by the share that
has settled; the gaps seen in the captured bays; and price tags per facing, as
a percentage. They are estimates from what the overlay already tracks, at
about 2 Hz; no KPI engine runs while capturing. They hide while the guidance
dock is amber or red and during a review, and TalkBack reads them as one
element.

## 8. Multi-Bay Capture (Long Shelves)

Multi-bay capture handles shelves too long for a single photo: the user side-steps along the shelf and captures one overlapping photo per bay, the SDK guides the side-step, dedups the overlap on device, and reports merged product counts across bays in a single session result.

Enable it by setting `multiBay` on the capture config (`null` = feature off, the default):

```kotlin
import ai.neurolabs.sdk.models.*
import ai.neurolabs.sdk.multibay.NLMultiBayOptions
import ai.neurolabs.sdk.ui.openNativeCaptureUI

val config = NLNativeCaptureConfig(
    guidanceMode = NLCaptureGuidanceMode.STRICT,
    multiBay = NLMultiBayOptions(
        minBays = 2,                   // minimum bays before the session can finish (default 1)
        maxBays = 4,                   // maximum bays per session (default 8; cap 20, or 30 for a continuous AR sweep)
        targetOverlapFraction = 0.30,  // fraction of the previous bay kept visible (default 0.30)
        minDetectionConfidence = 0.5,  // confidence floor for merge/count participation (default 0.5)
        onDeviceDedup = true,          // run overlap dedup at session finish (default true)
        generatePreview = true,        // compose the display-only stitched preview (default true)
        previewMaxDimension = 2048     // preview long-edge cap (default 2048, clamped 512..4096)
    )
)

sdk.openNativeCaptureUI(
    context = this,
    sessionId = sessionId,
    config = config
)
```

The same `multiBay` field exists on `NLCameraConfiguration` for the custom-camera config path, and on the WebView/Cordova bridge payload (camelCase field names identical across iOS, Android, and Cordova; absent fields take the defaults above).

The bay cap depends on the session's mode: a continuous sweep (`captureMode = NLCaptureMode.CONTINUOUS`) on the AR camera may plan up to `NLMultiBayOptions.MAX_SUPPORTED_CONTINUOUS_BAYS` (30) bays; every other session (a guided walk, any session on the default camera), and a continuous sweep that falls back to CameraX, may plan up to `NLMultiBayOptions.MAX_SUPPORTED_BAYS` (20 from v1.7.27; 8 before). A value outside the cap is clamped and logged when the camera opens. From v1.7.17 the WebView bridge resolves `maxBays` the same way; in v1.7.16 it clamped to 8 on every mode. Cordova's `NLCaptureActivity` launch already followed the mode in v1.7.16.

**Long guided walks (v1.7.27).** A guided (shutter) walk, and any session on the default camera, may plan up to `NLMultiBayOptions.MAX_SUPPORTED_BAYS` (20; 8 before v1.7.27); the default stays 8. A 10 m shelf is about 10–14 bays. The cost of a long walk does not grow with the ceiling: past 8 bays the finish-time dedup decodes each bay smaller so its working set stays at the 8-bay budget, and the AR "Review shelf" pages through segments of up to 8 bays (20 → 7 + 7 + 6), as for a long continuous sweep. `previewImageData` is still the one panorama, so past 8 bays treat it as a thumbnail (about 205 px a bay at 20). The bridge resolves the same 20. Hosts that asked for 9–20 bays on a guided or default-camera session were clamped to 8 and now get that many: check your plan if you relied on the clamp. `MAX_SUPPORTED_BAYS` is a `const val`, inlined where you read it: recompile against v1.7.27 to see 20.

```kotlin
val options = NLMultiBayOptions(minBays = 2, maxBays = 20) // guided: up to 20
```

### "Review shelf" for long sweeps and "On this shelf" (1.7.17)

- Past 8 bays the AR flow's review shows the shelf as pages of consecutive bays (9 → 5 + 4, 30 → 8 + 8 + 7 + 7), each stitched when the rep turns to it, with Previous / Next and a swipe. Up to 8 bays nothing changes, and `NLMultiBayResult.previewImageData` is still the one panorama.
- The same review lists the walk's facings by brand, with each brand's share of the recognised products, and by SKU. A facing counts as recognised at a match of 0.6 or more. It needs on-device recognition (section 11). Names come from your `productDetailsSource`, else from the SDK's default names (1.7.25, names only, so brands read "Unknown brand"); without recognition it shows the product total only.
- No API change.

Reading merged results:
- Activity Result / bridge: `NLNativeCaptureResultPayload.multiBay` (`NLNativeMultiBayResultSummary?`, null unless the session ran multi-bay) carries `countsByLabel: Map<String, Int>`, `baysCount`, `dedupTrusted`, and `previewImageFileUri`. It also carries the optional `realogram` (`NLStitchedRealogram` with camelCase keys: `version`, `coordinateSpace`, `sdkVersion`, `bays`, `shelves[{shelfIndex, rows[{rowIndex, slots[{slotIndex, xMin, yMin, xMax, yMax, bayIndex, detectorClass, trackId, productId, stackIndex, score}]}]}]`, `truncated`, `omittedProductCount`) and `segments` (`[{fromBay, toBay, trusted, countsByLabel}]`), each left out when the SDK built none. The realogram never crosses Binder: the WebView bridge carries it inline, while the Activity result carries `realogramFileUri` instead, a `file://` URI to `<cacheDir>/neurolabs/realogram-<sessionId>.json` holding the same JSON. Read it, then delete it; the SDK deletes any left older than 24 h at init.
- Bridge: `arAppearanceWithoutRecognition` (`Boolean?`) on `NLNativeCaptureOptions` / `NLNativeCaptureConfig` resolves options, then config, then `true`, into `CaptureScreenConfig.arAppearanceWithoutRecognition`. `arHighResolutionStills` (`Boolean?`) resolves the same way, then `false`.
- Compose: `NLCaptureScreen` / `NLCustomCameraView` accept an `onMultiBayResult: ((NLMultiBayResult) -> Unit)?` callback delivering the full result — `bays: List<NLBaySummary>`, `mergedProducts: List<NLMergedProduct>` (one entry per physical product instance after cross-bay dedup), `countsByLabel`, the stitched preview (`previewImageData`), and `dedupTrusted`.
- Use `NLMultiBayResult.productCount` for a product tally — it sums only `sku_single` + `sku_multipack`; `countsByLabel` also carries price/promo/poster buckets, so summing every label over-counts products.
- `countsByLabel` (`counts_by_label` on the wire) is keyed by detector class (`sku_single`, `sku_multipack`, price tag, promo, poster), not by product or SKU. Shelf, row and slot positions are in `NLMultiBayResult.realogram` (`NLStitchedRealogram`).

Meaning of `dedupTrusted`:
- `true` — counts and `mergedProducts` are on-device deduped: each physical product instance is counted once across overlapping bays.
- `false` — an adjacent-pair alignment broke, the dedup timed out, or `onDeviceDedup` was disabled; counts are then the per-bay sum (an upper bound), not a deduped count.

### Segments and the stitched realogram (1.7.18)

- A broken link between two adjacent bays no longer leaves every later bay unmerged: it starts a new segment, and the dedup runs inside each run of linked bays. `NLMultiBayResult.segments` (`NLDedupSegment`: `fromBay`, `toBay`, `trusted`, `countsByLabel`) lists them. `dedupTrusted` is still true only for one trusted segment. When every segment is trusted and they tile the walk, the submit sends `client_metadata.device_dedup` v2 (`version: 2`, `segments`); otherwise v1. "Review shelf" marks each broken link.
- `NLMultiBayResult.realogram` (`NLStitchedRealogram`) groups the walk's merged products into shelves, rows and slots in the first bay's frame, by geometry alone, so it exists with recognition off. SDK-managed flows send it as the mission submit's top-level `realogram`; a custom capture UI's `submitNotesJSON()` never carries it. Older backends ignore it.

### Registration, retakes and the shelf's bay order (1.7.19)

- Adjacent bays register with a full homography (rotation, scale and perspective), as on iOS, so a rep who turns, steps in or tilts between bays keeps the link. `ref_homographies` keep their shape. Registration has a 1.5 s share of the merge's 4 s timeout: on a slow phone a long walk breaks its last links instead of losing the whole merge, and "Review shelf" marks such a break "Bay N not linked — split here to keep up".
- A link that broke because the photos did not register is marked "Couldn't link bay N — retake it to join", with "Retake bay N". The camera opens with a "Retaking bay N" banner; the next photo replaces bay N in place (same bay index) and the review merges again. A retake is offered only while the session still holds the bay: a bay already handed to the upload queue cannot be replaced.
- A walk that folds back across a broken link (the next bay revisits an earlier one, within 0.75 m by AR position) is registered to that earlier bay, so its products count once. CameraX walks, which have no AR positions, make no attempt.
- A split walk's `device_dedup` v2 also sends `seams` (one per break, with the device's bound on products counted on both sides) and, with them, `links`. Every multi-bay submit whose bays have their spatial inputs sends `bay_order`, v1 or v2 (the bays left to right on the shelf; bay indexes everywhere else keep their capture order). The bays reach the merge and the submit in capture order (before 1.7.19, parallel commits could shuffle them).

Upload semantics:
- Each bay photo uploads as a normal capture through the operations queue (resumable mission flow, one image per capture).
- On `stopSession` the mission submit attaches a compact merge summary (`{bays, counts_by_label, dedup_trusted, ref_homographies, sdk_version}`) as structured `client_metadata.device_dedup` plus, transitionally, a `notes` duplicate for older backends. The backend stores the summary and serves `counts_by_label` only when `dedup_trusted` is true. It does not re-dedup from `ref_homographies` today.
- SDK-managed capture flows record that summary automatically. Only hosts presenting their own custom capture UI must pass `NLMultiBayResult.submitNotesJSON()` to `sdk.setMultiBaySubmitNotes(notes, sessionId)` before `stopSession`.

Config-only mode:
- There is no partner-facing in-camera mode toggle. The Single ↔ Multi-bay capture-mode chip and sheet are internal demo/debug chrome gated behind `NLSDKDebug.internalCameraToolsEnabled` (default `false`; never enable it in partner builds). Partners control the mode purely via configuration: `multiBay` set = multi-bay session, `multiBay = null` = single-bay session — programmatic `multiBay` configuration is unaffected by the gate.
- The Neurolabs demo app enables that chrome only in local debug builds; Firebase/release demo builds default to single-bay exactly like partner builds. The multi-bay feature itself is fully available in all builds via configuration — only the demo defaults changed.

### Count source and "On this shelf" (1.7.24)

- `multiBayCountSource` (experimental; on `NLCameraConfiguration` and
  `CaptureScreenConfig`, and as a nullable field on `NLNativeCaptureConfig` /
  `NLNativeCaptureOptions`, options, then config, then `AGGREGATOR`) picks the
  count an AR multi-bay result serves. `AGGREGATOR`, the default, changes
  nothing. `AR_TRACKLETS` on the AR camera serves the AR tracklet count:
  `countsByLabel`, `productCount` and the new `perBayCountsByLabel` hold every
  facing counted once by world identity. The aggregator always runs:
  `NLMultiBayResult.aggregatorCountsByLabel` / `aggregatorProductCount` hold
  its counts, and `countSource` says which served. The result falls back to
  the aggregator when there is no AR count, or when the AR count has no SKU
  facing and the aggregator has some.
- The submit keeps the aggregator's `counts_by_label` in both modes. Under
  `AR_TRACKLETS`, `ar_anchor_counts` adds `count_source: "ar_tracklets"`, and
  `NLNativeMultiBayResultSummary` adds `countSource` and
  `aggregatorCountsByLabel`. On the bridge an unknown value reads as absent
  (wire names `aggregator`, `ar_tracklets`).
- When recognition ran and matched no facing at or above the floor, "On this
  shelf" ends with "No catalogue matches", "0 of N facings recognised" and "The
  catalogue may not cover the products in this store." While the merge still
  counts, it says "Counting products...".

## 9. Post-Processing Hooks
Use Activity Result API and process captures when camera returns.

```kotlin
private val captureLauncher = registerForActivityResult(
    NLCaptureActivity.Contract()
) { result ->
    when (result) {
        is NLCaptureActivityResult.Success -> {
            // capture metadata is in result.payload
            val count = result.payload.captures.size
            Log.d("NLB", "camera returned with $count captures")
        }
        is NLCaptureActivityResult.Cancelled -> {
            Log.d("NLB", "camera cancelled")
        }
        is NLCaptureActivityResult.Error -> {
            Log.e("NLB", "camera error: ${result.error.message}")
        }
    }
}
```

## 10. Delegate/Event Callbacks

```kotlin
sdk.delegate = object : NeurolabsSDKDelegate {
    override fun onCaptureResult(result: NLNativeCaptureResult, captureId: String, sessionId: String) {}
    override fun onError(error: NLError, sessionId: String?, messageId: String?) {}
    override fun onQueueStatusChange(status: NLQueueStatus) {}
    override fun onLoadingProgress(progress: NLLoadingProgress) {}
    override fun onQueueItemEnqueued(item: NLQueuedItem) {}
    override fun onUploadSucceeded(item: NLQueuedItem) {}
    override fun onUploadFailed(item: NLQueuedItem, error: NLError) {}
}
```

### Product-capture camera failures (1.7.26)

`NLProductCaptureCameraHost` has an overload with `onCameraFailure`. Use it to learn why the camera could not run, instead of showing a black card. The overload without it keeps its signature and runs the same checks with a no-op callback: it does not bind without the `CAMERA` permission, and it binds when the permission is granted later.

```kotlin
var hostKey by remember { mutableIntStateOf(0) }
var failure by remember { mutableStateOf<NLProductCaptureCameraFailure?>(null) }

key(hostKey) {
    NLProductCaptureCameraHost(
        scanningEnabled = true,
        videoModeActive = false,
        videoConfig = NLProductCaptureVideoConfig(),
        onVideoProgress = { _, _ -> },
        onVideoReady = { _, _, _, _, _ -> },
        onVideoError = {},
        onCameraFailure = { failure = it },
        onBarcodeScanned = { scan -> /* ... */ },
    )
}

failure?.let { current ->
    // Show your own copy by current.reason.
    if (current.retryable) {
        Button(onClick = { failure = null; hostKey++ }) { Text("Try again") }
    }
}
```

| `reason` | When | `retryable` |
|---|---|---|
| `PERMISSION_DENIED` | No `CAMERA` permission (the SDK does not bind without it; ask for it first), or a device policy disables the camera. | no: send the user to Settings |
| `CAMERA_IN_USE` | Another app holds the camera, or too many cameras are open, and the camera has not opened within 10 s while CameraX retried. | yes |
| `CAMERA_UNAVAILABLE` | No back camera, or the camera hardware or session failed. | yes |
| `CONFIGURATION_INVALID` | CameraX refused the setup: the lifecycle had ended, your own CameraX use cases or `CameraXConfig` conflict with the SDK's, or the device cannot stream the combination. | no: fix the integration |

- The callback runs on the main thread. Each reason is reported once until the camera opens again.
- A busy camera (`CAMERA_IN_USE`, or another error CameraX retries) is reported only if the camera has not opened within 10 s. Any other error is reported at once.
- Ask for the `CAMERA` permission yourself. Without it the SDK does not bind and reports `PERMISSION_DENIED`; once the permission is granted and the activity resumes, it binds.
- `NLProductCaptureFlow` puts the failure's `message` in its state's `message`.
- To try again, recreate the host (a new `key`). Leaving composition unbinds exactly what that host bound.
- `message` is fixed English copy for logs. It never carries an exception's text.
- None of these failures is sent to the SDK's Sentry project: each is a device, user or integration condition.
- A recording that fails still reports through `onVideoError` only.

## 11. On-Device Recognition (v1.7.1)

Per-account, config-gated: your operations API key resolves YOUR org's
recognition config and vector dataset — enabling an account is a backend
flip, no app change. Every stage degrades gracefully; capture is never
blocked by recognition.

```kotlin
import ai.neurolabs.sdk.recognition.NLRecognitionBootstrap

val bootstrap = NLRecognitionBootstrap(
    context,
    NLRecognitionBootstrap.Configuration(
        operationsApiKey = "<your operations key>",
        operationsBaseUrl = "https://api.operations.neurolabs.ai/v1",
    ),
)
bootstrap.start(sdk, applicationScope) // safe to call again; see below
// bootstrap.status (StateFlow) → "provider: ready (N items)" etc.
// bootstrap.statusSummary → also says when the chain was built offline
```

**Offline.** Every build that completes online saves the recognition config
and the snapshot's signed manifest for that operations key (the file is named
by a one-way fingerprint of the key; the key is never stored). When a later
build cannot reach the Operations API (no signal, a timeout, a captive portal,
a 5xx), it builds from that record for up to the org's offline expiry after
the last full sync (`offline_ttl_days` in the recognition config, 1 to 30 days;
else `bootstrap.offlineCacheTTL`, 7 days; records saved before 1.7.19 read as
7 days), as long as the embedder and every snapshot shard
are still on the device and pass their sha256 checks. `bootstrap.offlineSnapshotDate`
is then the time of that sync, and `statusSummary` reads
`provider: ready (offline, 42 items, snapshot from 2026-10-01)`. A 401 or 403
still switches recognition off and forgets the record.

**Signed manifests (v1.7.23).** Every manifest, online or from the offline
record, must carry a valid signature from a key the SDK pins; otherwise the
load fails with `NLCatalogSnapshotLoader.IntegrityException` and recognition
stays off for that build. The staging key is trusted only on a Neurolabs
staging operations host. An offline record an older SDK saved is unsigned,
so it is not used; the next online build replaces it.

**Short-lived tokens.** If your bearer is a session token rather than a fixed
key, build the configuration with your `NLOperationsAuthProvider` and a stable
identity for the rep or org instead:

```kotlin
NLRecognitionBootstrap.Configuration(
    authProvider = myAuthProvider, // e.g. NLRefreshableAuthProvider { exchangeSessionToken() }
    offlineIdentity = repId,       // stable across tokens; must not be blank
    operationsBaseUrl = "https://api.operations.neurolabs.ai/v1",
)
```

Every request takes the provider's current token. A 401 drops it and the
request is made once more with a fresh one; only a second 401 switches
recognition off and forgets the record. The offline record is named after a
one-way hash of `offlineIdentity` (never stored as is), so a record saved under
yesterday's token serves today's, and a cold start with no network (and so no
token) still builds from it. A provider that cannot give a token counts as
offline. A blank identity throws `IllegalArgumentException`. `copy()` on this
configuration returns an API-key configuration: build a new one instead.

**Retries.** A build that ended unavailable is not final: calling `start` again
builds again once 60 s have passed after a network-type failure, or 1 h after
a definitive one (disabled, refused, mismatched). After a network-type failure
the bootstrap also rebuilds by itself when the device's network comes back (at
most 5 times per instance). A later ready build injects its provider into the
SDK like the first.

The embedder `.tflite` (DINOv3 ConvNeXt-Tiny) downloads through the Operations
API (`GET /v1/device-models/dinov3-convnext-tiny-android-tflite-v1`, sha256 and
size pinned in the SDK) once recognition-config has enabled recognition for your
org, and is cached, so later launches need no network. It is the only embedder
the SDK runs: a model your app ships as an asset is never used. When the model
cannot be had, recognition is off with the reason, for example
`embedder unavailable (not_entitled)`. The release AAR carries the
Qdrant Edge native libraries; the default index remains the built-in
brute-force this release.

Tap-to-product-card: captures expose per-detection matches via
`sdk.recognitionMatches(forCaptureId:)`; pair the SDK's
`DetectionOverlay(onDetectionTap = ...)` with
`NLDetectionInspectorSheet(detection, match, resolver, onDismiss)` and an
`NLProductDetailsResolver` built over `NLOperationsCatalogClient`.
Offline or unresolved products fall back to a UUID + similarity row.

Inspector floor (v1.7.24): `NLDetectionInspectorSheet` names a box only when
its match is at or above `NLReviewAnalytics.RECOGNITION_FLOOR` (0.5). Below
it, the sheet keeps the detection's class and says "Not recognised", with the
closest catalogue item and its score as a percentage. If you draw names on
boxes yourself (`DetectionOverlay(detectionLabels = ...)`), take them from
`NLInspectorMatchPolicy.boxName(match, product)`, which applies the same
floor; `NLInspectorMatchPolicy.isRecognised(match)` is the test alone.

Matches on the captures (v1.7.22): the SDK recognises a capture where it is
enqueued, mostly after `onCaptureComplete` (the `NLCaptureActivity` save loop,
or your own `enqueueCapture` call), so read the matches with
`sdk.recognitionMatches(forCaptureId:)` once the capture is enqueued. A
delivered capture's `CapturedImageData.recognitionMatches` is filled only when
it was recognised before delivery. The multi-bay realogram (rebuilt after
`NLCaptureActivity`'s save loop) and the visit KPIs read the stored matches.
To recognise a photo outside the camera (one you stored
yourself), call the suspend
`sdk.recognizeCapture(captureId, imageData, detections)`. It returns the
matches and keeps them for `recognitionMatches(forCaptureId:)`; null means
recognition did not run (no provider, the kill switch on, a provider not
ready, or an image that does not decode), and an empty map means it ran and
matched nothing. Nothing is queued or uploaded.

**Catalogue-mirror gate (1.7.26).** If your app keeps a catalogue mirror
from the change feed, tell the bootstrap where it is, so a recognised product
is never missing from it:

```kotlin
import ai.neurolabs.sdk.recognition.NLMirrorGateConfiguration
import ai.neurolabs.sdk.recognition.NLMirrorStatus

val configuration = NLRecognitionBootstrap.Configuration(
    operationsApiKey = "<your operations key>",
    operationsBaseUrl = "https://api.operations.neurolabs.ai/v1",
)
configuration.mirrorGate = NLMirrorGateConfiguration(
    provider = { NLMirrorStatus(mirror.cursor, mirror.consecutiveFailures) },
)
val bootstrap = NLRecognitionBootstrap(context, configuration)
bootstrap.onJoinDegradedChange = { reason -> /* null: back to normal */ }
```

Set it before building the bootstrap. The provider reports the active
account's mirror, on a background thread, and must not throw. A fresh
snapshot stamped with a feed position your mirror has not reached is held:
the bootstrap keeps serving the last good build. The hold ends when the
mirror reaches the stamp, or after 7 days or 5 consecutive mirror failures
(`NLMirrorGatePolicy`); the snapshot then activates and `joinDegraded` says
why (`MIRROR_TIMEOUT`, `MIRROR_FAILURES`, or `NO_PRIOR_SNAPSHOT` when there
was no earlier build to serve). While it is set, resolve a recognised item
missing from your mirror through `canonical_uuids`. Call `close()` on
sign-out. Without `mirrorGate` nothing changes.

**A crop and its recognition (1.7.25).** A crop keeps the capture id. Once the
camera has reported the crop (`onCaptureCropReplaced`, bound or not), the core
forgets the uncropped photo's `recognitionMatches`, `unknownEmbeddings` and
`priceReadings`. A photo that already had a recognition pass is recognised
again on the crop's bytes and detections, off the main thread. A photo no
pass ran for is left alone, and its pass sees the crop. No API change.

## 12. Notes

### Store context for visit KPIs (1.7.21)

A visit's KPIs need the outlet's store context (targets, assortment, planograms and the org's metric definitions). The SDK fetches, verifies and caches it per credential for the org's offline TTL (default 7 days). Outlet ids are Operations outlet UUIDs. The calls are extensions on `NeurolabsSDKCore` (`import ai.neurolabs.sdk.core.*`).

```kotlin
val result = sdk.prefetchStoreContext(routeOutletIds)  // never throws; result.refreshFailure is a code
val status = sdk.storeContextStatus(outletId)           // cache only, no network
sdk.setStoreContextIdentity(currentUser.id)  // only with setOperationsAuthProvider; hashed, never stored or sent
sdk.clearStoreContextCache()                  // sign-out
```

`status.state` is `READY`, `EXPIRED` or `MISSING`, and `status.reason` is a stable code (`not_assigned` means the outlet id is not your org's; treat an unknown code as missing). `device_kpis` are submitted only for a context that is ready and `isSignatureVerified`; the SDK pins the production key `store-context-v1` and requires signatures. The staging key `store-context-v2` is trusted only on a Neurolabs staging operations host. The full code list is in the README ("Store Context (visit KPIs)").

### Visit KPIs (1.7.21)

After an SDK-managed session (`NLCaptureActivity`, the bridge, Cordova) finishes with at least one capture, the SDK computes the visit's KPIs on the device and calls `NeurolabsSDKDelegate.onVisitKpis(result, sessionId)` (default no-op). On by default; `setVisitKpisEnabled(false)` turns it off.

With your own capture UI (`NLCustomCameraView`, or photos you queue with `enqueueCapture`), `stopSession(sessionId)` computes them once instead (1.7.23), from the photos queued for that session, under the same rules. Set the context on the session you stop. Since 1.7.24 what the run needs is recorded on disk, so a visit that spans an app kill counts every photo, with its recognition matches, once you call `stopSession` after the relaunch. A session the SDK submits on its own after a relaunch, with no `stopSession`, goes without `device_kpis`.

**Queue before you stop the session.** If you launch `enqueueCapture` in a coroutine from a per-photo callback and call `stopSession` when the camera finishes, the stop can come before the last enqueue returns. Since 1.7.26 the SDK covers this: `stopSession` waits for the session's `enqueueCapture` calls already running when it is called, up to 5 s, before the KPI run and the mission submit. On the bound it logs and goes on without them; it cancels nothing. An `enqueueCapture` you start after `stopSession` is not waited for, and on 1.7.25 and earlier the SDK does not wait at all. Awaiting your own enqueues (join their jobs, bounded) before `stopSession` is still recommended, as the demo's `DemoPendingEnqueues` does.

```kotlin
sdk.setVisitKpiContext(sessionId, NLVisitKpiContext(outletId, sectionsByCaptureId = emptyMap(), sectionsByBayIndex = emptyMap()))
// before the session finishes; refreshes the store context
val result = sdk.computeVisitKpis(sessionId, captures, multiBayResult, context)  // your own capture UI; read-only
val preview = sdk.computeVisitKpis(sessionId, captures, multiBayResult, context,  // a store context you supply:
    storeContext = NLVisitKpiHostStoreContext(storePartJson = storePart, orgPartJson = orgPart))
```

`computeVisitKpis(sessionId, captures, multiBay, context, storeContext)` (1.7.24) runs the same engine on a store part (`nl.store_context` v1) and org part (`nl.store_context_org` v1) you pass as JSON, for previews, demos and tests. Their shape is checked, never a signature, so the result is never submitted; a part that fails a check throws `VISIT_KPIS_STORE_CONTEXT_INVALID`.

#### Visit KPIs by session id (1.7.25)

`computeVisitKpis(sessionId, context, storeContext)` runs the same pull when you have only the session id, as a Cordova host does:

```kotlin
val preview = sdk.computeVisitKpis(sessionId, context = null,  // null: the context you set for it
    storeContext = NLVisitKpiHostStoreContext(storePartJson = storePart, orgPartJson = orgPart))
```

- The session must have been finished by a camera the SDK runs (`NLCaptureActivity`, the Cordova plugin) in this process, with at least one photo; a cancelled session counts. The SDK holds the newest 8 such sessions in memory: detections, sizes, times, recognition matches, the multi-bay result and its dedup setting. It keeps no pixels and writes nothing to disk.
- For a session you queued yourself (`enqueueCapture`), it reads the photos queued for it, until its `stopSession` run has taken them.
- The result is the one `computeVisitKpis(sessionId, captures, multiBay, context, storeContext)` gives for the same session, and is never submitted. The one difference: it uses the camera's `onDeviceDedup`, where the captures-based call takes it as on, so a walk captured with on-device dedup off gives a different result.
- A null `context` uses the one you set with `setVisitKpiContext`, even after `stopSession`.
- An id the SDK holds nothing for (another process, no photo, or 8 newer sessions since) throws `VISIT_KPIS_SESSION_UNKNOWN`. `VISIT_KPIS_DISABLED` and `VISIT_KPIS_STORE_CONTEXT_INVALID` come first.

`NLVisitKpiResult` carries the canonical `nl.visit_kpis` v1 JSON (`payloadJson`), `isProvisional` (always true on the device: label it "Provisional"), `storeContext` (`Used(offline)`, `Missing`, `Expired`), `perfectStoreScoreBp`, `actionCount` and `willSubmit`. Without a store context, show gaps and price-tag presence only, as "Needs store targets". The payload rides the mission submit as `client_metadata.device_kpis` only when the store context was ready and signature-verified and the payload passes the backend's checks; a `400 invalid_device_kpis` makes the SDK resubmit once without it. Details are in the README ("Visit KPIs").

### KPI rules (1.7.24)

- **K16 price-tag coverage.** A visit's `tag_paired` now comes from shelf
  geometry, measured in the facing's own size, not from the recognition price
  matcher's 100 px reach. A `price` or `promo` tag pairs one stack-0 facing:
  the tag's centre must sit between a quarter of the facing's height above
  its bottom and 1.5 of the tag's own heights below it, within half the
  facing's width; the nearest facing wins. A tag under a gap tags no product,
  and peg or hanging tags pair nothing. On three 19 Oct field captures 160 of
  163 tags paired, where none did before, so K16 rises and `add_tag` actions
  fall on full-resolution photos. zia-operations and iOS run the same rule.
  The recognition payload's `priceMatches` keep the matcher's rule.
  From 1.7.25 `priceReadings(forCaptureId)[].pairedDetectionId` uses the
  same pairing, so a host's price and K16 name the same product.
- **Compliance KPIs.** The brand block (K9), shelf position (K10) and
  adjacency (K11) KPIs, and the reposition (N4) and restore-block /
  fix-adjacency (N5) actions, are pinned byte for byte to zia-operations'
  58 shared layout rows. The engine already matched them, so nothing
  changes.

### Telemetry and privacy (Sentry)

The SDK reports errors to the Neurolabs Sentry project under this policy,
the same on Android, iOS and Cordova:

- **Only the SDK's own errors.** The SDK reports the errors it captures
  itself. It never calls `SentryAndroid.init` or `Sentry.init`: its client is
  private, so no uncaught-exception handler, ANR, network, session or
  lifecycle integration is installed in your app, a crash or ANR in your own
  code is never sent, and your own Sentry setup is untouched.
- **No credentials or personal data.** `isSendDefaultPii` is off. Messages
  are scrubbed before they are sent: a URL keeps only its scheme, host and
  path, so a signed URL's credentials never leave the device. Since 1.7.20
  an error that came from a server response carries only the HTTP status and
  the server's `error_code`, never the response body.
- **Opt out** with `sentryEnabled = false` (or `analyticsEnabled = false`) on
  `NLConfiguration`. Nothing is sent from a unit or instrumented test run.

### Other notes

- Per-session upload routing is supported with `options.taskUUID`.
- `autoCloseAfterCapture=true` closes after Save from preview/review flow.
- Use `allowManualFinish = true` with `minCapturesBeforeDone` and `maxCaptures` when you want "at least X, up to Y" capture sequences.
- Set `showsCapturedCountLabel = false` to hide the `N captured` chip in the top bar.
- For partner apps, avoid passing base64 images across process boundaries.
