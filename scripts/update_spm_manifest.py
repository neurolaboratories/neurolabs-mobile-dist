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
    updated = re.sub(r'url: ".*?"', f'url: "{asset_url}"', text, count=1)
    updated = re.sub(r'checksum: ".*?"', f'checksum: "{checksum}"', updated, count=1)

    if updated == text:
        print("No changes applied to Package.swift", file=sys.stderr)
        return 1

    manifest.write_text(updated)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
