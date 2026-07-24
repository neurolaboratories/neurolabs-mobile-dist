// swift-tools-version: 5.9
import PackageDescription

// Partner-facing iOS binary package manifest.
//
// Two binary products, each from its OWN release asset (SPM keys the binary
// artifact cache by URL, so two binaryTargets must not share one url — they
// collide; one xcframework product per zip):
//   • NeurolabsSDK    — main SDK. Asset NeurolabsSDK.xcframework-<v>.zip carries
//                       NeurolabsSDK.xcframework + its companion Sentry.xcframework.
//   • ProductAuditKit — camera/product-audit + barcode capture SDK. Asset
//                       ProductAuditKit.xcframework-<v>.zip. Independent of
//                       NeurolabsSDK and NOT linked to Sentry (no shim).
//
// scripts/update_spm_manifest.py stamps every neurolaboratories binaryTarget
// url + checksum on release; the getsentry SentryShim `.package(url:)`
// dependency is scoped out and preserved.
//
// The NLSentryShim target is REQUIRED for NeurolabsSDK: the prebuilt
// NeurolabsSDK.xcframework links Sentry DYNAMICALLY (@rpath/Sentry.framework),
// so a binary SPM consumer needs SPM to provide Sentry.framework at the exact
// version the binary was built against, or it crashes at dyld. Do NOT remove it
// or float the version independently of the release the framework was built
// from. ProductAuditKit does not use it.

let package = Package(
    name: "NeurolabsSDKDistribution",
    platforms: [
        .iOS(.v17)
    ],
    products: [
        .library(name: "NeurolabsSDK", targets: ["NeurolabsSDK", "NLSentryShim"]),
        .library(name: "ProductAuditKit", targets: ["ProductAuditKit"])
    ],
    dependencies: [
        .package(url: "https://github.com/getsentry/sentry-cocoa.git", exact: "9.21.0")
    ],
    targets: [
        .binaryTarget(
            name: "NeurolabsSDK",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.6.6/NeurolabsSDK.xcframework-v1.6.6.zip",
            checksum: "51028fcffed5475e6c51b32521442c8259805b930a276f448ab24edc3c539714"
        ),
        // Independent asset — its OWN zip, url and checksum. SPM keys the binary
        // artifact cache by URL, so two targets must NOT share one url (they
        // collide). One xcframework product per asset.
        .binaryTarget(
            name: "ProductAuditKit",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.6.6/ProductAuditKit.xcframework-v1.6.6.zip",
            checksum: "f485970dcd1f0b0a1513c905bc8c40ec3379cd92090231e0d4144e142b9d0783"
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
