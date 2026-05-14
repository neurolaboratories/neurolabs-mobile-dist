# Neurolabs Cordova SDK - Integration Guide

## 1. Scope
This guide is for partner hybrid apps integrating `neurolabs-cordova-sdk`.

## 2. Changes

The Cordova plugin is a thin bridge over the native SDKs, so most changes
listed here come from the underlying `neurolabs-android-sdk` and
`neurolabs-ios-sdk` releases that the plugin pulls via
`scripts/prepare-sdk.js` at install time. No public JS API has been broken
since v1.1.9.

### v1.3.2
- Plugin pulls native SDK v1.3.2 binaries on `cordova plugin add`:
  Android AAR + iOS xcframework refreshed via the mobile-dist manifests.
- Native v1.3.2 highlights (no JS surface change required):
  - Mixpanel ingestion now lands in the EU region (events were
    previously POSTed to the US endpoint and silently dropped). iOS also
    fixes a separate bug where Mixpanel rejected every event because
    `time` was serialized as a string rather than a JSON number.
  - Done button stays responsive while the SDK persists captures — disk
    I/O moved off the main thread on both platforms, inline spinner /
    progress indicator surfaced.
  - Android: native `SIGSEGV` fix in
    `com.google.ai.edge.litert.Model.nativeLoadAsset` when the TFLite
    asset is stored compressed in the APK; the loader probes the asset
    with `AssetManager.openFd` first and extracts to internal storage
    when the asset is not mmap-able.
  - Onboarding barcode pipeline normalises to GTIN-14 end-to-end and
    propagates the scanned barcode format through every product-lookup
    client.
  - iOS: new `NLOperationsCatalogClient` (in `ProductAuditKit`) for the
    operations catalog; replaces `precondition`-based validation with
    thrown errors so a malformed barcode no longer crashes the host app.

### v1.2.5
- Native sequence-counter parity: Cordova bridge surfaces the
  `showsSequenceCounterLabel` (and `showsCapturedCountLabel`) options to
  match the native SDK toggles.
- Demo SDK setup builds fixed; iOS Sentry injection timing hardened;
  Android LiteRT dependency pinning correction; sequence-counter
  argument plumbed through correctly.

### v1.2.3
- `openCamera` supports `cameraMode: "ar" | "default"` — `"default"`
  enables the 0.5×/1× lens switcher on both iOS and Android.
- `init` supports `analyticsEnabled`, `sentryEnabled`, `sentryDsn` for
  controlling SDK analytics and crash reporting.
- Tightened default quality validation thresholds (blur, glare,
  perspective) across both platforms.

### v1.2.2
- Internal: Android plugin integration handling refactor; no public JS
  API change.

### v1.2.1
- Cordova install hooks hardened; demo integration updated.

### v1.2.0
- Internal scaffolding for the v1.2.x line; no JS API change.

### v1.1.9
- Init and per-session routing use `taskUUID`.
- Native detector/model warmup is enforced in `init` and guarded in
  `openCamera`.
- `openCamera` can return `MODEL_INIT_FAILED` when native model
  initialization fails.
- `autoCloseAfterCapture=true` now keeps preview enabled and closes
  after Save confirmation.
- Manual finish (`Done`) is available when `autoCloseAfterCapture=false`
  and `allowManualFinish=true`.
- `cameraClosed` event now includes `message`.
- `captureQueued` events are deferred while camera is open and flushed
  after `cameraClosed`.

## 3. Install

Download the plugin package from `https://github.com/neurolaboratories/neurolabs-mobile-dist/releases`.
The install hooks download and wire up the native SDKs automatically — no manual AAR or xcframework
placement needed.

Native baseline requirements:
- Android: `minSdkVersion 26`, JDK 17, Kotlin 2.x.
- iOS: deployment target iOS 17.0+, Xcode 16.4+ recommended (release toolchain baseline).

### Android (Windows or macOS)

```bash
# Add the Android platform first, then install the plugin
cordova platform add android
cordova plugin add /path/to/neurolabs-cordova-sdk-vX.Y.Z.tgz
```

The `before_plugin_install` hook downloads `neurolabs-android-sdk.aar` from the matching GitHub
release, stores it inside the plugin, and `plugin.xml` copies it to `app/libs/` automatically.
`neurolabs.gradle` wires it into the build via `flatDir`.

