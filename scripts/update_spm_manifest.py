#!/usr/bin/env python3
from pathlib import Path
import re
import sys


def stamp_target(text: str, target_name: str, asset_url: str, checksum: str) -> str:
    """Rewrite the url + checksum of ONE .binaryTarget(name: "<target_name>", ...)
    block, matched by name. Each product ships from its own asset (SPM keys the
    binary artifact cache by URL, so binaryTargets must not share a url), so we
    stamp each target individually rather than globally. The getsentry
    SentryShim `.package(url:)` dependency carries no checksum and is not a
    binaryTarget, so it is never touched.
    """
    pattern = re.compile(
        r'(\.binaryTarget\(\s*name:\s*"' + re.escape(target_name) + r'",\s*'
        r'url:\s*")[^"]*(",\s*checksum:\s*")[^"]*(")',
        re.DOTALL,
    )
    new_text, n = pattern.subn(rf'\g<1>{asset_url}\g<2>{checksum}\g<3>', text)
    if n != 1:
        raise SystemExit(
            f"Expected exactly one binaryTarget named {target_name!r}, matched {n}"
        )
    return new_text


def main() -> int:
    args = sys.argv[1:]
    # <Package.swift> <sdk-url> <sdk-checksum> [<pak-url> <pak-checksum>]
    if len(args) not in (3, 5):
        print(
            "Usage: update_spm_manifest.py <Package.swift> <sdk-url> <sdk-checksum> "
            "[<productauditkit-url> <productauditkit-checksum>]",
            file=sys.stderr,
        )
        return 1

    manifest = Path(args[0])
    if not manifest.exists():
        print(f"Manifest not found: {manifest}", file=sys.stderr)
        return 1

    text = manifest.read_text()
    updated = stamp_target(text, "NeurolabsSDK", args[1], args[2])
    if len(args) == 5:
        updated = stamp_target(updated, "ProductAuditKit", args[3], args[4])

    if updated == text:
        print("No changes applied to Package.swift", file=sys.stderr)
        return 1

    manifest.write_text(updated)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
