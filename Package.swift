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
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.15/NeurolabsSDK.xcframework-v1.7.15.zip",
            checksum: "1b31610ea1f0930551a3d7ac3c4a79de82bb205d7347d5ee7044741d09dc0ded"
        ),
        .binaryTarget(
            name: "ProductAuditKit",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.15/ProductAuditKit.xcframework-v1.7.15.zip",
            checksum: "52e18c180ffd18055fa8d91897c0475f6029293ff115290b96ff620c8713bb4b"
        ),
        .binaryTarget(
            name: "RecognitionInterface",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.15/RecognitionInterface.xcframework-v1.7.15.zip",
            checksum: "11de7917b63c13184d472139cf0da19e0122ea6c051db51eaea3a2845000c9bc"
        ),
        .binaryTarget(
            name: "RecognitionEngine",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.15/RecognitionEngine.xcframework-v1.7.15.zip",
            checksum: "5347c75fb67638d7f2488ceebc773b199b838d5e771891d0261155d35a21efaf"
        ),
        .binaryTarget(
            name: "RecognitionEngineQdrant",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.15/RecognitionEngineQdrant.xcframework-v1.7.15.zip",
            checksum: "9870d8197d50006ab40e0c93fa502ef62808f14bb63d20f77e5cdce709f5eeb7"
        ),
        .binaryTarget(
            name: "RecognitionBootstrap",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.15/RecognitionBootstrap.xcframework-v1.7.15.zip",
            checksum: "18eb2afa452b432b7bc075e68d40a58aa7366117ad38c59bb312f3320ce2df45"
        ),
        .binaryTarget(
            name: "NLQdrantEdgeFFI",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.15/NLQdrantEdgeFFI.xcframework-v1.7.15.zip",
            checksum: "a5b2621bd50f6e47bc30996a20f9550434f4288879f8402d5f4099309f99948f"
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
