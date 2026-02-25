# neurolabs-mobile-dist

Partner-facing distribution repository for Neurolabs mobile SDK artifacts.

This repository is the single release entry point for:

- iOS (`NeurolabsSDK`) via Swift Package Manager binary package
- Android SDK artifacts (AAR/zip) via GitHub Release assets
- Cordova plugin package (`.tgz`) via GitHub Release assets

## Release Policy

- Releases are versioned with a shared tag: `vX.Y.Z`
- Each release is intended to contain matching iOS, Android, and Cordova artifacts
- Source repositories publish artifacts and notify this repo via CI (`repository_dispatch`)
- This repo updates manifests and publishes/updates the coordinated release metadata

## iOS (SwiftPM)

### Add the package in Xcode

1. `File` -> `Add Package Dependencies...`
2. Use this repository URL:
   - `https://github.com/neurolaboratories/neurolabs-mobile-dist`
3. Select the version/tag you need (for example `v1.0.0`)
4. Add product:
   - `NeurolabsSDK`

### Swift import

```swift
import NeurolabsSDK
```

### Notes

- The root `Package.swift` is a SwiftPM binary manifest that points to the iOS XCFramework zip in this repo's release assets.
- CI updates the binary URL and checksum automatically when an iOS release is published.

## Android

Android artifacts are published as release assets in this repository (for example `.aar` files).
This repo also supports Android Maven metadata in `android_ready` dispatch payloads and persists it in `manifests/android.json` (repository URL + coordinates) while still mirroring the AAR into this dist release.

### Typical integration (local AAR)

1. Download the `.aar` from the matching release tag
2. Add it to your app (for example under `app/libs/`)
3. Reference it from Gradle

Example:

```gradle
repositories {
    flatDir {
        dirs("libs")
    }
}

dependencies {
    implementation(files("libs/neurolabs-android-sdk-vX.Y.Z.aar"))
}
```

Refer to `manifests/android.json` for:
- mirrored AAR release asset URL + checksum
- optional Maven repository/coordinates (`latest.maven`)
- Gradle Maven snippets (`gradle_maven_repository_example`, `gradle_maven_dependency_example`)

## Cordova

Cordova plugin packages are published as release assets (`.tgz`).

### Custom camera parity notes

Recent Cordova + Android SDK releases add/expand custom camera IQ parity configuration support (exact field passthrough depends on the Cordova plugin version in the tag), including:

- `validationPreset` (including `ios_parity` on Android)
- live quality toggles (`liveQualityChecksEnabled`, `liveQualityTargetFps`)
- capture preview/review toggles (`showCapturePreview`, `showPreviewInStrictMode`, `freezePreviewOnCapture`)
- `customCameraTemplate` message/style/layout fields (banner, issue strip, review panel) (currently Android passthrough-first; iOS availability depends on SDK bridge model version in the tag)

When consuming new Cordova plugin builds from this dist repo, ensure the Android/iOS native SDK artifact versions in the same release tag support the requested fields.

Support summary (current parity state):

| Capability | Android (Cordova) | iOS (Cordova) |
|---|---|---|
| Custom camera IQ route from `openCamera` | Yes | Yes |
| Live quality checks + issue/banner feedback | Yes | Yes |
| Preview/review toggles | Yes | Yes |
| Template messages/labels/priority | Yes | Yes |
| Template banner style/placement/animation | Yes | Yes |
| Template review style | Yes | Yes |
| All template fields applied identically | No (platform-specific UI/runtime differences remain) | No |

iOS notes:
- `bannerMessageStrategy` is transported but not applied (iOS uses native template banner logic).
- Some Android-only issue strip tint semantics are not applied on iOS.

### Install from a release asset

```bash
cordova plugin add https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/vX.Y.Z/neurolabs-cordova-sdk-vX.Y.Z.tgz
```

Refer to `manifests/cordova.json` for the latest package URL and checksum.

## Machine-Readable Manifests

This repo includes metadata files for automation and partner tooling:

- `manifests/ios.json`
- `manifests/android.json`
- `manifests/cordova.json`

These files track the latest known version, release asset URL, and SHA256 checksum for each platform.

## CI/CD in This Repo

Real workflows used in this repo:

- `.github/workflows/dist-release.yml`
  - receives `ios_ready`, `android_ready`, `cordova_ready`
  - updates manifests and iOS `Package.swift`
  - creates/updates the coordinated release metadata
- `.github/workflows/manual-promote.yml`
  - manual fallback for recovery or backfill

## Integrity Verification

Consumers can validate downloaded artifacts using the SHA256 values in the corresponding manifest files.

## Support / Coordination

Use the same release tag (`vX.Y.Z`) across all Neurolabs mobile components when integrating a coordinated version.
