// Intentionally (almost) empty. This target exists so the binary
// distribution package resolves sentry-cocoa via SPM: the prebuilt
// NeurolabsSDK.xcframework links Sentry DYNAMICALLY (an
// @rpath/Sentry.framework load command) — without this shim a binary
// SPM consumer gets no Sentry.framework embedded and crashes at dyld.
// The Sentry version pinned in Package.swift MUST match the pin the
// framework was built with (see the iOS SDK Distribution/Package.swift).
