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
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.1.7/NeurolabsSDK.xcframework-v1.1.7.zip",
            checksum: "f2e2a2e6136cba6f196b74b959df8ec7d9f4ab922d34278fd79b906329724989"
        )
    ]
)
