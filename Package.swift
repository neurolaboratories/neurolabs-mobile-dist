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
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.6.9/NeurolabsSDK.xcframework-v1.6.9.zip",
            checksum: "3aa3dba851b81a187721bac95f39770700dd049f1af569be5e384affafd89e5e"
        ),
        .binaryTarget(
            name: "ProductAuditKit",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.6.9/ProductAuditKit.xcframework-v1.6.9.zip",
            checksum: "4d19cd1abf8864e99e4d05731c69217cdb8924ff0d802c8d7506bbdb52108c70"
        ),
        .binaryTarget(
            name: "RecognitionInterface",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.1/RecognitionInterface.xcframework-v1.7.1.zip",
            checksum: "a9b25aa03e8718638dab8c7833c357b2cbb05f176edb3f4cb1b8a2f26aa3919e"
        ),
        .binaryTarget(
            name: "RecognitionEngine",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.1/RecognitionEngine.xcframework-v1.7.1.zip",
            checksum: "0ddabf3fd48ce880b1082e2e441f065892347605fbbe1b79022081becab960bb"
        ),
        .binaryTarget(
            name: "RecognitionEngineQdrant",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.1/RecognitionEngineQdrant.xcframework-v1.7.1.zip",
            checksum: "a74e166d36f381d1ee6517772f4d69412a72d32d63fb00caeef63bb73113866b"
        ),
        .binaryTarget(
            name: "NLQdrantEdgeFFI",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.1/NLQdrantEdgeFFI.xcframework-v1.7.1.zip",
            checksum: "dcbccfadb2ff5255fe19d0fb79cd9a9feb57b5b08c3ef5d68b627779a64e8fc7"
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
