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
            url: "https://github.com/neurolaboratories/neurolabs-mobile-dist/releases/download/v1.5.0/NeurolabsSDK.xcframework-v1.5.0.zip",
            checksum: "54aefca30296a41da84d8c0cb7a6020ecb4cbccdbe938fe132b4bd18986d7eae"
        )
    ]
)
