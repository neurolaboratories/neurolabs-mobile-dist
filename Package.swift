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
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.6.12/NeurolabsSDK.xcframework-v1.6.12.zip",
            checksum: "23c89879168979686f3e5ca2f8f47092e08798d155b19cdc0feef29a1967ae8b"
        ),
        .binaryTarget(
            name: "ProductAuditKit",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.6.12/ProductAuditKit.xcframework-v1.6.12.zip",
            checksum: "8000870cfafea0a0a029d0c0f8015092275ab04b0a401f427b3a9ea06d6992a5"
        ),
        .binaryTarget(
            name: "RecognitionInterface",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.7/RecognitionInterface.xcframework-v1.7.7.zip",
            checksum: "734053a9c10a1061bc949391aa74fa0a0cd1446cacef21bf868f89de2280d167"
        ),
        .binaryTarget(
            name: "RecognitionEngine",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.7/RecognitionEngine.xcframework-v1.7.7.zip",
            checksum: "3222f70842d7933cacf178d0f4d5da83e18b21799a1d5c0e36b614ad79521f4f"
        ),
        .binaryTarget(
            name: "RecognitionEngineQdrant",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.7/RecognitionEngineQdrant.xcframework-v1.7.7.zip",
            checksum: "c07a48f018d5d55b5f4cfcbeaf0610a671695e66780e07486aafc0783517c032"
        ),
        .binaryTarget(
            name: "RecognitionBootstrap",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.7/RecognitionBootstrap.xcframework-v1.7.7.zip",
            checksum: "6dc05cf4772ba66e0cee357be422ee39b31c4dacf51d58524b8031a4282259b1"
        ),
        .binaryTarget(
            name: "NLQdrantEdgeFFI",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.7/NLQdrantEdgeFFI.xcframework-v1.7.7.zip",
            checksum: "10b4f8daff5e52467e4e444539e22a9a7771c7adc4d284fb10a5434ddb5a9b85"
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
