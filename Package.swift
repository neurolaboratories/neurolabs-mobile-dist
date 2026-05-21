// swift-tools-version: 5.9
import PackageDescription

// Partner-facing iOS binary package manifest.
// CI updates the url/checksum when a new iOS artifact is published to the dist repo release.

let package = Package(
    name: "NeurolabsSDKDistribution",
    platforms: [
        .iOS(.v17)
    ],
    products: [
        .library(name: "NeurolabsSDK", targets: ["NeurolabsSDK"])
    ],
    targets: [
        .binaryTarget(
            name: "NeurolabsSDK",
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.3.10/NeurolabsSDK.xcframework-v1.3.10.zip",
            checksum: "0eb00f1ac1f9ffbd2c16bc5d6e72070b6e43a7bb4ddb746ad9457627d9cbbae8"
        )
    ]
)
