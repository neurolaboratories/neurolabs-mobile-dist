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
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.20/NeurolabsSDK.xcframework-v1.7.20.zip",
            checksum: "c021daa3dde25b793cae99ee0b4ef96a7fc984435f631aff61005a75aceed4fe"
        ),
        .binaryTarget(
            name: "ProductAuditKit",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.20/ProductAuditKit.xcframework-v1.7.20.zip",
            checksum: "b031452da29f4b9582b7d52f6524c4b6f4e24aff347507c79cb5bbda7aa1abbe"
        ),
        .binaryTarget(
            name: "RecognitionInterface",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.20/RecognitionInterface.xcframework-v1.7.20.zip",
            checksum: "bd76206ce26a3a112b44e4dcfa5c6f27c4a7990d4a8993d544e10b6cba7d48df"
        ),
        .binaryTarget(
            name: "RecognitionEngine",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.20/RecognitionEngine.xcframework-v1.7.20.zip",
            checksum: "01cc36869674bc3b22de4490a36377b6a56c3ac7773a32384e85f086bf1b6ffb"
        ),
        .binaryTarget(
            name: "RecognitionEngineQdrant",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.20/RecognitionEngineQdrant.xcframework-v1.7.20.zip",
            checksum: "91950e0312fded6b5ba37cfac0d687a38f48790be539a3964f45c1ef788eb7d2"
        ),
        .binaryTarget(
            name: "RecognitionBootstrap",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.20/RecognitionBootstrap.xcframework-v1.7.20.zip",
            checksum: "235e7745801abb2f6dcf9e91da417eeedf369a96a897a690ba5cf139f2155cc1"
        ),
        .binaryTarget(
            name: "NLQdrantEdgeFFI",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.20/NLQdrantEdgeFFI.xcframework-v1.7.20.zip",
            checksum: "08779ba90235716fbe993b65d4b558b0b95154f2ca208f6efd0496a1d9c50d28"
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
