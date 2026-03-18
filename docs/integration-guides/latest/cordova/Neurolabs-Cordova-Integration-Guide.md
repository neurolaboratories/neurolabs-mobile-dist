# Neurolabs Cordova SDK - Integration Guide

## 1. Scope
This guide is for partner hybrid apps integrating `neurolabs-cordova-sdk`.

## 2. Changes Since v1.1.3
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
const Neurolabs = cordova.require('neurolabs-cordova-sdk.neurolabs');

await Neurolabs.init({
  apiKey: '<API_KEY>',
  apiBaseUrl: 'https://api.neurolabs.ai/v2',
  demoIRTaskUUID: '<DEFAULT_TASK_UUID>',
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

  // per-session routing override
  taskUUID: 'bfc85982-b955-4f65-9f32-b6dbed85f364',

  // image size constraints
  maxImageDimension: 1920,
  maxImageWidth: 1920,
  maxImageHeight: 1920,
  imageCompressionQuality: 0.85
});
```

## 7. Post-Processing + Lifecycle Events

```js
Neurolabs.addListener('captureResult', (payload) => {
  // Camera result payload from native side
  console.log('captureResult', payload);
});

Neurolabs.addListener('cameraClosed', ({ sessionId, cancelled, captureCount, message }) => {
  console.log('cameraClosed', sessionId, cancelled, captureCount, message);
});

Neurolabs.addListener('captureQueued', (item) => console.log('queued', item));
Neurolabs.addListener('uploadSucceeded', (item) => console.log('uploaded', item));
Neurolabs.addListener('uploadFailed', (payload) => console.warn('uploadFailed', payload));
Neurolabs.addListener('queueStatusChanged', (status) => console.log('queueStatusChanged', status));
```

## 8. Notes
- `openCamera` is the custom native camera entrypoint.
- Use the strict shelf payload above for full shelf guidance checks and auto-close after a validated save.
- `liveQualityChecksEnabled=true` is required for pill/rotation/warning/error guidance behavior.
- Keep `type: 'shelf'`, `guidanceMode: 'strict'`, `showDetections: false`, and `showCapturedRegions: false` for the custom-camera guidance UI path.
- `autoCloseAfterCapture=true` closes after Save from preview/review flow.
- `captureQueued` may arrive after `cameraClosed` when capture queueing happens while camera is still active.
- Keep base64 transport disabled unless explicitly needed.
