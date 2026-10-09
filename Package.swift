// swift-tools-version: 5.9
import PackageDescription

// Binary distribution manifest for the prebuilt xcframeworks.
// The URL/checksum are stamped per release (see the release train).
//
// Every product comes from its OWN release asset (SPM keys the binary
// artifact cache by URL — binaryTargets cannot share one zip):
//   • NeurolabsSDK           — main SDK (asset carries SDK + Sentry companion).
//   • ProductAuditKit        — camera/product-audit + barcode capture,
//                              independent, no Sentry link.
//   • RecognitionInterface   — on-device recognition protocols + snapshot
//                              loader (v1.7.x). Dependency-free.
//   • RecognitionEngine      — DINOv3 CoreML embedder, the on-device
//                              recognition provider, and the
//                              `NLVectorSearchable` index seam. NOT
//                              self-contained: the concrete vector engine
//                              lives in RecognitionEngineQdrant. (USearch was
//                              removed 2026-08 — Qdrant Edge is the only
//                              on-device vector engine, so "link
//                              RecognitionEngine alone" is never correct.)
//   • RecognitionEngineQdrant — Qdrant Edge index (payloads-in-shard, offline
//                              product details); links the NLQdrantEdgeFFI
//                              Rust dylib, which SPM provides as its own
//                              binary target below.
//   • RecognitionBootstrap   — config gate → tenant discovery → snapshot
//                              loader → embedder → index → provider. The one
//                              product a host app links for on-device
//                              recognition.
//
// LINK CLOSURES — these are binaryTargets, so SPM has no dependency graph to
// walk: whatever a product does not list is simply not linked, and the app
// dies at launch on an unsatisfied @rpath/<Name>.framework/<Name>. Every
// recognition product below therefore enumerates its FULL transitive closure,
// mirroring the source manifest in neurolabs-ios-sdk/Package.swift:
//   RecognitionInterface    → (none)
//   RecognitionEngine       → RecognitionInterface
//   RecognitionEngineQdrant → RecognitionEngine, RecognitionInterface,
//                             NLQdrantEdgeFFI
//   RecognitionBootstrap    → RecognitionEngine, RecognitionEngineQdrant,
//                             RecognitionInterface (+ NLQdrantEdgeFFI, via
//                             RecognitionEngineQdrant)
// Listing a target in several products is free — SPM links each target once.
// Do NOT trim these lists back to one entry "because the target is already in
// another product": that is exactly the defect that shipped from v1.7.2.
//
// ONE RELEASE LINE, ALWAYS. Every binaryTarget below must point at the SAME
// /releases/download/<tag>/ segment. On 2026-09-21 a v1.6.12 maintenance
// backport stamped NeurolabsSDK and ProductAuditKit while leaving the five
// recognition targets at v1.7.7, and `main` spent a day handing SPM consumers
// a 1.6.12 SDK — 363 fewer public declarations, no setRecognitionProvider —
// bolted to a 1.7.7 recognition stack it had nowhere to plug into.
// `scripts/verify_spm_manifest.py` now fails the release on exactly that, and
// runs on every stamp; run it yourself after any hand edit here.
//
// The 1.6.x source tree has no RecognitionEngine/RecognitionEngineQdrant/
// RecognitionBootstrap targets at all, so this manifest cannot describe it.
// A 1.6.x release needs its own branch and its own Package.swift — see
// "Release lines" in the README. The release train now rejects an iOS dispatch
// that does not carry an asset for every target below.
//
// The SentryShim target is REQUIRED for NeurolabsSDK: the prebuilt framework
// links Sentry dynamically, so consumers need SPM to provide Sentry.framework
// at the exact version the binary was linked against — do not remove it or
// float its version independently of the release notes. ProductAuditKit does
// not use it.

let package = Package(
    name: "NeurolabsSDKDistribution",
    platforms: [
        .iOS(.v17)
    ],
    products: [
        .library(name: "NeurolabsSDK", targets: ["NeurolabsSDK", "NLSentryShim"]),
        // Camera/product-audit + barcode capture SDK. Own asset, own checksum
        // (SPM keys the binary artifact cache by URL — two targets must not
        // share one zip). Independent of NeurolabsSDK, no Sentry link.
        .library(name: "ProductAuditKit", targets: ["ProductAuditKit"]),
        // On-device recognition (v1.7.x). See "LINK CLOSURES" above: each
        // product carries every framework its own framework dlopen's, so a
        // partner cannot get the link set wrong by reading prose.
        .library(name: "RecognitionInterface", targets: ["RecognitionInterface"]),
        // The provider-chain bootstrap — link THIS ONE for on-device
        // recognition. It pulls the whole chain in; no companion product has
        // to be added by hand.
        .library(
            name: "RecognitionBootstrap",
            targets: [
                "RecognitionBootstrap",
                "RecognitionEngineQdrant",
                "NLQdrantEdgeFFI",
                "RecognitionEngine",
                "RecognitionInterface"
            ]
        ),
        .library(
            name: "RecognitionEngine",
            targets: ["RecognitionEngine", "RecognitionInterface"]
        ),
        .library(
            name: "RecognitionEngineQdrant",
            targets: [
                "RecognitionEngineQdrant",
                "NLQdrantEdgeFFI",
                "RecognitionEngine",
                "RecognitionInterface"
            ]
        )
    ],
    dependencies: [
        .package(url: "https://github.com/getsentry/sentry-cocoa.git", exact: "9.21.0")
    ],
    targets: [
        .binaryTarget(
            name: "NeurolabsSDK",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.17/NeurolabsSDK.xcframework-v1.7.17.zip",
            checksum: "971ea590ac4016c9d767b236742c4f9e6e798be882b0f3ec73b2c286e5bf5995"
        ),
        .binaryTarget(
            name: "ProductAuditKit",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.17/ProductAuditKit.xcframework-v1.7.17.zip",
            checksum: "d18a573c7cd1f17ea4b7342ab7d30bab58f6a6b4a674ecfdc315edad98d8d9dd"
        ),
        .binaryTarget(
            name: "RecognitionInterface",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.17/RecognitionInterface.xcframework-v1.7.17.zip",
            checksum: "12fd6793664eb0e46dc37edf834f7a6ec3620dcdeae40c811b2134223efab8b0"
        ),
        .binaryTarget(
            name: "RecognitionEngine",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.17/RecognitionEngine.xcframework-v1.7.17.zip",
            checksum: "5286c3f3926234a60fef14939c3309749340a8f196934e828aca97f8f2d33fad"
        ),
        .binaryTarget(
            name: "RecognitionEngineQdrant",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.17/RecognitionEngineQdrant.xcframework-v1.7.17.zip",
            checksum: "5dfc331f0c6dc4dff68f3e8e6badd9d3459c5dc145e434ef3658861699db5fe0"
        ),
        .binaryTarget(
            name: "RecognitionBootstrap",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.17/RecognitionBootstrap.xcframework-v1.7.17.zip",
            checksum: "900f4eaeac6bd655d9cc5cb305a4c47a4dfa4c6e1d0cfbe9da9b5652ad977b09"
        ),
        .binaryTarget(
            name: "NLQdrantEdgeFFI",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.17/NLQdrantEdgeFFI.xcframework-v1.7.17.zip",
            checksum: "fe9af0c2ce8cda0a0b32ef8fb2c0044773c10a1f47ea968c5b855580625cb2d8"
        ),
        .target(
            name: "NLSentryShim",
            dependencies: [
                .product(name: "Sentry-Dynamic", package: "sentry-cocoa")
            ],
            path: "SentryShim"
        )
    ]
)
