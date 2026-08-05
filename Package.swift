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
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.6.8/NeurolabsSDK.xcframework-v1.6.8.zip",
            checksum: "e07e435f4ec02c77b513f772c58b72773313c44997192c208c5609f39d1f6da2"
        ),
        // Independent asset — its OWN zip, url and checksum. SPM keys the binary
        // artifact cache by URL, so two targets must NOT share one url (they
        // collide). One xcframework product per asset.
        .binaryTarget(
            name: "ProductAuditKit",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.6.8/ProductAuditKit.xcframework-v1.6.8.zip",
            checksum: "9e287a6abfe1671128c13f2c69ef841ebea3df7f2317a082ab1fb0a0ef83e69f"
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
