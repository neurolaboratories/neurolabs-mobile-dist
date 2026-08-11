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
    # Two calling conventions:
    #   Legacy positional (kept so old workflow revisions replay cleanly):
    #     <Package.swift> <sdk-url> <sdk-checksum> [<pak-url> <pak-checksum>]
    #   Named triples (v1.7.x — arbitrary binaryTargets, e.g. the recognition
    #     stack): <Package.swift> <target-name> <url> <checksum> [...]
    if len(args) < 3:
        print(
            "Usage: update_spm_manifest.py <Package.swift> "
            "(<sdk-url> <sdk-checksum> [<pak-url> <pak-checksum>] | "
            "<target> <url> <checksum> [<target> <url> <checksum> ...])",
            file=sys.stderr,
        )
        return 1

    manifest = Path(args[0])
    if not manifest.exists():
        print(f"Manifest not found: {manifest}", file=sys.stderr)
        return 1

    rest = args[1:]
    # Named mode iff the first value is not a URL (target names never are).
    named_mode = not rest[0].startswith("http")
    triples: list[tuple[str, str, str]] = []
    if named_mode:
        if len(rest) % 3 != 0:
            print("Named mode expects <target> <url> <checksum> triples", file=sys.stderr)
            return 1
        for i in range(0, len(rest), 3):
            triples.append((rest[i], rest[i + 1], rest[i + 2]))
    else:
        if len(rest) not in (2, 4):
            print("Legacy mode expects 2 or 4 positional values", file=sys.stderr)
            return 1
        triples.append(("NeurolabsSDK", rest[0], rest[1]))
        if len(rest) == 4:
            triples.append(("ProductAuditKit", rest[2], rest[3]))

    text = manifest.read_text()
    updated = text
    for target_name, url, checksum in triples:
        updated = stamp_target(updated, target_name, url, checksum)

    if updated == text:
        print("No changes applied to Package.swift", file=sys.stderr)
        return 1

    manifest.write_text(updated)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
