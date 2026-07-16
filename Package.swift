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
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.6.2/NeurolabsSDK.xcframework-v1.6.2.zip",
            checksum: "2a5de2afb1ea7612d69e932b4e7cca26ca6ddef898869f49b81c3f1a5500f6fb"
        )
    ]
)