### iOS (macOS only)

```bash
# Add the iOS platform first, then install the plugin
cordova platform add ios
cordova plugin add /path/to/neurolabs-cordova-sdk-vX.Y.Z.tgz
```

The hook downloads `NeurolabsSDK.xcframework` from the matching GitHub release and Cordova embeds
it automatically during build. Requires `curl` (standard on macOS) or `gh` CLI. For private releases
set `GITHUB_TOKEN`.

The iOS install hook injects the `Sentry` Swift Package dependency into the generated Xcode project
automatically during platform preparation. If Xcode still reports `unable to find module dependency:
Sentry`, re-run `cordova prepare ios` so the package graph refreshes in the generated project.

**Optional overrides** (use a pre-downloaded file or a specific URL instead of auto-download):

```bash
# Local file
NEUROLABS_IOS_XCFRAMEWORK_ZIP=/path/to/NeurolabsSDK.xcframework-vX.Y.Z.zip \
  cordova plugin add /path/to/neurolabs-cordova-sdk-vX.Y.Z.tgz

NEUROLABS_ANDROID_AAR_PATH=/path/to/neurolabs-android-sdk-vX.Y.Z.aar \
  cordova plugin add /path/to/neurolabs-cordova-sdk-vX.Y.Z.tgz

# Direct URL
NEUROLABS_IOS_XCFRAMEWORK_URL=https://github.com/.../NeurolabsSDK.xcframework-vX.Y.Z.zip \
  cordova plugin add /path/to/neurolabs-cordova-sdk-vX.Y.Z.tgz

NEUROLABS_ANDROID_AAR_URL=https://github.com/.../neurolabs-android-sdk-vX.Y.Z.aar \
  cordova plugin add /path/to/neurolabs-cordova-sdk-vX.Y.Z.tgz
```

### iOS + Android (macOS)

Add both platforms before installing the plugin — both hooks run in a single `cordova plugin add`.

## 4. SDK Initialization + Warmup

```js
const Neurolabs = cordova.require('ai.neurolabs.cordova.Neurolabs');

await Neurolabs.init({
  apiKey: '<API_KEY>',
  apiBaseUrl: 'https://api.neurolabs.ai/v2',
  taskUUID: '<DEFAULT_TASK_UUID>',
  allowBase64PhotoExport: false,
  analyticsEnabled: true,          // SDK analytics (default true)
  sentryEnabled: true,             // Sentry crash reporting (default true)
  // sentryDsn: 'https://...',     // optional custom Sentry DSN
});
```

Warmup is native-side; monitor progress through `loadingProgress` event.

```js
Neurolabs.addListener('loadingProgress', (payload) => {
  console.log('loading', payload);
});
```

## 5. Queue Management

```js
await Neurolabs.setAutoSyncEnabled(true);
await Neurolabs.setWifiOnlyUploadsEnabled(false);
await Neurolabs.setDeletePhotosOnUploadSuccess(true);

await Neurolabs.pauseQueue();
await Neurolabs.resumeQueue();
await Neurolabs.setRetryPolicy({ retryCount: 5 });

const status = await Neurolabs.getQueueStatus();
console.log('queue status', status);

await Neurolabs.flushQueue();
await Neurolabs.retryFailedUploads();
```

## 6. Open Custom Camera

```js
await Neurolabs.openCamera({
  sessionId: crypto.randomUUID(),
  type: 'shelf',
  cameraMode: 'default',          // 'ar' or 'default' — enables 0.5×/1× lens switcher
  guidanceMode: 'strict',
  validationPreset: 'ios_parity',

  confidenceThreshold: 0.25,
  iouThreshold: 0.45,
  maxCaptures: 1,

  showAlignmentGuidance: true,
  enableValidation: true,
  liveQualityChecksEnabled: true,
  liveQualityTargetFps: 6,

  // keep custom-camera guidance UI path
  showDetections: false,
  showCapturedRegions: false,

  // optional metadata/cropping
  sendDetectionsMetadata: true,
  enablePreviewCropping: true,

  // now defaults to true if omitted, but explicit is clearer
  autoCloseAfterCapture: true,

  // manual-finish mode (Done button):
  // allowManualFinish: true,
  // minCapturesBeforeDone: 3,

  // per-session routing override
  taskUUID: 'bfc85982-b955-4f65-9f32-b6dbed85f364',

  // image size constraints
  maxImageDimension: 1920,
  maxImageWidth: 1920,
  maxImageHeight: 1920,
  imageCompressionQuality: 0.85
});
```

