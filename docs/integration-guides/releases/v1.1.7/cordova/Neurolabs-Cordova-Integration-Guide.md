# Neurolabs Cordova SDK - Integration Guide

## 1. Scope
This guide is for partner hybrid apps integrating `neurolabs-cordova-sdk`.

## 2. Changes In v1.1.7
- Init and per-session routing use `taskUUID`.
- Native detector/model warmup is enforced in `init` and guarded in `openCamera`.
- `openCamera` can return `MODEL_INIT_FAILED` when native model initialization fails.
- `autoCloseAfterCapture=true` now keeps preview enabled and closes after Save confirmation.
- `cameraClosed` event now includes `message`.
- `captureQueued` events are deferred while camera is open and flushed after `cameraClosed`.

## 3. Install

```bash
cordova plugin add /path/to/neurolabs-cordova-sdk
```

## 4. SDK Initialization + Warmup

```js
const Neurolabs = cordova.require('ai.neurolabs.cordova.Neurolabs');

await Neurolabs.init({
  apiKey: '<API_KEY>',
  apiBaseUrl: 'https://api.neurolabs.ai/v2',
  taskUUID: '<DEFAULT_TASK_UUID>',
  allowBase64PhotoExport: false
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
