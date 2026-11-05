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
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.30/NeurolabsSDK.xcframework-v1.7.30.zip",
            checksum: "f59bde5a2d5c64e72a9cd792c3f5cc9d2d547a083630f7b8107755437c8cab62"
        ),
        .binaryTarget(
            name: "ProductAuditKit",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.30/ProductAuditKit.xcframework-v1.7.30.zip",
            checksum: "d4d9360ea3eefdb23333860016dacdd3e9ad61acafe4f1abc3a903e7b76cb70d"
        ),
        .binaryTarget(
            name: "RecognitionInterface",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.30/RecognitionInterface.xcframework-v1.7.30.zip",
            checksum: "6d9df8165d24866c9ed1e3072caf4bfb29091d28cf039556b2941fd840a80728"
        ),
        .binaryTarget(
            name: "RecognitionEngine",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.30/RecognitionEngine.xcframework-v1.7.30.zip",
            checksum: "b50b846d7e0cab5dc1006bc355191f24ee69986536efef7311a8a2ba6de02535"
        ),
        .binaryTarget(
            name: "RecognitionEngineQdrant",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.30/RecognitionEngineQdrant.xcframework-v1.7.30.zip",
            checksum: "83612336163816f7fa155d88b87f6b65e352c3aa30cd0cea06b16c6da836f0e0"
        ),
        .binaryTarget(
            name: "RecognitionBootstrap",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.30/RecognitionBootstrap.xcframework-v1.7.30.zip",
            checksum: "5a42de11ebb00662172f17b2cfd4787a9c27067d5eb16a0d39df43bdda9fb06a"
        ),
        .binaryTarget(
            name: "NLQdrantEdgeFFI",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.30/NLQdrantEdgeFFI.xcframework-v1.7.30.zip",
            checksum: "f1fc9a8badd638092b33bc47af1228b607944db18520e683205b2df79689d0a2"
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
