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
//                              loader (v1.7.x).
//   • RecognitionEngine      — DINOv3 provider chain over the USearch index;
//                              self-contained (USearch archived in).
//   • RecognitionEngineQdrant — Qdrant Edge index (payloads-in-shard, offline
//                              product details); links the NLQdrantEdgeFFI
//                              Rust dylib, which SPM provides as its own
//                              binary target below.
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
        // On-device recognition (v1.7.x). RecognitionEngine + Interface power
        // NLRecognitionBootstrap for binary consumers; the Qdrant product
        // bundles the Rust FFI dylib target so one product line links both.
        .library(name: "RecognitionInterface", targets: ["RecognitionInterface"]),
        // The provider-chain bootstrap. Link together with RecognitionEngine
        // + RecognitionInterface (its framework references their dylibs).
        .library(name: "RecognitionBootstrap", targets: ["RecognitionBootstrap"]),
        .library(name: "RecognitionEngine", targets: ["RecognitionEngine"]),
        .library(
            name: "RecognitionEngineQdrant",
            targets: ["RecognitionEngineQdrant", "NLQdrantEdgeFFI"]
        )
    ],
    dependencies: [
        .package(url: "https://github.com/getsentry/sentry-cocoa.git", exact: "9.21.0")
    ],
    targets: [
        .binaryTarget(
            name: "NeurolabsSDK",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.6.11/NeurolabsSDK.xcframework-v1.6.11.zip",
            checksum: "e7026b7ed7a7e7a7c09cc4ca71531ee7237933f2ecf483ac55809727cd129161"
        ),
        .binaryTarget(
            name: "ProductAuditKit",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.6.11/ProductAuditKit.xcframework-v1.6.11.zip",
            checksum: "d6af7f89bcd0720fb8c779ca6e3450012b13484a5017604d1ffa8adbd0affad3"
        ),
        .binaryTarget(
            name: "RecognitionInterface",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.2/RecognitionInterface.xcframework-v1.7.2.zip",
            checksum: "a66822575e2668d1ee7d8e0e405cad8600930bd80a5872b520e99ade8bccbbf5"
        ),
        .binaryTarget(
            name: "RecognitionEngine",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.2/RecognitionEngine.xcframework-v1.7.2.zip",
            checksum: "a806383ee2e86c3538ea0dbd2093abb9b1ef04b4f256a95f9170b797643d7381"
        ),
        .binaryTarget(
            name: "RecognitionEngineQdrant",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.2/RecognitionEngineQdrant.xcframework-v1.7.2.zip",
            checksum: "3dde3c7dadf1f95684e2e2257aa60d8daea63ca73c5c3743a2bb9240b065f367"
        ),
        .binaryTarget(
            name: "RecognitionBootstrap",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.2/RecognitionBootstrap.xcframework-v1.7.2.zip",
            checksum: "336e1579f43b069cedd5192a59a2dd6bb6034bf9d51af9b0a57c88fcd79eaa9a"
        ),
        .binaryTarget(
            name: "NLQdrantEdgeFFI",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.2/NLQdrantEdgeFFI.xcframework-v1.7.2.zip",
            checksum: "0279e69ec9bb55eedf1a7c118a0fa764c767e65c134935b15c7502f46c4b3ad8"
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