Manual-finish example:

```js
await Neurolabs.openCamera({
  sessionId: crypto.randomUUID(),
  type: 'shelf',
  guidanceMode: 'strict',
  maxCaptures: 10,
  autoCloseAfterCapture: false,
  allowManualFinish: true,
  minCapturesBeforeDone: 3
});
```

## 7. Post-Processing + Lifecycle Events

```js
// Fires when the camera screen is dismissed (Done or Close pressed).
// captureCount is the number of photos queued for upload — NOT the photo data itself.
// To retrieve photo data, use getPhoto() with the captureId from captureQueued (see section 8).
Neurolabs.addListener('cameraClosed', ({ sessionId, cancelled, captureCount, message }) => {
  console.log('cameraClosed', sessionId, cancelled, captureCount, message);
});

// Fires once per photo taken, immediately after each capture is added to the upload queue.
// captureQueued events are buffered while the camera is open and always delivered after cameraClosed.
// Use the captureId here to retrieve the local photo via getPhoto().
Neurolabs.addListener('captureQueued', ({ captureId, queueItemId, sessionId }) => {
  console.log('queued', captureId, queueItemId);
});

// Fires after the Neurolabs server has processed an uploaded photo and returned an analysis result.
// This is a server-side callback — it does NOT fire when the photo is taken locally.
// Payload: { captureId, sessionId, success, message, detectionCount, capturedRegionCount }
Neurolabs.addListener('captureResult', (payload) => {
  console.log('captureResult', payload);
});

Neurolabs.addListener('uploadSucceeded', (item) => console.log('uploaded', item));
Neurolabs.addListener('uploadFailed', (payload) => console.warn('uploadFailed', payload));
Neurolabs.addListener('queueStatusChanged', (status) => console.log('queueStatusChanged', status));
```

## 8. Retrieving Photos Locally

Photos are stored in the device's app cache after capture. Use `getPhoto()` to access them by `captureId`
(from `captureQueued`) or `queueItemId`.

```js
const capturedIds = [];

Neurolabs.addListener('captureQueued', ({ captureId }) => {
  capturedIds.push(captureId);
});

Neurolabs.addListener('cameraClosed', async ({ cancelled }) => {
  if (cancelled) return;
  for (const captureId of capturedIds) {
    // format: 'fileUri' returns { uri: 'file://...' } — a temp path in the app cache
    // format: 'base64'  returns { base64: '...' }    — requires allowBase64PhotoExport: true in init()
    const photo = await Neurolabs.getPhoto({ captureId, format: 'fileUri' });
    console.log('photo uri', photo.uri);
  }
  capturedIds.length = 0;
});
```

`deletePhoto()` accepts the same query shape (`captureId`, `queueItemId`, or `responseId`) and removes
the local file from the cache.

## 9. Notes
- `openCamera` is the custom native camera entrypoint.
- Use the strict shelf payload above for full shelf guidance checks and auto-close after a validated save.
- `liveQualityChecksEnabled=true` is required for pill/rotation/warning/error guidance behavior.
- Keep `type: 'shelf'`, `guidanceMode: 'strict'`, `showDetections: false`, and `showCapturedRegions: false` for the custom-camera guidance UI path.
- `guidanceMode: 'guidance'` should only be used as a temporary fallback if a partner explicitly wants looser Android behavior than the parity recommendation.
- `autoCloseAfterCapture=true` closes after Save from preview/review flow.
- `Done` appears only in manual-finish mode: `autoCloseAfterCapture=false` + `allowManualFinish=true`.
- Use `minCapturesBeforeDone` to require a minimum number of captures before `Done` becomes active.
- If `allowManualFinish=false`, `maxCaptures` acts as a hard limit and capture disables at the limit.
- `captureQueued` events are buffered while the camera is open and always delivered after `cameraClosed` — never during an active session.
- Keep base64 transport disabled unless explicitly needed.
