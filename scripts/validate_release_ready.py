#!/usr/bin/env python3
"""Gate for the 3-platform release-readiness check.

A version is "ready" only when all three platform artifacts are present AND
each one is internally consistent:
  - non-empty asset_url and checksum_sha256 (a partial dispatch writes neither),
  - the asset_url embeds the state file's version tag (catches a stale artifact
    left over from an earlier partial run being counted for a newer version).

Presence-only checking previously let stale/partial states (e.g. v1.3.1,
v1.3.5) pass as ready.
"""
from pathlib import Path
import json
import sys


REQUIRED = {"ios", "android", "cordova"}


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: validate_release_ready.py <state-file>", file=sys.stderr)
        return 1

    state_file = Path(sys.argv[1])
    if not state_file.exists():
        print(f"Missing state file: {state_file}", file=sys.stderr)
        return 1

    state = json.loads(state_file.read_text())
    if not isinstance(state, dict):
        print("Release not ready. State file is not a JSON object.", file=sys.stderr)
        return 2

    version = state.get("version")
    if not isinstance(version, str) or not version.strip():
        print("Release not ready. State file has no valid version string.", file=sys.stderr)
        return 2
    version = version.strip()

    artifacts = state.get("artifacts")
    if not isinstance(artifacts, dict):
        print("Release not ready. State file has no valid artifacts dictionary.", file=sys.stderr)
        return 2
    missing = sorted(REQUIRED - set(artifacts.keys()))
    if missing:
        print(f"Release not ready. Missing platforms: {', '.join(missing)}", file=sys.stderr)
        return 2

    problems = []
    for platform in sorted(REQUIRED):
        entry = artifacts.get(platform)
        if not isinstance(entry, dict):
            problems.append(f"{platform}: invalid platform entry (expected an object)")
            continue
        asset_url = (entry.get("asset_url") or "").strip()
        checksum = (entry.get("checksum_sha256") or "").strip()
        if not asset_url:
            problems.append(f"{platform}: empty asset_url")
        if not checksum:
            problems.append(f"{platform}: empty checksum_sha256")
        # Asset URLs embed the tag as a path segment
        # (…/releases/download/<version>/<asset>); matching the full segment
        # avoids prefix collisions (v1.4.3 inside v1.4.30).
        if asset_url and f"/releases/download/{version}/" not in asset_url:
            problems.append(f"{platform}: asset_url does not reference {version} ({asset_url})")

    if problems:
        print("Release not ready:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 2

    print("ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
