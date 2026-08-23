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
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.3/NeurolabsSDK.xcframework-v1.7.3.zip",
            checksum: "7230f93bd9733730d2b4444cb2a998f7cf8b5d6e7b3e99161f9bdc174965b33e"
        ),
        .binaryTarget(
            name: "ProductAuditKit",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.3/ProductAuditKit.xcframework-v1.7.3.zip",
            checksum: "ce261be1821908aa9a356a3dfc9b2462f7352669fc46a6cd9155b44abd5acf8b"
        ),
        .binaryTarget(
            name: "RecognitionInterface",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.3/RecognitionInterface.xcframework-v1.7.3.zip",
            checksum: "19ff79426871544d38e0664211efa7f94b710724a3dab21f80e20334733e71cb"
        ),
        .binaryTarget(
            name: "RecognitionEngine",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.3/RecognitionEngine.xcframework-v1.7.3.zip",
            checksum: "1418f7155bef9ee476e1f6e8fe941722a2cd7d749032ec7c69d7fb1b05db277d"
        ),
        .binaryTarget(
            name: "RecognitionEngineQdrant",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.3/RecognitionEngineQdrant.xcframework-v1.7.3.zip",
            checksum: "46d520f50e87b6057d5b7df86e1495950a6fadadf7be70dea7f9bad9358f7aef"
        ),
        .binaryTarget(
            name: "RecognitionBootstrap",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.3/RecognitionBootstrap.xcframework-v1.7.3.zip",
            checksum: "e500f71f76de06d35f01c360e7d27bc9dd1e8ae0ff72348e1ee681a29e4680e7"
        ),
        .binaryTarget(
            name: "NLQdrantEdgeFFI",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.3/NLQdrantEdgeFFI.xcframework-v1.7.3.zip",
            checksum: "5748c52e51ac26773b0b7797026efbacc966fa01b576d1f3e5455cd4327127ea"
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
