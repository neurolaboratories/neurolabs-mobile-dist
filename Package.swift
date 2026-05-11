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
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.3.1/NeurolabsSDK.xcframework-v1.3.1.zip",
            checksum: "dcb237e22581e9394176acf56ef04c6cb0a9a140b0af4db0d7aa9eb1c785ee6d"
        )
    ]
)
