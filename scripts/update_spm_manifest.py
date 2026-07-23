#!/usr/bin/env python3
from pathlib import Path
import re
import sys


def main() -> int:
    if len(sys.argv) != 4:
        print("Usage: update_spm_manifest.py <Package.swift> <asset-url> <checksum>", file=sys.stderr)
        return 1

    manifest = Path(sys.argv[1])
    asset_url = sys.argv[2]
    checksum = sys.argv[3]

    if not manifest.exists():
        print(f"Manifest not found: {manifest}", file=sys.stderr)
        return 1

    text = manifest.read_text()
    # Scope the url rewrite to the neurolaboratories asset URL so it never
    # clobbers the getsentry SentryShim `.package(url:)` dependency. There are
    # now TWO neurolaboratories binaryTargets (NeurolabsSDK + ProductAuditKit)
    # that share ONE release zip, so rewrite EVERY neurolaboratories url and
    # EVERY checksum to the same values (count=0). checksum: appears only on
    # binaryTargets (the Sentry dep pins via `exact:`, not a checksum).
    updated = re.sub(
        r'url: "https://github\.com/neurolaboratories/[^"]*"',
        f'url: "{asset_url}"',
        text,
    )
    updated = re.sub(r'checksum: ".*?"', f'checksum: "{checksum}"', updated)

    if updated == text:
        print("No changes applied to Package.swift", file=sys.stderr)
        return 1

    manifest.write_text(updated)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
