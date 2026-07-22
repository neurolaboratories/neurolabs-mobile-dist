// swift-tools-version: 5.9
import PackageDescription

// Partner-facing iOS binary package manifest.
// CI updates the binaryTarget url/checksum when a new iOS artifact is
// published to the dist repo release (scripts/update_spm_manifest.py — it
// rewrites ONLY the neurolaboratories asset url + the checksum, so the
// SentryShim below is preserved across releases).
//
// The NLSentryShim target is REQUIRED: the prebuilt NeurolabsSDK.xcframework
// links Sentry DYNAMICALLY (@rpath/Sentry.framework), so a binary SPM consumer
// needs SPM to provide Sentry.framework at the exact version the binary was
// built against, or it crashes at dyld. Do NOT remove it or float the version
// independently of the release the framework was built from.

let package = Package(
    name: "NeurolabsSDKDistribution",
    platforms: [
        .iOS(.v17)
    ],
    products: [
        .library(name: "NeurolabsSDK", targets: ["NeurolabsSDK", "NLSentryShim"])
    ],
    dependencies: [
        .package(url: "https://github.com/getsentry/sentry-cocoa.git", exact: "9.21.0")
    ],
    targets: [
        .binaryTarget(
            name: "NeurolabsSDK",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.6.6/NeurolabsSDK.xcframework-v1.6.6.zip",
            checksum: "76aaa6bd089492b884b2ac46e543ebc161627eb7c40eece827fe7dc31bd8fad2"
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
