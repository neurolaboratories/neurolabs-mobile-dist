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
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.5/NeurolabsSDK.xcframework-v1.7.5.zip",
            checksum: "c3f86adfeb8b40f8c7debd8990463789f246e21048cf3d6d3deb2273252d92c6"
        ),
        .binaryTarget(
            name: "ProductAuditKit",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.5/ProductAuditKit.xcframework-v1.7.5.zip",
            checksum: "05126b572af1faba3bfb69f97334efcc0d5674a4164f1507f9b95ea11c48e82c"
        ),
        .binaryTarget(
            name: "RecognitionInterface",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.5/RecognitionInterface.xcframework-v1.7.5.zip",
            checksum: "21f6751ce8b5917ce358aa294ab1e692f599f2267e8dbbc20e8487941edabaaf"
        ),
        .binaryTarget(
            name: "RecognitionEngine",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.5/RecognitionEngine.xcframework-v1.7.5.zip",
            checksum: "d43830c2b574ff4914815ab3d90d0b2c6f979fdfd46e147f35202f4565015b7d"
        ),
        .binaryTarget(
            name: "RecognitionEngineQdrant",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.5/RecognitionEngineQdrant.xcframework-v1.7.5.zip",
            checksum: "3e231cf9f87b66ba1c8bc9de14c476e231cc1592e0dc2069596deda666bad743"
        ),
        .binaryTarget(
            name: "RecognitionBootstrap",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.5/RecognitionBootstrap.xcframework-v1.7.5.zip",
            checksum: "06b0fae32e0cfec83d6efe8ae2a2507c09385a30480030ff9df65229f61aef29"
        ),
        .binaryTarget(
            name: "NLQdrantEdgeFFI",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.7.5/NLQdrantEdgeFFI.xcframework-v1.7.5.zip",
            checksum: "764bb8c16464f4efa313faf944a2a8265c8abbf01b79a8fad3fb0924f84c639a"
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
